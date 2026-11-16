# Stability audit

How much of Soft Bloom rests on things T3 Code promises to keep, and how much rests on internals that can change in any release. Audited against T3 Code `main` at `70a7cfe` (2026-11-16) and Soft Bloom v10.

## What T3 officially supports

From T3's source (`packages/shared/src/themeCss.ts`, the guide that `t3_theme_read` returns):

- **Colour roles** (61 of them, `packages/shared/src/themePalettes.ts`). The guide says: *"Prefer colors over CSS."* Roles accept transparency: T3 parses and keeps the alpha.
- **29 stable CSS selectors** (`THEME_CSS_HOOKS`). A T3 test fails if one disappears from the source, so these are a real contract. Everything else, in the guide's words, *"change[s] between releases, so do not use them"*.
- **CSS limits:**
  - `css` holds up to 50,000 characters.
  - It can't load files: no `@import`, no `image-set()`, and `url()` only with `data:` or `#id`.
  - Any declaration value that contains a backslash is dropped.
  - T3 applies it as an adopted stylesheet *after* its own styles.
- **Background images** (new on Nov 16): a JPEG, PNG or WebP of up to 16 MB placed next to the theme file, used through `var(--theme-background-image)`. The guide says *"Do not embed images in `css`"*.
- **Deliberately not themeable:** success, info, provider and channel identity colours (comment in `apps/web/src/index.css`).

## How Soft Bloom v10 measures up

Every selector in the generated CSS, sorted:

| Group | Count | Selectors |
|---|---:|---|
| Official stable hooks, standard HTML/ARIA attributes, global pseudo-elements | 31 | chat header, conversation, timeline scroll, message rows and bubbles, `.chat-markdown`, code blocks, composer form/host/editable, send button (`[data-chat-composer-form] button[type="submit"]`), sidebar inner, terminal drawer, button, dialog/popover/menu/tooltip popups, scroll thumb, `::selection`, `:root` |
| Internal, **can move to stable** | 5 | `[data-app-sidebar]` (token scope) and four `[data-sidebar-row]` rules |
| Internal, **needed, degrades gracefully** | 21 | the scene on `[data-slot="sidebar-wrapper"]` (and `::before` / `::after`); clearing opaque layers (`sidebar-inset`, the chat column wrapper, `[data-timeline-loading]`, `.bg-background`); `[data-workspace-area="panel"]` and `"pull-requests"`; `composer-shell` (T3's glass variables); `composer-context-strip`; pasted-image tiles (`group/attachment`); `settings-group`; the extra popup kinds (sheet, alert, command, select, combobox, autocomplete, preview card, toast) and the `-backdrop` family |

There are **no values with backslashes**, so nothing gets dropped by T3's filter.

### What "degrades gracefully" means here

If T3 renames one of these internals, that rule simply stops matching. Nothing breaks layout, because every fragile rule only sets colours, backgrounds, borders or shadows, never sizes or positions. The worst case for each:

| If this changes | What you'd see |
|---|---|
| `sidebar-wrapper` | No dither scene; plain dark palette (from the colour roles) |
| `sidebar-inset`, chat column wrapper | Scene hidden behind an opaque dark page |
| `panel`, `pull-requests` | That area uses the default dark surface instead of tinted glass |
| `composer-shell` variables | Chat bar falls back to T3's own glass at your Glass opacity setting |
| extra popup slot names | That popup type uses T3's default surface (still palette-coloured) |
| `group/attachment` | Pasted-image tiles use T3's default tile |

## Recommendations

1. **Move the 15 translucent token values into colour roles.** This is done on the `roles-first` branch as v11, *not published*. It:
   - deletes the CSS token block and the fragile `[data-app-sidebar]` selector (T3 maps roles into the sidebar scope itself);
   - gives stable-without-CSS users the full palette, transparency included.

   Before publishing, verify live:
   - the main chat, Settings, Usage, popovers and `html_render` charts;
   - the chips that derive colours from roles.

   T3 feeds roles into a few JavaScript calculations as well as CSS.
2. **Use the stable `[data-thread-item]` hook** (plus the standard `aria-current`) for sidebar rows. This is also done on `roles-first`.
3. **Keep the embedded SVG art, on purpose.** The official background-image path only works for themes installed with `t3 theme set` (it loads from the server's themes folder). A theme imported through **Add theme**, which is how most community users will install, can't carry an image file. Embedded `data:` SVG is explicitly allowed by T3's filter and is the only way to ship the scene in a single importable file. Optionally, a future version could *also* ship a raster background for `t3 theme set` users.
4. **Treat the `--info-foreground` override as optional.** T3 keeps "info" fixed on purpose. The override works today because theme CSS applies after T3's styles, but it isn't part of the contract.
5. **Re-run `tools/surface_map.py` on every T3 update** and diff `docs/SURFACE-MAP.md`. A removed slot or workspace area shows up as a changed line.
