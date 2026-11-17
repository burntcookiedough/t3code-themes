# Soft Bloom design spec

The rules behind the look. Every change and every variant should follow them, so the theme stays one coherent thing.

## Character

Dark, moody and dreamy. A night scene rendered like print: dithered and stippled, never smooth gradients alone. Warm near-black, with one cream accent. Quiet by default; it only responds when you act.

## Palette

| Name | Value | Role |
|---|---|---|
| base | `#09090b` | the scene; the darkest "floor" you see through glass |
| deep | `#060607` | sidebar and chrome tint, code |
| ink | `#060607` (glass) / `#08080a` (solid) | popups and dialogs: *darker* than the scene |
| text | `#ede6d6` | primary text, 16:1 on base |
| muted | `#9b968c` | secondary text, 6.8:1 |
| faint | `#938d84` | placeholders and quiet icons, 6.0:1 |
| cream (accent) | `#f1e7d0` | the **only** accent: focus, links, checked switches, glows, hairlines |
| moonlight | `#b9c3d6` | "in progress" status only |
| error / warning / update | `#e5737a` / `#e0b36a` / `#9ec8b8` | muted versions of the usual meanings |

**Rules:**
- **One accent.** Never add a second accent hue. Status colours stay desaturated so they never compete with cream.
- **Text contrast:** every text colour is at least **4.5:1** on the surface it sits on. The theme's own text colours are 6:1 or better.
- **Cream at different strengths:** hairlines, hovers and tints are all cream at low alpha. That's what makes the theme read as one material.

| Use | Cream alpha |
|---|---|
| hover | 3.5–6.5% |
| hairline | 5–9% |
| input border | 12% |
| focus edge | 18–26% |
| selection | 28% |

## Layering (bottom to top)

| Layer | What | Treatment |
|---|---|---|
| 0. Scene | grain, sparkles, halo, dithered star | static; sits behind the whole window |
| 1. Page | chat, Pull requests | transparent: you see the scene |
| 2. Panels | sidebar, chat bar, headers | frosted glass: deep tint 50–72%, blur 8–16px |
| 3. Side panels | right panel (browser/terminal/files/diff) | 90% tint, **no blur** (they slide and resize) |
| 4. Popups | dialogs, Settings, Usage, menus, popovers, toasts | deep ink, *darker than the scene*: Glass opacity +12% (dialogs) / +14% (small popups), blur 24px, a thin top highlight, a deep shadow |
| 5. Dim layer | behind modals | near-black 62%, blur 4px |

Opening something should feel like **sinking into it**, never like lifting a lighter panel. Higher layers are darker or equal, never lighter.

## Shape and edges

- **Corners:** keep T3's own radii (the theme doesn't change geometry).
- **Edges:** 1px cream hairlines; glass panels add an inset 1px top highlight (cream 3–6%).
- **Shadows:** big and soft for popups (`0 30px 90px` black 70%) plus a 1px dark outer ring.

## States

| State | Treatment |
|---|---|
| Hover | cream tint 3.5–6.5%, 160–200 ms ease |
| Press | scale 0.96 (buttons), 0.92 (send) |
| Focus | cream edge plus a soft cream glow, one 350 ms transition |
| Selected thread | brief cream tint that fades out over 2.4 s; no persistent box, never a coloured edge |
| Ready to send | send button gets a cream ring and glow, and one small pop |
| In progress | moonlight `#b9c3d6` |
| Disabled | T3's default (muted) |

## Motion

- **Nothing moves while idle.** No ambient animation, no loops.
- **One-shot only:** motion happens because you did something (focus, hover, press, select, ready).
- **Never animate under glass** (a `backdrop-filter` re-blurs every frame), and **never blur something that slides or resizes**.
- **Reduce motion** turns off every animation and transition.

## Art

- Made of dots: dither and stipple, created with SVG filters (blur, then posterize into steps, then threshold against stretched noise).
- **One focal piece** (the star), placed in empty space at the edges, never under text. It fades out where the text column sits.
- **Embedded as SVG** in the CSS, so the theme stays one importable file (see STABILITY-AUDIT.md).

## Performance budget

- No `:has()` on large or root containers.
- At most three live blurs on screen at once while idle (sidebar, chat bar, header). Popups add one while they're open.
- CSS under 50,000 characters; the whole file well under Add theme's 256 KB (v11 is about 22.6 KB).

## Accessibility

- Text 4.5:1 minimum; the theme's own text colours are 6:1 or better.
- Focus is always visible (cream edge).
- Reduce motion is fully respected.
- **Light mode isn't designed.** The theme is dark-only.
