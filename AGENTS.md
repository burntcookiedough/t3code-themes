# For coding agents

You're probably here to make or change a T3 Code theme. Start with **[docs/THEME-GUIDE.md](docs/THEME-GUIDE.md)**: the theme format, every colour role and the CSS token it drives, what theme CSS may contain, which selectors are stable, the glass recipe these themes use, the surfaces to check, performance rules, and the pitfalls we already hit.

## Map

| Path | What |
|---|---|
| `themes/*.json` | The installable themes. Generated: change the sources, not these files. |
| `source/soft-bloom/generate.py` | Soft Bloom: palette, art (dithered SVG) and CSS. `python source/soft-bloom/generate.py themes/soft-bloom.json` |
| `source/theme-examples/` | The 20 scene themes: `build.py` (palettes, CSS), `scenemin.py` (SVG shrinking), `verify.py` (pixel check), `tune_veils.py` (readability), `vendor/` (Anthropic's scene code, unmodified, Apache-2.0). |
| `tools/capture/` | Headless screenshots of all surfaces under every theme, plus an off-palette colour report. |
| `tools/surface_map.py` | Maps T3's source: areas, slots, hard-coded colours. |
| `docs/SURFACE-MAP.md` | Its output for the T3 version these themes were built against. |
| `docs/soft-bloom.md` | How Soft Bloom is built: palette, layers, art. |
| `screenshots/` | Gallery images (made with `tools/capture` in a sandbox, never real user data). |

## Rules

- Keep each theme's CSS under 50,000 characters, with no backslash (§4 of the guide).
- Never run captures against someone's real T3 data folder: use `t3 serve --base-dir <sandbox>`.
- Keep the scene themes' Apache-2.0 notice in their CSS and in `NOTICE`.
- Edges and focus glows use the text colour, never the accent; nothing animates behind glass.
