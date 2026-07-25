# Generates profile-card.svg: a neofetch-style profile card with the
# actual photo from profile.png on the left and system-info-style
# stats on the right.
#
# Run with:  uv run --with pillow generate_card.py

from __future__ import annotations

import base64
import io
from xml.sax.saxutils import escape

from PIL import Image

# ------------------------------------------------------------------- photo

# Crop box for profile.png (head and shoulders region of the selfie)
CROP = (0, 60, 576, 880)
PHOTO_RADIUS = 12


def photo_svg(path: str, x0: float, y0: float, height: float) -> tuple[str, float]:
    """Embed the cropped photo as base64 JPEG. Returns (svg, width)."""
    img = Image.open(path).convert("RGB").crop(CROP)
    w, h = img.size
    width = height * w / h
    # 2x target size keeps it sharp on retina screens without a huge file
    img = img.resize((int(width * 2), int(height * 2)), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=82)
    b64 = base64.b64encode(buf.getvalue()).decode()

    svg = f"""<clipPath id="photo-clip">
  <rect x="{x0}" y="{y0}" width="{width:.1f}" height="{height}" rx="{PHOTO_RADIUS}"/>
</clipPath>
<image x="{x0}" y="{y0}" width="{width:.1f}" height="{height}"
       clip-path="url(#photo-clip)" preserveAspectRatio="xMidYMid slice"
       href="data:image/jpeg;base64,{b64}"/>
<rect x="{x0}" y="{y0}" width="{width:.1f}" height="{height}" rx="{PHOTO_RADIUS}"
      fill="none" stroke="#30363d" stroke-width="1.5"/>"""
    return svg, width


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
    pad = 26
    photo_h = len(INFO_LINES) * INFO_LINE_H + 8

    photo, photo_w = photo_svg("profile.png", pad, pad, photo_h)
    info_x = pad + photo_w + 34
    width = info_x + INFO_COLS * INFO_CHAR_W + pad
    height = photo_h + 2 * pad

    info = info_svg(info_x, pad + 14)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}">
<style>
  .info {{ font-family: Menlo, Consolas, 'DejaVu Sans Mono', monospace; font-size: {INFO_FONT}px; }}
</style>
<rect width="100%" height="100%" rx="14" fill="#0d1117" stroke="#30363d" stroke-width="2"/>
{photo}
{info}
</svg>
"""
    with open("profile-card.svg", "w") as f:
        f.write(svg)
    print(f"profile-card.svg written ({width:.0f}x{height:.0f})")


if __name__ == "__main__":
    main()
