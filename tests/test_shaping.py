"""Shaping tests: run with ``python -m pytest tests``.

Each line of a ``tests/cases/*.tsv`` file is

    input <TAB> expected glyph names (space separated) [<TAB> comment]

and is checked against every built font listed in fonts.toml. Lines starting
with ``#`` and blank lines are ignored. Glyph names are those of the upstream
Zbalermorna fonts, which all share one naming scheme.

``corpus.tsv`` has a third column instead of a comment: the same text in the
upstream Private Use Area encoding. That text must shape to the same glyphs,
which checks that the upstream behaviour for PUA input is preserved.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from latmo.shape import glyph_names  # noqa: E402

CASES = ROOT / "tests" / "cases"


def built_fonts() -> list[Path]:
    with open(ROOT / "fonts.toml", "rb") as f:
        cfg = tomllib.load(f)["font"]
    paths = []
    for font in cfg:
        stem = f"{font['family'].replace(' ', '')}-{font['style'].replace(' ', '')}"
        paths.append(ROOT / "fonts" / f"{stem}.otf")
    return paths


def load(name: str) -> list[tuple[str, list[str], str]]:
    rows = []
    if not (CASES / name).exists():
        return rows
    for lineno, line in enumerate((CASES / name).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t")
        rows.append((parts[0], parts[1].split(), parts[2] if len(parts) > 2 else f"{name}:{lineno}"))
    return rows


FONTS = built_fonts()


@pytest.fixture(params=FONTS, ids=[p.stem for p in FONTS])
def font(request) -> Path:
    if not request.param.exists():
        pytest.fail(f"{request.param} is not built; run python -m latmo.build")
    return request.param


@pytest.mark.parametrize("text,expected,note", load("manual.tsv"),
                         ids=lambda v: v if isinstance(v, str) else None)
def test_manual(font, text, expected, note):
    assert glyph_names(font, text) == expected, note


def test_corpus_latin(font):
    if not load("corpus.tsv"):
        pytest.skip("no corpus")
    failures = []
    for text, expected, _ in load("corpus.tsv"):
        got = glyph_names(font, text)
        if got != expected:
            failures.append(f"{text}\n  expected {' '.join(expected)}\n  got      {' '.join(got)}")
    assert not failures, f"{len(failures)} mismatches:\n" + "\n".join(failures[:40])


def test_corpus_pua(font):
    if not load("corpus.tsv"):
        pytest.skip("no corpus")
    failures = []
    for text, expected, pua in load("corpus.tsv"):
        got = glyph_names(font, pua)
        if got != expected:
            failures.append(f"{text} (PUA)\n  expected {' '.join(expected)}\n  got      {' '.join(got)}")
    assert not failures, f"{len(failures)} mismatches:\n" + "\n".join(failures[:40])


def test_rlig_cannot_be_disabled(font):
    """Turning off every discretionary ligature feature changes nothing."""
    off = {tag: False for tag in ("liga", "clig", "dlig", "hlig", "calt")}
    for text in (".i mi klama le zarci", "la .djan. .e'u", ".uai coi"):
        assert glyph_names(font, text, off) == glyph_names(font, text)
