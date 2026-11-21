"""Build Latin-input Zbalermorna fonts from the upstream fonts.

Usage: python -m latmo.build [FONT_ID ...]

fonts.toml lists the fonts. For each one, the build:

1. loads the upstream OTF from zbalermorna/fonts/;
2. adds the Latin punctuation the upstream font lacks. It comes from the
   Latin companion font the upstream design was derived from, from the
   upstream font itself where it has full Latin, or else is built from the
   upstream font's own semicolon and double quote (see ``latin`` in
   fonts.toml);
3. adds the ``lat.*`` input glyphs (see latmo/features.py) and maps Latin
   characters to them. Where a Latin source exists, the input glyphs have
   Latin outlines, so the text still reads as Latin Lojban where no shaping
   happens;
4. compiles the generated lookups and puts them ahead of the font's own
   lookups in the ``rlig`` feature, which ligature switches leave on;
5. renames the font and writes OTF and WOFF2 to fonts/.
"""

from __future__ import annotations

import copy
import io
import math
import statistics
import sys
import tomllib
from pathlib import Path

from fontTools.feaLib.builder import Builder
from fontTools.feaLib.parser import Parser
from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import otTables
from fontTools.varLib.instancer import instantiateVariableFont

from . import features

ROOT = Path(__file__).resolve().parent.parent

