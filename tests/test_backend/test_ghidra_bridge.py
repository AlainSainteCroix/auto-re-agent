"""Tests for backend protocol and stub backend."""

from __future__ import annotations

import os
from unittest.mock import patch

from re_agent.backend.ghidra_bridge import GhidraBridgeBackend
from re_agent.backend.protocol import BackendCapabilities, REBackend
from re_agent.backend.stub import StubBackend
from re_agent.core.models import FunctionEntry


def test_stub_backend_capabilities() -> None:
    backend = StubBackend()
    caps = backend.capabilities
    assert caps.has_decompile
    assert isinstance(caps, BackendCapabilities)


def test_stub_backend_decompile() -> None:
    backend = StubBackend()
    result = backend.decompile("0x6F86A0")
    assert result.address == "0x6F86A0"
    assert len(result.decompiled) > 0


def test_stub_backend_remaining() -> None:
    entries = [
        FunctionEntry(address="0x100", name="Foo", class_name="CTest", caller_count=5),
    ]
    backend = StubBackend(remaining_functions=entries)
    result = backend.remaining("CTest")
    assert len(result) == 1
    assert result[0].name == "Foo"


def test_stub_backend_is_re_backend() -> None:
    backend = StubBackend()
    assert isinstance(backend, REBackend)


# -- Capability probing tests -------------------------------------------------


def test_subcmd_exists_exit_zero() -> None:
    """Exit code 0 means the sub-command is available."""
    backend = GhidraBridgeBackend(cli_path="fake-ghidra")
    with patch("re_agent.backend.ghidra_bridge.run_cmd_split") as mock:
        mock.return_value = (0, "help text", "")
        assert backend._subcmd_exists("asm") is True
        mock.assert_called_once()


def test_subcmd_exists_unknown_command_in_stderr() -> None:
    """'unknown command' in stderr means the sub-command does NOT exist."""
    backend = GhidraBridgeBackend(cli_path="fake-ghidra")
    with patch("re_agent.backend.ghidra_bridge.run_cmd_split") as mock:
        mock.return_value = (1, "", "Error: unknown command 'asm'")
        assert backend._subcmd_exists("asm") is False


def test_subcmd_exists_nonzero_no_unknown_pattern() -> None:
    """Non-zero exit with no 'unknown command' pattern means available."""
    backend = GhidraBridgeBackend(cli_path="fake-ghidra")
    with patch("re_agent.backend.ghidra_bridge.run_cmd_split") as mock:
        # First call: --help returns non-zero with generic error
        # Second call: __probe__ also returns non-zero with generic error
        mock.side_effect = [
            (1, "", "Error: missing required argument"),
            (1, "", "Error: missing required argument"),
        ]
        assert backend._subcmd_exists("asm") is True


def test_subcmd_exists_unrecognized_args_not_false_negative() -> None:
    """'unrecognized arguments' should NOT cause false negatives."""
    backend = GhidraBridgeBackend(cli_path="fake-ghidra")
    with patch("re_agent.backend.ghidra_bridge.run_cmd_split") as mock:
        # --help returns non-zero with "unrecognized arguments"
        # This should NOT be treated as "unknown command"
        mock.side_effect = [
            (1, "", "error: unrecognized arguments: --help"),
            (1, "", "error: missing operand"),
        ]
        assert backend._subcmd_exists("asm") is True


# -- get_asm tests ------------------------------------------------------------


def test_get_asm_reads_output_file() -> None:
    """``dump-asm`` writes to a file; get_asm must read it back and parse it."""
    asm_text = "0x100 PUSH RBP\n0x101 CALL foo\n0x106 CALL bar\n0x10b RET\n"

    def fake_run_cmd(args, timeout_s):  # type: ignore[no-untyped-def]
        # Contract: ghidra-bridge dump-asm <target> <output_path>
        assert args[1] == "dump-asm"
        out_path = args[-1]
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(asm_text)
        return (True, "")

    backend = GhidraBridgeBackend(cli_path="fake-ghidra")
    with patch("re_agent.backend.ghidra_bridge.run_cmd", side_effect=fake_run_cmd):
        result = backend.get_asm("0x100")

    assert result is not None
    assert result.address == "0x100"
    assert result.instruction_count == 4
    assert result.call_count == 2
    assert result.instructions == asm_text


def test_get_asm_returns_none_on_cli_failure() -> None:
    """A non-zero CLI exit yields None (and leaves no temp file behind)."""
    backend = GhidraBridgeBackend(cli_path="fake-ghidra")
    with patch("re_agent.backend.ghidra_bridge.run_cmd", return_value=(False, "boom")):
        assert backend.get_asm("0x100") is None


def test_get_asm_tolerates_non_utf8_bytes() -> None:
    """A disassembly dump with stray non-UTF-8 bytes must not raise."""

    def fake_run_cmd(args, timeout_s):  # type: ignore[no-untyped-def]
        out_path = args[-1]
        # Write raw bytes including an invalid UTF-8 sequence (0xff).
        with open(out_path, "wb") as fh:
            fh.write(b"0x100 MOV RAX, \xff\xfe junk\n0x108 CALL foo\n")
        return (True, "")

    backend = GhidraBridgeBackend(cli_path="fake-ghidra")
    with patch("re_agent.backend.ghidra_bridge.run_cmd", side_effect=fake_run_cmd):
        result = backend.get_asm("0x100")

    assert result is not None
    assert result.instruction_count == 2
    assert result.call_count == 1


def test_get_asm_returns_none_on_empty_output() -> None:
    """CLI exits 0 but writes nothing to disassemble -> None."""

    def fake_run_cmd(args, timeout_s):  # type: ignore[no-untyped-def]
        out_path = args[-1]
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write("   \n")
        return (True, "")

    backend = GhidraBridgeBackend(cli_path="fake-ghidra")
    with patch("re_agent.backend.ghidra_bridge.run_cmd", side_effect=fake_run_cmd):
        assert backend.get_asm("0x100") is None


def test_get_asm_returns_none_when_output_unreadable() -> None:
    """CLI succeeds but the output file is gone/unreadable -> None (no raise)."""

    def fake_run_cmd(args, timeout_s):  # type: ignore[no-untyped-def]
        # Remove the temp file the caller created, so read-back fails.
        out_path = args[-1]
        os.unlink(out_path)
        return (True, "")

    backend = GhidraBridgeBackend(cli_path="fake-ghidra")
    with patch("re_agent.backend.ghidra_bridge.run_cmd", side_effect=fake_run_cmd):
        assert backend.get_asm("0x100") is None


def test_capabilities_probe_uses_dump_asm() -> None:
    """has_asm must be driven by the real ``dump-asm`` sub-command."""
    backend = GhidraBridgeBackend(cli_path="fake-ghidra")
    probed: list[str] = []

    def fake_subcmd_exists(subcmd: str) -> bool:
        probed.append(subcmd)
        return True

    with patch.object(backend, "_subcmd_exists", side_effect=fake_subcmd_exists):
        caps = backend.capabilities

    assert "dump-asm" in probed
    assert "asm" not in probed
    assert caps.has_asm is True
