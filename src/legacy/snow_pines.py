"""Generate the Snow Pines T3 Code theme CSS (scene art as embedded SVG)."""
import random
import sys

OUT = sys.argv[1]


def f(v):
    return str(round(v)) if abs(v) >= 10 else f"{v:.1f}".rstrip("0").rstrip(".")


def tree(cx, base, h, body, shade, snow, snow_op, rng):
    """A layered pine: stacked tiers with a shaded right half and snow on each tier's top."""
    w = h * 0.46
    trunk = h * 0.07
    top = base - h
    crown_bottom = base - trunk
    n = max(3, int(h / 42))
    step = (crown_bottom - top) / n
    out = [f"<rect x='{f(cx - h*0.025)}' y='{f(crown_bottom - 2)}' width='{f(h*0.05)}' height='{f(trunk + 2)}' fill='#1a1f38'/>"]
    for i in range(n):
        ty = top + i * step * 0.92
        by = top + (i + 1) * step + step * 0.25
        tw = w * (0.04 + 0.5 * i / n)
        bw = w * (0.32 + 0.68 * (i + 1) / n)
        droop = step * 0.18
        l_top, r_top = cx - tw / 2, cx + tw / 2
        l_bot, r_bot = cx - bw / 2, cx + bw / 2
        out.append(
            f"<polygon points='{f(l_top)},{f(ty)} {f(r_top)},{f(ty)} {f(r_bot)},{f(by + droop)} "
            f"{f(cx)},{f(by)} {f(l_bot)},{f(by + droop)}' fill='{body}'/>"
        )
        out.append(
            f"<polygon points='{f(cx)},{f(ty)} {f(r_top)},{f(ty)} {f(r_bot)},{f(by + droop)} {f(cx)},{f(by)}' fill='{shade}'/>"
        )
        # Snow: a jagged band along the top of the tier.
        depth = 0.2 + rng.random() * 0.1
        sl = l_top + (l_bot - l_top) * depth
        sr = r_top + (r_bot - r_top) * depth
        sy = ty + (by + droop - ty) * depth
        pts = [(l_top, ty), (r_top, ty), (sr, sy)]
        k = 3
        for j in range(1, k):
            x = sr + (sl - sr) * j / k
            y = sy - (by - ty) * (0.04 + 0.08 * rng.random()) * (1 if j % 2 else 0.4)
            pts.append((x, y))
        pts.append((sl, sy))
        out.append(
            "<polygon points='" + " ".join(f"{f(x)},{f(y)}" for x, y in pts)
            + f"' fill='{snow}' opacity='{snow_op}'/>"
        )
    return "".join(out)


def cluster(width, height, seed, mirror, cabin):
    rng = random.Random(seed)
    g = []
    ground = height - 46

    def x_at(frac):
        return width * (1 - frac) if mirror else width * frac

    # Far row: hazy blue pines.
    for _ in range(6):
        fr = rng.uniform(0.0, 0.85)
        h = rng.uniform(120, 190) * (1.15 - fr * 0.5)
        g.append(tree(x_at(fr), ground - 18, h, "#2a3466", "#252d5c", "#9fadde", 0.45, rng))
    # Haze between rows.
    g.append(f"<rect x='0' y='{height-150}' width='{width}' height='150' fill='url(#haze)'/>")
    # Mid row.
    for _ in range(4):
        fr = rng.uniform(0.0, 0.62)
        h = rng.uniform(170, 260) * (1.12 - fr * 0.6)
        g.append(tree(x_at(fr), ground - 6, h, "#1f4f5c", "#1a4351", "#d3def6", 0.8, rng))
    # Front row: the big teal pines at the edge.
    for fr, h in [(0.05, 400), (0.2, 300), (0.33, 220), (0.45, 160)]:
        fr += rng.uniform(-0.02, 0.02)
        g.append(tree(x_at(fr), ground + 8, h * rng.uniform(0.92, 1.05), "#1b5a55", "#164a47", "#eef3ff", 0.95, rng))
    if cabin:
        cx = x_at(0.58)
        cy = ground + 4
        g.append(
            f"<rect x='{f(cx-26)}' y='{f(cy-30)}' width='52' height='30' fill='#2a2440'/>"
            f"<polygon points='{f(cx-34)},{f(cy-28)} {f(cx)},{f(cy-54)} {f(cx+34)},{f(cy-28)}' fill='#e9eefc'/>"
            f"<rect x='{f(cx-8)}' y='{f(cy-22)}' width='12' height='11' fill='#ffc76b'/>"
            f"<circle cx='{f(cx-2)}' cy='{f(cy-16)}' r='22' fill='url(#lamp)'/>"
        )
    # Snowy ground.
    if mirror:
        d = f"M0 {height} L0 {height-22} Q{width*0.5} {height-58} {width} {height-70} L{width} {height} Z"
    else:
        d = f"M0 {height} L0 {height-70} Q{width*0.5} {height-58} {width} {height-22} L{width} {height} Z"
    g.append(f"<path d='{d}' fill='url(#ground)'/>")
    defs = (
        "<defs>"
        "<linearGradient id='ground' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#dfe5fb'/><stop offset='1' stop-color='#8e8fc4'/></linearGradient>"
        "<linearGradient id='haze' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#3a3070' stop-opacity='0'/><stop offset='1' stop-color='#4a3d80' stop-opacity='.55'/></linearGradient>"
        "<radialGradient id='lamp'><stop offset='0' stop-color='#ffcf7a' stop-opacity='.55'/><stop offset='1' stop-color='#ffcf7a' stop-opacity='0'/></radialGradient>"
        "</defs>"
    )
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>"
        + defs + "".join(g) + "</svg>"
    )


