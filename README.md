# Soft Bloom for T3 Code

A dark, dreamy theme for [T3 Code](https://github.com/pingdotgg/t3code). It's built on a dithered "soft bloom" scene: a warm near-black background, a stippled star glow, pixel sparkles and a fine dot grain. The sidebar, chat, dialogs and panels sit on top of it as frosted glass.

The theme is one JSON file. A Python script generates it, and T3 Code's `t3 theme` command installs it.

| | |
|---|---|
| Current version | **v10** (`themes/soft-bloom.json`) |
| Built against | T3 Code `0.1.10-nightly.20261116` |
| Needs | A T3 Code build with **theme CSS** support (nightly as of Nov 2026). Stable `0.1.9` only applies the colours. See [Compatibility](#compatibility). |
| Appearance | Dark only |

## Install

**Easiest:** in T3 Code open **Settings → Appearance → Add theme**, then drop `themes/soft-bloom.json` into the dialog (or paste its contents). The CSS comes along with the colours.

**Or from a terminal:**

```powershell
t3 theme set themes/soft-bloom.json
```

This publishes the file as the theme `soft-bloom`, and every connected T3 Code window switches to it. After that you can also pick **Soft Bloom** under Settings → Appearance → Themes.

## Change it

Edit `src/generate.py`, then regenerate and publish:

```powershell
./scripts/publish.ps1          # Windows
./scripts/publish.sh           # macOS / Linux / Git Bash
```

Both scripts run `python src/generate.py themes/soft-bloom.json` and then `t3 theme set themes/soft-bloom.json`.

The generator only uses the Python standard library. All the art (dither filters, stars, grain) is drawn as SVG and embedded in the CSS, so the theme has no external files. The CSS must stay under T3's 50,000-character limit. It's currently about 19,400.

## Roll back

| Command | What you get |
|---|---|
| `t3 theme set t3-chat` | T3 Code's default look |
| `t3 theme set themes/archive/soft-bloom-v2-dither.json --id soft-bloom-v2` | v2: dither art in the chat area only, no motion |
| `t3 theme set themes/archive/soft-bloom-v1-original.json --id soft-bloom-original` | v1: the first Soft Bloom |
| `t3 theme set themes/archive/soft-bloom-v6.json --id soft-bloom-v6` | any archived version |

`themes/archive/` also holds the earlier explorations: **Ink Night**, **Dream Tide** and **Snow Pines**.

## Compatibility

How Soft Bloom interacts with T3 Code's own settings. Everything here was checked on a live install unless it says otherwise.

| T3 setting | What happens |
|---|---|
| **Appearance → Color scheme** | The theme defines only a dark appearance. Use Dark or System; Light isn't designed for. |
| **Glass opacity** | Dialogs, menus, popovers, the command palette and toasts follow it, kept deep: dialogs add 12%, small popups add 14%. The **chat bar** is fixed at 50% by the theme so its frost stays visible. Raise the slider for more solid popups. |
| **Contrast** | Works. T3 derives its contrast colours from the theme's tokens. |
| **Chat width** | Tuned for *Comfortable*. With *Wide*, the text column reaches further right and can overlap the faint edge of the star art. It stays readable because the art is masked under the text, but it looks busier. *(Not visually tested.)* |
| **Typography / font sizes** | Unaffected. |
| **Reduce motion (OS setting)** | Turns off the send-button pop and every transition. The theme has no always-on animation. |
| **Sidebar collapsed / floating / Labs "boring sidebar"** | All use `[data-slot="sidebar-inner"]`, which the theme styles. *(Only the default sidebar was visually tested.)* |
| **Mobile app** | T3 doesn't apply themes on mobile. |

More detail:

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): how the layers, tokens and glass fit together, every selector the theme relies on, and why each choice was made.
- [`docs/SURFACES.md`](docs/SURFACES.md): every surface, whether it was tested, and its known issues.
- [`docs/MAINTAINING.md`](docs/MAINTAINING.md): what to check when T3 Code updates, especially when theme CSS reaches the stable release.
- [`docs/CHANGELOG.md`](docs/CHANGELOG.md): every version and what it fixed.
- [`docs/ROADMAP.md`](docs/ROADMAP.md): research findings and the plan for a community release.
