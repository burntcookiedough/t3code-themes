"""Builds T3 Code themes from the twenty scenes of Anthropic's theme-examples plugin.

    python build.py            # writes ../../themes/<id>.json for every scene

Each theme is the scene's own reduced-motion still (see scenemin.py), with the glass, popups,
dialogs and interactions of Soft Bloom (../soft-bloom/generate.py) recoloured for the scene. Light
scenes get light themes: T3 shows them when Settings > Appearance is Light (or System on a light OS).
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
THEMES_DIR = os.path.join(HERE, "..", "..", "themes")   # the repo's installable themes
sys.path.insert(0, HERE)
import scenemin  # noqa: E402

CSS_LIMIT = 50_000          # T3: longer CSS is dropped on import, silently
COLLECTION = {"id": "theme-examples-scenes", "label": "theme-examples scenes"}
# T3 reserves its built-in theme ids and names; a scene that shares one gets its own.
RENAMED = {"ember": ("ember-glow", "Ember Glow")}

# base: the scene's ground colour; accent: picked from its art; text: the reading colour.
PALETTES = {
    "honu-lagoon":        ("#86d9e4", "#9e2249", "#08303c"),
    "koi-mosaic":         ("#90d5ca", "#a4461a", "#0b3230"),
    "halftone-dawn":      ("#f4e4d0", "#ad4229", "#3a261d"),
    "halftone-dusk":      ("#212538", "#ec9068", "#ece4d8"),
    "plotter-tide":       ("#f3eee3", "#9e553b", "#2b2a33"),
    "plotter-tide-night": ("#141a27", "#e6ab94", "#e7e4dd"),
    "dither-dunes":       ("#ece2cd", "#a8432a", "#382c20"),
    "dither-dunes-night": ("#231d17", "#ef8456", "#f0e4d0"),
    "paper-garden":       ("#f8f2e6", "#b83f2c", "#2d3226"),
    "paper-garden-kraft": ("#2f2b25", "#f07f66", "#f2eadb"),
    "night-reef":         ("#0d1a3c", "#55d8c3", "#e3eef5"),
    "snow-pines":         ("#1c1d4d", "#f2bb92", "#eceefe"),
    "braille-stars":      ("#0b1230", "#b6c4ff", "#e8ecfb"),
    "teletext-clouds":    ("#14225c", "#f4cd52", "#eef1ff"),
    "vector-range":       ("#061611", "#86e3c3", "#e1f3ec"),
    "departure-board":    ("#1f1710", "#f2a33a", "#f4e7d4"),
    "blueprint":          ("#163f73", "#f2d27c", "#ecf3fc"),
    "deep-water":         ("#08354a", "#86e2e8", "#e3f5f7"),
    "aurora":             ("#090b22", "#74e8b0", "#eceaf9"),
    "ember":              ("#150709", "#ff9d58", "#f7e8e1"),
}


# ---------------------------------------------------------------- colour helpers

def rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hexc(c):
    return "#" + "".join(f"{max(0, min(255, round(v))):02x}" for v in c)


def mix(a, b, t):
    """a moved toward b by t (0..1)."""
    ca, cb = rgb(a), rgb(b)
    return hexc(tuple(x + (y - x) * t for x, y in zip(ca, cb)))


def rgba(h, a):
    r, g, b = rgb(h)
    return f"rgba({r},{g},{b},{a})"


def lum(h):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = rgb(h)
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


# ---------------------------------------------------------------- palette

def palette(scene):
    base, accent, text = PALETTES[scene["id"]]
    dark = scene["window"] == "dark"
    g = scene["glass"]
    tint = g["tint"]
    p = dict(dark=dark, base=base, accent=accent, text=text, tint=tint,
             blur=g["blur"], opacity=g["opacity"])
    p["edge"] = text                          # every hairline: the text colour at low alpha
    p["glow"] = text                          # focus edges and glows: the text colour, never the accent
    # T3's fixed status green ("Done", added lines) softened toward the text colour: still green, in key.
    green, t = ("#74d3a4", 0.3) if dark else ("#1f6b4b", 0.2)
    while t < 1 and not all(contrast(mix(green, text, t), g) >= 4.6 for g in (base, tint)):
        t = round(t + 0.05, 2)  # toward the text colour until it reads on the scene and the glass
    p["success"] = mix(green, text, t)
    p["error_fg"] = "#f0a3a8" if dark else "#8c1d18"
    if dark:
        p["deep"] = mix(tint, "#000000", 0.45)       # chrome, code, terminal
        p["ink"] = mix(tint, "#000000", 0.55)        # popups: darker than the scene
        p["ink_solid"] = mix(tint, "#000000", 0.4)   # knobs and triggers inside dialogs
        p["raised"] = mix(tint, text, 0.08)
        p["bubble"] = mix(tint, text, 0.05)
        p["info"] = mix(text, accent, 0.35)
        p["accent_fg"] = p["ink"] if contrast(p["ink"], accent) >= contrast("#ffffff", accent) else "#ffffff"
    else:
        p["deep"] = mix(tint, "#ffffff", 0.35)
        p["ink"] = mix(tint, "#ffffff", 0.45)        # popups: a clean sheet over the scene
        p["ink_solid"] = mix(tint, "#ffffff", 0.7)
        p["raised"] = mix(tint, text, 0.06)
        p["bubble"] = mix(tint, "#ffffff", 0.55)
        p["info"] = mix(text, accent, 0.45)
        p["accent_fg"] = "#ffffff" if contrast("#ffffff", accent) >= contrast(text, accent) else text
    # Secondary text and placeholders: as soft as they can be while reading at 4.5:1 on every
    # surface they sit on: the scene's ground, the glass tint, popups, and the raised and hover fills
    # (the text colour at 6-7% over the ground and the glass).
    grounds = [base, tint, p["ink"], mix(base, text, 0.07), mix(tint, text, 0.07)]
    p["muted"] = softest(text, base, 0.34, grounds, 4.6)
    p["faint"] = softest(text, base, 0.44, grounds, 4.6)
    return p


def softest(text, toward, start, grounds, need):
    t = start
    while t > 0:
        c = mix(text, toward, t)
        if all(contrast(c, g) >= need for g in grounds):
            return c
        t = round(t - 0.01, 2)
    return text


def check_contrast(sid, p):
    """Reading colours against the panels they sit on: the scene's base and the glass tint."""
    problems = []
    for name, need in (("text", 7.0), ("muted", 4.5), ("faint", 4.5), ("accent", 3.0), ("glow", 3.0), ("info", 4.5), ("success", 4.5)):
        for ground in ("base", "tint", "ink"):
            r = contrast(p[name], p[ground])
            if r < need:
                problems.append(f"{sid}: {name} on {ground} is {r:.2f}:1, needs {need}:1")
    r = contrast(p["accent_fg"], p["accent"])
    if r < 4.5:
        problems.append(f"{sid}: text on accent buttons is {r:.2f}:1")
    return problems


