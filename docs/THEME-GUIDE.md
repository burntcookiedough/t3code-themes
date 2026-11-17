# Making T3 Code themes: the complete guide

Everything we learned building the themes in this repo, written so you (or your coding agent) can start a new theme without rediscovering it. Facts here were checked against T3 Code `0.1.10-nightly.20261116` and its source (`pingdotgg/t3code` at `70a7cfe`); theme CSS ships in stable **v0.1.10**.

**Agents: read this whole file first.** Then copy the closest theme in `themes/`, change it, and verify with the tools in the last sections.

---

## 1. What a theme is

One JSON file:

```json
{
  "version": 1,
  "id": "my-theme",
  "name": "My Theme",
  "appearance": "dark",
  "canvas": "#0d0f14",
  "accent": "#e8c27a",
  "colors": { "text": "#ede6d6", "border": "rgba(237,230,214,.08)" },
  "css": "/* optional, up to 50,000 characters */",
  "collection": { "id": "my-collection", "label": "My themes" }
}
```

| Field | Rules |
|---|---|
| `version` | Must be `1`. |
| `id` | Lowercase letters, numbers, hyphens. Defaults to the name. **Reserved:** `t3-chat`, `grove`, `ocean`, `ember`, `iris` (the built-ins); a file using one is refused. |
| `name` | 48 characters or fewer. |
| `appearance` | `"dark"` or `"light"`. A theme fills that *half* of T3's appearance (see §2). |
| `canvas`, `accent` | Hex. T3's agent tools derive a palette from them; Add theme fills any role you leave out of `colors` with T3's default for the appearance. Set every role you care about in `colors`. |
| `colors` | Any of the 61 roles in §3. Values may be translucent (`rgba(...)`). |
| `variants` | Optional `{ "light": {roles}, "dark": {roles} }` for the *other* appearance (colours only; `css` is shared). |
| `css` | ≤ 50,000 characters. Over the limit, Add theme refuses the file ("Theme CSS must be text of 50000 characters or fewer"). |
| `collection` | Optional; groups themes on the picker and lets Remove take the whole group. Kept by Add theme. |

**Prefer colour roles over CSS.** Roles reach surfaces you never open, survive T3 updates, and still apply where CSS doesn't.

## 2. Installing, and how T3 picks what shows

- **Settings → Appearance → Add theme:** drop one or many `.json` files (≤ 256 KB each), or paste JSON. Stored in that client.
- **`t3 theme set <file>`:** publishes the file to the machine (`~/.t3/userdata/themes/<id>.json`) and switches every local client to it. It accepted 51 KB files on the nightly above. `t3 theme set <id>` switches to a built-in or published theme; `--id` publishes under another id.
- **Halves:** T3 keeps a *light* and a *dark* theme and shows one according to **Color scheme** (Light, Dark, System). A light-appearance theme picked while the app is dark is stored but not visible until the scheme is light. Pairs of themes make good halves with Color scheme = System.
- **Background image file:** a JPEG/PNG/WebP (≤ 16 MB) at `<themesDir>/<id>.jpg` is exposed as `var(--theme-background-image)`. Only for themes installed with `t3 theme set`; an Add-theme import can't carry a file. To ship one importable file, embed art as a `data:` SVG in `css` instead (this repo does).

## 3. Colour roles and the CSS tokens they drive

T3's stylesheet maps each role to a token (`apps/web/src/index.css`), both at `:root` and inside the sidebar scope `[data-app-sidebar]`, so one role value reaches both.

