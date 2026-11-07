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

The built fonts are in [`fonts/`](fonts), as OTF and WOFF2.

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
dictionary words and sentences, and `tests/cases/corpus-ziholafti.tsv` has
sentences from Joi Massat's *zi’o lafti*. The expected output of both corpora
comes from an independent Latin-to-Zbalermorna renderer, shaped with the
original upstream font. Each corpus line is also checked in the PUA encoding,
which must give the same glyphs, so the tests also cover upstream behaviour.
`tests/test_build.py` checks the built fonts' metrics and names, and builds
every upstream font to check that its Latin input shapes like the same text in
the PUA encoding.

## Licenses

The build code is under the MIT license (see [`LICENSE`](LICENSE)). The built
fonts are Modified Versions under the SIL Open Font License 1.1 (see
[`fonts/OFL.txt`](fonts/OFL.txt)). The vendored Lato fonts are also under the
OFL (see [`vendor/lato/OFL.txt`](vendor/lato/OFL.txt)).
`tests/cases/corpus-ziholafti.tsv` contains text from
[*zi’o lafti*](https://suzypavlis.neocities.org/lojban/prux/ziholafti) © 2026
by Joi Massat, used and adapted under
[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/), and is itself
under CC BY-NC 4.0. The upstream repository in `zbalermorna/` keeps its own
license.