# Latin punctuation and symbols to add when the upstream font lacks them, as
# (glyph name, code point of its source glyph, code points to map to it).
# comma, quotesingle and quoteright are not mapped: U+002C, U+0027 and U+2019
# go to input glyphs, and the generated lookups use these as punctuation forms.
PUNCTUATION = [
    ("comma", 0x2C, []),
    ("quotesingle", 0x27, []),
    ("quoteright", 0x2019, []),
    ("quoteleft", 0x2018, [0x2018]),
    ("quotedblleft", 0x201C, [0x201C]),
    ("quotedblright", 0x201D, [0x201D]),
    ("quotesinglbase", 0x201A, [0x201A]),
    ("quotedblbase", 0x201E, [0x201E]),
    ("hyphen", 0x2D, [0x2D, 0x2010]),
    ("endash", 0x2013, [0x2013]),
    ("emdash", 0x2014, [0x2014]),
    ("ellipsis", 0x2026, [0x2026]),
    ("slash", 0x2F, [0x2F]),
    ("backslash", 0x5C, [0x5C]),
    ("asterisk", 0x2A, [0x2A]),
    ("plus", 0x2B, [0x2B]),
    ("equal", 0x3D, [0x3D]),
    ("at", 0x40, [0x40]),
    ("underscore", 0x5F, [0x5F]),
    ("bar", 0x7C, [0x7C]),
    ("asciicircum", 0x5E, [0x5E]),
    ("grave", 0x60, [0x60]),
    ("bullet", 0x2022, [0x2022]),
    ("periodcentered", 0xB7, [0xB7]),
] + [(name, 0x30 + i, [0x30 + i]) for i, name in enumerate(
    ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"])]

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
    names += list(f.DIPHTHONG_MARK.values()) + list(f.DIPHTHONG_FULL.values())
    names += [f.PERIOD, f.APOSTROPHE, f.SEPARATOR, f.STRESS, f.STRETCH]
    return names


class Font:
    def __init__(self, path: Path):
        # Keep the upstream timestamp so rebuilds are byte-for-byte reproducible.
        self.tt = TTFont(path, recalcTimestamp=False)
        self.cff = self.tt["CFF "].cff
        self.top = self.cff.topDictIndex[0]
        self.order = list(self.tt.getGlyphOrder())
        # The upstream cmap before any Latin input is mapped.
        self.own_cmap = dict(self.tt.getBestCmap())

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
        # Measure the compiled glyph: CFF rounds coordinates, so the unrounded
        # outline's xMin can be a unit off.
        bounds = cs.calcBounds(None)
        lsb = round(bounds[0]) if bounds else 0
        strings = self.top.CharStrings
        if strings.charStringsAreIndexed:
            strings.charStrings[name] = len(strings.charStringsIndex)
            strings.charStringsIndex.append(cs)
        else:
            strings.charStrings[name] = cs
        self.order.append(name)
        self.top.charset = self.order
        self.tt.setGlyphOrder(self.order)
        # fontTools does not recompute lsb for CFF fonts; hmtx lsb must be xMin.
        self.tt["hmtx"].metrics[name] = (width, lsb)

    def map(self, codepoint: int, name: str) -> None:
        for table in self.tt["cmap"].tables:
            if table.isUnicode() or (table.platformID, table.platEncID) == (3, 1):
                if table.format in (4, 12) and (codepoint <= 0xFFFF or table.format == 12):
                    table.cmap[codepoint] = name


Outline = tuple[int, RecordingPen]  # advance width and outline, in font units


class CompanionSource:
    """A Latin font, scaled to the upstream design. It is the companion font
    the upstream design was derived from, or the upstream font itself when it
    has full Latin (Fira Code ZLM)."""

    def __init__(self, path: Path, target: Font, axes: dict | None = None):
        self.path = path
        self.tt = TTFont(path)
        if "fvar" in self.tt:
            self.tt = instantiateVariableFont(self.tt, axes or {"wght": 400})
        self.glyphs = self.tt.getGlyphSet()
        self.cmap = self.tt.getBestCmap()
        self.scale = self._fit_scale(target)

    def _fit_scale(self, target: Font) -> float:
        # Upstream fonts copied the companion's punctuation; match advances.
        upm = self.tt["head"].unitsPerEm
        tgt_upm = target.tt["head"].unitsPerEm
        ratios = []
        tmet = target.tt["hmtx"].metrics
        for cp in map(ord, "!?()[]:;"):
            name = target.own_cmap.get(cp)
            src = self.cmap.get(cp)
            if name and src and self.glyphs[src].width:
                ratios.append(tmet[name][0] / (self.glyphs[src].width * tgt_upm / upm))
        base = tgt_upm / upm
        if not ratios:
            print(f"  warning: no shared punctuation to fit {self.path.name} to; "
                  "using the unitsPerEm ratio", file=sys.stderr)
            return base
        return base * statistics.median(ratios)

    def outline(self, codepoint: int) -> Outline | None:
        name = self.cmap.get(codepoint)
        if name is None:
            return None
        glyph = self.glyphs[name]
        recording = DecomposingRecordingPen(self.glyphs)
        glyph.draw(recording)
        scaled = RecordingPen()
        out = TransformPen(scaled, Transform().scale(self.scale))
        if "glyf" in self.tt:
            # TrueType contours run the opposite way from CFF ones.
            out = ReverseContourPen(out)
        recording.replay(out)
        return round(glyph.width * self.scale), scaled


def _contours(glyphs, name: str) -> list[tuple[list, tuple]]:
    """Split a glyph into contours, each with its bounds."""
    recording = DecomposingRecordingPen(glyphs)
    glyphs[name].draw(recording)
    contours, current = [], []
    for op, args in recording.value:
        current.append((op, args))
        if op in ("closePath", "endPath"):
            bounds = BoundsPen(None)
            for op2, args2 in current:
                getattr(bounds, op2)(*args2)
            contours.append((current, bounds.bounds))
            current = []
    return contours


def _place(contours: list[list], transform: Transform) -> RecordingPen:
    out = RecordingPen()
    pen = TransformPen(out, transform)
    for contour in contours:
        for op, args in contour:
            getattr(pen, op)(*args)
    return out


class DerivedSource:
    """Punctuation built from the upstream font's own outlines, for fonts with
    no usable Latin companion: the comma is the tail of the semicolon, set
    with the colon's side bearings; the curly quotes are that tail raised to
    the height of the double quote (and turned for the opening quotes), and
    the low quotes are the tail on the baseline; the straight quote is half
    of the double quote. Quotes get the double quote's left side bearing on
    both sides, and pairs keep its gap between the two marks."""

    def __init__(self, target: Font):
        glyphs = target.tt.getGlyphSet()
        cmap, hmtx = target.own_cmap, target.tt["hmtx"]
        semicolon, quotedbl, colon = cmap[ord(";")], cmap[ord('"')], cmap[ord(":")]
        self.comma = min(_contours(glyphs, semicolon), key=lambda c: c[1][1])
        colon_x0 = min(c[1][0] for c in _contours(glyphs, colon))
        colon_x1 = max(c[1][2] for c in _contours(glyphs, colon))
        self.colon_lsb, self.colon_rsb = colon_x0, hmtx[colon][0] - colon_x1
        quotes = sorted(_contours(glyphs, quotedbl), key=lambda c: c[1][0])
        self.straight = quotes[0]
        self.lsb = quotes[0][1][0]
        # White space between the two marks of the double quote.
        self.space = quotes[-1][1][0] - quotes[0][1][2]
        self.top = max(c[1][3] for c in quotes)

    def _mark(self, raised: bool, turned: bool, x: float) -> RecordingPen:
        """The comma tail with its left edge at x, raised or on the baseline."""
        contour, (x0, y0, x1, y1) = self.comma
        t = Transform().translate(x - x0, self.top - y1 if raised else 0)
        if turned:
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            t = t.translate(cx, cy).rotate(math.pi).translate(-cx, -cy)
        return _place([contour], t)

    def _quotes(self, count: int, raised: bool, turned: bool) -> Outline:
        ink = self.comma[1][2] - self.comma[1][0]
        merged = RecordingPen()
        for i in range(count):
            self._mark(raised, turned, self.lsb + i * (ink + self.space)).replay(merged)
        width = 2 * self.lsb + count * ink + (count - 1) * self.space
        return round(width), merged

    def outline(self, codepoint: int) -> Outline | None:
        if codepoint == 0x2C:
            x0, x1 = self.comma[1][0], self.comma[1][2]
            width = self.colon_lsb + (x1 - x0) + self.colon_rsb
            return round(width), _place([self.comma[0]], Transform().translate(self.colon_lsb - x0, 0))
        if codepoint == 0x27:
            x0, x1 = self.straight[1][0], self.straight[1][2]
            return round(2 * x0 + (x1 - x0)), _place([self.straight[0]], Transform())
        shapes = {0x2019: (1, True, False), 0x2018: (1, True, True), 0x201A: (1, False, False),
                  0x201D: (2, True, False), 0x201C: (2, True, True), 0x201E: (2, False, False)}
        if codepoint in shapes:
            return self._quotes(*shapes[codepoint])
        return None


def make_source(cfg: dict, font: Font, src: Path):
    latin = cfg.get("latin", "derive")
    if latin == "derive":
        return DerivedSource(font)
    if latin == "self":
        return CompanionSource(src, font)
    return CompanionSource(ROOT / latin, font, cfg.get("latin_axes"))


def compile_generated(font: Font, targets: dict[int, str]) -> tuple[otTables.GSUB, list[int]]:
    """Compile the generated lookups. Returns the GSUB and the indices of the
    lookups to register, in order."""
    fea = features.generate(targets)
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
        for rec in getattr(st, "SubstLookupRecord", None) or []:
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

    # Shift the features' lookup indices, fold the PUA feature into rlig, and
    # record the new position of each remaining feature.
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
        if ls.ReqFeatureIndex != 0xFFFF:
            req = final.get(ls.ReqFeatureIndex)
            ls.ReqFeatureIndex = 0xFFFF if req is None else req

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


RIBBI = ("Regular", "Bold", "Italic", "Bold Italic")

# License description (name ID 13) and URL (name ID 14) by fonts.toml key.
LICENSES = {
    "OFL-1.1": ("This Font Software is licensed under the SIL Open Font License, "
                "Version 1.1.", "https://openfontlicense.org"),
    "Apache-2.0": ("Licensed under the Apache License, Version 2.0.",
                   "https://www.apache.org/licenses/LICENSE-2.0"),
    "GPL-2.0": ("Licensed under the GNU General Public License, version 2.",
                "https://www.gnu.org/licenses/old-licenses/gpl-2.0.html"),
}


def rename(font: Font, cfg: dict) -> None:
    """Set names, license strings, version strings and style bits."""
    family, style, version = cfg["family"], cfg["style"], cfg.get("version", "0.1")
    name = font.tt["name"]
    upstream_family = name.getDebugName(16) or name.getDebugName(1)
    ps_family = family.replace(" ", "")
    ps = f"{ps_family}-{style.replace(' ', '')}"
    full = f"{family} {style}"
    for rec in list(name.names):
        if rec.nameID in (1, 3, 4, 6, 10, 13, 14, 16, 17, 21, 22):
            name.removeNames(nameID=rec.nameID)
    name.setName(family, 1, 3, 1, 0x409)
    bold, italic = "Bold" in style, "Italic" in style
    ribbi = {(False, False): "Regular", (True, False): "Bold",
             (False, True): "Italic", (True, True): "Bold Italic"}[(bold, italic)]
    name.setName(ribbi, 2, 3, 1, 0x409)
    name.setName(f"{ps};latmo {version}", 3, 3, 1, 0x409)
    name.setName(f"Version {version}; latmo", 5, 3, 1, 0x409)
    name.setName(full, 4, 3, 1, 0x409)
    name.setName(ps, 6, 3, 1, 0x409)
    if style not in RIBBI:
        name.setName(family, 16, 3, 1, 0x409)
        name.setName(style, 17, 3, 1, 0x409)
    # Drop Mac-platform names; modern systems read the Windows ones.
    name.names = [r for r in name.names if r.platformID == 3]
    name.setName(f"Latin-input version of the Zbalermorna font {upstream_family}: "
                 "renders Latin-orthography Lojban as Zbalermorna.", 10, 3, 1, 0x409)
    # Upstream fonts often carry Lato's license strings from the template they
    # were made from; replace them with this font's own.
    license = cfg["license"]
    if license in LICENSES:
        text, url = LICENSES[license]
        name.setName(text, 13, 3, 1, 0x409)
        name.setName(url, 14, 3, 1, 0x409)
        font.tt["OS/2"].fsType = 0  # installable: no embedding restrictions
    else:
        name.setName(cfg["license_text"], 13, 3, 1, 0x409)
    font.cff.fontNames = [ps]
    font.top.FullName = full
    font.top.FamilyName = family
    font.top.version = version
    font.tt["head"].fontRevision = float(version)
    # Style bits must agree with the names; browsers and font menus use them.
    os2, head = font.tt["OS/2"], font.tt["head"]
    sel = os2.fsSelection & ~0b1100001  # clear ITALIC, BOLD, REGULAR
    sel |= (1 if italic else 0) | (1 << 5 if bold else 0) | (0 if bold or italic else 1 << 6)
    os2.fsSelection = sel
    head.macStyle = (head.macStyle & ~0b11) | (1 if bold else 0) | (2 if italic else 0)
    if bold and os2.usWeightClass < 600:
        os2.usWeightClass = 700


def build_font(cfg: dict, out_dir: Path | None = None) -> list[Path]:
    src = ROOT / cfg["source"]
    font = Font(src)
    missing = [g for g in required_upstream() if not font.has(g)]
    if missing:
        raise SystemExit(f"{cfg['id']}: upstream glyphs missing: {' '.join(missing)}")
    source = make_source(cfg, font, src)
    derived = source if isinstance(source, DerivedSource) else None

    def add_outline(name: str, outline: Outline) -> None:
        width, recording = outline
        font.add_glyph(name, width, recording.replay)

    # Punctuation the upstream font lacks. Where it has the character, under
    # whatever glyph name, its own glyph is kept and nothing is added.
    targets: dict[int, str] = {}
    for gname, source_cp, cps in PUNCTUATION:
        if font.has(gname):
            glyph = gname
        elif source_cp in font.own_cmap:
            glyph = font.own_cmap[source_cp]
        else:
            outline = source.outline(source_cp)
            if outline is None and source_cp in features.PUNCTUATION_TARGETS:
                derived = derived or DerivedSource(font)
                outline = derived.outline(source_cp)
            if outline is None:
                continue  # browsers fall back to the next font for these
            add_outline(gname, outline)
            glyph = gname
        if source_cp in features.PUNCTUATION_TARGETS:
            targets[source_cp] = glyph
        for cp in cps:
            if cp not in font.own_cmap:
                font.map(cp, glyph)

    # Input glyphs. Their outlines are only seen where no shaping happens:
    # Latin where a Latin source exists, otherwise the upstream glyph that
    # shaping would produce.
    fallback = dict(features.lowering(targets))
    for gname, cps in input_cmap().items():
        outline = source.outline(cps[0])
        if outline is None:
            base = fallback[gname.removesuffix(".str")] if gname != features.lat("h") \
                else features.APOSTROPHE
            width = font.tt["hmtx"][base][0]
            recording = DecomposingRecordingPen(font.tt.getGlyphSet())
            font.tt.getGlyphSet()[base].draw(recording)
            outline = (width, recording)
        add_outline(gname, outline)
        for cp in cps:
            font.map(cp, gname)
    for gname in features.internal_glyphs():
        font.add_glyph(gname, 0)

    generated, order = compile_generated(font, targets)
    merge_gsub(font, generated, order, cfg.get("pua_feature"))

    rename(font, cfg)

    out_dir = out_dir or ROOT / "fonts"
    out_dir.mkdir(parents=True, exist_ok=True)
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
