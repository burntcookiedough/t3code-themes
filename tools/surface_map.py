"""Map every T3 Code web surface from source, and how Soft Bloom covers it.

    python tools/surface_map.py <t3code checkout> [theme.json] > docs/SURFACE-MAP.md

Reads apps/web/src (and packages/shared/src/themeCss.ts for the stable hook list).
Re-run it when T3 Code updates and diff the output to see what changed.
Standard library only.
"""
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict

ROOT = sys.argv[1]
THEME = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "..", "themes", "soft-bloom.json")
WEB = os.path.join(ROOT, "apps", "web", "src")
HOOKS_FILE = os.path.join(ROOT, "packages", "shared", "src", "themeCss.ts")

TOKEN_NAMES = (
    "background|foreground|card|card-foreground|popover|popover-foreground|primary|primary-foreground|"
    "secondary|secondary-foreground|muted|muted-foreground|accent|accent-foreground|destructive|"
    "destructive-foreground|border|input|ring|placeholder|secondary-label|icon-muted|surface-raised|"
    "sidebar[a-z-]*|message-[a-z-]+|code-[a-z-]+|error[a-z-]*|warning[a-z-]*|update[a-z-]*|info[a-z-]*|"
    "success[a-z-]*|toolbar[a-z-]*|terminal[a-z-]*|app-chrome[a-z-]*|chat-[a-z-]+"
)
PROPS = "bg|text|border|ring|fill|stroke|from|via|to|outline|divide|shadow|decoration|caret|placeholder"
TOKEN_CLASS = re.compile(rf"\b(?:[a-z-]+:)*(?:{PROPS})-(?:{TOKEN_NAMES})(?:/\d+)?\b")
PALETTE = (
    "red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|"
    "pink|rose|slate|gray|zinc|neutral|stone"
)
PALETTE_CLASS = re.compile(rf"\b(?:[a-z-]+:)*(?:{PROPS})-(?:(?:{PALETTE})-\d{{2,3}}|white|black)(?:/\d+)?\b")
LITERAL_COLOR = re.compile(r"(?<![\w&])#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?|oklch|oklab)\(")
SLOT_DEF = re.compile(r"""data-slot["']?\s*[:=]\s*[{]?\s*["'`]([a-z0-9-]+)["'`]""")
DATA_ATTR = re.compile(r"""["'\s{(](data-[a-z][a-z0-9-]+)["']?\s*[:=]""")
WORKSPACE_AREA = re.compile(r"""(?:data-workspace-area["']?\s*[:=]\s*[{]?\s*|workspaceAreaProps\(\s*)["'`]([a-z-]+)["'`]""")
COMMENT = re.compile(r"/\*[\s\S]*?\*/|(?<![:\"'])//[^\n]*")

ROOT_COMPONENT_AREAS = [
    ("Chat", r"^(ChatView|ChatMarkdown|ChatHeader|Message|Timeline|Work|CommandBlock|Proposed|Thread(?!Details))"),
    ("Composer", r"^(Composer|ContextChip|EnvironmentContextChip|PromptStash|Mention)"),
    ("Command palette", r"^CommandPalette"),
    ("Sidebar", r"^(Sidebar|AppSidebar|ProjectPin|Snooze|CustomSnooze)"),
    ("Diffs", r"^(Diff|PierreDiff)"),
    ("Git & branches", r"^(Git|Branch)"),
    ("Thread details", r"^ThreadDetails"),
    ("Toasts & notices", r"(Toast|Announcer|Banner|Notice|Warning)"),
    ("Dialogs", r"(Dialog|Modal)"),
    ("Empty states", r"(EmptyState|Empty)"),
]


