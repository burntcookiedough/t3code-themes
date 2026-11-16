"""Generate three "Ink & Bloom" T3 Code themes (colors + CSS with embedded SVG art).

Usage: python -I gen.py <out_dir>
Writes ink-bloom-<variant>.json for each variant and prints CSS sizes.
"""
import json
import math
import random
import sys

OUT_DIR = sys.argv[1]


def n(v):
    return str(round(v)) if abs(v) >= 10 else f"{v:.1f}".rstrip("0").rstrip(".")


def uri(svg):
    enc = svg.replace("%", "%25").replace("#", "%23").replace("<", "%3C").replace(">", "%3E").replace('"', "'")
    return f'url("data:image/svg+xml,{enc}")'


def rgba(hex_color, alpha):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"


# ---------- art primitives ----------

def star_points(cx, cy, r, points, inner, rng, wobble=0.12):
    """A slightly irregular, hand-drawn looking star."""
    rot = rng.uniform(0, math.pi * 2)
    pts = []
    for i in range(points * 2):
        rad = r if i % 2 == 0 else r * inner
        rad *= 1 + rng.uniform(-wobble, wobble)
        a = rot + i * math.pi / points
        pts.append(f"{n(cx + math.cos(a) * rad)},{n(cy + math.sin(a) * rad)}")
    return " ".join(pts)


def stars_tile(size, count, rmin, rmax, color, glow_every, glow_op, dash_count, seed, star_op=0.95):
    rng = random.Random(seed)
    glow, crisp = [], []
    for i in range(count):
        x, y = rng.uniform(16, size - 16), rng.uniform(16, size - 16)
        r = rng.uniform(rmin, rmax)
        pts = rng.choice([4, 5, 5, 6])
        inner = 0.32 if pts == 4 else rng.uniform(0.38, 0.48)
        p = star_points(x, y, r, pts, inner, rng)
        crisp.append(f"<polygon points='{p}' opacity='{n(rng.uniform(star_op - 0.25, star_op))}'/>")
        if glow_every and i % glow_every == 0:
            glow.append(f"<circle cx='{n(x)}' cy='{n(y)}' r='{n(r * 2.2)}'/>")
    for _ in range(dash_count):
        x, y = rng.uniform(16, size - 16), rng.uniform(16, size - 16)
        crisp.append(
            f"<ellipse cx='{n(x)}' cy='{n(y)}' rx='{n(rng.uniform(4, 8))}' ry='{n(rng.uniform(1.4, 2.4))}' opacity='{n(rng.uniform(0.35, 0.7))}'/>"
        )
    defs = "<filter id='g' x='-50%' y='-50%' width='200%' height='200%'><feGaussianBlur stdDeviation='6'/></filter>"
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}'><defs>{defs}</defs>"
        f"<g fill='{color}' filter='url(#g)' opacity='{glow_op}'>{''.join(glow)}</g>"
        f"<g fill='{color}'>{''.join(crisp)}</g></svg>"
    )


def ink_waves_tile(w, h, count, color, opacity, seed):
    """Horizontal, tapered, wavy brush strokes like the storybook sea."""
    rng = random.Random(seed)
    paths = []
    for _ in range(count):
        length = rng.uniform(140, 320)
        x0 = rng.uniform(10, w - length - 10)
        y0 = rng.uniform(14, h - 14)
        thick = rng.uniform(5, 13)
        segs = rng.randint(3, 5)
        step = length / segs
        top = [(x0, y0)]
        for s in range(1, segs + 1):
            top.append((x0 + s * step, y0 + rng.uniform(-6, 6) - thick * math.sin(math.pi * s / segs) * 0.6))
        bot = []
        for s in range(segs, -1, -1):
            taper = math.sin(math.pi * s / segs)
            bot.append((x0 + s * step + rng.uniform(-4, 4), top[s][1] + thick * taper + rng.uniform(0, 3)))
        d = f"M{n(top[0][0])} {n(top[0][1])}"
        for i in range(1, len(top)):
            (px, py), (qx, qy) = top[i - 1], top[i]
            d += f" Q{n((px + qx) / 2)} {n(py - rng.uniform(2, 7))} {n(qx)} {n(qy)}"
        for i in range(1, len(bot)):
            (px, py), (qx, qy) = bot[i - 1], bot[i]
            d += f" Q{n((px + qx) / 2)} {n(py + rng.uniform(2, 6))} {n(qx)} {n(qy)}"
        paths.append(f"<path d='{d} Z'/>")
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}'>"
        f"<g fill='{color}' opacity='{opacity}'>{''.join(paths)}</g></svg>"
    )


