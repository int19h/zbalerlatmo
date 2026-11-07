"""Build-level tests: metrics and metadata of the built fonts, and a smoke
test that the generator works on every upstream font."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from latmo.build import build_font, load_config  # noqa: E402
from latmo.shape import glyph_names  # noqa: E402

CONFIG = load_config()


def built(cfg: dict) -> Path:
    return ROOT / "fonts" / f"{cfg['family'].replace(' ', '')}-{cfg['style'].replace(' ', '')}.otf"


@pytest.mark.parametrize("cfg", CONFIG, ids=[c["id"] for c in CONFIG])
def test_added_glyph_metrics(cfg):
    """Every glyph the build adds has hmtx lsb equal to its outline's xMin."""
    font = TTFont(built(cfg))
    upstream = set(TTFont(ROOT / cfg["source"]).getGlyphOrder())
    glyphs = font.getGlyphSet()
    wrong = []
    for name in font.getGlyphOrder():
        if name in upstream:
            continue
        pen = BoundsPen(glyphs)
        glyphs[name].draw(pen)
        if pen.bounds is not None and round(pen.bounds[0]) != font["hmtx"][name][1]:
            wrong.append(name)
    assert not wrong


@pytest.mark.parametrize("cfg", CONFIG, ids=[c["id"] for c in CONFIG])
def test_names(cfg):
    font = TTFont(built(cfg))
    name = font["name"]
    assert name.getDebugName(1) == cfg["family"]
    assert name.getDebugName(5) == f"Version {cfg['version']}; latmo"
    assert font["CFF "].cff.fontNames == [f"{cfg['family'].replace(' ', '')}-{cfg['style']}"]
    bold = "Bold" in cfg["style"]
    assert bool(font["OS/2"].fsSelection & (1 << 5)) == bold
    assert bool(font["head"].macStyle & 1) == bold


UPSTREAM = sorted((ROOT / "zbalermorna" / "fonts").glob("*.otf"))

# The same text in Latin and in the upstream PUA encoding.
SMOKE_LATIN = "la .djan. .e'u COI .uai ko'a"
SMOKE_PUA = ("\ued84\ueda0 \ued89\ued91\ued96\uedb0\ued97\ued89 "
             "\ued89\ueda1\ued8a\ueda4 \ued86\ueda8\ued98 \ued89\uedab\ueda6 \ued82\ueda3\ued8a\ueda0")


def pua_feature(source: Path) -> str:
    """The upstream feature holding the Zbalermorna lookups."""
    tags = {fr.FeatureTag for fr in TTFont(source)["GSUB"].table.FeatureList.FeatureRecord}
    return "liga" if "liga" in tags else "calt"


@pytest.mark.parametrize("source", UPSTREAM, ids=[p.stem for p in UPSTREAM])
def test_every_upstream_font_builds(source, tmp_path):
    """The generator works on all upstream fonts, not only the configured ones:
    Latin input shapes exactly as the same text in the PUA encoding does in
    the original upstream font. Lato stands in for each Latin companion."""
    cfg = {"id": source.stem, "source": str(source.relative_to(ROOT)),
           "latin": "vendor/lato/Lato-Regular.ttf", "family": "Smoke Test",
           "style": "Regular", "pua_feature": pua_feature(source), "version": "0.1"}
    otf = build_font(cfg, out_dir=tmp_path)[0]
    assert glyph_names(otf, SMOKE_LATIN) == glyph_names(source, SMOKE_PUA)
