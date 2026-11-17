"""Make a new T3 Code theme in one command, with the same glass treatment as every theme in this repo.

    python tools/new_theme.py --id my-theme --name "My Theme" --appearance dark \
        --base "#0b0d14" --accent "#e8c27a" --text "#ece8e0" [--art scene.svg] [--out my-theme.json]

--base is the background colour, --accent the colour for buttons, links and switches, --text the reading
colour (it is also every edge and focus ring). --art (SVG, PNG, JPEG or WebP) is shown behind the whole
window; without it the background is a soft gradient of --base. --tint (the glass colour) is derived from
--base unless given. Secondary text, placeholders and status colours are tuned for contrast automatically.

The theme is checked like the ones in this repo: contrast targets, T3's 50,000-character CSS limit, no
backslash in the CSS, a valid id and name. Nothing is written if a check fails. Install the result with
Settings > Appearance > Add theme, or `t3 theme set <file>`.
"""
import argparse
import base64
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "source", "theme-examples"))
import build      # noqa: E402  (palette, roles, CSS template and checks shared with the scene themes)
import scenemin   # noqa: E402

RESERVED = {"t3-chat", "grove", "ocean", "ember", "iris"}
RASTER = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


def scene_background(art, base, dark):
    if not art:
        lift = build.mix(base, "#ffffff" if dark else "#000000", 0.04)
        sink = build.mix(base, "#000000", 0.25 if dark else 0.06)
        return f"linear-gradient(180deg, {lift} 0%, {base} 55%, {sink} 100%)"
    ext = os.path.splitext(art)[1].lower()
    if ext == ".svg":
        return scenemin.to_css_url(open(art, encoding="utf-8").read())
    if ext in RASTER:
        data = base64.b64encode(open(art, "rb").read()).decode("ascii")
        return f'url("data:{RASTER[ext]};base64,{data}")'
    sys.exit(f"--art must be .svg, .png, .jpg or .webp, not {ext}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--id", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--appearance", choices=("dark", "light"), required=True)
    ap.add_argument("--base", required=True, help="background colour, hex")
    ap.add_argument("--accent", required=True, help="buttons, links, switches, hex")
    ap.add_argument("--text", required=True, help="reading colour and every edge, hex")
    ap.add_argument("--tint", help="glass colour, hex (default: derived from --base)")
    ap.add_argument("--art", help="an image shown behind the whole window (.svg, .png, .jpg, .webp)")
    ap.add_argument("--out", help="output file (default: <id>.json in the current folder)")
    a = ap.parse_args()

    problems = []
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", a.id) or a.id in RESERVED:
        problems.append(f"id {a.id!r}: use lowercase letters, numbers and hyphens, not a built-in id ({', '.join(sorted(RESERVED))})")
    if len(a.name.strip()) == 0 or len(a.name) > 48:
        problems.append("name: 1 to 48 characters")
    for flag in ("base", "accent", "text", "tint"):
        value = getattr(a, flag)
        if value is not None and not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
            problems.append(f"--{flag} {value!r}: use a 6-digit hex colour like #1a2b3c")
    if problems:
        sys.exit("Not written:\n  " + "\n  ".join(problems))

    dark = a.appearance == "dark"
    tint = a.tint or (build.mix(a.base, "#000000", 0.3) if dark else build.mix(a.base, "#ffffff", 0.45))
    scene = {"id": a.id, "title": a.name, "window": a.appearance, "glass": {"tint": tint, "blur": 16, "opacity": 0.5}}
    build.PALETTES[a.id] = (a.base, a.accent, a.text)
    p = build.palette(scene)
    problems += build.check_contrast(a.id, p)
    credit = f"/* {a.name}: made with tools/new_theme.py from github.com/burntcookiedough/t3code-themes */"
    css = build.css_for(scene, p, scene_background(a.art, a.base, dark), 0.34 if dark else 0.42, credit=credit)
    if len(css) > build.CSS_LIMIT:
        problems.append(f"CSS is {len(css)} characters; T3 allows {build.CSS_LIMIT}. Use smaller art (or an SVG).")
    if "\\" in css:
        problems.append("CSS contains a backslash, which T3 drops")
    if problems:
        sys.exit("Not written. Adjust the colours (usually --text or --base) and run again:\n  " + "\n  ".join(problems))

    theme = {"version": 1, "id": a.id, "name": a.name.strip(), "appearance": a.appearance,
             "canvas": a.base, "accent": a.accent, "colors": build.roles(p), "css": css}
    out = a.out or f"{a.id}.json"
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(theme, fh, indent=2, ensure_ascii=False)
    print(f"Wrote {out}: {a.appearance}, {len(css)} CSS characters, every contrast check passed.")
    print("Install: Settings > Appearance > Add theme (drop the file in), or: t3 theme set " + out)


if __name__ == "__main__":
    main()
