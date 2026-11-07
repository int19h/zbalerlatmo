"""Build Latin-input Zbalermorna fonts from the upstream fonts.

Usage: python -m latmo.build [FONT_ID ...]

Fonts are configured in fonts.toml. For each font this:

1. loads the upstream OTF from zbalermorna/fonts/;
2. adds Latin punctuation the upstream font lacks, taken from the configured
   Latin companion font (the one the upstream design was derived from);
3. adds the ``lat.*`` input glyphs (see latmo/features.py) and maps Latin
   characters to them; input glyphs carry Latin outlines, so text still reads
   as Latin Lojban where no shaping happens;
4. compiles the generated lookups and merges them ahead of the font's own
   lookups in the ``rlig`` feature, which applications cannot switch off;
5. renames the font and writes OTF and WOFF2 to fonts/.
"""

from __future__ import annotations

import copy
import statistics
import sys
import tomllib
from pathlib import Path

from fontTools.feaLib.builder import Builder
from fontTools.feaLib.parser import Parser
from fontTools.misc.transform import Transform
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import otTables
import io

from . import features

ROOT = Path(__file__).resolve().parent.parent

# Latin punctuation and symbols to copy from the companion font when the
# upstream font lacks them, as (glyph name, code points).
PUNCTUATION = [
    ("comma", [0x2C]),
    ("quotesingle", []),        # reached via the apostrophe logic only
    ("quoteright", []),         # likewise
    ("quoteleft", [0x2018]),
    ("quotedblleft", [0x201C]),
    ("quotedblright", [0x201D]),
    ("quotesinglbase", [0x201A]),
    ("quotedblbase", [0x201E]),
    ("hyphen", [0x2D, 0x2010]),
    ("endash", [0x2013]),
    ("emdash", [0x2014]),
    ("ellipsis", [0x2026]),
    ("slash", [0x2F]),
    ("backslash", [0x5C]),
    ("asterisk", [0x2A]),
    ("plus", [0x2B]),
    ("equal", [0x3D]),
    ("at", [0x40]),
    ("underscore", [0x5F]),
    ("bar", [0x7C]),
    ("asciicircum", [0x5E]),
    ("grave", [0x60]),
    ("bullet", [0x2022]),
    ("periodcentered", [0xB7]),
    ("zero", [0x30]), ("one", [0x31]), ("two", [0x32]), ("three", [0x33]),
    ("four", [0x34]), ("five", [0x35]), ("six", [0x36]), ("seven", [0x37]),
    ("eight", [0x38]), ("nine", [0x39]),
]

# Code points used to source the Latin fallback outline of each input glyph.
STRESSED = {  # vowel -> code points that mean "stressed vowel"
    "a": [0xE1, 0xE0, 0xC1, 0xC0, 0x41],
    "e": [0xE9, 0xE8, 0xC9, 0xC8, 0x45],
    "i": [0xED, 0xEC, 0xCD, 0xCC, 0x49],
    "o": [0xF3, 0xF2, 0xD3, 0xD2, 0x4F],
    "u": [0xFA, 0xF9, 0xDA, 0xD9, 0x55],
    "y": [0xFD, 0x1EF3, 0xDD, 0x1EF2, 0x59],
}


def input_cmap() -> dict[str, list[int]]:
    """Input glyph -> code points mapped to it. The first is the outline source."""
    m: dict[str, list[int]] = {}
    for c in features.CONSONANTS:
        m[features.lat(c)] = [ord(c), ord(c.upper())]
    for v in features.VOWELS:
        m[features.lat(v)] = [ord(v)]
        m[features.lat(v) + ".str"] = STRESSED[v]
    m[features.lat("stress")] = [0x301, 0x300]
    m[features.lat("tilde")] = [0x7E]
    m[features.lat("period")] = [0x2E]
    m[features.lat("comma")] = [0x2C]
    m[features.lat("h")] = [ord("h"), ord("H")]
    m[features.lat("quotesingle")] = [0x27]
    m[features.lat("quoteright")] = [0x2019]
    return m


