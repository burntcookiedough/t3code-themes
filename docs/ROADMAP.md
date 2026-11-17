# Roadmap: from personal theme to community release

The goal: when theme CSS ships in **stable** T3 Code, anyone can install Soft Bloom in one step and it just works on their machine, window size and settings.

## What we learned (research, Nov 2026)

From T3 Code's public source (`pingdotgg/t3code`) and the installed `0.1.10-nightly`:

- **How people will install it.** Settings → Appearance → **Add theme** accepts a dropped or pasted `.json` (T3 or VS Code format) and **keeps our CSS** (`ThemeImportDialog.tsx`). `t3 theme set <file>` works too. Both share the same file, so one asset serves everyone.
- **Size limits differ by install path:**
  - `t3 theme set <file>` was thought to reject files over **32 KB**. On `0.1.10-nightly.20261116` it accepted 51 KB files (checked 2026-11-17 with the theme-examples ports). Ours is about 23 KB.
  - Add theme accepts up to 256 KB.
  - CSS over T3's CSS limit (50,000 characters) is **silently dropped** on import, leaving only the colours, with no error shown.
- **Export exists** ("Export theme file"), so users can re-share. There's also a theme *collection* concept (`collection: { id, label }`) used to group variants.
- **No public gallery or community format yet.** Web search turns up nothing T3-specific, so we'd be early.
- **Open upstream issues** that affect custom themes. We should test against them and mention them in the README:
  - [#31756](https://github.com/pingdotgg/t3code/issues/31756) file explorer ignores theme colours
  - [#35288](https://github.com/pingdotgg/t3code/issues/35288) message minimap shows a track line when the border colour is opaque (ours is translucent, so it's probably fine; verify)
  - [#10997](https://github.com/pingdotgg/t3code/issues/10997) / [#27464](https://github.com/pingdotgg/t3code/issues/27464) native right-click menus ignore themes (desktop and Linux)
  - [#26872](https://github.com/pingdotgg/t3code/issues/26872), [#35342](https://github.com/pingdotgg/t3code/issues/35342) `html_render` charts with custom accents or muted colours
  - [#33044](https://github.com/pingdotgg/t3code/issues/33044) PDF attachment chips look like errors
  - [#36710](https://github.com/pingdotgg/t3code/issues/36710) agents can't switch back to the stock theme (tell users: Settings → Appearance, or `t3 theme set t3-chat`)

## P0: stability (before any release)

1. **Theme doctor script** (`tools/doctor.js`): paste it into DevTools, or run it through a preview. It checks every hook the theme depends on (see ARCHITECTURE.md) plus key computed styles:
   - the scene is present
   - page layers are transparent
   - switch knobs aren't transparent
   - popups have the glass applied
   - `.no-transitions` isn't stuck

   It prints a pass/fail list. Users can attach the output to bug reports.
2. **CI on every push** (GitHub Actions):
   - the JSON matches T3's required fields
   - CSS is under 50,000 characters
   - the JSON file is under 256 KB (Add theme's limit)
   - regenerating from `src/generate.py` reproduces the committed file
   - colour-role contrast stays at or above 4.5:1
3. **Fallbacks for unstable hooks:**
   - put the base gradient on `html`/`body` too, so a renamed wrapper degrades to "dark" rather than "flat T3 default";
   - keep every rule scoped, so a missing hook does nothing rather than breaking layout.
4. **Test matrix:**
   - Chat width: Compact / Comfortable / Wide
   - Sidebar: expanded / collapsed / floating / Labs "boring"
   - Glass opacity 0 / 50 / 100, Contrast 100 / max
   - Window sizes: 1024, 1280, 1707, 2560 wide
   - Web vs desktop app, and Windows / macOS / Linux if possible

## P1: release quality

5. **Install docs for non-technical users:** Add theme (drag the file in) as the main path, `t3 theme set` as the alternative. Add before/after screenshots taken in a **demo workspace** (no personal threads or emails).
6. **Variants**, generated from the same script and shipped as a collection:
   - **Soft Bloom**, the full look.
   - **Soft Bloom Lite:** no blur, no art. For low-end GPUs and remote desktops.
   - Possibly accent options (cream / rose / sage).
7. **Accessibility:**
   - `prefers-reduced-transparency` makes surfaces solid (where the browser supports it);
   - `prefers-contrast: more` gives stronger borders;
   - a focus-ring audit;
   - a keep-every-text-colour-at-4.5:1 check in CI.
8. **Packaging:**
   - an MIT LICENSE;
   - GitHub Releases with the JSON as a downloadable asset;
   - semantic versions with "tested on T3 Code x.y.z" in every release note;
   - an issue template asking for T3 version, OS, screenshot and doctor output.

## P2: upstream and community

9. **Ask T3 to make the hooks we rely on stable** (`sidebar-wrapper`, `workspace-area="panel"|"pull-requests"`, `composer-shell` and its glass variables) and to add a stable hook for the scene layer. Report anything the doctor finds broken.
10. **Share it** once stable ships: a T3 Discord/GitHub discussion, and a README GIF of Settings, the chat and the right panel.
11. **Performance budget:** record a DevTools trace for opening the right panel, scrolling a long thread and opening Settings, and keep frames under 16 ms. Publish the numbers.
