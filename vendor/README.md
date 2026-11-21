# Vendored Latin companion fonts

The build copies missing punctuation, and the Latin outlines of the input
glyphs, from the Latin font each upstream Zbalermorna design was derived from.
These are unmodified copies; each directory keeps its license.

| Directory | Font | Used for | License | Source |
| --- | --- | --- | --- | --- |
| `lato/` | Lato 2.015 Regular, Light | Crisa, Dunda, Tisna | OFL 1.1 | Debian `fonts-lato` |
| `playfairdisplay/` | Playfair Display (variable), Italic | Vrude, Vrude Italic | OFL 1.1 | google/fonts `ofl/playfairdisplay` |
| `exo2/` | Exo 2 (variable) | Balvi | OFL 1.1 | google/fonts `ofl/exo2` |
| `robotoslab/` | Roboto Slab (variable) | Tanbo | Apache 2.0 | google/fonts `apache/robotoslab` |
| `lobster/` | Lobster | Nerfopi | OFL 1.1 | google/fonts `ofl/lobster` |
| `goudybookletter1911/` | Goudy Bookletter 1911 | Primihi | OFL 1.1 | google/fonts `ofl/goudybookletter1911` |

The google/fonts files are from commit
`06bfe0d62a98375cb09c942fa18e68bd32cff057`. The build instances variable
fonts at the weight given by `latin_axes` in `fonts.toml` (400 by default).