def bloom_star(size, color, stroke, blur, opacity):
    """One big star outline, blurred into a soft glow (the second inspo image)."""
    rng = random.Random(42)
    c = size / 2
    pts = star_points(c, c, size * 0.36, 5, 0.42, rng, wobble=0.04)
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}' viewBox='0 0 {size} {size}'>"
        f"<defs><filter id='b' x='-40%' y='-40%' width='180%' height='180%'><feGaussianBlur stdDeviation='{blur}'/></filter></defs>"
        f"<polygon points='{pts}' fill='none' stroke='{color}' stroke-width='{stroke}' stroke-linejoin='round' filter='url(#b)' opacity='{opacity}'/>"
        f"<polygon points='{pts}' fill='{color}' filter='url(#b)' opacity='{opacity * 0.18}'/></svg>"
    )


def grain_tile(opacity):
    return (
        "<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'>"
        "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='2' stitchTiles='stitch'/>"
        "<feColorMatrix values='0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 1 0'/></filter>"
        f"<rect width='180' height='180' filter='url(#n)' opacity='{opacity}'/></svg>"
    )


# ---------- palette -> T3 color roles ----------

def roles(p):
    return {
        "canvas": p["base"], "chrome": p["deep"], "toolbar": p["deep"],
        "toolbarForeground": p["text"], "toolbarBorder": p["line"],
        "toolbarControl": p["raised"], "toolbarControlForeground": p["text"], "toolbarControlHover": p["hover"],
        "surface": p["surface"], "surfaceRaised": p["raised"], "surfaceOverlay": p["raised"],
        "text": p["text"], "textMuted": p["muted"], "border": p["line"], "input": p["input"],
        "focus": p["accent"], "accent": p["accent"], "accentForeground": p["deep"],
        "accentSurface": p["hover"], "accentSurfaceForeground": p["text"],
        "secondary": p["raised"], "secondaryForeground": p["text"],
        "muted": p["raised"], "mutedForeground": p["muted"],
        "placeholder": p["faint"], "secondaryLabel": p["muted"], "iconMuted": p["faint"],
        "error": "#e5737a", "errorForeground": "#f0a3a8", "errorSurface": "#2a1418",
        "warning": "#e0b36a", "warningForeground": "#ecc98e", "warningSurface": "#2a2214",
        "update": "#9ec8b8", "updateForeground": "#b6d8ca", "updateSurface": "#132420",
        "messageSurface": p["bubble"], "messageForeground": p["text"],
        "messageAction": p["accent"], "messageActionForeground": p["deep"], "messageActionHover": p["accentHover"],
        "codeBackground": p["deep"], "codeForeground": p["text"],
        "searchMatchBackground": "#5a4a24", "searchMatchForeground": p["text"],
        "searchMatchActiveBackground": p["accent"], "searchMatchActiveForeground": p["deep"],
        "sidebar": p["deep"], "sidebarForeground": p["text"], "sidebarMutedForeground": p["muted"],
        "sidebarControlSurface": p["surface"], "sidebarRowHover": p["surface"],
        "sidebarRowActive": p["raised"], "sidebarRowSelected": p["raised"], "sidebarBorder": p["line"],
        "terminalBackground": p["deep"], "terminalForeground": p["text"], "terminalCursor": p["accent"],
        "terminalSelection": p["input"], "terminalScrollbar": p["input"], "terminalScrollbarHover": p["faint"],
    }


# ---------- CSS ----------

