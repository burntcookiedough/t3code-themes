# Architecture

A T3 Code theme has two parts:

- **`colors`**: about 60 named colour roles (`canvas`, `surface`, `text`, `sidebarRowSelected`, `terminalBackground`, …). T3 maps them onto its CSS variables.
- **`css`**: up to 50,000 characters, applied after T3's own styles. Background images must be embedded as `data:` URLs, and `@import` isn't allowed.

Soft Bloom uses both. The colour roles give every surface the right base palette. The CSS adds the scene, the glass and the interactions on top.

## Palette

| Name | Value | Used for |
|---|---|---|
| base | `#09090b` | the scene's background |
| deep | `#060607` | sidebar and chrome tint, code blocks |
| surface / raised | `#121215` / `#18181c` | cards, selected rows (colour roles) |
| text | `#ede6d6` | main text (≈ 16:1 on base) |
| muted | `#9b968c` | secondary text (≈ 6.8:1) |
| faint | `#938d84` | placeholders, muted icons (≈ 6:1) |
| cream (accent) | `#f1e7d0` | focus, links, checked switches, glows, hairlines (at low alpha) |

Every hairline and tint is the same cream at a different alpha, which keeps the whole theme looking like one material.

## Layer model

```
html / body
└─ [data-slot="sidebar-wrapper"]   ← THE SCENE (fills the whole window)
     background: base gradient + vignette + stipple grain
     ::before   pixel sparkles + dithered halo (top-left), masked under the text column
     ::after    big dithered star (bottom-right gutter), masked toward the text
   ├─ [data-slot="sidebar-inner"]          frosted glass  (50% tint, blur 14px)
   └─ [data-slot="sidebar-inset"]          transparent
        ├─ chat column wrapper, [data-workspace-area="conversation"]   transparent
        │    ├─ [data-chat-header]          glass bar (72% tint, blur 8px)
        │    ├─ messages                    transparent; user bubbles 92% solid
        │    └─ [data-slot="composer-shell"]  T3's own glass, tuned (50%, blur 16px)
        ├─ [data-workspace-area="pull-requests"]   transparent + shade over the star
        └─ [data-workspace-area="panel"]   right panel: 90% tint, NO blur
portals (outside the wrapper)
   [data-slot$="-popup"]       one glass recipe for every popup
   [data-slot$="-backdrop"]    one dim layer for every modal
```

**Why the scene is on the wrapper rather than `body`:** the wrapper is the root of T3's app layout and spans the window, so one scene sits behind the sidebar, the chat, the Pull requests page and the right panel. Portaled popups still blur it, because `backdrop-filter` sees everything painted behind them.

## Design tokens

T3 builds almost every surface from about 15 CSS variables. Overriding them is what makes surfaces the theme never targets directly still match. They're set on `:root` **and** `[data-app-sidebar]`, because T3 redeclares its tokens there.

| Token | Value | Effect |
|---|---|---|
| `--border` | cream 7.5% | every hairline in the app |
| `--input` | cream 12% | input borders, unchecked switch tracks |
| `--accent` | cream 6.5% | hover fills |
| `--muted`, `--secondary`, `--surface-raised` | cream 5–5.5% | chips, buttons, raised blocks |
| `--card` | `rgba(22,22,26,.55)` | cards on the scene |
| `--popover` | `rgba(16,16,19,.86)` | popover fallback |
| `--code-background` | `rgba(6,6,7,.72)` | code blocks |
| `--app-chrome-background`, `--toolbar-background` | `rgba(6,6,7,.55)` | desktop titlebar and toolbars |
| `--toolbar-*`, `--sidebar-border` | cream 5–8.5% | toolbar controls, sidebar edge |
| `--surface-grain` | `none` | turns off T3's own grain; the scene has its own |

`--background` is deliberately **not** made transparent globally. T3 uses it both as a page surface and as the fill for small controls (switch knobs, select triggers). So the theme clears specific page layers instead. Inside modals it's set to solid `#0e0e11` (see the v7 fix in the changelog).