def roles(p):
    dark = p["dark"]
    status = dict(
        error="#e5737a", errorForeground="#f0a3a8", errorSurface="#2a1418",
        warning="#e0b36a", warningForeground="#ecc98e", warningSurface="#2a2214",
        update="#9ec8b8", updateForeground="#b6d8ca", updateSurface="#132420",
        searchMatchBackground="#5a4a24",
    ) if dark else dict(
        error="#b3261e", errorForeground="#8c1d18", errorSurface="#fbe4e2",
        warning="#9a6700", warningForeground="#7a5200", warningSurface="#fbf0d9",
        update="#2f7d62", updateForeground="#22604b", updateSurface="#e2f3ec",
        searchMatchBackground="#f3d36b",
    )
    # Status panels (error, warning and update notices) tinted into the theme's own glass, not one fixed
    # wine or olive that clashes with a teal or cream scene.
    for kind in ("error", "warning", "update"):
        status[f"{kind}Surface"] = rgba(mix(p["ink"], status[kind], 0.2 if dark else 0.12), 0.92)
    e = p["edge"]
    r = {
        "canvas": p["base"], "chrome": p["deep"], "toolbar": p["deep"],
        "toolbarForeground": p["text"], "toolbarBorder": rgba(e, 0.08),
        "toolbarControl": p["raised"], "toolbarControlForeground": p["text"], "toolbarControlHover": p["raised"],
        "surface": p["tint"], "surfaceRaised": p["raised"], "surfaceOverlay": p["ink"],
        "text": p["text"], "textMuted": p["muted"], "border": rgba(e, 0.1), "input": rgba(e, 0.14),
        "focus": p["glow"], "accent": p["accent"], "accentForeground": p["accent_fg"],
        "accentSurface": p["raised"], "accentSurfaceForeground": p["text"],
        "secondary": p["raised"], "secondaryForeground": p["text"],
        "muted": p["raised"], "mutedForeground": p["muted"],
        "placeholder": p["faint"], "secondaryLabel": p["muted"], "iconMuted": p["faint"],
        "messageSurface": p["bubble"], "messageForeground": p["text"],
        "messageAction": p["accent"], "messageActionForeground": p["accent_fg"],
        "messageActionHover": mix(p["accent"], p["text"], 0.15),
        "codeBackground": p["deep"], "codeForeground": p["text"],
        "searchMatchForeground": p["text"],
        "searchMatchActiveBackground": p["accent"], "searchMatchActiveForeground": p["accent_fg"],
        "sidebar": p["tint"], "sidebarForeground": p["text"], "sidebarMutedForeground": p["muted"],
        "sidebarControlSurface": p["raised"], "sidebarRowHover": p["raised"],
        "sidebarRowActive": p["raised"], "sidebarRowSelected": p["raised"], "sidebarBorder": rgba(e, 0.08),
        "terminalBackground": p["deep"], "terminalForeground": p["text"], "terminalCursor": p["accent"],
        "terminalSelection": rgba(p["accent"], 0.3), "terminalScrollbar": rgba(e, 0.18),
        "terminalScrollbarHover": rgba(e, 0.3),
        **status,
    }
    # Translucent glass values: T3 maps each role onto its token for the app and the sidebar scope.
    r.update({
        "accentSurface": rgba(e, 0.07), "muted": rgba(e, 0.055), "secondary": rgba(e, 0.06),
        "surfaceRaised": rgba(e, 0.06), "surface": rgba(p["tint"], 0.55),
        "surfaceOverlay": rgba(p["ink"], 0.9), "codeBackground": rgba(p["deep"], 0.78),
        "chrome": rgba(p["deep"], 0.6), "toolbar": rgba(p["deep"], 0.6),
        "toolbarControl": rgba(e, 0.06), "toolbarControlHover": rgba(e, 0.1),
    })
    return r