# Upstream glyphs the generated lookups emit; their absence is an error.
def required_upstream() -> list[str]:
    f = features
    names = list(f.RADICAL.values()) + list(f.VOWEL_MARK.values())
    names += list(f.VOWEL_FULL.values()) + list(f.GLIDE.values())
    names += [f.PERIOD, f.APOSTROPHE, f.SEPARATOR, f.STRESS, f.STRETCH]
    return names


class Font:
    def __init__(self, path: Path):
        self.tt = TTFont(path)
        self.cff = self.tt["CFF "].cff
        self.top = self.cff.topDictIndex[0]
        self.order = list(self.tt.getGlyphOrder())

    def has(self, name: str) -> bool:
        return name in self.top.CharStrings

    def add_glyph(self, name: str, width: int, draw=None) -> None:
        """Add a glyph; ``draw(pen)`` draws its outline (none if omitted)."""
        if self.has(name):
            raise ValueError(f"glyph {name} already exists")
        private = self.top.Private
        pen = T2CharStringPen(width - private.nominalWidthX, None)
        if draw is not None:
            draw(pen)
        cs = pen.getCharString(private=private, globalSubrs=self.cff.GlobalSubrs)
        strings = self.top.CharStrings
        if strings.charStringsAreIndexed:
            strings.charStrings[name] = len(strings.charStringsIndex)
            strings.charStringsIndex.append(cs)
        else:
            strings.charStrings[name] = cs
        self.order.append(name)
        self.top.charset = self.order
        self.tt.setGlyphOrder(self.order)
        # lsb is recomputed from the outline on save.
        self.tt["hmtx"].metrics[name] = (width, 0)

    def map(self, codepoint: int, name: str) -> None:
        for table in self.tt["cmap"].tables:
            if table.isUnicode() or (table.platformID, table.platEncID) == (3, 1):
                if table.format in (4, 12) and (codepoint <= 0xFFFF or table.format == 12):
                    table.cmap[codepoint] = name


class LatinSource:
    """The Latin companion font, scaled to the upstream design."""

    def __init__(self, path: Path, target: Font):
        self.tt = TTFont(path)
        self.glyphs = self.tt.getGlyphSet()
        self.cmap = self.tt.getBestCmap()
        self.scale = self._fit_scale(target)

    def _fit_scale(self, target: Font) -> float:
        # Upstream fonts copied the companion's punctuation; match advances.
        upm = self.tt["head"].unitsPerEm
        tgt_upm = target.tt["head"].unitsPerEm
        ratios = []
        tmet = target.tt["hmtx"].metrics
        for name in ("exclam", "question", "parenleft", "parenright",
                     "colon", "semicolon", "bracketleft", "bracketright"):
            if name in tmet and name in self.glyphs:
                src = self.glyphs[name].width * tgt_upm / upm
                if src:
                    ratios.append(tmet[name][0] / src)
        base = tgt_upm / upm
        return base * (statistics.median(ratios) if ratios else 1.0)

    def glyph_for(self, codepoint: int):
        name = self.cmap.get(codepoint)
        return None if name is None else self.glyphs[name]

    def copy_into(self, font: Font, name: str, glyph) -> None:
        transform = Transform().scale(self.scale)
        width = round(glyph.width * self.scale)

        recording = DecomposingRecordingPen(self.glyphs)
        glyph.draw(recording)

        def draw(pen):
            recording.replay(TransformPen(pen, transform))

        font.add_glyph(name, width, draw)


def compile_generated(font: Font) -> tuple[otTables.GSUB, list[int]]:
    """Compile the generated lookups. Returns the GSUB and the indices of the
    lookups to register, in order."""
    fea = features.generate()
    doc = Parser(io.StringIO(fea), glyphNames=set(font.order)).parse()
    builder = Builder(font.tt, doc)
    saved = font.tt.get("GSUB")
    if "GSUB" in font.tt:
        del font.tt["GSUB"]
    builder.build(tables=["GSUB"])
    gsub = font.tt["GSUB"].table
    if saved is not None:
        font.tt["GSUB"] = saved
    else:
        del font.tt["GSUB"]
    named = builder.named_lookups_
    order = [named[name].lookup_index for name in features.LOOKUP_ORDER]
    return gsub, order