| Role | Token(s) | Paints |
|---|---|---|
| `canvas` | `--background` | page background **and** small controls (switch knobs, select triggers): never make it transparent globally |
| `text` | `--foreground`, `--card-foreground`, `--popover-foreground` | body text |
| `textMuted` | (muted text) | secondary text |
| `surface` | `--card` | cards |
| `surfaceRaised` | `--surface-raised` | raised blocks |
| `surfaceOverlay` | `--popover` | popovers, menus, **and T3's "dropdown glass"** (see §6) |
| `border` | `--border` | every hairline |
| `input` | `--input` | input borders, unchecked switch tracks |
| `focus` | `--ring` | focus outlines |
| `accentSurface` / `accentSurfaceForeground` | `--accent` / `--accent-foreground` | hover fills |
| `secondary`, `secondaryForeground` | `--secondary*` | secondary buttons |
| `muted`, `mutedForeground` | `--muted*` | chips, muted text |
| `placeholder`, `secondaryLabel`, `iconMuted` | `--placeholder`, `--secondary-label`, `--icon-muted` | |
| `messageSurface`, `messageForeground` | `--message-surface`, `--message-foreground` | user message bubbles |
| `messageAction`, `messageActionForeground`, `messageActionHover` | `--primary`, `--primary-foreground`, `--message-action-hover` | primary buttons, send button, checked switches |
| `codeBackground`, `codeForeground` | `--code-background`, `--code-foreground` | code blocks (syntax colours come from T3's code theme, not roles) |
| `chrome` | `--app-chrome-background` | desktop titlebar |
| `toolbar*` (6 roles) | `--toolbar-*` | toolbars and their controls |
| `sidebar` | `--sidebar` | sidebar surface |
| `sidebarForeground`, `sidebarMutedForeground`, `sidebarControlSurface`, `sidebarRowHover`, `sidebarRowActive`, `sidebarRowSelected`, `sidebarBorder` | `--sidebar-*` | sidebar text, rows, edge |
| `error*`, `warning*`, `update*` (3 each) | `--error*`, `--warning*`, `--update*` | status colours |
| `searchMatch*` (4) | used directly | find-in-thread highlights |
| `terminal*` (6) | `--terminal-*` | terminal canvas (opaque by design) |
| `accent` | derived accents | |

**Not themeable on purpose:** success, info, provider and channel identity colours. (`--info-foreground` can be overridden from CSS because theme CSS loads last, but it's outside the contract.)

## 4. What theme CSS may contain

T3 filters theme CSS (`packages/shared/src/themeCss.ts`), applies it as an adopted stylesheet **after** its own styles, and drops what fails:

- No `@import`, no `image-set()`, no `src()`. `url()` only with `data:` or `#id`.
- **Any declaration whose value contains a backslash is dropped.** In a `data:` URL, percent-encode `\` as `%5C`.
- A quoted `url("...")` string must not contain line breaks.
- In data URLs encode `%`→`%25`, `#`→`%23`, `"`→`%22`; encode `<` before `/style` (`%3C/style`) so the CSS stays safe inside any `<style>` tag. Other `<`/`>` can stay raw.
- T3's own rules are often more specific: use `!important` when a rule has no effect.
- Single quotes inside the SVG keep it compact: `url("data:image/svg+xml,<svg xmlns='...'>...")`.

## 5. Selectors

**Stable hooks** (T3 tests that these stay in the source):
`[data-slot="sidebar"]`, `[data-slot="sidebar-inner"]`, `[data-thread-item]`, `[data-slot="project-monogram"]`, `[data-chat-header]`, `[data-workspace-area="conversation"]`, `.messages-timeline-scroll`, `[data-timeline-row-kind]`, `[data-message-role="user"]`, `[data-user-message-bubble]`, `[data-message-role="assistant"]`, `.chat-markdown`, `.chat-markdown-codeblock`, `[data-chat-composer-form]`, `[data-slot="composer-host"]`, `.composer-tiptap`, `[data-thread-details-card]`, `[data-thread-terminal-drawer]`, `[data-settings-page-scroll]`, `[data-slot="button"]`, `[data-slot="input"]`, `[data-slot="switch"]`, `[data-slot="select-trigger"]`, `[data-slot="dialog-popup"]`, `[data-slot="popover-popup"]`, `[data-slot="menu-popup"]`, `[data-slot="tooltip-popup"]`, `[data-slot="scroll-area-scrollbar"]`, `[data-slot="scroll-area-thumb"]`. Also standard ARIA such as `[aria-current="page"]`.

**Needed for full-window themes but not guaranteed** (all exist today; check after every T3 update with `tools/surface_map.py`):

| Selector | Why |
|---|---|
| `[data-slot="sidebar-wrapper"]` | the root layout element: put a whole-window scene here |
| `[data-slot="sidebar-inset"]`, `… > *:has(> [data-chat-column])` | opaque page layers to clear |
| `[data-workspace-area="conversation"] > [data-timeline-loading]`, `> .bg-background` | the new-thread page's cover |
| `[data-workspace-area="panel"]`, `="pull-requests"` | right panel, Pull requests page |
| `[data-slot="composer-shell"]` + vars `--glass-opacity`, `--glass-blur`, `--glass-saturation`, `--chat-composer-glass-surface`, `--chat-composer-outline`, `--chat-composer-highlight` | the chat bar's own glass: tune these instead of stacking a second glass |
| `[data-slot$="-popup"]`, `[data-slot$="-backdrop"]` | every popup and modal dim layer (T3 names them all this way) |
| `[data-slot="settings-group"]`, `[data-slot="composer-context-strip"]`, `[class*="group/attachment"]` | Settings cards, the row under the composer, pasted-image tiles |

Rules that only set colours, backgrounds, borders and shadows degrade gracefully when a selector goes away: never use them for layout.

## 6. Recipe: a scene behind the whole window, with glass

What every theme in this repo does (see `source/soft-bloom/generate.py`, `source/theme-examples/build.py`):

1. **Scene** on `[data-slot="sidebar-wrapper"]` (`background: <base> url(data:…) center / cover`). It spans sidebar, chat, Pull requests and panels; portaled popups still blur it.
2. **Clear the opaque layers** listed in §5 (`background: transparent !important`).
3. **Sidebar:** `[data-slot="sidebar-inner"]` as frosted glass (tint at 0.5–0.8 + `backdrop-filter: blur(12–16px)`).
4. **Chat header:** glass bar. **Conversation:** transparent, with a *reading veil* (a horizontal gradient of the tint, full strength across the column ±440px, fading to transparent by ±620px) when the art is busy.
5. **Composer:** set the `composer-shell` glass variables; put the focus glow on `composer-host`'s `box-shadow`.
6. **Popups** (`[data-slot$="-popup"]`): a deep "ink" tint, *darker* than the scene in dark themes, following the user's Glass opacity: `color-mix(in srgb, <ink> min(100%, calc(var(--glass-opacity, 80%) + 12%)), transparent)`, blur 24px. **Backdrops:** one dim layer.
7. **Inside big modals** (`dialog`, `sheet`, `alert-dialog`, `command-dialog`): set `--background` to a **solid** colour (switch knobs and select triggers paint with it), `--sidebar: transparent`, `--card` faint.
8. **Thread details card** (`[data-thread-details-card]`): T3 paints it with its *dropdown glass* (the popover colour plus a bright edge). It stays on screen, so restyle it like the sidebar glass, or it looks like a stray popup.
9. **Right panel:** tint, **no blur** (it slides and resizes).
10. **Banners attached above the chat box** (usage limit reached, `/clear`'s "fresh session", replies; `[data-composer-banner-surface]`): set `--chat-composer-attached-surface` to the chat box's glass colour and `--chat-composer-attached-outline` to your hairline. Under a custom theme T3 otherwise paints them with `surfaceRaised` (often a faint tint) and a warning/error-coloured outline. While one is attached T3 hides the chat box's own frame, so **remove your own ring/shadow from `composer-host` too** (`[data-slot="composer-host"]:has([data-composer-banner-surface="attached"])`), or it wraps the stack in a second frame.
11. **Status colours:** `success` and the diff counts aren't roles, but tokens you can set from CSS: `--success`, `--success-foreground`, `--diff-addition-foreground`, `--diff-deletion-foreground` (and `--info`, `--info-foreground`). Otherwise "Done" and `+N` stay T3's bright emerald on every theme. Derive `errorSurface`/`warningSurface`/`updateSurface` from your glass, and give `[data-slot="alert"]` your hairline instead of the status-coloured outline.
12. **Selected thread:** no accent edge; a short fade (`[data-thread-item] [aria-current="page"]` animation to transparent) so it doesn't look stuck.
13. **Reduced motion:** wrap every transition/animation off under `prefers-reduced-motion: reduce`.

## 7. Surfaces to check

Every theme in this repo is captured on these 15 surfaces by `tools/capture` (§10): chat thread (bubbles, code block, changed-files card, details card), new thread, model picker, thread menu, command palette (Ctrl/Cmd+K), a banner attached to the chat box (`/clear`), tooltip, Files panel, Diff panel, terminal drawer, delete confirmation, Settings, Settings → Appearance, Usage, Pull requests. Also worth a look by hand: toasts, find bar, Browser panel, onboarding/empty states. `docs/SURFACE-MAP.md` lists every area, slot and hard-coded colour found in T3's source.

## 8. Performance rules (learned the hard way)

1. **Nothing animates behind glass.** `backdrop-filter` re-blurs whenever the pixels behind it change; an animated background under three glass surfaces made the app lag. Keep scenes static.
2. **No blur on surfaces that slide or resize** (the right panel).
3. **No `:has()` on the root wrapper:** it re-checks style on every DOM change. Local `:has()` on a small element is fine.
4. **Only one-shot animations**, triggered by interaction (focus glow, send-button pop). Nothing loops while idle. ("No continuously repainting animations" is also a T3 rule.)
5. Don't blur every message bubble; a near-opaque fill reads the same.
6. Prefer small text-shadows (≤ 2px blur) on chat text.

## 9. Design rules this repo follows

- **Contrast:** body text ≥ 7:1 on flat surfaces; secondary text and placeholders ≥ 4.5:1 on the ground, the glass tint and the popup colour; focus outlines ≥ 3:1. Over art, measure the pixels under the text column (`source/theme-examples/tune_veils.py`): 4.5:1 on 99.5% of them, 3:1 on all.
- **No coloured edges.** Hairlines, focus edges, glows and rings use the text colour at low alpha, never the accent; the accent is for fills (buttons, switches, links).
- **Popups darker than the scene** in dark themes; a clean light sheet in light themes.
- **One material:** every surface is the same glass in different strengths; no default-grey T3 panel left over.

## 10. Tools in this repo

| Tool | What it does |
|---|---|
| `tools/capture/capture.mjs` | Drives T3 in headless Chrome: installs themes through the real Add theme dialog, opens the 14 surfaces, screenshots each, and reports **off-palette colours** (backgrounds, borders, text far from every colour the theme defines). |
| `tools/capture/sheet.py` | One contact sheet per theme from those screenshots. |
| `tools/surface_map.py` | Maps every area, `data-slot` and hard-coded colour in a T3 source checkout; diff its output after T3 updates. |
| `source/theme-examples/scenemin.py` + `verify.py` | Shrinks SVG art to fit the CSS limit without changing what it draws, and proves it pixel by pixel in Chrome. |
| `source/theme-examples/tune_veils.py` | Measures how strong a reading veil must be for text over art. |

**Run captures against a sandbox, never your real data:**

```sh
t3 serve --mode web --port 3799 --host 127.0.0.1 --base-dir ./sandbox --no-browser   # separate data folder
t3 project add --base-dir ./sandbox ./demo-project
t3 thread start --base-dir ./sandbox --provider claudeAgent --model claude-haiku-5-5 --wait . "…"   # a real, cheap demo turn
t3 pair --base-dir ./sandbox          # one-time token for the capture config
node tools/capture/capture.mjs capture.json
```

`tools/capture/sheet.py <outDir> --compare <surface> x,y,w,h [scale] [cols]` puts one region of one surface side by side for every theme: the fastest way to spot the theme that's styled differently. `capture.json` takes `origin`, `token`, `thread` (`/<environmentId>/<threadId>`), `themeFiles`, optional `themes`, `surfaces`, `outDir`, `redact` (text to swap before screenshots), `format`/`quality`. In a fresh `--base-dir`, providers start disabled; the Claude provider's instance id is `claudeAgent`.

## 11. Pitfalls we hit (so you don't)

| Symptom | Cause | Fix |
|---|---|---|
| Add theme refuses the file | CSS over 50,000 characters | shrink art (`scenemin.py`), minify CSS |
| One declaration silently ignored | its value contains `\` | percent-encode (`%5C`) |
| Invisible switch knobs in Settings | `--background` made transparent inside dialogs | solid `--background` in the modal token layer |
| A flat panel hides the scene on the new-thread page | T3's `[data-timeline-loading]` / `.bg-background` cover | clear it (§5) |
| Double frame around the chat bar | a second glass stacked on T3's composer glass | tune `composer-shell` variables instead |
| App lags, fans spin | animated background under `backdrop-filter`; blur on the right panel; `:has()` on the root | §8 |
| Selected thread looks stuck | persistent selected-row fill | fade it out; no accent edge |
| A dark card with a bright edge on a glass theme | T3's dropdown glass on `[data-thread-details-card]` | §6 step 8 |
| Code colours don't match the palette | syntax colours come from T3's code theme, not roles | accept, or style tokens by hand |
| Add theme refuses one file of a batch | reserved id (`ember`, …) | rename the id |
| Light theme "doesn't apply" | the app is in Dark; a light theme fills the light half | set Color scheme to Light or System |
| A `<style>` page breaks when the CSS is embedded | a raw `</style` inside a data URL | encode as `%3C/style` |
| A second frame around the chat box when a banner (e.g. "usage limit reached") is attached | the theme's ring/shadow on `composer-host`, which contains the banner | §6 step 10 |
| Bright emerald "Done" and diff counts on every theme | T3's fixed `--success` | §6 step 11 |
| Solid wine/olive error and warning notices | fixed `errorSurface`/`warningSurface` roles | derive them from the theme's glass |
| Preview tab screenshots fail or freeze transitions | hidden preview tabs produce no frames; `.no-transitions` stays on | use headless Chrome (`tools/capture`) |

## 12. A workflow for agents

1. Read this file, then `docs/SURFACE-MAP.md` for the current T3 layout.
2. Copy the closest theme from `themes/` (Soft Bloom for an original scene; a scene port for a light theme), or start from a generator in `source/`.
3. Set the colour roles first; check §9 contrast targets in code.
4. Add CSS only for what roles can't do; follow §6.
5. Keep the CSS under 50,000 characters; check for `\`.
6. Capture all surfaces in a sandbox (§10); read the off-palette report and the contact sheet; fix; repeat.
7. Install with Add theme and look at it yourself in the real app.
