"""Tests for semantic rule matching robustness against invalid regex."""

from __future__ import annotations

import pytest

from re_agent.core.models import HookEntry, SemanticRule
from re_agent.parity.rules import (
    _match_pattern,
    apply_semantic_rules,
    rule_matches_entry,
)


def _entry() -> HookEntry:
    return HookEntry(
        class_path="CTrain",
        fn_name="Go",
        address="0x1000",
        reversed=True,
        locked=False,
        is_virtual=False,
    )


def test_literal_pattern_substring() -> None:
    assert _match_pattern("hello world", "world") is True
    assert _match_pattern("hello world", "nope") is False


def test_valid_regex_pattern() -> None:
    assert _match_pattern("call foo()", "re:foo\\(\\)") is True
    assert _match_pattern("call foo()", "re:^bar") is False


def test_invalid_regex_does_not_raise(capsys: pytest.CaptureFixture[str]) -> None:
    """An unterminated character class used to raise re.error and abort the run."""
    assert _match_pattern("anything", "re:[unterminated") is False
    err = capsys.readouterr().err
    assert "invalid semantic rule regex" in err


def test_rule_matches_entry_survives_bad_symbol_regex() -> None:
    rule = SemanticRule(
        id="r1",
        reason="x",
        severity="red",
        addresses=[],
        symbols=["re:(unbalanced"],
        source_all_of=[],
        source_any_of=[],
        source_none_of=[],
    )
    # Must not raise; the bad pattern simply fails to match.
    assert rule_matches_entry(rule, _entry()) is False


def test_apply_semantic_rules_survives_bad_source_regex() -> None:
    rule = SemanticRule(
        id="r2",
        reason="bad pattern",
        severity="yellow",
        addresses=[],
        symbols=[],
        source_all_of=["re:*invalid"],
        source_any_of=[],
        source_none_of=[],
    )
    # source_all_of with a non-matching (invalid) pattern -> finding emitted,
    # but crucially no exception escapes.
    findings = apply_semantic_rules(_entry(), "some source body", [rule])
    assert len(findings) == 1
    assert findings[0].level == "yellow"
