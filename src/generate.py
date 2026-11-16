"""Soft Bloom - a dithered, dreamy dark theme for T3 Code.

Generates the theme JSON (colour roles + CSS with embedded SVG art).

    python src/generate.py themes/soft-bloom.json
    t3 theme set themes/soft-bloom.json

See README.md and docs/ for how the theme is built and why.
"""
import json
import random
import sys

OUT = sys.argv[1]

P = dict(base="#09090b", deep="#060607", skyTop="#060607", skyBottom="#0d0c0f", surface="#121215",
         raised="#18181c", hover="#1f1f24", input="#2a2a30", line="#1b1b20", bubble="#16161a",
         text="#ede6d6", muted="#9b968c", faint="#938d84", accent="#f1e7d0", accentHover="#faf1de")
CREAM = P["accent"]
INK = "#060607"        # deep glass tint for popups / dialogs (darker than the scene)
INK_SOLID = "#08080a"  # solid fill for knobs and triggers inside dialogs


def uri(svg):
    enc = svg.replace("%", "%25").replace("#", "%23").replace("<", "%3C").replace(">", "%3E").replace('"', "'")
    return f'url("data:image/svg+xml,{enc}")'


def rgba(hex_color, a):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {a})"


def dither_filter(fid, blur, freq, seed, levels="0 0.08 0.13 0.19 0.26 0.34 0.43 0.53 0.64 0.76 0.88 1", bias=0.44):
    """Blur -> posterize into bands -> subtract noise -> hard threshold = stippled dither."""
    return (
        f"<filter id='{fid}' x='-50%' y='-50%' width='200%' height='200%' color-interpolation-filters='sRGB'>"
        f"<feGaussianBlur in='SourceAlpha' stdDeviation='{blur}' result='b'/>"
        f"<feComponentTransfer in='b' result='p'><feFuncA type='discrete' tableValues='{levels}'/></feComponentTransfer>"
        f"<feTurbulence type='fractalNoise' baseFrequency='{freq}' numOctaves='1' seed='{seed}' result='t'/>"
        "<feColorMatrix in='t' type='matrix' values='0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0' result='n0'/>"
        "<feComponentTransfer in='n0' result='n'><feFuncA type='linear' slope='3.4' intercept='-1.2'/></feComponentTransfer>"
        f"<feComposite in='p' in2='n' operator='arithmetic' k1='0' k2='1' k3='-1' k4='{bias}' result='d'/>"
        "<feComponentTransfer in='d' result='m'><feFuncA type='discrete' tableValues='0 1'/></feComponentTransfer>"
        f"<feFlood flood-color='{CREAM}' result='c'/>"
        "<feComposite in='c' in2='m' operator='in'/>"
        "</filter>"
    )


def star_points(cx, cy, r, inner, rot=-90):
    import math
    pts = []
    for i in range(10):
        rad = r if i % 2 == 0 else r * inner
        a = math.radians(rot) + i * math.pi / 5
        pts.append(f"{cx + math.cos(a) * rad:.0f},{cy + math.sin(a) * rad:.0f}")
    return " ".join(pts)


def bloom_svg():
    """A big star outline, rendered as a dithered glow. Hollow centre like the photo."""
    s = 520
    pts = star_points(s / 2, s / 2 + 12, 190, 0.43, rot=-72)
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{s}' height='{s}' viewBox='0 0 {s} {s}'>"
        f"<defs>{dither_filter('d', 30, 0.42, 7)}</defs>"
        f"<polygon points='{pts}' fill='none' stroke='#000' stroke-width='46' stroke-linejoin='round' filter='url(#d)'/>"
        "</svg>"
    )


def halo_svg():
    """A faint dithered moon-glow for the opposite corner."""
    s = 360
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{s}' height='{s}' viewBox='0 0 {s} {s}'>"
        f"<defs>{dither_filter('h', 40, 0.7, 13, levels="0 0.06 0.1 0.15 0.21 0.28 0.36 0.45")}</defs>"
        f"<circle cx='{s/2}' cy='{s/2}' r='80' filter='url(#h)'/>"
        "</svg>"
    )


