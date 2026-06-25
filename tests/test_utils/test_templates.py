"""Tests for the string-template rendering utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from re_agent.utils.templates import render_template, render_template_string


def test_render_template_substitutes(tmp_path: Path) -> None:
    tpl = tmp_path / "greet.md"
    tpl.write_text("Hello $name, welcome to $place.", encoding="utf-8")
    assert render_template(tpl, name="Alain", place="Martinique") == "Hello Alain, welcome to Martinique."


def test_render_template_leaves_unknown_placeholders(tmp_path: Path) -> None:
    tpl = tmp_path / "partial.md"
    tpl.write_text("Known=$known Unknown=$missing", encoding="utf-8")
    # safe_substitute must not raise on unresolved placeholders.
    assert render_template(tpl, known="ok") == "Known=ok Unknown=$missing"


def test_render_template_missing_file_raises_clear_error(tmp_path: Path) -> None:
    """A missing template must raise FileNotFoundError naming the path, not a bare error."""
    missing = tmp_path / "does_not_exist.md"
    with pytest.raises(FileNotFoundError, match=r"Template file not found: .*does_not_exist\.md"):
        render_template(missing)


def test_render_template_unreadable_raises_oserror(tmp_path: Path) -> None:
    """A path that exists but cannot be read as a file surfaces as a clear OSError."""
    # A directory passed where a file is expected raises OSError (IsADirectoryError),
    # which must be wrapped with the offending path rather than propagating raw.
    directory = tmp_path / "subdir"
    directory.mkdir()
    with pytest.raises(OSError, match=r"Could not read template file"):
        render_template(directory)


def test_render_template_string_substitutes() -> None:
    assert render_template_string("$a + $b", a="1", b="2") == "1 + 2"
