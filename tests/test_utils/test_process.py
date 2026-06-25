"""Tests for subprocess execution utilities."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

from re_agent.utils.process import run_cmd, run_cmd_split


def test_run_cmd_success() -> None:
    ok, out = run_cmd(["true"])
    assert ok is True
    assert out == ""


def test_run_cmd_nonzero_exit() -> None:
    ok, _out = run_cmd(["false"])
    assert ok is False


def test_run_cmd_missing_executable() -> None:
    ok, out = run_cmd(["definitely-not-a-real-binary-xyz"])
    assert ok is False
    assert "Command not found" in out


def test_run_cmd_timeout() -> None:
    ok, out = run_cmd(["sleep", "5"], timeout_s=1)
    assert ok is False
    assert "TIMEOUT" in out


def test_run_cmd_permission_error_does_not_crash() -> None:
    """A non-executable cli_path raises PermissionError (an OSError); the
    wrapper must report it cleanly instead of letting it propagate."""
    with patch("re_agent.utils.process.subprocess.run", side_effect=PermissionError(13, "Permission denied")):
        ok, out = run_cmd(["./not-executable"])
    assert ok is False
    assert "Could not run" in out
    assert "./not-executable" in out


def test_run_cmd_oserror_does_not_crash() -> None:
    """Other OSErrors (e.g. 'Exec format error') are caught, not raised."""
    with patch("re_agent.utils.process.subprocess.run", side_effect=OSError(8, "Exec format error")):
        ok, out = run_cmd(["./corrupt-binary"])
    assert ok is False
    assert "Could not run" in out


def test_run_cmd_split_success() -> None:
    rc, out, err = run_cmd_split(["true"])
    assert rc == 0
    assert out == ""
    assert err == ""


def test_run_cmd_split_missing_executable() -> None:
    rc, _out, err = run_cmd_split(["definitely-not-a-real-binary-xyz"])
    assert rc == -1
    assert "Command not found" in err


def test_run_cmd_split_timeout() -> None:
    rc, _out, err = run_cmd_split(["sleep", "5"], timeout_s=1)
    assert rc == -1
    assert "TIMEOUT" in err


def test_run_cmd_split_permission_error_does_not_crash() -> None:
    with patch("re_agent.utils.process.subprocess.run", side_effect=PermissionError(13, "Permission denied")):
        rc, _out, err = run_cmd_split(["./not-executable"])
    assert rc == -1
    assert "Could not run" in err
    assert "./not-executable" in err


def test_run_cmd_split_oserror_does_not_crash() -> None:
    with patch("re_agent.utils.process.subprocess.run", side_effect=OSError(8, "Exec format error")):
        rc, _out, err = run_cmd_split(["./corrupt-binary"])
    assert rc == -1
    assert "Could not run" in err


def test_timeout_expired_still_handled_separately() -> None:
    """TimeoutExpired must keep its dedicated message, not fall into OSError."""
    with patch(
        "re_agent.utils.process.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="x", timeout=1),
    ):
        ok, out = run_cmd(["x"], timeout_s=1)
    assert ok is False
    assert "TIMEOUT" in out