Inside big modals (`dialog`, `sheet`, `alert-dialog`, `command-dialog`) a second token layer applies: `--sidebar: transparent`, `--card: cream 7%`, and cream-tinted sidebar row states. This makes Settings' left nav and group cards glass-over-glass.

## Stable hooks the theme relies on

T3 documents these selectors as stable:
`data-slot="sidebar"|"sidebar-inner"`, `data-thread-item`, `data-chat-header`, `data-workspace-area="conversation"`, `.messages-timeline-scroll`, `data-message-role`, `data-user-message-bubble`, `.chat-markdown`, `.chat-markdown-codeblock`, `data-chat-composer-form`, `data-slot="composer-host"`, `data-thread-terminal-drawer`, `data-slot="button"|"input"|"switch"|"select-trigger"|"dialog-popup"|"popover-popup"|"menu-popup"|"tooltip-popup"|"scroll-area-thumb"`.

The theme also uses these, found by reading the live app. They are **not** guaranteed stable, so they're the first things to check after an update:

| Selector | Why |
|---|---|
| `[data-slot="sidebar-wrapper"]` | where the scene lives |
| `[data-slot="sidebar-inset"]`, `> *:has(> [data-chat-column])` | opaque page layers that have to be cleared |
| `[data-workspace-area="pull-requests"]` (+ `> header`) | the Pull requests page |
| `[data-workspace-area="panel"]` | the right panel |
| `[data-workspace-area="conversation"] > [data-timeline-loading]`, `> .bg-background` | the new-thread page cover |
| `[data-slot="composer-shell"]` and its vars `--glass-opacity`, `--glass-blur`, `--glass-saturation`, `--chat-composer-glass-surface`, `--chat-composer-outline`, `--chat-composer-highlight` | T3's own composer glass |
| `[data-slot="composer-context-strip"]` | the row under the composer ("Full access") |
| `[data-chat-composer-form] button[type="submit"]` | the send button |
| `[contenteditable] > p:only-child > br.ProseMirror-trailingBreak:only-child` | "the composer is empty" |
| `[data-sidebar-row]` | sidebar row transitions |
| `[data-slot$="-popup"]`, `[data-slot$="-backdrop"]` | every popup and modal dim layer (T3 names all of them this way) |
| `[data-slot="settings-group"]` | Settings group cards |
| `[class*="group/attachment"]` | pasted-image tiles |
| `[data-app-sidebar]` | where T3 redeclares its tokens |

## The art

All of it is drawn in `src/generate.py`:

- **Dither filter** (`dither_filter`): blur the shape, posterize it into about 12 bands, subtract stretched fractal noise, then hard-threshold. The result is stippled dots whose density follows the glow, with stepped bands for a mosaic feel. Two subtle points:
  - The noise is stretched (`slope 3.4, intercept -1.2`). Otherwise the change from solid to empty is abrupt.
  - The threshold bias is `0.44`, not `0.5`, so areas with no glow stay completely empty instead of picking up stray dots.
- **Big star** (`bloom_svg`): a 5-point outline with a hollow centre, after the blurred-star reference photo.
- **Pixel sparkles** (`stars_svg`): `crispEdges` plus-shapes with a few tiny dithered glows.
- **Stipple grain**: thresholded high-frequency noise, giving sparse 1px dots.

## Performance rules (learned the hard way)

1. **Nothing animates behind glass.** A `backdrop-filter` re-blurs whenever the pixels behind it change. v3 animated the background under three frosted surfaces, and the app lagged. The scene has been static since v4.
2. **No blur on surfaces that slide or resize.** The right panel animates open, and blurring it made opening it laggy (v7 removed the blur).
3. **No `:has()` on the root wrapper.** v6 used `sidebar-wrapper:has(...)`, which makes the browser re-check style on DOM changes anywhere in the app. v7 replaced it with a local shade on the page itself.
4. **Interactions run only when triggered.** The focus glow and send-button pop are one-shot transitions, so nothing runs while idle.
5. **Message bubbles aren't blurred.** Blurring every visible bubble while scrolling is expensive, and at 92% opacity it wasn't visible anyway.
