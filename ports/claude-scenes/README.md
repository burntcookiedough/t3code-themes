# theme-examples scenes for T3 Code

The twenty scenes from Anthropic's [theme-examples](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/theme-examples) plugin for the Claude Code desktop app, ported to T3 Code themes. Each one puts the scene behind the whole window, with the same frosted-glass treatment as Soft Bloom: sidebar, chat bar, popups, Settings, Usage, Pull requests, the right panel and the fading selected-thread highlight.

The scenes are Apache-2.0 and the ports keep that license. Each theme file carries the license notice in its CSS. See [NOTICE](NOTICE) for what changed. These ports are not made or endorsed by Anthropic.

| Dark | Light |
|---|---|
| Halftone Dusk, Plotter Tide Night, Dither Dunes Night, Paper Garden Kraft, Night Reef, Snow Pines, Braille Stars, Block Clouds, Vector Range, Departure Board, Blueprint, Deep Water, Aurora, Ember Glow | Honu Lagoon, Koi Mosaic, Halftone Dawn, Plotter Tide, Dither Dunes, Paper Garden |

In T3, two of these show with a comma: "Plotter Tide, Night" and "Paper Garden, Kraft".

## Install

In T3 Code, open **Settings → Appearance → Add theme** and drop any of the files from `themes/` into the dialog. You can drop all twenty at once. They're grouped as one collection, so the Remove dialog can remove them together.

Or from a terminal, one file at a time: `t3 theme set themes/snow-pines.json`. That publishes the theme on this machine and switches to it. On nightly `0.1.10-nightly.20261116` it accepted every file here, the largest being 51 KB.

**Light scenes** fill T3's *light* half. They show when **Color scheme** is Light, or System on a light OS. The scenes that come in pairs can be used as the two halves: for example, Halftone Dawn for light and Halftone Dusk for dark, with Color scheme set to System.

## Still, not animated

In the Claude app these scenes move. Here each one is the still picture Anthropic composed for "reduce motion". T3's glass re-blurs whenever anything behind it changes, so a moving scene under the sidebar and chat bar makes the app lag. Soft Bloom ran into the same problem and dropped its animation. The fireworks from the plugin aren't included either, because T3 themes can't run code.

## Readability

- **Chat column:** a soft veil of the scene's own glass tint sits behind it. It covers the column at full strength at any window width, then fades into the scene over 180px, so it has no edge. The required strength is measured, not guessed: `tune_veils.py` renders each scene at two window sizes and picks the weakest veil at which body text reads at 4.5:1 on 99.5% of the pixels under the column, and at 3:1 on all of them. The results go in `veils.json`, plus a small margin.
- **Sidebar:** frosted (at least 12px blur, 70% tint) whatever the scene's own glass setting.
- **Colours:** secondary text and placeholders are tuned to read at 4.5:1 on the scene's ground colour, its glass tint and the popup colour.
- **Edges:** edges and focus glows use the text colour, never the accent.

## How it's built

```
python build.py        # Node 22.6+ and Python 3, standard library only
python verify.py build/scenes.json
```

1. `dump-scenes.mts` runs the plugin's own scene code from `vendor/` and saves every scene's SVG in `build/scenes.json`.
2. `scenemin.py` makes each scene's reduced-motion still, then shrinks it to fit T3's 50,000-character CSS limit. It removes the animation code and anything the still never shows, and culls shapes outside the frame. It rewrites paths, draws tiles and dots as strokes, and shortens ids and numbers.
3. `build.py` wraps each still in the theme's CSS and colour roles. It fails if a theme breaks a T3 limit or a contrast target, or if a scene has no measured veil.
4. `verify.py` renders every original still and its shrunk version in headless Chrome at two scales, compares them pixel by pixel, and exits with an error if more than 0.2% of any scene's pixels differ visibly:
   - **18 scenes:** no pixel at either scale is off by more than 24 of 255 in any channel, and most are exactly identical. (At some other scales Snow Pines has a few dozen glyph-edge pixels that land a sub-pixel apart.)
   - **The two Halftones:** about 0.1% of pixels differ, a few of them strongly. These are edge pixels of dots that land a fraction of a pixel away, because dots placed along evenly spaced runs replace dots placed one by one.

## Known limits

- **Size:** the largest theme (Dither Dunes Night) uses 48,577 of the 50,000 characters, so any added CSS needs a matching saving.
- **Chat width:** checked at the Comfortable chat width. With *Wide*, the text column reaches past the veil's full-strength band.
- **Ember:** this scene is called **Ember Glow** (`ember-glow`). T3 reserves the id `ember` for its built-in Ember theme, and a second theme named "Ember" would be confusing next to it.
