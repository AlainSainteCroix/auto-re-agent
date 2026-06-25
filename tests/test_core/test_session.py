"""Tests for JSON-backed Session persistence robustness."""

from __future__ import annotations

from pathlib import Path

from re_agent.core.session import Session


def test_load_valid_file_roundtrips(tmp_path: Path) -> None:
    p = tmp_path / "progress.json"
    p.write_text('{"functions": {"005e3e90": {"success": true}}, "runs": []}')
    s = Session(p)
    assert s.is_completed("0x5e3e90") is True
    assert s.is_attempted("0x5e3e90") is True


def test_load_malformed_json_falls_back_to_empty(tmp_path: Path) -> None:
    p = tmp_path / "progress.json"
    p.write_text("{ this is not json")
    s = Session(p)
    assert s.get_summary()["total_functions"] == 0


def test_load_toplevel_list_falls_back_to_empty(tmp_path: Path) -> None:
    """A parseable-but-wrong-shape file (a list) must not crash later access."""
    p = tmp_path / "progress.json"
    p.write_text("[1, 2, 3]")
    s = Session(p)
    # Would raise AttributeError on .values() without the structure guard.
    assert s.get_summary()["total_functions"] == 0
    assert s.is_completed("0x1") is False


def test_load_missing_functions_key_falls_back(tmp_path: Path) -> None:
    p = tmp_path / "progress.json"
    p.write_text('{"runs": []}')
    s = Session(p)
    assert s.is_attempted("0x1") is False
    assert s.get_all_functions() == []


def test_load_wrong_typed_functions_falls_back(tmp_path: Path) -> None:
    """``functions`` as a list (not a dict) must not crash .get()."""
    p = tmp_path / "progress.json"
    p.write_text('{"functions": ["a", "b"], "runs": "nope"}')
    s = Session(p)
    assert s.is_completed("0x1") is False
    assert s.get_summary()["total_functions"] == 0


def test_load_preserves_valid_functions_drops_bad_runs(tmp_path: Path) -> None:
    p = tmp_path / "progress.json"
    p.write_text('{"functions": {"005e3e90": {"success": true}}, "runs": 42}')
    s = Session(p)
    assert s.is_completed("0x5e3e90") is True
    # runs was an int -> coerced to empty list, no crash.
    assert s.get_all_functions()[0]["success"] is True
