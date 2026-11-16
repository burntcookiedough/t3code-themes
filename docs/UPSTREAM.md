# Contributing upstream to T3 Code

What we found, what T3's rules allow, and what we plan to post. Checked 2026-11-17 against `pingdotgg/t3code` (`CONTRIBUTING.md`, `AGENTS.md`, issue and PR templates).

## T3's rules, in short

- **PRs must fix a bug,** one problem per PR, with evidence (before/after screenshots for UI). They must name the model that wrote them, and you can have at most 3 open. New features, UI overhauls and architecture changes are auto-closed.
- **Feature requests go to [Ideas discussions](https://github.com/pingdotgg/t3code/discussions/categories/ideas),** not issues or PRs.
- **The most valued help:** flagging duplicates, confirming fixed bugs, linking dead PRs. *"A +1 on an existing PR is ALWAYS better than another PR"*, but only after testing it and reporting what you saw.
- **Models:** PRs written by Gemini or Muse Wonder are closed. Claude Opus 5.5 is fine.

## Theme bugs we checked

| Issue | Status | Our action |
|---|---|---|
| [#31756](https://github.com/pingdotgg/t3code/issues/31756) file explorer ignores theme colours | Fixed by merged [#31785](https://github.com/pingdotgg/t3code/pull/31785) | None |
| [#36710](https://github.com/pingdotgg/t3code/issues/36710) agents can't switch back to the stock theme | Maintainer fix open: [#36724](https://github.com/pingdotgg/t3code/pull/36724) | None |
| [#35288](https://github.com/pingdotgg/t3code/issues/35288) minimap track line with opaque borders | Contributor fix open: [#35577](https://github.com/pingdotgg/t3code/pull/35577) | None. Soft Bloom's border is translucent, so we don't reproduce it |

None of the bugs we found are unaddressed, so **no PR from us** (the rules would close it).

## Related Ideas that already exist (upvote rather than duplicate)

- [#33317](https://github.com/pingdotgg/t3code/discussions/33317) Theme files: optional canvas backdrop (glow + dot/grid pattern)
- [#32665](https://github.com/pingdotgg/t3code/discussions/32665) Theme files: add a colour role for the composer outline
- [#37449](https://github.com/pingdotgg/t3code/discussions/37449) Theme hooks for sidebar rows

## Draft Ideas post (not yet posted)

**Title:** Theme CSS: add the page layers to the stable hook list

> Theme CSS (#35247) documents 29 stable selectors in `THEME_CSS_HOOKS`, and the guide warns that other class names change between releases. Themes that paint the whole window, such as a backdrop behind the sidebar and chat or a distinct right panel, have to use selectors outside that list today:
>
> - `[data-workspace-area="panel"]`: the right panel. This is the rule suggested when #32131 was closed.
> - `[data-workspace-area="pull-requests"]` and `[data-workspace-area="settings"]`: the other page areas.
> - `[data-slot="sidebar-wrapper"]` and `[data-slot="sidebar-inset"]`: the app shell that holds the sidebar and the page.
>
> They already exist in the source. They just aren't covered by `themeCssHooks.test.ts`, so a rename would silently break themes that use them.
>
> **Proposal:** add these existing selectors to `THEME_CSS_HOOKS`, and so to the guide. There's no new UI or behaviour; the existing test then protects them like the other hooks.
>
> For context, I maintain a full-window theme (a dithered backdrop behind the sidebar and chat, with glass panels). Of its selectors, the ones outside the stable list are exactly these page layers, plus the composer's glass wrapper `composer-shell` (related: #32665).
>
> *Drafted with Claude Opus 5.5 in T3 Code.*