def build_css(name, p, art_layers, art_sizes, art_repeat, art_pos, bloom, bloom_size, bloom_pos, grain_op, center_fade):
    cream = p["accent"]
    art_images = ",\n    ".join(art_layers) if art_layers else "none"
    return f"""/* {name} - Ink & Bloom family. Art lives on pseudo-layers behind the chat; the reading column stays calm. */

[data-workspace-area="conversation"] {{
  isolation: isolate;
  background-color: {p['base']} !important;
  background-image:
    {uri(grain_tile(grain_op))},
    radial-gradient(120% 90% at 50% 45%, transparent 55%, rgba(0, 0, 0, 0.55) 100%),
    linear-gradient(180deg, {p['skyTop']} 0%, {p['base']} 55%, {p['skyBottom']} 100%) !important;
  background-size: 180px 180px, 100% 100%, 100% 100% !important;
  background-repeat: repeat, no-repeat, no-repeat !important;
}}

/* Art layer: ink strokes + stars, faded out behind the reading column */
[data-workspace-area="conversation"]::before {{
  content: "";
  position: absolute;
  inset: 0;
  z-index: -1;
  pointer-events: none;
  background-image:
    {art_images};
  background-size: {art_sizes};
  background-repeat: {art_repeat};
  background-position: {art_pos};
  -webkit-mask-image: linear-gradient(90deg, #000 0%, #000 3%, rgba(0, 0, 0, {center_fade}) 11%, rgba(0, 0, 0, {center_fade}) 80%, #000 96%, #000 100%);
          mask-image: linear-gradient(90deg, #000 0%, #000 3%, rgba(0, 0, 0, {center_fade}) 11%, rgba(0, 0, 0, {center_fade}) 80%, #000 96%, #000 100%);
}}

/* Bloom layer: one big soft star glow that slowly breathes */
[data-workspace-area="conversation"]::after {{
  content: "";
  position: absolute;
  inset: 0;
  z-index: -1;
  pointer-events: none;
  background-image: {uri(bloom) if bloom else 'none'};
  background-size: {bloom_size};
  background-repeat: no-repeat;
  background-position: {bloom_pos};
  animation: ink-bloom-breathe 9s ease-in-out infinite alternate;
}}

@keyframes ink-bloom-breathe {{
  from {{ opacity: 0.72; }}
  to   {{ opacity: 1; }}
}}

@media (prefers-reduced-motion: reduce) {{
  [data-workspace-area="conversation"]::after {{ animation: none; }}
}}

/* Let the scene show through the chat */
.messages-timeline-scroll,
[data-chat-composer-form],
[data-workspace-area="conversation"] > [data-timeline-loading],
[data-workspace-area="conversation"] > .bg-background {{
  background: transparent !important;
}}

[data-chat-header] {{
  background: {rgba(p['deep'], 0.55)} !important;
  backdrop-filter: blur(14px) saturate(115%);
  border-color: {rgba(cream, 0.07)} !important;
}}

/* Frosted glass: translucent ink, blur, a hairline of cream light */
[data-user-message-bubble] {{
  background: {rgba(p['bubble'], 0.62)} !important;
  backdrop-filter: blur(16px) saturate(120%);
  border: 1px solid {rgba(cream, 0.10)} !important;
  box-shadow: inset 0 1px 0 {rgba(cream, 0.06)}, 0 6px 24px rgba(0, 0, 0, 0.35);
}}

[data-slot="composer-host"] {{
  background: {rgba(p['surface'], 0.58)} !important;
  backdrop-filter: blur(20px) saturate(125%);
  border: 1px solid {rgba(cream, 0.12)} !important;
  box-shadow: inset 0 1px 0 {rgba(cream, 0.07)}, 0 0 0 1px rgba(0, 0, 0, 0.25), 0 12px 40px rgba(0, 0, 0, 0.5), 0 0 60px {rgba(cream, 0.035)};
}}

[data-slot="composer-context-strip"] {{
  background: transparent !important;
  backdrop-filter: none !important;
}}

[data-slot="composer-host"]:focus-within {{
  border-color: {rgba(cream, 0.22)} !important;
  box-shadow: inset 0 1px 0 {rgba(cream, 0.08)}, 0 12px 40px rgba(0, 0, 0, 0.5), 0 0 70px {rgba(cream, 0.07)};
}}

[data-message-role="assistant"] .chat-markdown {{
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.7);
}}

/* Links: warm cream instead of default blue */
.chat-markdown a,
[data-user-message-bubble] a {{
  color: {cream} !important;
  text-decoration-color: {rgba(cream, 0.35)} !important;
  text-underline-offset: 3px;
}}

.chat-markdown a:hover {{
  text-decoration-color: {cream} !important;
}}

.chat-markdown-codeblock {{
  background: {rgba(p['deep'], 0.82)} !important;
  border: 1px solid {rgba(cream, 0.06)};
}}

/* Popups get the same glass */
[data-slot="popover-popup"],
[data-slot="menu-popup"],
[data-slot="dialog-popup"] {{
  background: {rgba(p['surface'], 0.86)} !important;
  backdrop-filter: blur(18px) saturate(120%);
  border-color: {rgba(cream, 0.10)} !important;
}}

[data-slot="tooltip-popup"] {{
  background: {rgba(p['raised'], 0.92)} !important;
  backdrop-filter: blur(10px);
}}

/* Sidebar: the darkest strip of the night, with the same grain */
[data-slot="sidebar-inner"] {{
  background-color: {p['deep']} !important;
  background-image: {uri(grain_tile(grain_op * 0.8))} !important;
  background-size: 180px 180px !important;
}}

[data-thread-item][data-active="true"],
[data-thread-item][aria-current="page"] {{
  box-shadow: inset 2px 0 0 {rgba(cream, 0.55)};
}}

/* Softer, lighter icons */
svg.lucide {{
  stroke-width: 1.6;
}}

::selection {{
  background: {rgba(cream, 0.28)};
}}

[data-slot="scroll-area-thumb"],
::-webkit-scrollbar-thumb {{
  background: {rgba(cream, 0.16)} !important;
  border-radius: 8px;
}}
"""