def sparkle(x, y, size, op):
    """Pixel-art sparkle: a plus of 1px arms around a 2x2 core (crisp edges)."""
    a = size
    return (
        f"<g opacity='{op}'>"
        f"<rect x='{x}' y='{y}' width='2' height='2'/>"
        f"<rect x='{x - a}' y='{y}' width='{a}' height='1' opacity='.75'/>"
        f"<rect x='{x + 2}' y='{y + 1}' width='{a}' height='1' opacity='.75'/>"
        f"<rect x='{x + 1}' y='{y - a}' width='1' height='{a}' opacity='.75'/>"
        f"<rect x='{x}' y='{y + 2}' width='1' height='{a}' opacity='.75'/>"
        "</g>"
    )


def stars_svg(size, seed):
    rng = random.Random(seed)
    parts = []
    for _ in range(9):
        x, y = rng.randint(12, size - 12), rng.randint(12, size - 12)
        parts.append(sparkle(x, y, rng.choice([2, 3, 3, 4, 5]), round(rng.uniform(0.45, 0.9), 2)))
    for _ in range(16):
        x, y = rng.randint(4, size - 4), rng.randint(4, size - 4)
        parts.append(f"<rect x='{x}' y='{y}' width='1' height='1' opacity='{round(rng.uniform(0.25, 0.7), 2)}'/>")
    for _ in range(3):
        x, y = rng.randint(30, size - 30), rng.randint(30, size - 30)
        parts.append(f"<circle cx='{x}' cy='{y}' r='7' filter='url(#g)'/>")
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}' shape-rendering='crispEdges'>"
        f"<defs>{dither_filter('g', 4, 0.9, 3, levels='0 0.35 0.7 1')}</defs>"
        f"<g fill='{CREAM}'>{''.join(parts)}</g></svg>"
    )


def stipple_grain(op):
    """Sparse 1px dither speckle instead of smooth film grain."""
    return (
        "<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'>"
        "<filter id='s' x='0' y='0' width='100%' height='100%'>"
        "<feTurbulence type='fractalNoise' baseFrequency='1.6' numOctaves='1' seed='5' stitchTiles='stitch'/>"
        "<feColorMatrix type='matrix' values='0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 2.4 0 0 0 -1.35'/>"
        "<feComponentTransfer><feFuncA type='discrete' tableValues='0 1'/></feComponentTransfer>"
        "</filter>"
        f"<rect width='160' height='160' filter='url(#s)' opacity='{op}'/></svg>"
    )


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


