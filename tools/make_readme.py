"""Writes README.md, docs/GALLERY.md and themes.json (a list of every theme for agents) from themes/*.json.

    python tools/make_readme.py
"""
import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
REPO = "burntcookiedough/t3code-themes"
DL = f"https://github.com/{REPO}/releases/latest/download"

# What each theme shows, in a line. Written for the still pictures (the plugin's own blurbs describe motion).
BLURBS = {
    "soft-bloom": "Very dark and dreamy: a dithered star glow and pixel sparkles behind frosted glass, with cream accents.",
    "aurora": "Green and violet northern lights over a dark ridge.",
    "blueprint": "A cyanotype sheet with a plotted comet orbit in the corner.",
    "braille-stars": "A night sky and a Milky Way drawn in braille dots.",
    "deep-water": "Light falling through deep teal water, a turtle's shadow below.",
    "departure-board": "Amber LED letters on a dark board.",
    "dither-dunes": "One-bit dunes in sand-coloured dots under a terracotta sun.",
    "dither-dunes-night": "The same dunes after dark: pale dots on umber and an ember sun.",
    "ember-glow": "A warm red glow rising from the corners of a dark room.",
    "halftone-dawn": "A two-ink riso sunrise in halftone dots on cream paper.",
    "halftone-dusk": "The riso sunrise on night-blue paper: an ember sun in dots.",
    "honu-lagoon": "A lagoon from above in ASCII tiles, with a coral-pink turtle.",
    "koi-mosaic": "A tiled koi pond from above: two koi and lily pads.",
    "night-reef": "A night reef with a glowing tile turtle and ray.",
    "paper-garden": "Cut-paper leaves at the edges of a warm white sheet, one coral bloom.",
    "paper-garden-kraft": "Cut-paper leaves on dark kraft paper, one coral bloom.",
    "plotter-tide": "Pen-plotter tide lines on warm paper.",
    "plotter-tide-night": "The plotter's tide chart in pale ink on blue-black paper.",
    "snow-pines": "An ASCII pine forest at dusk under falling snow.",
    "teletext-clouds": "Night clouds and a crescent moon built from teletext blocks.",
    "vector-range": "Phosphor-green wireframe mountains on black.",
}


def card(t, blurbs):
    tid, name = t["id"], t["name"]
    kind = "Dark" if t["appearance"] == "dark" else "Light"
    return (f"<a href=\"screenshots/{tid}.webp\"><img src=\"screenshots/{tid}.webp\" alt=\"{name} in T3 Code\"></a><br>"
            f"<b>{name}</b> · {kind} · <a href=\"{DL}/{tid}.json\">Download</a> · "
            f"<a href=\"docs/GALLERY.md#{tid}\">More screens</a><br><sub>{blurbs.get(tid, '')}</sub>")


