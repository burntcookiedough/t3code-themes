# Changelog

## v8 (current)
- Settings, Usage and every other popup are now **darker than the main screen** instead of lighter. They use a deep ink tint (`#060607`, Glass opacity + 12%; small popups + 14%), a darker dim layer behind modals (62%), a deeper shadow with a thin top highlight, a darker Settings nav, and quieter cards and selected rows.
- Fix: the publish scripts fall back to `~/.t3/bin/t3.cmd` when `t3` isn't on PATH.

## v7
- **Fix:** switch knobs were invisible in Settings. T3 paints knobs and select triggers with `--background`, which v6 made transparent inside modals. It's now solid `#0e0e11` there.
- **Performance:** the right panel no longer uses a live blur (it slides and resizes, so the blur lagged). It's a 90% tint instead.
- **Performance:** removed the `:has()` on the root wrapper (it made the browser re-check style app-wide). The Pull requests page shades the star itself instead.
- Popups follow **Settings → Appearance → Glass opacity** (small popups add 8%).
- Added documentation, a generator and publish scripts, and moved everything into this repo.

## v6
- Design-token layer (`--border`, `--input`, `--accent`, `--muted`, `--card`, `--popover`, chrome/toolbar, `--surface-grain: none`), so every surface uses the same palette.
- One glass recipe for every `[data-slot$="-popup"]` and one dim layer for every `-backdrop`.
- Settings, Usage, the command palette and sheets: glass-over-glass token layer, transparent nav, hairline group cards.
- The Pull requests page sits on the scene; the right panel was themed.

## v5
- The scene moved from the chat area to the root layout, so it spans the sidebar too; the sidebar became frosted glass.
- Cleared T3's opaque page layers.
- Fixed the double frame around the chat bar on the new-thread page (the glow now hugs the input box only).

## v4
- Removed the background animation (stepped animation looked choppy; smooth animation under glass caused lag).
- Removed the cream/green edge on the selected sidebar row.
- No blur on message bubbles; lighter header blur; normal composer blur.
- Moved the star to the empty bottom-right gutter (it sat under text on wide windows).

## v3
- Used T3's own composer glass instead of a stacked second layer (the real reason the frost hadn't shown).
- Added the focus glow, send-button pop, sidebar and button micro-interactions, a twinkle/breathe background (later removed), and contrast fixes.

## v2
- Dithered and stippled art: a posterized-noise dither star, pixel sparkles and stipple grain.
- Cleaner pasted-image tiles.

## v1
- First Soft Bloom: warm near-black, a big soft blurred star, cream accents, film grain.
- Earlier explorations (Snow Pines, Ink Night, Dream Tide) are in `themes/archive/`.