CSS = f"""/* Soft Bloom v8 - one dithered scene behind the whole window; sidebar and chat sit on top as glass. */

/* The scene lives on the root layout wrapper, so it spans sidebar + chat */
[data-slot="sidebar-wrapper"] {{
  position: relative;
  isolation: isolate;
  background-color: {P['base']} !important;
  background-image:
    {uri(stipple_grain(0.10))},
    radial-gradient(120% 90% at 55% 45%, transparent 55%, rgba(0, 0, 0, 0.6) 100%),
    linear-gradient(180deg, {P['skyTop']} 0%, {P['base']} 55%, {P['skyBottom']} 100%) !important;
  background-size: 160px 160px, 100% 100%, 100% 100% !important;
  background-repeat: repeat, no-repeat, no-repeat !important;
}}

/* Pixel sparkles + faint dithered halo (top-left, seen blurred through the sidebar).
   Faded where the reading column usually sits. */
[data-slot="sidebar-wrapper"]::before {{
  content: "";
  position: absolute;
  inset: 0;
  z-index: -1;
  pointer-events: none;
  background-image: {uri(stars_svg(460, 11))}, {uri(halo_svg())};
  background-size: 460px 460px, 420px 420px;
  background-repeat: repeat, no-repeat;
  background-position: 30px 20px, left -120px top -110px;
  -webkit-mask-image: linear-gradient(90deg, #000 0%, #000 20%, rgba(0, 0, 0, 0.16) 30%, rgba(0, 0, 0, 0.16) 78%, #000 88%, #000 100%);
          mask-image: linear-gradient(90deg, #000 0%, #000 20%, rgba(0, 0, 0, 0.16) 30%, rgba(0, 0, 0, 0.16) 78%, #000 88%, #000 100%);
}}

/* The big dithered star, bottom-right in the empty gutter */
[data-slot="sidebar-wrapper"]::after {{
  content: "";
  position: absolute;
  inset: 0;
  z-index: -1;
  pointer-events: none;
  background-image: {uri(bloom_svg())};
  background-size: 560px 560px;
  background-repeat: no-repeat;
  background-position: right -150px bottom -170px;
  opacity: 0.42;
  -webkit-mask-image: linear-gradient(270deg, #000 0%, #000 7%, rgba(0, 0, 0, 0.22) 22%, rgba(0, 0, 0, 0.22) 100%);
          mask-image: linear-gradient(270deg, #000 0%, #000 7%, rgba(0, 0, 0, 0.22) 22%, rgba(0, 0, 0, 0.22) 100%);
}}

/* ---------- Design tokens ----------
   T3 builds every surface from these tokens, so setting them here restyles
   screens and panels I never touch directly. Re-declared on [data-app-sidebar]
   because T3 redefines its tokens there. */
:root, [data-app-sidebar] {{
  --border: {rgba(CREAM, 0.075)} !important;
  --input: {rgba(CREAM, 0.12)} !important;
  --accent: {rgba(CREAM, 0.065)} !important;
  --muted: {rgba(CREAM, 0.05)} !important;
  --secondary: {rgba(CREAM, 0.055)} !important;
  --surface-raised: {rgba(CREAM, 0.055)} !important;
  --card: rgba(22, 22, 26, 0.55) !important;
  --popover: rgba(16, 16, 19, 0.86) !important;
  --code-background: rgba(6, 6, 7, 0.72) !important;
  --app-chrome-background: rgba(6, 6, 7, 0.55) !important;
  --toolbar-background: rgba(6, 6, 7, 0.55) !important;
  --toolbar-border: {rgba(CREAM, 0.06)} !important;
  --toolbar-control: {rgba(CREAM, 0.05)} !important;
  --toolbar-control-hover: {rgba(CREAM, 0.085)} !important;
  --sidebar-border: {rgba(CREAM, 0.06)} !important;
  --surface-grain: none !important;
}}

/* Clear every opaque layer between the scene and the content */
[data-slot="sidebar-inset"],
[data-slot="sidebar-inset"] > *:has(> [data-chat-column]),
[data-workspace-area="conversation"],
[data-workspace-area="conversation"] > [data-timeline-loading],
[data-workspace-area="conversation"] > .bg-background,
.messages-timeline-scroll,
[data-chat-composer-form] {{
  background-color: transparent !important;
  background-image: none !important;
}}

/* Sidebar: frosted glass over the scene. The scene is static, so the blur is computed once. */
[data-slot="sidebar-inner"] {{
  background-color: {rgba(P['deep'], 0.5)} !important;
  background-image: none !important;
  backdrop-filter: blur(14px) saturate(115%);
  border-right: 1px solid {rgba(CREAM, 0.06)};
}}

/* Right panel (browser, terminal, files, diff): tinted, no live blur, because it slides and resizes */
[data-workspace-area="panel"] {{
  background-color: {rgba(P['deep'], 0.9)} !important;
  background-image: none !important;
  border-left: 1px solid {rgba(CREAM, 0.06)};
}}

[data-thread-terminal-drawer] {{
  border-top: 1px solid {rgba(CREAM, 0.07)};
}}

/* Pull requests list runs to the right edge: shade the star behind it */
[data-workspace-area="pull-requests"] {{
  background-color: transparent !important;
  background-image: linear-gradient(270deg, {rgba(P['base'], 0.82)} 0%, {rgba(P['base'], 0.5)} 18%, transparent 34%) !important;
}}

/* Page headers (chat, pull requests) share one glass bar */
[data-workspace-area="pull-requests"] > header {{
  background: {rgba(P['deep'], 0.72)} !important;
  backdrop-filter: blur(8px);
  border-bottom: 1px solid {rgba(CREAM, 0.06)};
}}

[data-chat-header] {{
  background: {rgba(P['deep'], 0.72)} !important;
  backdrop-filter: blur(8px);
  border-color: {rgba(CREAM, 0.06)} !important;
}}

/* Frosted glass */
[data-user-message-bubble] {{
  background: {rgba(P['bubble'], 0.92)} !important;
  border: 1px solid {rgba(CREAM, 0.09)} !important;
  box-shadow: inset 0 1px 0 {rgba(CREAM, 0.05)}, 0 6px 24px rgba(0, 0, 0, 0.4);
}}

/* ---------- Chat bar ----------
   Uses T3's own glass layer (tuned here) instead of stacking a second one. */
[data-slot="composer-shell"] {{
  --glass-opacity: 50%;
  --glass-blur: 16px;
  --glass-saturation: 1.12;
  --chat-composer-glass-surface: #141417;
  --chat-composer-outline: {rgba(CREAM, 0.11)};
  --chat-composer-highlight: {rgba(CREAM, 0.07)};
}}

[data-slot="composer-host"] {{
  box-shadow: 0 14px 44px rgba(0, 0, 0, 0.55) !important;
}}

[data-slot="composer-host"] [contenteditable="true"] {{
  caret-color: {CREAM};
}}

/* Focus: the bar's own edge warms to cream and a soft glow fades in.
   One transition on focus; nothing runs while idle. */
[data-slot="composer-host"] {{
  transition: box-shadow 0.35s ease;
}}

[data-slot="composer-host"]:focus-within {{
  box-shadow: 0 0 0 1px {rgba(CREAM, 0.18)}, 0 0 28px {rgba(CREAM, 0.08)}, 0 14px 44px rgba(0, 0, 0, 0.55) !important;
}}

[data-slot="composer-host"]:focus-within:not(:has([contenteditable="true"] > p:only-child > br.ProseMirror-trailingBreak:only-child)) {{
  box-shadow: 0 0 0 1px {rgba(CREAM, 0.26)}, 0 0 32px {rgba(CREAM, 0.11)}, 0 14px 44px rgba(0, 0, 0, 0.55) !important;
}}

/* Send button: a small pop when it becomes ready, a press when clicked */
[data-chat-composer-form] button[type="submit"] {{
  transition: transform 0.18s cubic-bezier(0.2, 0.9, 0.3, 1.4), box-shadow 0.3s ease, background-color 0.3s ease !important;
}}

[data-chat-composer-form] button[type="submit"]:enabled {{
  box-shadow: 0 0 0 1px {rgba(CREAM, 0.3)}, 0 0 18px {rgba(CREAM, 0.22)} !important;
  animation: sb-send-ready 0.5s cubic-bezier(0.2, 0.9, 0.3, 1.3);
}}

[data-chat-composer-form] button[type="submit"]:enabled:active {{
  transform: scale(0.92);
}}

@keyframes sb-send-ready {{
  0%   {{ transform: scale(0.86); }}
  60%  {{ transform: scale(1.08); }}
  100% {{ transform: scale(1); }}
}}

/* Pasted images / attachments: clean, solid tiles with a hairline edge */
[data-slot="composer-context-strip"] {{
  background: transparent !important;
  backdrop-filter: none !important;
}}

[data-slot="composer-host"] .group\\/attachment,
[data-slot="composer-host"] [class*="group/attachment"] {{
  background: {P['deep']} !important;
  border-color: {rgba(CREAM, 0.12)} !important;
  isolation: isolate;
}}

[data-message-role="assistant"] .chat-markdown {{
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.7);
}}

.chat-markdown a,
[data-user-message-bubble] a {{
  color: {CREAM} !important;
  text-decoration-color: {rgba(CREAM, 0.35)} !important;
  text-underline-offset: 3px;
}}

.chat-markdown-codeblock {{
  background: {rgba(P['deep'], 0.85)} !important;
  border: 1px solid {rgba(CREAM, 0.06)};
}}

/* ---------- Popups & overlays ----------
   Every T3 popup slot ends in "-popup" (dialog, sheet, command palette, alert,
   popover, menu, select, combobox, autocomplete, preview card, toast, tooltip). */
/* Deep ink glass: darker than the scene behind it, so opening a popup feels like
   sinking into it rather than lifting a lighter panel on top.
   Follows Settings > Appearance > Glass opacity (+12% so it stays deep). */
[data-slot$="-popup"] {{
  background-color: color-mix(in srgb, {INK} min(100%, calc(var(--glass-opacity, 80%) + 12%)), transparent) !important;
  background-image: none !important;
  backdrop-filter: blur(24px) saturate(105%) !important;
  border-color: {rgba(CREAM, 0.08)} !important;
  box-shadow:
    inset 0 1px 0 {rgba(CREAM, 0.06)},
    0 0 0 1px rgba(0, 0, 0, 0.6),
    0 30px 90px rgba(0, 0, 0, 0.7) !important;
}}

/* Small popups usually sit over text: nearly solid */
[data-slot="popover-popup"],
[data-slot="menu-popup"],
[data-slot="select-popup"],
[data-slot="combobox-popup"],
[data-slot="autocomplete-popup"],
[data-slot="preview-card-popup"],
[data-slot="toast-popup"] {{
  background-color: color-mix(in srgb, {INK} min(100%, calc(var(--glass-opacity, 80%) + 14%)), transparent) !important;
}}

[data-slot="tooltip-popup"] {{
  background-color: rgba(10, 10, 12, 0.96) !important;
  backdrop-filter: blur(10px) !important;
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.6), 0 10px 28px rgba(0, 0, 0, 0.6) !important;
}}

/* Dim layers behind modals (the popover click-catcher stays invisible) */
[data-slot$="-backdrop"]:not([data-slot="popover-backdrop"]) {{
  background-color: rgba(2, 2, 3, 0.62) !important;
  backdrop-filter: blur(4px) !important;
}}

/* Inside big modals (Settings, Usage, command palette, sheets): quiet glass-over-glass.
   Cream reads as a soft edge, not a fill. */
[data-slot="dialog-popup"],
[data-slot="sheet-popup"],
[data-slot="alert-dialog-popup"],
[data-slot="command-dialog-popup"] {{
  /* Solid on purpose: switch knobs and select triggers paint with --background. */
  --background: {INK_SOLID};
  --sidebar: transparent;
  --card: {rgba(CREAM, 0.045)};
  --sidebar-row-hover: {rgba(CREAM, 0.035)};
  --sidebar-row-active: {rgba(CREAM, 0.06)};
  --sidebar-row-selected: {rgba(CREAM, 0.055)};
}}

/* Settings nav: a shade deeper than the content, like the app sidebar */
[data-slot="dialog-popup"] nav {{
  background-color: rgba(0, 0, 0, 0.22) !important;
  border-right: 1px solid {rgba(CREAM, 0.05)};
}}

[data-slot="dialog-popup"] [data-slot="settings-group"] {{
  border: 1px solid {rgba(CREAM, 0.055)};
  box-shadow: inset 0 1px 0 {rgba(CREAM, 0.03)};
}}

/* ---------- Sidebar ---------- */
[data-sidebar-row] {{
  transition: background-color 0.2s ease;
}}

/* ---------- Small interactions ---------- */
[data-slot="button"] {{
  transition: transform 0.12s ease, background-color 0.18s ease, color 0.18s ease, border-color 0.18s ease;
}}

[data-slot="button"]:active:not(:disabled) {{
  transform: scale(0.96);
}}

.chat-markdown a {{
  transition: text-decoration-color 0.2s ease;
}}

[data-user-message-bubble] {{
  transition: border-color 0.25s ease;
}}

[data-user-message-bubble]:hover {{
  border-color: {rgba(CREAM, 0.16)} !important;
}}

@media (prefers-reduced-motion: reduce) {{
  [data-chat-composer-form] button[type="submit"] {{
    animation: none !important;
  }}
  [data-slot="button"],
  [data-sidebar-row],
  [data-slot="composer-host"] {{
    transition: none !important;
  }}
}}

::selection {{
  background: {rgba(CREAM, 0.28)};
}}

[data-slot="scroll-area-thumb"],
::-webkit-scrollbar-thumb {{
  background: {rgba(CREAM, 0.16)} !important;
  border-radius: 8px;
}}
"""

theme = {"version": 1, "name": "Soft Bloom", "appearance": "dark", "canvas": P["base"], "accent": P["accent"],
         "colors": roles(P), "css": CSS}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(theme, fh, indent=2)
print(len(CSS), "chars css")
