# Maintaining the themes across T3 Code updates

Theme CSS shipped in stable T3 Code **v0.1.10** (November 2026). These themes were built against `0.1.10-nightly.20261116`. This is what to check when T3 updates.

## Health check

1. **Re-map T3.** Run `python tools/surface_map.py <t3code checkout> themes/soft-bloom.json > docs/SURFACE-MAP.md` and diff it. A removed slot or workspace area shows up as a changed line.
2. **Capture every surface** of every theme in a sandbox with `tools/capture` (see §10 of [THEME-GUIDE.md](THEME-GUIDE.md)). Read `report.json` for new off-palette colours, and look at the contact sheets (`python tools/capture/sheet.py <outDir>`).
3. **Things that mean something broke:**
   - **A flat, opaque area where the scene used to show through:** T3 renamed or added a page wrapper. Find the element with a solid `background-color` between `[data-slot="sidebar-wrapper"]` and the content, and add it to the "clear every opaque layer" rule in both generators.
   - **No scene at all:** `[data-slot="sidebar-wrapper"]` was renamed. Move the scene to the new root layout element (or `body`).
   - **Invisible switch knobs or controls:** a control now paints with a token the theme made transparent. Check `--background`, `--sidebar` and `--card` inside modals, and the colour roles.
   - **A double frame around the chat bar:** T3 changed the composer's glass. Re-check `composer-shell` and `composer-host`.
   - **A dark card with a bright edge on a glass theme:** another persistent element now uses T3's dropdown glass. Restyle it like `[data-thread-details-card]`.
   - **The panel's tabs or window-controls inset look darker than the chat header:** check `[data-right-panel-tabbar]` and its parent panel. Paint the header tint once on the panel; avoid stacking another tint on the bar.

The hooks most likely to change are listed in §5 of the guide.

## Rules for changes

- **Keep each theme's CSS under 50,000 characters.** Both generators print the size, and the scenes' build fails over it. Over the limit, Add theme refuses the file.
- **Mind the file size.** Add theme accepts up to 256 KB. `t3 theme set <file>` accepted 51 KB files on `0.1.10-nightly.20261116`.
- **Don't animate anything under a `backdrop-filter`**, and don't blur anything that slides or resizes.
- **Keep the scene on a fixed compositor layer** (`::before`, plus Soft Bloom's `::after`) inside the isolated wrapper; preserve the sidebar blur. Compare real installed files with `tools/capture/perf.mjs` after layer changes.
- **Avoid `:has()` on large or root containers.**
- **Prefer colour roles over CSS.** A role reaches screens you never open, and works where theme CSS isn't supported.
- **After a change:** regenerate (`source/`), run the health check, regenerate the screenshots and README (`tools/make_readme.py`).
