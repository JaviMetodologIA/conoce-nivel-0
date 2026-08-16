#!/usr/bin/env python3
"""Build the governed A²(R)E method marks from local vector authorities."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT / "src/brand-release-v3/assets/Poppins-Bold.ttf"
OUTPUTS = {
    "primary": ROOT / "src/assets/method-a2re-primary.svg",
    "compact": ROOT / "src/assets/method-a2re-compact.svg",
}
NAVY = "#0a122a"
NAVY_ALT = "#172d5f"
GOLD = "#ffd700"
WHITE = "#f8fafc"


def glyph_path(font: TTFont, character: str) -> tuple[str, int]:
    cmap = font.getBestCmap()
    glyph_name = cmap.get(ord(character))
    if not glyph_name:
        raise RuntimeError(f"METHOD_MARK_GLYPH_MISSING:{ord(character):04X}")
    glyph_set = font.getGlyphSet()
    pen = SVGPathPen(glyph_set)
    glyph_set[glyph_name].draw(pen)
    return pen.getCommands(), font["hmtx"].metrics[glyph_name][0]


def outlined_run(
    font: TTFont,
    text: str,
    x: float,
    baseline: float,
    size: float,
    fill: str,
    tracking: float = 0,
) -> str:
    scale = size / font["head"].unitsPerEm
    paths: list[str] = []
    cursor = x
    for character in text:
        path, advance = glyph_path(font, character)
        paths.append(
            f'<path d="{path}" fill="{fill}" transform="translate({cursor:.3f} {baseline:.3f}) scale({scale:.6f} {-scale:.6f})"/>'
        )
        cursor += advance * scale + tracking
    return "".join(paths)


def primary_svg(font: TTFont) -> str:
    a = outlined_run(font, "A", 55, 157, 126, WHITE)
    two = outlined_run(font, "²", 134, 84, 49, GOLD)
    re = outlined_run(font, "(R)E", 76, 202, 43, WHITE, -1.1)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" role="img" aria-labelledby="title desc">
<title id="title">A²(R)E</title>
<desc id="desc">Aprender, Aprehender, (R)Evolucionar</desc>
<defs>
  <linearGradient id="canvas" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{NAVY_ALT}"/><stop offset=".62" stop-color="{NAVY}"/><stop offset="1" stop-color="#050813"/></linearGradient>
  <radialGradient id="halo" cx="76%" cy="20%" r="58%"><stop stop-color="{GOLD}" stop-opacity=".28"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient>
</defs>
<rect width="256" height="256" rx="44" fill="url(#canvas)"/>
<rect width="256" height="256" rx="44" fill="url(#halo)"/>
<rect x="12" y="12" width="232" height="232" rx="34" fill="none" stroke="#ffffff" stroke-opacity=".12"/>
<path d="M39 171A101 101 0 1 1 217 88" fill="none" stroke="{GOLD}" stroke-width="7" stroke-linecap="round"/>
<circle cx="217" cy="88" r="5" fill="{GOLD}"/>
{a}{two}{re}
</svg>
'''


def compact_svg(font: TTFont) -> str:
    a = outlined_run(font, "A", 35, 88, 76, WHITE)
    two = outlined_run(font, "²", 86, 47, 29, GOLD)
    re = outlined_run(font, "(R)E", 137, 84, 55, WHITE, -1.1)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 120" role="img" aria-labelledby="title desc">
<title id="title">A²(R)E</title>
<desc id="desc">Aprender, Aprehender, (R)Evolucionar</desc>
<defs><linearGradient id="canvas" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{NAVY_ALT}"/><stop offset=".68" stop-color="{NAVY}"/><stop offset="1" stop-color="#050813"/></linearGradient></defs>
<rect width="480" height="120" rx="34" fill="url(#canvas)"/>
<rect x="5" y="5" width="470" height="110" rx="29" fill="none" stroke="#ffffff" stroke-opacity=".13"/>
<path d="M27 91C7 52 31 19 83 17C171 14 331 13 431 37C458 44 467 69 447 89" fill="none" stroke="{GOLD}" stroke-width="5" stroke-linecap="round"/>
<circle cx="447" cy="89" r="4" fill="{GOLD}"/>
{a}{two}{re}
</svg>
'''


def render() -> dict[str, bytes]:
    font = TTFont(FONT, recalcBBoxes=False, recalcTimestamp=False)
    return {
        "primary": primary_svg(font).encode("utf-8"),
        "compact": compact_svg(font).encode("utf-8"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = render()
    for name, payload in rendered.items():
        target = OUTPUTS[name]
        if args.check:
            if not target.is_file() or target.read_bytes() != payload:
                raise SystemExit(f"METHOD_MARK_DRIFT:{target.relative_to(ROOT)}")
        else:
            target.write_bytes(payload)
        print(f"{name} {hashlib.sha256(payload).hexdigest()} {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