VARIANTS = {
    "ink-night": {
        "label": "Ink Night",
        "about": "Storybook sea: dark navy, visible ink waves, lots of hand-drawn cream stars, a faint bloom.",
        "p": dict(base="#0a0e19", deep="#070a12", skyTop="#070a13", skyBottom="#0e1424", surface="#111727",
                  raised="#161d30", hover="#1c2439", input="#253049", line="#1a2134", bubble="#151c2e",
                  text="#ece4d0", muted="#9a97a3", faint="#6f6e7d", accent="#efe2c0", accentHover="#f7ecd0"),
        "art": lambda c: (
            [uri(stars_tile(420, 22, 3, 8.5, c, 5, 0.55, 8, 7)),
             uri(stars_tile(300, 10, 1.6, 3.4, c, 0, 0, 4, 21, 0.8)),
             uri(ink_waves_tile(720, 460, 15, "#2a3a64", 0.55, 3))],
            "420px 420px, 300px 300px, 720px 460px", "repeat, repeat, repeat", "0 0, 140px 90px, 0 0"),
        "bloom": lambda c: bloom_star(700, c, 34, 30, 0.32),
        "bloom_size": "620px 620px", "bloom_pos": "right -200px top -230px",
        "grain": 0.07, "fade": 0.1,
    },
    "soft-bloom": {
        "label": "Soft Bloom",
        "about": "Film photo: warm near-black, one big glowing star, few soft stars, heavier grain. Minimal and moody.",
        "p": dict(base="#09090b", deep="#060607", skyTop="#060607", skyBottom="#0d0c0f", surface="#121215",
                  raised="#18181c", hover="#1f1f24", input="#2a2a30", line="#1b1b20", bubble="#16161a",
                  text="#ede6d6", muted="#9b968c", faint="#6d6a64", accent="#f1e7d0", accentHover="#faf1de"),
        "art": lambda c: (
            [uri(stars_tile(520, 9, 2.5, 6, c, 2, 0.7, 0, 11, 0.75))],
            "520px 520px", "repeat", "60px 40px"),
        "bloom": lambda c: bloom_star(760, c, 46, 38, 0.6),
        "bloom_size": "720px 720px", "bloom_pos": "left -260px bottom -260px",
        "grain": 0.11, "fade": 0.14,
    },
    "dream-tide": {
        "label": "Dream Tide",
        "about": "The blend: deep ink, faint waves, glowing cream stars, a soft bloom in the corner. Recommended.",
        "p": dict(base="#090b13", deep="#06080e", skyTop="#06080e", skyBottom="#0d1120", surface="#10141f",
                  raised="#151a28", hover="#1b2131", input="#242b3e", line="#181d2b", bubble="#141927",
                  text="#ece5d3", muted="#9a98a2", faint="#6e6d7b", accent="#efe3c4", accentHover="#f8eed4"),
        "art": lambda c: (
            [uri(stars_tile(460, 16, 2.6, 7.5, c, 3, 0.65, 5, 5)),
             uri(stars_tile(280, 8, 1.4, 2.8, c, 0, 0, 3, 17, 0.7)),
             uri(ink_waves_tile(760, 480, 11, "#22304f", 0.45, 9))],
            "460px 460px, 280px 280px, 760px 480px", "repeat, repeat, repeat", "0 0, 90px 130px, 0 0"),
        "bloom": lambda c: bloom_star(720, c, 40, 34, 0.42),
        "bloom_size": "640px 640px", "bloom_pos": "right -230px top -250px",
        "grain": 0.08, "fade": 0.1,
    },
}

for vid, v in VARIANTS.items():
    p = v["p"]
    layers, sizes, repeats, pos = v["art"](p["accent"])
    css = build_css(v["label"], p, layers, sizes, repeats, pos, v["bloom"](p["accent"]),
                    v["bloom_size"], v["bloom_pos"], v["grain"], v["fade"])
    theme = {"version": 1, "name": v["label"], "appearance": "dark",
             "canvas": p["base"], "accent": p["accent"], "colors": roles(p), "css": css}
    path = f"{OUT_DIR}/{vid}.json"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(theme, fh, indent=2)
    print(vid, len(css), "chars css")