# ---------------------------------------------------------------- CSS

TEMPLATE = """
[data-slot="sidebar-wrapper"] {{
  isolation: isolate;
  background: none !important;
}}
[data-slot="sidebar-wrapper"]::before {{
  content: ""; position: fixed; inset: 0; pointer-events: none; z-index: -1;
  will-change: transform;
  background: {base} SCENE center / cover no-repeat !important;
}}
:root {{ --surface-grain: none !important; --info-foreground: {info} !important;
  --success: {success} !important; --success-foreground: {success} !important;
  --diff-addition-foreground: {success} !important; --diff-deletion-foreground: {error_fg} !important; }}

[data-slot="sidebar-inset"],
[data-slot="sidebar-inset"] > *:has(> [data-chat-column]),
[data-workspace-area="conversation"] > [data-timeline-loading],
.messages-timeline-scroll,
[data-chat-composer-form] {{ background-color: transparent !important; background-image: none !important; }}

/* A soft reading veil behind the chat column: full strength across the column at any window width,
   then it fades to the scene over 180px at both sides, so there is no edge */
[data-workspace-area="conversation"] {{
  background-color: transparent !important;
  background-image: linear-gradient(90deg, transparent calc(50% - 620px), {veil} calc(50% - 440px), {veil} calc(50% + 440px), transparent calc(50% + 620px)) !important;
}}

[data-slot="sidebar-inner"] {{
  background-color: {side_glass} !important; background-image: none !important;
  {side_blur}border-right: 1px solid {e06};
}}
/* The thread details card stays on screen, so it is glass like the sidebar, not popup ink.
   (T3 gives it its dropdown glass: the popover colour with a bright edge.) */
[data-thread-details-card] {{
  background: {side_glass} !important; {side_blur}
  border-color: {e07} !important;
  box-shadow: inset 0 1px 0 {hi05}, 0 10px 30px {shadow_soft} !important;
}}
/* Paint the material once across the panel, including its tabbar/native-controls inset. */
[data-workspace-area="panel"] {{ background-color: {header} !important; background-image: none !important; border-left: 1px solid {e06}; }}
[data-right-panel-tabbar] {{ background: transparent !important; border-color: {e06} !important; }}
[data-thread-terminal-drawer] {{ border-top: 1px solid {e07}; }}
[data-workspace-area="pull-requests"] {{ background-color: {page_veil} !important; background-image: none !important; }}
[data-workspace-area="pull-requests"] > header,
[data-chat-header] {{ background: {header} !important; backdrop-filter: blur(10px); border-color: {e06} !important; border-bottom: 1px solid {e06}; }}

[data-user-message-bubble] {{
  background: {bubble92} !important; border: 1px solid {e09} !important;
  box-shadow: inset 0 1px 0 {hi05}, 0 6px 24px {shadow_soft};
  transition: border-color .25s ease;
}}
[data-user-message-bubble]:hover {{ border-color: {e16} !important; }}

[data-slot="composer-shell"] {{
  --glass-opacity: {composer_op}%; --glass-blur: {composer_blur}px; --glass-saturation: 1.1;
  --chat-composer-glass-surface: {tint}; --chat-composer-outline: {e11}; --chat-composer-highlight: {hi07};
}}
/* The chat box: a soft shadow and, while focused, a text-coloured edge and glow. While a banner is
   attached above it, T3 drops the chat box's own frame, so these step aside too (else a second frame). */
[data-slot="composer-host"] {{ transition: box-shadow .35s ease; }}
[data-slot="composer-host"]:not(:has([data-composer-banner-surface="attached"])) {{ box-shadow: 0 14px 44px {shadow} !important; }}
[data-slot="composer-host"]:not(:has([data-composer-banner-surface="attached"])):focus-within {{
  box-shadow: 0 0 0 1px {a32}, 0 0 30px {a12}, 0 14px 44px {shadow} !important;
}}
[data-slot="composer-host"] [contenteditable="true"] {{ caret-color: {accent}; }}
/* Dragging a file or thread over the chat box: T3's ring is the accent; make it the text colour. */
[data-chat-composer-surface] {{ --tw-ring-color: {a32} !important; }}
/* Banners attached above the chat box (usage limits, snooze, /clear, replies): the chat box's glass and
   hairline, not a faint surface with a coloured outline. */
[data-composer-banner-surface] {{
  --chat-composer-attached-surface: {tint} !important;
  --chat-composer-attached-outline: {e11} !important;
}}
[data-slot="alert"]:not([data-variant="default"]):not([data-variant="sidebar"]) {{ border-color: {e09} !important; }}
[data-chat-composer-form] button[type="submit"] {{
  transition: transform .18s cubic-bezier(.2,.9,.3,1.4), box-shadow .3s ease, background-color .3s ease !important;
}}
[data-chat-composer-form] button[type="submit"]:enabled {{
  box-shadow: 0 0 0 1px {a35}, 0 0 18px {a25} !important; animation: tx-send-ready .5s cubic-bezier(.2,.9,.3,1.3);
}}
[data-chat-composer-form] button[type="submit"]:enabled:active {{ transform: scale(.92); }}
@keyframes tx-send-ready {{ 0% {{ transform: scale(.86); }} 60% {{ transform: scale(1.08); }} 100% {{ transform: scale(1); }} }}
[data-slot="composer-context-strip"] {{ background: transparent !important; backdrop-filter: none !important; }}
[data-slot="composer-host"] [data-chat-composer-expanded-image] {{ background: {deep} !important; border-color: {e12} !important; isolation: isolate; }}

[data-message-role="assistant"] .chat-markdown {{ text-shadow: {text_shadow}; }}
.chat-markdown a, [data-user-message-bubble] a {{
  color: {link} !important; text-decoration-color: {link35} !important; text-underline-offset: 3px;
  transition: text-decoration-color .2s ease;
}}
.chat-markdown-codeblock {{ background: {code} !important; border: 1px solid {e06}; }}

[data-slot$="-popup"] {{
  background-color: color-mix(in srgb, {ink} min(100%, calc(var(--glass-opacity, 80%) + 12%)), transparent) !important;
  background-image: none !important; backdrop-filter: blur(24px) saturate(105%) !important;
  border-color: {e09} !important;
  box-shadow: inset 0 1px 0 {hi06}, 0 0 0 1px {ring}, 0 30px 90px {popup_shadow} !important;
}}
[data-slot="popover-popup"], [data-slot="menu-popup"], [data-slot="select-popup"], [data-slot="combobox-popup"],
[data-slot="autocomplete-popup"], [data-slot="preview-card-popup"], [data-slot="toast-popup"] {{
  background-color: color-mix(in srgb, {ink} min(100%, calc(var(--glass-opacity, 80%) + 14%)), transparent) !important;
}}
/* Sheets slide in and out, so no live blur on them (it re-blurs every frame): near-solid instead. */
[data-slot="sheet-popup"] {{ background-color: {sheet} !important; backdrop-filter: none !important; }}
[data-slot="tooltip-popup"] {{
  background-color: {tooltip} !important; backdrop-filter: blur(10px) !important;
  box-shadow: 0 0 0 1px {ring}, 0 10px 28px {shadow_soft} !important;
}}
[data-slot$="-backdrop"]:not([data-slot="popover-backdrop"]) {{ background-color: {dim} !important; backdrop-filter: blur(4px) !important; }}
[data-slot="dialog-popup"], [data-slot="sheet-popup"], [data-slot="alert-dialog-popup"], [data-slot="command-dialog-popup"] {{
  --background: {ink_solid}; --sidebar: transparent; --card: {card_in_modal};
  --sidebar-row-hover: {e035}; --sidebar-row-active: {e06}; --sidebar-row-selected: {e055};
}}
[data-slot="dialog-popup"] nav {{ background-color: {modal_nav} !important; border-right: 1px solid {e05}; }}
[data-slot="dialog-popup"] [data-slot="settings-group"] {{ border: 1px solid {e055}; box-shadow: inset 0 1px 0 {hi03}; }}

[data-thread-item] [role="button"] {{ transition: background-color .2s ease; }}
[data-thread-item] [aria-current="page"] {{ animation: tx-select-fade 2.4s ease-out forwards; }}
[data-thread-item] [aria-current="page"]:hover {{ background-color: {e045} !important; }}
@keyframes tx-select-fade {{ 0%, 30% {{ background-color: {e08}; }} 100% {{ background-color: transparent; }} }}

[data-slot="button"] {{ transition: transform .12s ease, background-color .18s ease, color .18s ease, border-color .18s ease; }}
[data-slot="button"]:active:not(:disabled) {{ transform: scale(.96); }}

@media (prefers-reduced-motion: reduce) {{
  [data-chat-composer-form] button[type="submit"], [data-chat-composer-form] button[type="submit"]:enabled {{
    animation: none !important; transition: none !important;
  }}
  [data-slot="button"]:active:not(:disabled), [data-chat-composer-form] button[type="submit"]:enabled:active {{ transform: none !important; }}
  [data-thread-item] [aria-current="page"] {{ animation: none !important; background-color: transparent !important; }}
  [data-slot="button"], [data-thread-item] [role="button"], [data-slot="composer-host"] {{ transition: none !important; }}
}}
::selection {{ background: {a28}; }}
[data-slot="scroll-area-thumb"], ::-webkit-scrollbar-thumb {{ background: {thumb} !important; border-radius: 8px; }}
"""


