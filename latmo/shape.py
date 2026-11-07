"""Shape text with HarfBuzz and report glyph names.

Usage: python -m latmo.shape FONT TEXT...
"""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

import uharfbuzz as hb


@lru_cache(maxsize=None)
def _load(path: str):
    blob = hb.Blob.from_file_path(path)
    face = hb.Face(blob)
    font = hb.Font(face)
    names = [font.glyph_to_string(i) for i in range(face.glyph_count)]
    return font, names


def shape(path: str | Path, text: str, features: dict | None = None) -> list[tuple[str, int, int, int]]:
    """Return (glyph name, x advance, x offset, y offset) for each output glyph."""
    font, names = _load(str(path))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features or {})
    return [
        (names[info.codepoint], pos.x_advance, pos.x_offset, pos.y_offset)
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions)
    ]


def glyph_names(path: str | Path, text: str, features: dict | None = None) -> list[str]:
    return [g[0] for g in shape(path, text, features)]


def main(argv: list[str]) -> None:
    path, *texts = argv
    for text in texts:
        print(f"{text}\t{' '.join(glyph_names(path, text))}")


if __name__ == "__main__":
    main(sys.argv[1:])