def dots(size, count, rmin, rmax, omin, omax, seed, color="#ffffff"):
    rng = random.Random(seed)
    c = "".join(
        f"<circle cx='{f(rng.uniform(0,size))}' cy='{f(rng.uniform(0,size))}' r='{f(rng.uniform(rmin,rmax))}' opacity='{f(rng.uniform(omin,omax))}'/>"
        for _ in range(count)
    )
    return f"<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}'><g fill='{color}'>{c}</g></svg>"


def uri(svg):
    return "url(\"data:image/svg+xml," + svg.replace("%", "%25").replace("#", "%23").replace("<", "%3C").replace(">", "%3E") + "\")"


left = cluster(620, 520, 7, False, False)
right = cluster(620, 520, 11, True, True)
stars = dots(360, 26, 0.5, 1.1, 0.35, 0.85, 3)
snow_far = dots(220, 14, 0.7, 1.2, 0.35, 0.6, 5, "#e6ecff")
snow_mid = dots(320, 8, 1.1, 1.7, 0.4, 0.65, 9)
snow_near = dots(480, 5, 1.8, 2.6, 0.45, 0.75, 13)

layers = [
    (uri(right), "auto min(62%, 520px)", "no-repeat", "100% 100%", "100% 100%"),
    (uri(left), "auto min(62%, 520px)", "no-repeat", "0 100%", "0 100%"),
    (uri(snow_near), "480px 480px", "repeat", "0 0", "480px 960px"),
    (uri(snow_mid), "320px 320px", "repeat", "0 0", "-320px 640px"),
    (uri(snow_far), "220px 220px", "repeat", "0 0", "220px 440px"),
    (uri(stars), "360px 360px", "repeat", "0 0", "0 0"),
    ("radial-gradient(120% 60% at 50% 100%, #5a4690 0%, rgba(90,70,144,0) 70%)", "100% 100%", "no-repeat", "0 0", "0 0"),
    ("linear-gradient(180deg, #110f2a 0%, #1a1740 38%, #28215a 70%, #3b2f6e 100%)", "100% 100%", "no-repeat", "0 0", "0 0"),
]

images = ",\n    ".join(l[0] for l in layers)
sizes = ", ".join(l[1] for l in layers)
repeats = ", ".join(l[2] for l in layers)
starts = ", ".join(l[3] for l in layers)
ends = ", ".join(l[4] for l in layers)

css = f"""/* Snow Pines: night sky, stars, falling snow, pine clusters at the edges */
[data-workspace-area="conversation"] {{
  background-color: #1a1740 !important;
  background-image:
    {images} !important;
  background-size: {sizes} !important;
  background-repeat: {repeats} !important;
  background-position: {starts};
  animation: snow-pines-fall 60s steps(960) infinite;
}}

@keyframes snow-pines-fall {{
  from {{ background-position: {starts}; }}
  to   {{ background-position: {ends}; }}
}}

@media (prefers-reduced-motion: reduce) {{
  [data-workspace-area="conversation"] {{ animation: none; }}
}}

/* Let the scene show through the chat */
.messages-timeline-scroll,
[data-chat-composer-form] {{
  background: transparent !important;
}}

[data-chat-header] {{
  background: rgba(17, 15, 42, 0.6) !important;
  backdrop-filter: blur(12px);
  border-color: rgba(170, 184, 230, 0.12) !important;
}}

/* Frosted cards so text stays readable over the art */
[data-user-message-bubble] {{
  background: rgba(40, 36, 84, 0.78) !important;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(190, 205, 255, 0.16) !important;
}}

[data-message-role="assistant"] .chat-markdown {{
  text-shadow: 0 1px 3px rgba(8, 6, 28, 0.85);
}}

.chat-markdown-codeblock {{
  background: rgba(17, 15, 40, 0.88) !important;
}}

[data-slot="composer-host"] {{
  background: rgba(20, 18, 46, 0.82) !important;
  backdrop-filter: blur(14px);
  border-color: rgba(170, 190, 255, 0.22) !important;
  box-shadow: 0 10px 34px rgba(5, 4, 20, 0.5);
}}

[data-slot="sidebar-inner"] {{
  background: linear-gradient(180deg, #100e27 0%, #16133a 100%) !important;
}}

[data-slot="scroll-area-thumb"],
::-webkit-scrollbar-thumb {{
  background: rgba(170, 190, 255, 0.25) !important;
  border-radius: 8px;
}}
"""

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write(css)
with open(OUT.replace(".css", "-preview.svg"), "w", encoding="utf-8") as fh:
    fh.write(left)
print(len(css), "chars")