def minify_css(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{};,>])\s*", r"\1", css)
    css = re.sub(r":\s+", ":", css)
    css = css.replace(";}", "}")
    # `:has(> x)` and `a > b` lost their spaces, which CSS accepts; descendant spaces are kept.
    return css.strip()


VEIL_MARGIN = 0.03   # on top of what tune_veils.py measured


def css_for(scene, p, scene_url, veil):
    dark, e, a = p["dark"], p["edge"], p["accent"]
    # The sidebar's text sits on the art too: always frosted and mostly opaque, whatever the scene's
    # own glass (Plotter Tide's is unblurred, which let its contour lines run through thread titles).
    side_alpha = round(min(0.84, max(0.70, p["opacity"] + 0.28)), 2)
    blur = max(p["blur"], 12)
    hi = "#ffffff" if not dark else e
    vals = dict(
        title=scene["title"], sid=scene["id"], base=p["base"], tint=p["tint"], accent=a, deep=p["deep"],
        info=p["info"], ink=p["ink"], ink_solid=p["ink_solid"], success=p["success"], error_fg=p["error_fg"],
        veil=rgba(p["tint"], round(veil + VEIL_MARGIN, 2)),
        side_glass=rgba(p["tint"], side_alpha),
        side_blur=f"backdrop-filter: blur({blur}px) saturate(115%); ",
        page_veil=rgba(p["tint"], 0.62), header=rgba(p["tint"], 0.78),
        bubble92=rgba(p["bubble"], 0.94), code=rgba(p["deep"], 0.86),
        composer_op=round(min(78, max(55, p["opacity"] * 100 + 22))), composer_blur=max(12, blur),
        e035=rgba(e, 0.035), e045=rgba(e, 0.045), e05=rgba(e, 0.05), e055=rgba(e, 0.055), e06=rgba(e, 0.07),
        e07=rgba(e, 0.08), e08=rgba(e, 0.08), e09=rgba(e, 0.1), e11=rgba(e, 0.13), e12=rgba(e, 0.13),
        e16=rgba(e, 0.18),
        hi03=rgba(hi, 0.03 if dark else 0.5), hi05=rgba(hi, 0.05 if dark else 0.6),
        hi06=rgba(hi, 0.06 if dark else 0.7), hi07=rgba(hi, 0.07 if dark else 0.6),
        # Edges and glows (focus, send button, drag) use the text colour, never the accent: no coloured
        # edges. The accent stays a fill (switches, buttons, links).
        a12=rgba(p["glow"], 0.12), a25=rgba(p["glow"], 0.22), a32=rgba(p["glow"], 0.34), a35=rgba(p["glow"], 0.32),
        sheet=rgba(p["ink"], 0.97),
        a28=rgba(a, 0.3),
        link=a if contrast(a, p["base"]) >= 4.5 else p["text"], link35=rgba(a, 0.45),
        shadow="rgba(0,0,0,.55)" if dark else "rgba(40,40,50,.18)",
        shadow_soft="rgba(0,0,0,.4)" if dark else "rgba(40,40,50,.12)",
        popup_shadow="rgba(0,0,0,.7)" if dark else "rgba(40,40,50,.24)",
        ring="rgba(0,0,0,.6)" if dark else rgba(e, 0.08),
        tooltip=rgba(p["ink"], 0.97), dim="rgba(2,2,3,.62)" if dark else "rgba(30,30,36,.26)",
        card_in_modal=rgba(e, 0.045) if dark else "rgba(255,255,255,.55)",
        modal_nav="rgba(0,0,0,.22)" if dark else "rgba(0,0,0,.035)",
        text_shadow="0 1px 2px rgba(0,0,0,.7)" if dark else f"0 0 2px {rgba(p['tint'], 0.8)}",
        thumb=rgba(e, 0.18 if dark else 0.24),
    )
    css = minify_css(TEMPLATE.format(**vals))
    assert "SCENE" in css
    # The file travels on its own (Add theme, Export theme file), so the notice travels with it.
    credit = (f"/* {scene['title']}: modified from the \"{scene['id']}\" scene of Anthropic's theme-examples plugin "
              f"(github.com/anthropics/claude-plugins-official/tree/main/plugins/theme-examples), "
              f"licensed under the Apache License 2.0 (apache.org/licenses/LICENSE-2.0). "
              f"Made a still and restyled for T3 Code; not made or endorsed by Anthropic. */")
    return credit + css.replace("SCENE", scene_url)


