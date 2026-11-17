# For coding agents

This repo holds 21 ready-made T3 Code themes and everything needed to make new ones. Pick the playbook that matches what your user asked, and follow it to the end. For anything about how themes work, read **[docs/THEME-GUIDE.md](docs/THEME-GUIDE.md)**. It covers the format, every colour role, what theme CSS may contain, stable selectors, the glass recipe, the surfaces to check, performance rules and known pitfalls.

Requirements: T3 Code **v0.1.10 or newer** (theme CSS shipped then). The CLI is `t3`; if it isn't on PATH it is `~/.t3/bin/t3` (Windows: `~/.t3/bin/t3.cmd`). Agents running inside T3 Code can also use its `t3_theme_read` / `t3_theme_set` tools.

## Playbook 1: install themes for the user

1. Choose themes from **[themes.json](themes.json)**. Each entry has an `id`, `name`, `appearance` (dark/light), a one-line `description`, a `download` URL and a `screenshot` URL. If the user described a look rather than a name, pick from the descriptions and show the screenshots.
2. Download the files: `https://github.com/burntcookiedough/t3code-themes/releases/latest/download/<id>.json` (or all of them in `.../t3code-themes.zip`).
3. Install each one: `t3 theme set <file>`. This publishes it on this machine and switches the app to it; the last one installed is the one showing. Or tell the user to drop the files into **Settings → Appearance → Add theme**.
4. Check: `t3 theme show` lists the ids. For a **light** theme, the app shows it only when Color scheme is Light (or System on a light computer); tell the user, or switch with your T3 tools.
5. To go back: `t3 theme set <previous id>` (`t3 theme show` names the current one first), or `t3 theme set t3-chat` for T3's default.

## Playbook 2: make a new theme

1. Agree on the look: dark or light, a background colour, an accent (buttons, links, switches), a text colour, and optionally a picture for behind the whole window (SVG works best; PNG/JPEG/WebP must stay small because the CSS limit is 50,000 characters).
2. Generate it:
   ```sh
   python tools/new_theme.py --id my-theme --name "My Theme" --appearance dark \
       --base "#0b0d14" --accent "#e8c27a" --text "#ece8e0" --art scene.svg --out my-theme.json
   ```
   It applies the same treatment as every theme here (frosted sidebar, glass popups and dialogs, text-coloured edges, tuned secondary text and status colours) and refuses to write a file that fails a contrast, size or format check. Its messages say what to change.
3. Install it (Playbook 1, step 3) and ask the user to look at a conversation, Settings, a popup and the right panel.
4. Verify on every surface, optionally (Playbook 4). For deeper changes, such as new art treatments or extra CSS, read the guide's §6 recipe and §11 pitfalls first.
5. To add it to this repo's gallery: put the file in `themes/`, capture its screenshots, run `python tools/make_readme.py`.

## Playbook 3: change a theme in this repo

The files in `themes/` are generated; never edit them by hand.
- Soft Bloom: edit `source/soft-bloom/generate.py`, then `python source/soft-bloom/generate.py themes/soft-bloom.json`.
- The 20 scenes: edit `source/theme-examples/build.py` (palettes, colour roles, CSS template), then `python source/theme-examples/build.py` (needs Node 22.6+; it validates all 20 before writing any). If you change how scenes are shrunk (`scenemin.py`), run `python source/theme-examples/verify.py source/theme-examples/build/scenes.json` to prove the pictures didn't change.
- Then verify (Playbook 4), regenerate screenshots and `python tools/make_readme.py`.

## Playbook 4: verify on every surface

Run against a **sandbox** T3, never the user's real data:
```sh
t3 serve --mode web --port 3799 --host 127.0.0.1 --base-dir ./sandbox --no-browser   # separate data folder
t3 project add --base-dir ./sandbox ./some-demo-project
t3 thread start --base-dir ./sandbox --provider claudeAgent --model claude-haiku-5-5 --wait . "…"   # one cheap demo turn
t3 pair --base-dir ./sandbox                                                          # one-time token
node tools/capture/capture.mjs capture.json
```
`capture.mjs` installs the themes through the real Add theme dialog, opens 15 surfaces per theme, checks each really opened, screenshots it, and reports colours that don't belong to the theme and any accent-coloured edge. It exits 1 on failure. See the guide's §10 for the config, contact sheets (`tools/capture/sheet.py`) and `tools/capture/perf.mjs` (paint and raster cost while panels animate).

## Map

| Path | What |
|---|---|
| `themes/*.json` | The installable themes (every file in this folder is one theme). Generated. |
| `themes.json` | A machine-readable list of them: id, name, dark/light, description, download and screenshot URLs. Generated. |
| `tools/new_theme.py` | Make a new theme from a few colours and optional art. |
| `source/soft-bloom/` | Soft Bloom's generator (palette, dithered SVG art, CSS). |
| `source/theme-examples/` | The 20 scene themes: `build.py`, `scenemin.py` (shrinks SVG art losslessly), `verify.py`, `tune_veils.py`, `vendor/` (Anthropic's scene code, unmodified, Apache-2.0). |
| `tools/capture/` | Surface capture, contact sheets, performance traces. |
| `tools/surface_map.py`, `docs/SURFACE-MAP.md` | Every area, slot and hard-coded colour in T3's source, and how Soft Bloom covers them. |
| `tools/make_readme.py` | Writes `README.md`, `docs/GALLERY.md` and `themes.json`. |
| `docs/` | `THEME-GUIDE.md` (start here), `MAINTAINING.md`, `soft-bloom.md`, `GALLERY.md`. |
| `screenshots/` | Gallery images, taken in a sandbox with demo content only. |

## Rules

- Keep each theme's CSS under 50,000 characters, with no backslash (§4 of the guide).
- Edges, focus rings and glows use the text colour, never the accent. Nothing animates behind glass, and nothing that slides is blurred.
- Never run captures against someone's real T3 data folder, and never commit screenshots that show real threads, names or paths.
- Keep the scene themes' Apache-2.0 notice in their CSS and in `NOTICE`.
