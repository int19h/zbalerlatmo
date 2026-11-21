# zbalerlatmo

These fonts render ordinary Latin-orthography Lojban as
[Zbalermorna](https://jackhumbert.github.io/zbalermorna/write-up) using only
OpenType shaping. The text stays plain Lojban, so it can be searched, copied
and edited without an input method, and a page switches between Latin and
Zbalermorna by changing its `font-family`.

The fonts are built from the upstream Zbalermorna fonts in
[`zbalermorna/`](zbalermorna), imported with their history from
[jackhumbert/zbalermorna](https://github.com/jackhumbert/zbalermorna). The
upstream Private Use Area encoding (U+ED80 to U+EDBF) works as before, so IME
users can use the same fonts.

| Font | Built from | Latin companion |
| --- | --- | --- |
| Crisa Latmo Regular | `crisa-regular.otf` | Lato Regular |
| Crisa Latmo Light | `crisa-light.otf` | Lato Light |
| Vrude Latmo Regular | `vrude-regular.otf` | Playfair Display |
| Vrude Latmo Italic | `vrude-italic-regular.otf` | Playfair Display Italic |
| Balvi Latmo | `balvi-regular.otf` | Exo 2 |
| Tanbo Latmo | `tanbo-regular.otf` | Roboto Slab |
| Nerfopi Latmo | `nerfopi-regular.otf` | Lobster |
| Primihi Latmo | `primihi-regular.otf` | Goudy Bookletter 1911 |
| Dunda Latmo | `dunda-regular.otf` | Lato Regular |
| Tisna Latmo Bold | `tisna-bold.otf` | Lato Regular |
| Ritli Latmo | `ritli-regular.otf` | none |
| Piper Karot Latmo | `piper-karot.otf` | none |
| Fira Code ZLM Latmo | `fira-code-zlm.otf` | its own Latin |

The built fonts are in [`fonts/`](fonts), as OTF and WOFF2.

The Latin companion is the font each upstream design was derived from, and
supplies the punctuation the upstream font lacks. Where it has none that can
be used, the build makes the comma and the quotation marks from the font's own
semicolon and double quote, and leaves other punctuation (dashes, digits) to
the next font in the CSS `font-family` list. Fira Code ZLM already contains all
of Fira Code. The upstream repository's two prototype fonts,
`unicode-drakono.otf` and `unicode-manri.otf`, are not built.

## Using the fonts on a web page

```css
@font-face {
  font-family: "Crisa Latmo";
  src: url("CrisaLatmo-Regular.woff2") format("woff2");
}

.zbalermorna {
  font-family: "Crisa Latmo", serif;
}
```

Apply the font only to Lojban. Inside a Lojban element, wrap anything in
another language in an element that keeps the Latin font. That includes the
contents of `zoi gy. … .gy.` and `la'o gy. … .gy.`, and English tooltips:

```html
<p class="lojban">.i se finti la'o gy. <span class="glico">Burt Bacharach</span> .gy.</p>
```

```css
.zbalermorna .glico { font-family: serif; }
```

## What the fonts understand

The fonts expect well-formed Latin Lojban.

- A name (cmevla) is any word that ends in a consonant, since no other kind of
  Lojban word does. Names are written with full vowels; all other words,
  fu'ivla included, use vowel diacritics. The font finds a name from its last
  letter, so the periods around it are optional: `la prux.`, `la .prux.` and
  `la prux` all work. A period that is present is drawn as the period radical,
  the pause dot. A name written against the word before it, with no space or
  period between them (`laprux.`), takes that word in too, which is also how
  Lojban reads it.
- A word that starts with a vowel should start with a period (`.i`, `.ui`). A
  bare vowel still gets the period radical.
- `i` and `u` before a vowel become the glide radicals, and glides take
  precedence over diphthongs: `.maias.` is ma-ias. When two of them come before
  a vowel, only the second is a glide: `.mariias.` is ma-ri-ias. The diphthongs
  `ai`, `ei`, `oi` and `au` each become one diphthong diacritic, or one
  full-vowel letter in a name.
- The apostrophe can be written `'`, `’` (U+2019) or `h`. Between two vowels,
  `'` and `’` are the apostrophe; anywhere else they are quotation marks.
- A comma between two letters separates syllables (`.i,an.` against `.ian.`).
  Anywhere else it is an ordinary comma.
- Stress is a capital vowel (`klAma`) or a vowel with an acute or grave accent
  (`kláma`, precomposed or combining), and it is drawn as the stress dot. A
  diphthong or glide syllable gets one dot even when both vowels are capitals
  (`COI`, `.UI`).
- A tilde after a vowel (`gle~ki~~`) draws the stretch mark.
- `.V'V` attitudinals such as `.e'u` use the combined period-and-apostrophe
  form, as in the upstream fonts.
- Punctuation and digits stay Latin. Quotation marks, dashes, the ellipsis and
  digits come from the Latin companion font.
- Fira Code ZLM stays monospaced: as upstream, every vowel sign takes its own
  cell. Its programming ligatures (in `calt`) can still be turned off, except
  those that start with `.` or `~` (`..`, `~~`, `~@`), since those characters
  are always the period radical and the stretch mark. Its upstream font has
  no lookups of its own, so in Fira Code ZLM a bare vowel gets no period
  radical and `.V'V` attitudinals use the ordinary period and apostrophe.

All of this is in `rlig`, the required ligatures feature. Ligature switches in
applications and `font-variant-ligatures: none` in CSS leave it on; only
`font-feature-settings: "rlig" 0` turns it off. Where no shaping happens at
all, the text shows as Latin Lojban. For characters the font does not cover,
such as `q` and `w`, browsers use the next font in the `font-family` list.

## Building

```bash
pip install -r requirements.txt
python -m latmo.build            # all fonts in fonts.toml
python -m latmo.build crisa-regular
```

`fonts.toml` lists the fonts to build.
[`latmo/features.py`](latmo/features.py) generates the lookups, and
[`latmo/build.py`](latmo/build.py) adds the glyphs and cmap entries and puts
the generated lookups ahead of the upstream font's own lookups.

To see what a string shapes to:

```bash
python -m latmo.shape fonts/CrisaLatmo-Regular.otf ".i mi klama la .djan."
```

## Tests

```bash
python -m pytest tests
```

`tests/cases/manual.tsv` has hand-checked cases. `tests/cases/corpus.tsv` has
dictionary words and sentences, `tests/cases/corpus-ziholafti.tsv` has
sentences from Joi Massat's *zi’o lafti*, and `tests/cases/corpus-corners.tsv`
has corner cases: names, glides, diphthongs, apostrophes, stress and the
stretch mark. The expected output of the corpora comes from an independent
Latin-to-Zbalermorna renderer, shaped with the original upstream Crisa; the
few corner cases that renderer cannot express are written by hand and marked
as such. These expected glyph names are checked on the fonts
marked `reference` in `fonts.toml` (Crisa), in Latin and in the PUA encoding.
Every other font is checked against its own upstream font: each corpus line in
Latin must shape like the same text in the PUA encoding does in the original.
`tests/cases/punctuation.tsv` covers punctuation the upstream fonts lack:
every font must give it real glyphs and leave the Zbalermorna around it as
upstream shapes the same text without it.
`tests/test_build.py` checks the built fonts' metrics and names, and builds
every upstream font to check that its Latin input shapes like the same text in
the PUA encoding.

## Licenses

The build code is under the MIT license (see [`LICENSE`](LICENSE)). Each built
font keeps the license of the font it was derived from: most are under the SIL
Open Font License 1.1, Tanbo Latmo is under the Apache License 2.0, and Ritli
Latmo under the GPL. Dunda Latmo is based on Tengwar Annatar, which its author
distributes under his own terms, not an open font license. [`fonts/LICENSES.md`](fonts/LICENSES.md) lists each
font's license and copyright notices. The vendored companion fonts keep their
own licenses (see [`vendor/README.md`](vendor/README.md)).
`tests/cases/corpus-ziholafti.tsv` contains text from
[*zi’o lafti*](https://suzypavlis.neocities.org/lojban/prux/ziholafti) © 2026
by Joi Massat, used and adapted under
[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/), and is itself
under CC BY-NC 4.0. The upstream repository in `zbalermorna/` keeps its own
license.
