"""Shaping tests: run with ``python -m pytest tests``.

Each line of a ``tests/cases/*.tsv`` file is

    input <TAB> expected glyph names (space separated) [<TAB> comment]

Lines starting with ``#`` and blank lines are skipped. In ``corpus*.tsv``
files the third column is the same text in the upstream Private Use Area
encoding instead of a comment.

The expected glyph names are those of Crisa, so they are checked only on the
fonts marked ``reference`` in fonts.toml. Upstream fonts differ in their own
lookups (final forms, ligatures, the attitudinal shorthand), so every font is
checked against its own upstream font instead: each corpus line in Latin must
shape like the same text in the PUA encoding does in the original font.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

import pytest
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from latmo.shape import glyph_names, shape  # noqa: E402

CASES = ROOT / "tests" / "cases"


def config() -> list[dict]:
    with open(ROOT / "fonts.toml", "rb") as f:
        return tomllib.load(f)["font"]


def built(cfg: dict) -> Path:
    stem = f"{cfg['family'].replace(' ', '')}-{cfg['style'].replace(' ', '')}"
    return ROOT / "fonts" / f"{stem}.otf"


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


CONFIG = config()
REFERENCE = [c for c in CONFIG if c.get("reference")]
CORPORA = sorted(p.name for p in CASES.glob("corpus*.tsv"))


def font_fixture(cfgs):
    @pytest.fixture(params=cfgs, ids=[c["id"] for c in cfgs])
    def fixture(request) -> dict:
        if not built(request.param).exists():
            pytest.fail(f"{built(request.param)} is not built; run python -m latmo.build")
        return request.param
    return fixture


reference_font = font_fixture(REFERENCE)
any_font = font_fixture(CONFIG)


# Exact glyph names, on the reference fonts.

@pytest.mark.parametrize("text,expected,note", load("manual.tsv"),
                         ids=lambda v: v if isinstance(v, str) else None)
def test_manual(reference_font, text, expected, note):
    assert glyph_names(built(reference_font), text) == expected, note


@pytest.mark.parametrize("corpus", CORPORA)
def test_corpus_latin(reference_font, corpus):
    font = built(reference_font)
    failures = []
    for text, expected, _ in load(corpus):
        got = glyph_names(font, text)
        if got != expected:
            failures.append(f"{text}\n  expected {' '.join(expected)}\n  got      {' '.join(got)}")
    assert not failures, f"{len(failures)} mismatches:\n" + "\n".join(failures[:40])


@pytest.mark.parametrize("corpus", CORPORA)
def test_corpus_pua(reference_font, corpus):
    font = built(reference_font)
    failures = []
    for text, expected, pua in load(corpus):
        got = glyph_names(font, pua)
        if got != expected:
            failures.append(f"{text} (PUA)\n  expected {' '.join(expected)}\n  got      {' '.join(got)}")
    assert not failures, f"{len(failures)} mismatches:\n" + "\n".join(failures[:40])


# Every font, against its upstream font.

# Diphthongs written as two vowels in the PUA encoding, and their composed
# code points. Some upstream fonts (Fira Code ZLM) only render the composed
# ones, which is what their input methods send.
COMPOSE = {
    "": "", "": "", "": "", "": "",
    "": "", "": "", "": "", "": "",
}


def compose(pua: str) -> str:
    for pair, single in COMPOSE.items():
        pua = pua.replace(pair, single)
    return pua


@pytest.mark.parametrize("corpus", CORPORA)
def test_matches_upstream(any_font, corpus):
    font, upstream = built(any_font), ROOT / any_font["source"]
    failures = []
    for text, _, pua in load(corpus):
        got, want = shape(font, text), shape(upstream, compose(pua))
        if got != want:
            failures.append(f"{text}\n  upstream {want}\n  got      {got}")
    assert not failures, f"{len(failures)} mismatches:\n" + "\n".join(failures[:40])


# Characters a font may leave to the browser's next font: the optional
# punctuation and digits, which the fonts without a Latin companion lack.
OPTIONAL = set("0123456789-–—…/\\*+=@_|^`•·‚„")


def test_manual_leaves_no_input_glyphs(any_font):
    """No Latin input glyph survives shaping the manual cases, and every
    character the font covers gets a real glyph. Only OPTIONAL characters
    may be missing from the font."""
    font = built(any_font)
    covered = TTFont(font).getBestCmap()
    left = {}
    for text, _, _ in load("manual.tsv"):
        missing = {c for c in text if ord(c) not in covered} - {" "}
        assert missing <= OPTIONAL, (text, missing)
        text = "".join(c for c in text if c not in missing)
        stray = [g for g in glyph_names(font, text) if g.startswith("lat.") or g == ".notdef"]
        if stray:
            left[text] = stray
    assert not left


# Strings with no Lojban letters: where the upstream font covers them, the
# built font must shape them the same way (Fira Code ZLM's own Latin and its
# programming ligatures, for example).
PUNCTUATION_SAMPLES = ["-->", "--", "<!-- -->", "|- -|", "==", "!=", "<=", ">=",
                       "( ) [ ] { }", "1234567890", "1 + 2 = 3", "#$%&", "\"\" (?)", "?!"]


def test_punctuation_matches_upstream(any_font):
    font, upstream = built(any_font), ROOT / any_font["source"]
    cmap = TTFont(upstream).getBestCmap()
    for text in PUNCTUATION_SAMPLES:
        if all(ord(c) in cmap for c in text):
            assert shape(font, text) == shape(upstream, text), text


def test_rlig_cannot_be_disabled(any_font):
    """Turning off every discretionary ligature feature changes nothing."""
    font = built(any_font)
    off = {tag: False for tag in ("liga", "clig", "dlig", "hlig", "calt")}
    for text in (".i mi klama le zarci", "la .djan. .e'u", ".uai coi"):
        assert glyph_names(font, text, off) == glyph_names(font, text)