def _shift_lookup_refs(lookup, offset: int) -> None:
    for st in lookup.SubTable:
        if lookup.LookupType == 7:
            st = st.ExtSubTable
        for attr in ("SubstLookupRecord",):
            for rec in getattr(st, attr, None) or []:
                rec.LookupListIndex += offset
        for setattr_ in ("SubRuleSet", "SubClassSet", "ChainSubRuleSet", "ChainSubClassSet"):
            for s in getattr(st, setattr_, None) or []:
                if s is None:
                    continue
                for rule in (getattr(s, "SubRule", None) or getattr(s, "SubClassRule", None)
                             or getattr(s, "ChainSubRule", None)
                             or getattr(s, "ChainSubClassRule", None) or []):
                    for rec in rule.SubstLookupRecord or []:
                        rec.LookupListIndex += offset


def merge_gsub(font: Font, generated: otTables.GSUB, order: list[int], pua_feature: str | None) -> None:
    """Put the generated lookups first and register everything under rlig."""
    ours = generated.LookupList.Lookup
    n = len(ours)
    if "GSUB" in font.tt:
        orig = font.tt["GSUB"].table
    else:
        orig = copy.deepcopy(generated)
        orig.LookupList.Lookup = []
        orig.FeatureList.FeatureRecord = []
    upstream = orig.LookupList.Lookup
    for lk in upstream:
        _shift_lookup_refs(lk, n)
    orig.LookupList.Lookup = list(ours) + list(upstream)
    orig.LookupList.LookupCount = len(orig.LookupList.Lookup)

    # Collect features as (tag, lookup indices) keyed by original index.
    records = orig.FeatureList.FeatureRecord
    for fr in records:
        fr.Feature.LookupListIndex = [i + n for i in fr.Feature.LookupListIndex]
    pua_lookups: list[int] = []
    kept = []
    remap: dict[int, int | None] = {}
    for i, fr in enumerate(records):
        if fr.FeatureTag == pua_feature:
            pua_lookups += [i for i in fr.Feature.LookupListIndex if i not in pua_lookups]
            remap[i] = None  # folded into rlig
        else:
            remap[i] = len(kept)
            kept.append(fr)
    rlig = otTables.FeatureRecord()
    rlig.FeatureTag = "rlig"
    rlig.Feature = otTables.Feature()
    rlig.Feature.FeatureParams = None
    rlig.Feature.LookupListIndex = list(order) + pua_lookups
    rlig.Feature.LookupCount = len(rlig.Feature.LookupListIndex)
    kept.append(rlig)
    # Sort by tag as the spec recommends, and remap LangSys indices.
    sorted_kept = sorted(kept, key=lambda fr: fr.FeatureTag)
    pos = {id(fr): j for j, fr in enumerate(sorted_kept)}
    final = {i: (None if r is None else pos[id(kept[r])]) for i, r in remap.items()}
    rlig_index = pos[id(rlig)]
    orig.FeatureList.FeatureRecord = sorted_kept
    orig.FeatureList.FeatureCount = len(sorted_kept)

    def fix(ls):
        if ls is None:
            return
        idx = [final[i] for i in ls.FeatureIndex if final[i] is not None]
        if rlig_index not in idx:
            idx.append(rlig_index)
        ls.FeatureIndex = sorted(idx)
        ls.FeatureCount = len(ls.FeatureIndex)

    scripts = orig.ScriptList.ScriptRecord
    have = {sr.ScriptTag for sr in scripts}
    for tag in ("DFLT", "latn"):
        if tag not in have:
            sr = otTables.ScriptRecord()
            sr.ScriptTag = tag
            sr.Script = otTables.Script()
            sr.Script.LangSysRecord = []
            sr.Script.LangSysCount = 0
            ls = otTables.LangSys()
            ls.LookupOrder = None
            ls.ReqFeatureIndex = 0xFFFF
            ls.FeatureIndex = []
            sr.Script.DefaultLangSys = ls
            scripts.append(sr)
    scripts.sort(key=lambda sr: sr.ScriptTag)
    orig.ScriptList.ScriptCount = len(scripts)
    for sr in scripts:
        if sr.Script.DefaultLangSys is None:
            ls = otTables.LangSys()
            ls.LookupOrder = None
            ls.ReqFeatureIndex = 0xFFFF
            ls.FeatureIndex = []
            sr.Script.DefaultLangSys = ls
        fix(sr.Script.DefaultLangSys)
        for lsr in sr.Script.LangSysRecord:
            fix(lsr.LangSys)

    if "GSUB" not in font.tt:
        t = newTable("GSUB")
        t.table = orig
        font.tt["GSUB"] = t