def area_of(rel):
    parts = rel.replace("\\", "/").split("/")
    if parts[0] == "routes":
        name = parts[-1].rsplit(".", 1)[0]
        name = name.replace("_chat.", "").replace("$", ":")
        if name.startswith("settings."):
            return "Settings page: " + name.split(".", 1)[1]
        return "Route: " + name
    if parts[0] == "components":
        if len(parts) > 2:
            return "components/" + parts[1]
        base = parts[1]
        for label, pattern in ROOT_COMPONENT_AREAS:
            if re.search(pattern, base):
                return label
        return "components (other)"
    return parts[0] if len(parts) > 1 else "app shell"


def read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def stable_hooks():
    text = read(HOOKS_FILE)
    pairs = re.findall(r"""selector:\s*(?:'([^']*)'|"([^"]*)"),\s*styles:\s*(?:'([^']*)'|"([^"]*)")""", text)
    return [(a or b, c or d) for a, b, c, d in pairs]


def theme_css():
    try:
        return json.load(open(THEME, encoding="utf-8")).get("css", "")
    except OSError:
        return ""


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    files = []
    for dirpath, _, names in os.walk(WEB):
        for name in names:
            if not re.search(r"\.(tsx?|css)$", name) or ".test." in name or name.endswith(".gen.ts"):
                continue
            path = os.path.join(dirpath, name)
            files.append((os.path.relpath(path, WEB), read(path)))

    css = theme_css()
    theme_slots = set(re.findall(r'data-slot[$^*]?="([a-z0-9-]+)"', css))
    theme_slot_suffixes = set(re.findall(r'data-slot\$="([a-z0-9-]+)"', css))
    theme_attrs = set(re.findall(r"\[(data-[a-z-]+)", css))
    theme_areas = set(re.findall(r'data-workspace-area="([a-z-]+)"', css))
    hooks = stable_hooks()
    stable_slots = {re.search(r'"(.+)"', s).group(1) for s, _ in hooks if "data-slot" in s}
    stable_attrs = {re.match(r"\[(data-[a-z-]+)", s).group(1) for s, _ in hooks if s.startswith("[data-") and "data-slot" not in s}

    areas = defaultdict(lambda: {"files": [], "tokens": Counter(), "palette": Counter(), "literal": 0, "slots": set(), "attrs": set()})
    slot_owner = defaultdict(set)
    workspace_areas = defaultdict(set)
    palette_hotspots = []

    for rel, text in files:
        code = COMMENT.sub("", text)
        area = area_of(rel)
        a = areas[area]
        a["files"].append(rel)
        tokens = TOKEN_CLASS.findall(code)
        palette = PALETTE_CLASS.findall(code)
        literal = LITERAL_COLOR.findall(code) if not rel.endswith(".css") else []
        a["tokens"].update(tokens)
        a["palette"].update(palette)
        a["literal"] += len(literal)
        for slot in SLOT_DEF.findall(code):
            a["slots"].add(slot)
            slot_owner[slot].add(rel.replace("\\", "/"))
        for attr in DATA_ATTR.findall(code):
            a["attrs"].add(attr)
        for wa in WORKSPACE_AREA.findall(code):
            workspace_areas[wa].add(rel.replace("\\", "/"))
        if palette or (literal and rel.endswith(".tsx")):
            palette_hotspots.append((len(palette) + len(literal), rel.replace("\\", "/"), sorted(set(palette))[:6], len(literal)))

    def slot_covered(slot):
        return slot in theme_slots or any(slot.endswith("-" + sfx) for sfx in theme_slot_suffixes)

    out = []
    w = out.append
    w("# T3 Code surface map")
    w("")
    w("Generated by `tools/surface_map.py` from T3 Code's web source. Do not edit by hand; re-run it.")
    w("")
    try:
        sha = subprocess.run(["git", "-C", ROOT, "log", "-1", "--format=%h (%cs)"], capture_output=True, text=True).stdout.strip()
    except OSError:
        sha = ""
    version = re.search(r"Soft Bloom (v\d+)", css)
    w(f"T3 Code source: `pingdotgg/t3code` at `{sha or 'unknown'}`. Theme: Soft Bloom {version.group(1) if version else '(unknown version)'}.")
    w("")
    w(f"- Source files scanned: **{len(files)}** (`apps/web/src`, tests excluded)")
    w(f"- Surface areas: **{len(areas)}**")
    w(f"- `data-slot` hooks defined: **{len(slot_owner)}**, of which **{len(stable_slots)}** are in T3's stable list")
    w(f"- Workspace areas: {', '.join('`' + k + '`' for k in sorted(workspace_areas))}")
    w(f"- Soft Bloom CSS touches {len(theme_slots)} slots, {len(theme_slot_suffixes)} slot suffix patterns and {len(theme_attrs)} other data attributes")
    w("")
    w("**Columns:** *token uses* = Tailwind classes that read theme tokens (themed automatically). "
      "*palette / literal* = hard-coded colours that ignore themes (cohesion risks). "
      "*stable hooks* = selectors from T3's official list present in that area.")
    w("")

    w("## T3's stable CSS hooks")
    w("")
    w("| Selector | What it styles | Used by Soft Bloom |")
    w("|---|---|---|")
    for selector, styles in hooks:
        slot = re.search(r'data-slot="(.+)"', selector)
        attr = re.match(r"\[(data-[a-z-]+)", selector)
        used = (slot and slot_covered(slot.group(1))) or (attr and not slot and attr.group(1) in theme_attrs) or (
            selector.startswith(".") and selector in css)
        w(f"| `{selector}` | {styles} | {'yes' if used else '—'} |")
    w("")

    w("## Surface areas")
    w("")
    w("| Area | Files | Token uses | Palette / literal colours | Stable hooks | Slots defined |")
    w("|---|---:|---:|---:|---|---|")
    for name in sorted(areas, key=lambda n: (not n.startswith("Route"), not n.startswith("Settings"), n)):
        a = areas[name]
        sh = sorted({f'[data-slot="{s}"]' for s in a["slots"] if s in stable_slots} | {f"[{x}]" for x in a["attrs"] if x in stable_attrs})
        w(f"| {name} | {len(a['files'])} | {sum(a['tokens'].values())} | {sum(a['palette'].values())} / {a['literal']} | "
          f"{', '.join('`' + h + '`' for h in sh) or '—'} | {', '.join(sorted(a['slots']))[:160] or '—'} |")
    w("")

    w("## Every `data-slot` (overlays, controls, layout)")
    w("")
    w("| Slot | Defined in | Stable hook | Soft Bloom styles it |")
    w("|---|---|---|---|")
    for slot in sorted(slot_owner):
        owners = sorted(slot_owner[slot])
        w(f"| `{slot}` | {', '.join(owners[:2])}{' …' if len(owners) > 2 else ''} | {'yes' if slot in stable_slots else '—'} | {'yes' if slot_covered(slot) else '—'} |")
    w("")

    w("## Workspace areas")
    w("")
    w("| Area | Rendered in | Soft Bloom styles it |")
    w("|---|---|---|")
    for wa in sorted(workspace_areas):
        owners = sorted(workspace_areas[wa])
        w(f"| `{wa}` | {', '.join(owners[:3])} | {'yes' if wa in theme_areas else '—'} |")
    w("")

    w("## Where themes can't reach: hard-coded colour hotspots")
    w("")
    w("Files that paint with fixed Tailwind palette colours or literal colours instead of theme tokens. "
      "Some are intentional identity colours (providers, success/info, diff +/-); the rest are where a theme "
      "looks inconsistent. Top 40 by count.")
    w("")
    w("| File | Palette classes | Literal colours | Examples |")
    w("|---|---:|---:|---|")
    for count, rel, examples, lit in sorted(palette_hotspots, reverse=True)[:40]:
        pc = count - lit
        w(f"| `{rel}` | {pc} | {lit} | {', '.join('`' + e + '`' for e in examples) or '—'} |")
    w("")
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