# ---------------------------------------------------------------- build

def dump_scenes():
    out = subprocess.run(["node", "--experimental-strip-types", "--no-warnings", "dump-scenes.mts"],
                         cwd=HERE, capture_output=True, text=True, encoding="utf-8", check=True).stdout
    os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
    with open(os.path.join(HERE, "build", "scenes.json"), "w", encoding="utf-8") as fh:
        fh.write(out)
    return json.loads(out)


def main():
    scenes = dump_scenes()
    # Measured by tune_veils.py: how strong each veil must be for chat text to read over the art.
    veils = json.load(open(os.path.join(HERE, "veils.json"), encoding="utf-8"))
    problems, report, built = [], [], []
    for s in scenes:
        p = palette(s)
        problems += check_contrast(s["id"], p)
        if s["id"] not in veils:
            problems.append(f"{s['id']}: no measured veil; run python tune_veils.py")
            continue
        url = scenemin.to_css_url(scenemin.minify(scenemin.reference_still(s["svg"])))
        css = css_for(s, p, url, veils[s["id"]])
        if len(css) > CSS_LIMIT:
            problems.append(f"{s['id']}: CSS is {len(css)} characters, over T3's {CSS_LIMIT}")
        if "\\" in css:
            problems.append(f"{s['id']}: CSS has a backslash; T3 drops such declarations")
        tid, name = RENAMED.get(s["id"], (s["id"], s["title"]))
        theme = {
            "version": 1, "id": tid, "name": name, "appearance": s["window"],
            "canvas": p["base"], "accent": p["accent"], "collection": COLLECTION,
            "colors": roles(p), "css": css,
        }
        built.append(theme)
        report.append(f"{tid:20} {s['window']:5} css {len(css):6} / {CSS_LIMIT}")
    print("\n".join(report))
    if problems:  # nothing is written unless every theme passes
        print("\nPROBLEMS (no files written):\n" + "\n".join(problems))
        sys.exit(1)
    os.makedirs(THEMES_DIR, exist_ok=True)
    for theme in built:
        with open(os.path.join(THEMES_DIR, f"{theme['id']}.json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(theme, fh, indent=2, ensure_ascii=False)
    print(f"\nwrote {len(built)} themes to {os.path.normpath(THEMES_DIR)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
