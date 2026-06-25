"""Tests for read_hooks CSV parsing robustness."""

from __future__ import annotations

from pathlib import Path

from re_agent.parity.engine import read_hooks


def _write(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "hooks.csv"
    p.write_text(text, encoding="utf-8")
    return p


def test_numeric_bool_columns(tmp_path: Path) -> None:
    p = _write(
        tmp_path,
        "class,fn_name,address,reversed,locked,is_virtual\nCTrain,Go,0x1000,1,0,1\n",
    )
    hooks = read_hooks(p)
    assert len(hooks) == 1
    h = hooks[0]
    assert h.reversed is True
    assert h.locked is False
    assert h.is_virtual is True


def test_empty_bool_cells_use_defaults_not_crash(tmp_path: Path) -> None:
    """Empty cells fed to int() used to raise ValueError; now they default."""
    p = _write(
        tmp_path,
        "class,fn_name,address,reversed,locked,is_virtual\nCTrain,Go,0x1000,,,\n",
    )
    hooks = read_hooks(p)
    assert len(hooks) == 1
    # reversed defaults to True, locked/is_virtual default to False.
    assert hooks[0].reversed is True
    assert hooks[0].locked is False
    assert hooks[0].is_virtual is False


def test_word_bool_cells(tmp_path: Path) -> None:
    p = _write(
        tmp_path,
        "class,fn_name,address,reversed,locked,is_virtual\nCTrain,Go,0x1000,true,no,YES\n",
    )
    hooks = read_hooks(p)
    assert hooks[0].reversed is True
    assert hooks[0].locked is False
    assert hooks[0].is_virtual is True


def test_garbage_bool_cells_fall_back_to_default(tmp_path: Path) -> None:
    p = _write(
        tmp_path,
        "class,fn_name,address,reversed,locked,is_virtual\nCTrain,Go,0x1000,maybe,??,N/A\n",
    )
    hooks = read_hooks(p)
    assert hooks[0].reversed is True
    assert hooks[0].locked is False
    assert hooks[0].is_virtual is False


def test_short_row_missing_trailing_cells_does_not_crash(tmp_path: Path) -> None:
    """A row shorter than the header yields None for trailing fields
    (csv.DictReader restval); int(None) would have raised TypeError."""
    p = _write(
        tmp_path,
        "class,fn_name,address,reversed,locked,is_virtual\nCTrain,Go,0x1000,1\n",
    )
    hooks = read_hooks(p)
    assert len(hooks) == 1
    assert hooks[0].reversed is True
    assert hooks[0].locked is False
    assert hooks[0].is_virtual is False


def test_unreversed_word_is_filtered_out(tmp_path: Path) -> None:
    """reversed=false (word) must be honoured: filtered unless included."""
    p = _write(
        tmp_path,
        "class,fn_name,address,reversed\nCTrain,Go,0x1000,false\n",
    )
    assert read_hooks(p) == []
    assert len(read_hooks(p, include_unreversed=True)) == 1


def test_invalid_address_still_skipped(tmp_path: Path) -> None:
    p = _write(
        tmp_path,
        "class,fn_name,address,reversed\nCTrain,Bad,notanaddr,1\nCTrain,Good,0x2000,1\n",
    )
    hooks = read_hooks(p)
    assert len(hooks) == 1
    assert hooks[0].address == "0x2000"
