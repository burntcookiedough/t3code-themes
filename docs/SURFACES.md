# Surface audit (v9, re-checked for v11)

Every surface checked, how it was checked, and what's known. "Live" means it was verified in a running T3 Code `0.1.10-nightly.20261116` web client at 1707×960, or in the desktop app where it says so.

v11 moved the tokens into colour roles without a visual change. Before it was merged, the chat, sidebar, Settings → General, Usage, the model picker and the selected-row fade were re-checked live and matched v10.

| Surface | How it's themed | Verified | Notes |
|---|---|---|---|
| Window background (scene) | `sidebar-wrapper` + `::before` / `::after` | Live | Static. The star sits in the bottom-right gutter. |
| Sidebar | frosted glass, 50% / blur 14px | Live + desktop | Selected row: the highlight fades out after the click (v9); hover still highlights; no accent edge. Fade curve checked by stepping the animation by hand (preview tabs don't play animations). |
| Chat header | glass bar, 72% / blur 8px | Live | |
| Conversation (messages) | transparent; art masked under the column | Live + desktop | Assistant text has a soft text-shadow. |
| User message bubbles | 92% solid, cream hairline, hover edge | Live | No blur (performance). |
| Links in messages | cream with a soft underline | Live | |
| Code blocks | `--code-background` 72% + hairline | Live | |
| Chat bar (composer) | T3's own glass, tuned to 50% / 16px, cream focus edge and glow | Live + desktop | The glow hugs only the input box (fixed in v5). |
| Row under the composer ("Full access") | transparent | Live | |
| Send button | cream glow when ready, pop on enable, press on click | Live (styles) | The pop couldn't be triggered from a read-only session. |
| Pasted image tiles | solid deep tile, cream hairline | Live | |
| New-thread page | T3's cover layer cleared | Live | |
| Pull requests page | transparent + shade over the star, glass header | Live | |
| Usage dialog | modal glass + token layer | Live | Provider bar colours are T3's brand colours and are kept. |
| Settings → General | deep ink modal, darker nav, hairline group cards | Live (v8) | Switch knobs fixed in v7. |
| Settings → Appearance | same | Live | |
| Settings → Providers | same | Live | |
| Other Settings pages | same building blocks (`settings-group`, switch, select-trigger, input) | Not individually opened | Expected to match. Send a screenshot if one doesn't. |
| Popovers (model picker) | deep ink glass, follows Glass opacity + 14% | Live | |
| Menus, select, combobox, autocomplete, preview card | shared popup glass | Computed-style probe | Same rule as popovers. |
| Command palette | shared popup glass | Not opened | The shortcut couldn't be triggered in the preview. |
| Toasts | shared popup glass | Not seen | No toast fired during testing. |
| Tooltips | 96% solid, small shadow | Rule only | |
| Modal dim layers | near-black 62% + 4px blur | Live (v8) | The popover click-catcher stays invisible. |
| Right panel (browser / terminal / files / diff) | 90% deep tint, hairline, no blur | Live | Blur removed in v7 because opening the panel lagged. |
| Terminal drawer | top hairline; terminal colours from roles | Rule only | The terminal canvas keeps an opaque background for legibility. |
| Thread details card | T3's own glass with theme tokens | Live | |
| Scrollbars | cream 16% thumb | Live | |
| Text selection | cream 28% | Rule only | |
| Desktop titlebar / toolbars | chrome / toolbar tokens 55% | Desktop capture | |
| Diff colours | T3 defaults | — | Kept on purpose for legibility. |
| Light mode | — | — | Not supported; the theme is dark-only. |
| Mobile | — | — | T3 doesn't apply themes on mobile. |

## Known issues and limits

- **Chat width "Wide"** wasn't visually tested. The art masks are percentages tuned for "Comfortable".
- **Command palette and toasts** are covered by the shared popup rule but weren't seen live.
- The **"Long 0:09" dictation pill** seen in an early screenshot comes from a separate app (murmur-long-dictation) drawn over T3. A T3 theme can't restyle it.
- The desktop app was checked through screenshots taken by a helper agent. Most of the verification ran in T3's web client, which uses the same renderer and the same theme.
