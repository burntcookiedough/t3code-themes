# Maintaining Soft Bloom across T3 Code updates

T3 Code is moving fast, and the theme CSS API is nightly-only as of Nov 2026. This is what to check when T3 updates, and especially when theme CSS reaches the **stable** release.

## Quick health check (about 5 minutes)

1. `t3 theme show`: `soft-bloom` should be listed and active.
2. Open these screens and compare them with the expectations in [SURFACES.md](SURFACES.md):
   - a conversation
   - the new-thread page
   - Pull requests
   - Settings → General
   - Usage
   - the model picker
   - the right panel
3. Things that would mean something broke:
   - **A flat, opaque area where the scene used to show through:** T3 renamed or added a page wrapper. Find it in DevTools (an element with a solid `background-color` between `[data-slot="sidebar-wrapper"]` and the content) and add it to the "Clear every opaque layer" list in `src/generate.py`.
   - **No scene at all:** `[data-slot="sidebar-wrapper"]` was renamed. Move the scene rules to the new root layout element (or to `body`).
   - **Invisible switch knobs or controls:** some control now paints with a token the theme made transparent. Check `--background`, `--sidebar` and `--card` inside modals.
   - **A double frame around the chat bar:** T3 changed the composer's glass structure. Re-check `composer-shell` / `composer-host`.

## When theme CSS reaches stable

- The stable `t3 theme set <file>` already accepts this JSON. Before CSS support arrives, stable ignores the `css` field and applies only the colour roles. That's still a coherent dark palette, just without the scene and glass.
- After upgrading, run the health check above. Stable may keep different selectors from the nightly this was built against (`0.1.10-nightly.20261116`).
- The hooks most likely to change are listed under "not guaranteed stable" in [ARCHITECTURE.md](ARCHITECTURE.md).

## Rules for changes

- **Keep the CSS under 50,000 characters.** The generator prints the size.
- **Don't animate anything that sits under a `backdrop-filter`,** and don't blur anything that slides or resizes. See "Performance rules" in ARCHITECTURE.md.
- **Avoid `:has()` on large or root containers.**
- **Prefer tokens over selectors.** A token change reaches screens you never open.
- **After a change:** regenerate, publish, then run the health check.