def grid(themes, blurbs):
    rows = []
    for i in range(0, len(themes), 2):
        pair = themes[i:i + 2]
        cells = "".join(f"<td width=\"50%\" valign=\"top\">{card(t, blurbs)}</td>" for t in pair)
        rows.append(f"<tr>{cells}</tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def main():
    themes = []
    for f in sorted(os.listdir(os.path.join(ROOT, "themes"))):
        if f.endswith(".json"):
            t = json.load(open(os.path.join(ROOT, "themes", f), encoding="utf-8"))
            t.setdefault("id", f[:-5])  # a theme file without an id takes its filename's
            themes.append(t)
    blurbs = BLURBS
    soft = [t for t in themes if t["id"] == "soft-bloom"]
    scenes = [t for t in themes if t["id"] != "soft-bloom"]
    dark = [t for t in scenes if t["appearance"] == "dark"]
    light = [t for t in scenes if t["appearance"] == "light"]

    readme = f"""# T3 Code Themes

{len(themes)} themes for [T3 Code](https://github.com/pingdotgg/t3code). Each one puts a scene behind the whole window and turns the sidebar, chat bar, popups, Settings and panels into frosted glass in its colours. Every surface has been checked in the real app.

**Needs T3 Code v0.1.10 or newer** (custom theme CSS shipped in v0.1.10).

## Install

1. **[Download all themes (.zip)]({DL}/t3code-themes.zip)** and unzip it, or download a single theme from the gallery below.
2. In T3 Code, open **Settings → Appearance → Add theme**.
3. Drop one or more `.json` files into the dialog. Pick the theme under **Themes**.

Or from a terminal: `t3 theme set path/to/theme.json`.

**Light themes** show when **Color scheme** is Light, or System on a light computer. Dark themes show when it's Dark or System on a dark computer. Paired themes (Halftone Dawn and Halftone Dusk, for example) work well as your light and dark choice with Color scheme set to System.

## Let your coding agent do it

Paste one of these into Claude Code, Codex or any agent inside T3 Code. Both point the agent at [AGENTS.md](AGENTS.md), which has step-by-step playbooks.

**Install themes:**

```text
Install T3 Code themes for me from https://github.com/burntcookiedough/t3code-themes.
Read https://raw.githubusercontent.com/burntcookiedough/t3code-themes/main/AGENTS.md and follow
"Playbook 1: install themes" from start to finish.
The themes I want: <names from the gallery, a description of the look I like, or "all of them">.
When you're done, tell me which theme is showing and how to switch between them.
```

**Make your own theme:**

```text
Make me a custom T3 Code theme. Clone https://github.com/burntcookiedough/t3code-themes and follow
"Playbook 2: make a new theme" in its AGENTS.md from start to finish: agree on the look with me,
generate it with tools/new_theme.py, fix anything its checks reject, install it, and tell me what to
look at to judge it.
The look I want: <dark or light, the colours and mood, and any picture to show behind the app>.
```

## Soft Bloom

{grid(soft, blurbs)}

## Scenes: dark

Twenty scenes from Anthropic's [theme-examples](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/theme-examples) plugin for Claude Code, made into T3 Code themes (Apache-2.0, not made or endorsed by Anthropic). They're still pictures: in T3, anything moving behind the frosted glass makes the app lag.

{grid(dark, blurbs)}

## Scenes: light

{grid(light, blurbs)}

## Make your own

Everything we learned building these is written down, so you or your coding agent can start without rediscovering it:

- **[docs/THEME-GUIDE.md](docs/THEME-GUIDE.md)** covers the theme format, every colour role and what it paints, what theme CSS may contain, stable selectors, the glass recipe, the surfaces to check, performance rules and known pitfalls.
- **[AGENTS.md](AGENTS.md)** has playbooks for coding agents: install themes, make a new one, change one here, verify on every surface. `themes.json` lists every theme for them.
- **[tools/new_theme.py](tools/new_theme.py)** makes a complete theme from a background, accent and text colour, plus optional art, with the same glass treatment and checks as these.
- **[tools/capture](tools/capture/)** screenshots every surface of T3 under each theme and flags colours that don't belong.

To regenerate the themes:

```sh
python source/soft-bloom/generate.py themes/soft-bloom.json   # Soft Bloom
python source/theme-examples/build.py                         # the 20 scenes (needs Node 22.6+)
python tools/make_readme.py                                   # this README, the gallery, themes.json
```

## License

Soft Bloom, the tools and the docs are [MIT](LICENSE). The twenty scene themes and the plugin code they come from are Apache-2.0; see [NOTICE](NOTICE). This project isn't affiliated with T3 Code or Anthropic.
"""
    with open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(readme)

    # The gallery page: every captured screen of every theme.
    order = soft + dark + light
    parts = ["# Gallery\n\nEvery theme on five screens: a conversation, a new thread, the model picker, Settings and the Files panel. "
             "All screenshots were taken in a sandbox T3 Code with demo content.\n"]
    for t in order:
        tid = t["id"]
        shots = "".join(
            f"<img src=\"../screenshots/{tid}/{s}.webp\" width=\"49%\" alt=\"{t['name']}: {s}\"> "
            for s in ("new-thread", "model-picker", "settings", "files-panel"))
        parts.append(f"## {t['name']}\n<a id=\"{tid}\"></a>\n\n"
                     f"{'Dark' if t['appearance'] == 'dark' else 'Light'} · [Download]({DL}/{tid}.json)\n\n"
                     f"<img src=\"../screenshots/{tid}.webp\" alt=\"{t['name']}: a conversation\">\n\n{shots}\n")
    with open(os.path.join(ROOT, "docs", "GALLERY.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(parts))
    # A machine-readable list for agents choosing and downloading themes.
    raw = f"https://raw.githubusercontent.com/{REPO}/main"
    index = [{"id": t["id"], "name": t["name"], "appearance": t["appearance"], "description": blurbs.get(t["id"], ""),
              "file": f"themes/{t['id']}.json", "download": f"{DL}/{t['id']}.json",
              "screenshot": f"{raw}/screenshots/{t['id']}.webp"} for t in order]
    with open(os.path.join(ROOT, "themes.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(index, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"README.md, docs/GALLERY.md and themes.json: {len(themes)} themes")


if __name__ == "__main__":
    main()