def rename(font: Font, family: str, style: str, version_note: str) -> None:
    ps_family = family.replace(" ", "")
    ps = f"{ps_family}-{style.replace(' ', '')}"
    full = f"{family} {style}"
    name = font.tt["name"]
    for rec in list(name.names):
        if rec.nameID in (1, 3, 4, 6, 16, 17, 21, 22):
            name.removeNames(nameID=rec.nameID)
    name.setName(family, 1, 3, 1, 0x409)
    name.setName(style if style in ("Regular", "Bold", "Italic", "Bold Italic") else "Regular", 2, 3, 1, 0x409)
    name.setName(f"{ps};{version_note}", 3, 3, 1, 0x409)
    name.setName(full, 4, 3, 1, 0x409)
    name.setName(ps, 6, 3, 1, 0x409)
    if style not in ("Regular", "Bold", "Italic", "Bold Italic"):
        name.setName(family, 16, 3, 1, 0x409)
        name.setName(style, 17, 3, 1, 0x409)
    # Drop Mac-platform names; modern systems read the Windows ones.
    name.names = [r for r in name.names if r.platformID == 3]
    old_desc = name.getDebugName(10) or ""
    name.setName(
        ("Latin-input build of the upstream Zbalermorna font: renders Latin-"
         "orthography Lojban as Zbalermorna. " + old_desc).strip(), 10, 3, 1, 0x409)
    font.cff.fontNames = [ps]
    font.top.FullName = full
    font.top.FamilyName = family


def build_font(cfg: dict) -> list[Path]:
    src = ROOT / cfg["source"]
    font = Font(src)
    missing = [g for g in required_upstream() if not font.has(g)]
    if missing:
        raise SystemExit(f"{cfg['id']}: upstream glyphs missing: {' '.join(missing)}")
    latin = LatinSource(ROOT / cfg["latin"], font)

    # Punctuation.
    for gname, cps in PUNCTUATION:
        if font.has(gname):
            target = gname
        else:
            # Source by name if the code point list is empty.
            glyph = None
            if gname in latin.glyphs:
                glyph = latin.glyphs[gname]
            elif cps:
                glyph = latin.glyph_for(cps[0])
            if glyph is None:
                print(f"  note: no source for {gname}", file=sys.stderr)
                continue
            latin.copy_into(font, gname, glyph)
            target = gname
        for cp in cps:
            font.map(cp, target)

    # Input glyphs, with Latin fallback outlines.
    for gname, cps in input_cmap().items():
        glyph = latin.glyph_for(cps[0])
        if glyph is None:
            font.add_glyph(gname, 0)
        else:
            latin.copy_into(font, gname, glyph)
        for cp in cps:
            font.map(cp, gname)
    for gname in features.internal_glyphs():
        font.add_glyph(gname, 0)

    generated, order = compile_generated(font)
    merge_gsub(font, generated, order, cfg.get("pua_feature"))

    version = cfg.get("version", "0.1")
    rename(font, cfg["family"], cfg["style"], f"latmo {version}")
    head = font.tt["head"]
    head.fontRevision = float(version)

    out_dir = ROOT / "fonts"
    out_dir.mkdir(exist_ok=True)
    stem = f"{cfg['family'].replace(' ', '')}-{cfg['style'].replace(' ', '')}"
    otf = out_dir / f"{stem}.otf"
    font.tt.save(otf)
    woff2 = out_dir / f"{stem}.woff2"
    font.tt.flavor = "woff2"
    font.tt.save(woff2)
    return [otf, woff2]


def load_config() -> list[dict]:
    with open(ROOT / "fonts.toml", "rb") as f:
        return tomllib.load(f)["font"]


def main(argv: list[str]) -> None:
    fonts = load_config()
    wanted = set(argv)
    for cfg in fonts:
        if wanted and cfg["id"] not in wanted:
            continue
        for path in build_font(cfg):
            print(path.relative_to(ROOT))


if __name__ == "__main__":
    main(sys.argv[1:])
