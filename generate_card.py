# Generates profile-card.svg: a neofetch-style profile card with an
# ASCII-art rendering of profile.png on the left and system-info-style
# stats on the right.
#
# Run with:  uv run --with pillow generate_card.py

from __future__ import annotations

import math
from xml.sax.saxutils import escape

from PIL import Image, ImageEnhance

# ---------------------------------------------------------------- ASCII art

ASCII_COLS = 46
CHAR_W = 8.0  # px per character cell (monospace, font-size 13)
LINE_H = 13.5
RAMP = " .,:;+*?%S#@"  # sparse -> dense

# Crop box for profile.png (head and shoulders region of the selfie)
CROP = (20, 60, 556, 840)

FACE_CENTER = (0.5, 0.42)  # vignette center, normalized to crop
VIGNETTE_START, VIGNETTE_END, VIGNETTE_STRENGTH = 0.30, 0.80, 0.88


def smoothstep(a: float, b: float, x: float) -> float:
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def quantize(v: float) -> int:
    # Round channels so identical colors merge into longer tspan runs
    return max(0, min(255, int(round(v / 20) * 20)))


def build_ascii_rows(path: str) -> list[list[tuple[str, str]]]:
    """Returns rows of (char, hexcolor) cells."""
    img = Image.open(path).convert("RGB").crop(CROP)
    img = ImageEnhance.Color(img).enhance(1.25)
    img = ImageEnhance.Brightness(img).enhance(1.15)

    w, h = img.size
    rows_n = int(ASCII_COLS * (h / w) * (CHAR_W / LINE_H))
    img = img.resize((ASCII_COLS, rows_n), Image.LANCZOS)

    rows: list[list[tuple[str, str]]] = []
    px = img.load()
    for y in range(rows_n):
        row: list[tuple[str, str]] = []
        for x in range(ASCII_COLS):
            r, g, b = px[x, y]
            dx = x / ASCII_COLS - FACE_CENTER[0]
            dy = y / rows_n - FACE_CENTER[1]
            dist = math.sqrt(dx * dx + dy * dy * 1.6)
            fade = 1.0 - VIGNETTE_STRENGTH * smoothstep(
                VIGNETTE_START, VIGNETTE_END, dist
            )
            r, g, b = r * fade, g * fade, b * fade
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            ch = RAMP[min(int(lum / 256 * len(RAMP)), len(RAMP) - 1)]
            color = f"#{quantize(r):02x}{quantize(g):02x}{quantize(b):02x}"
            row.append((ch, color))
        rows.append(row)
    return rows


def ascii_svg(rows: list[list[tuple[str, str]]], x0: float, y0: float) -> str:
    parts = []
    for i, row in enumerate(rows):
        y = y0 + i * LINE_H
        spans = []
        # merge consecutive same-color cells into one tspan
        run_chars, run_color = "", None
        for ch, color in row + [("", None)]:
            if color != run_color and run_chars:
                if run_chars.strip():
                    spans.append(
                        f'<tspan fill="{run_color}">{escape(run_chars)}</tspan>'
                    )
                else:
                    spans.append(f"<tspan>{escape(run_chars)}</tspan>")
                run_chars = ""
            run_chars += ch
            run_color = color
        parts.append(
            f'<text x="{x0}" y="{y:.1f}" xml:space="preserve" class="art" '
            f'textLength="{ASCII_COLS * CHAR_W:.0f}" '
            f'lengthAdjust="spacingAndGlyphs">{"".join(spans)}</text>'
        )
    return "\n".join(parts)


# ------------------------------------------------------------- info column

C_KEY = "#ffa657"  # orange keys
C_VAL = "#79c0ff"  # blue values
C_DOT = "#484f58"  # dim dot leaders
C_HDR = "#e6edf3"  # white headers
C_DASH = "#8b949e"

INFO_COLS = 66  # characters per line in the right column
INFO_FONT = 13.0
INFO_LINE_H = 19.0
INFO_CHAR_W = 7.83


def kv(key: str, value: str) -> str:
    dots = INFO_COLS - len(key) - len(value) - 6
    dots = max(dots, 1)
    return (
        f'<tspan fill="{C_DOT}">. </tspan>'
        f'<tspan fill="{C_KEY}">{escape(key)}:</tspan>'
        f'<tspan fill="{C_DOT}"> {"." * dots} </tspan>'
        f'<tspan fill="{C_VAL}">{escape(value)}</tspan>'
    )


def header(title: str) -> str:
    dashes = INFO_COLS - len(title) - 3
    return (
        f'<tspan fill="{C_HDR}" font-weight="bold">{escape(title)}</tspan>'
        f'<tspan fill="{C_DASH}"> {"─" * dashes}</tspan>'
    )


INFO_LINES: list[str | None] = [
    header("mohussain@github"),
    kv("OS", "macOS, Linux"),
    kv("Uptime", "3+ years in software engineering"),
    kv("Host", "FNB Corporation (prev. Amazon)"),
    kv("Kernel", "Backend / Full-Stack Engineer"),
    kv("IDE", "Cursor, VS Code"),
    None,
    kv("Languages.Programming", "Python, TypeScript, SQL"),
    kv("Languages.Web", "React, HTML, CSS"),
    kv("Languages.Real", "English"),
    None,
    kv("Frameworks", "FastAPI, React, Playwright, pytest-bdd"),
    kv("Databases", "Postgres, pgvector"),
    kv("Cloud", "Azure, AWS"),
    None,
    kv("Hobbies.Software", "AI apps, Developer Tools, Automation"),
    kv("Hobbies.Real", "Cricket"),
    None,
    header("─ Contact"),
    kv("LinkedIn", "syed-mohammed-hussain"),
    kv("GitHub", "MhussainD4772"),
    kv("Location", "Pittsburgh, Pennsylvania"),
    None,
    header("─ GitHub Stats"),
    kv("Repos", "18 | Followers: 6"),
    kv("Commits", "969 (and counting)"),
]


def info_svg(x0: float, y0: float) -> str:
    parts = []
    y = y0
    for line in INFO_LINES:
        if line is not None:
            parts.append(
                f'<text x="{x0}" y="{y:.1f}" xml:space="preserve" class="info" '
                f'textLength="{INFO_COLS * INFO_CHAR_W:.0f}" '
                f'lengthAdjust="spacingAndGlyphs">{line}</text>'
            )
        y += INFO_LINE_H
    return "\n".join(parts)


# ------------------------------------------------------------------- card

def main() -> None:
    rows = build_ascii_rows("profile.png")

    pad = 26
    art_w = ASCII_COLS * CHAR_W
    art_h = len(rows) * LINE_H
    info_x = pad + art_w + 34
    width = info_x + INFO_COLS * INFO_CHAR_W + pad
    height = max(art_h, len(INFO_LINES) * INFO_LINE_H) + 2 * pad

    art = ascii_svg(rows, pad, pad + 10)
    info = info_svg(info_x, pad + 14)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}">
<style>
  .art  {{ font-family: Menlo, Consolas, 'DejaVu Sans Mono', monospace; font-size: 13px; }}
  .info {{ font-family: Menlo, Consolas, 'DejaVu Sans Mono', monospace; font-size: {INFO_FONT}px; }}
</style>
<rect width="100%" height="100%" rx="14" fill="#0d1117" stroke="#30363d" stroke-width="2"/>
{art}
{info}
</svg>
"""
    with open("profile-card.svg", "w") as f:
        f.write(svg)
    print(f"profile-card.svg written ({width:.0f}x{height:.0f}, {len(rows)} art rows)")


if __name__ == "__main__":
    main()
