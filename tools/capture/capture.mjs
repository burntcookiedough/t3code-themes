// Screenshots every surface of T3 Code under every theme, checks each surface really opened, and
// reports colours that don't belong to the theme.
//
//   node tools/capture/capture.mjs <config.json>
//
// Config: {
//   origin: "http://127.0.0.1:3799",      a T3 server (use a sandbox: t3 serve --base-dir <dir> --port 3799)
//   token: "ABCD1234",                    one-time pairing token from: t3 pair --base-dir <dir>
//   thread: "/<environmentId>/<threadId>", a thread with some content
//   themeFiles: ["themes/a.json", ...],   installed through Settings > Appearance > Add theme
//   themes: ["a", ...],                   ids to capture (default: every file)
//   surfaces: ["chat", ...],              default: every surface in SURFACES below
//   outDir: "screens", profileDir: ".capture-profile", width: 1707, height: 960, port: 9335,
//   format: "png" | "webp" | "jpeg", quality: 90,
//   redact: { "my-hostname": "local" }    text replaced on the page just before each screenshot
// }
//
// Writes <outDir>/<theme>/<surface>.<format> and <outDir>/report.json. For each surface the report lists:
// - colours: visible backgrounds and text far (OKLab distance > 0.08) from every colour the theme defines
//   (its roles and its stylesheet). T3's own mixes of theme colours show up at small distances.
// - edges: borders, outlines, ring shadows (and those of ::before/::after) in the theme's accent, or far
//   from the theme's colours. A border that matches its own fill (a solid button) is not an edge.
// Exits with status 1 if a theme didn't install, a surface didn't open, or a theme wasn't applied.
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs'
import { join } from 'node:path'
import { launch, sleep } from './cdp.mjs'

const cfg = JSON.parse(readFileSync(process.argv[2], 'utf8'))
const W = cfg.width || 1707, H = cfg.height || 960

const click = (selector, label) => `(()=>{const re=${label};const e=[...document.querySelectorAll(${JSON.stringify(selector)})]
  .find(x=>re.test((x.getAttribute('aria-label')||'').trim())||re.test(x.textContent.trim()));if(!e)return false;e.click();return true})()`
const button = label => click('button', `/^${label}/`)
// The right panel reopens on the surface it showed last; "Add panel surface" lists them all again.
const panelSurface = name => `(async()=>{const find=()=>[...document.querySelectorAll('[data-workspace-area="panel"] button, [role="menuitem"]')]
  .find(b=>b.textContent.trim().startsWith(${JSON.stringify(name)}));let b=find();
  if(!b){[...document.querySelectorAll('button')].find(x=>x.getAttribute('aria-label')==='Add panel surface')?.click();
    await new Promise(r=>setTimeout(r,600));b=find()}if(!b)return false;b.click();return true})()`
const seen = selector => `!!document.querySelector(${JSON.stringify(selector)})`
// T3 remembers an open terminal drawer or right panel per thread: close both, so each surface starts clean.
const RESET = `(async()=>{const b=l=>[...document.querySelectorAll('button')].find(x=>x.getAttribute('aria-label')===l);
  if(document.querySelector('[data-thread-terminal-drawer]'))b('Toggle terminal drawer')?.click();
  if(document.querySelector('[data-workspace-area="panel"]'))b('Toggle right panel')?.click();
  await new Promise(r=>setTimeout(r,700));return true})()`

// Each surface: where to go, the steps that open it, and `expect`, a check that it really opened.
const SURFACES = {
  'chat': { path: 'thread', expect: seen('[data-user-message-bubble]') },
  'new-thread': { path: '/', expect: `${seen('[data-chat-composer-form]')}&&!document.querySelector('[data-message-role]')` },
  // A banner attached above the chat box. /clear arms one; usage-limit stops and other notices use the same surface.
  'composer-banner': { path: 'thread', expect: seen('[data-composer-banner-surface="attached"]'), steps: [
    { js: `(()=>{const e=document.querySelector('[data-slot="composer-host"] [contenteditable="true"]');e.focus();return true})()` },
    { type: '/clear' }, { wait: 600 }, { enter: true }, { wait: 1200 }] },
  'model-picker': { path: 'thread', expect: seen('[data-slot="popover-popup"]'),
    steps: [{ js: `(()=>{document.querySelector('[data-chat-provider-model-picker]').click();return true})()` }] },
  'thread-menu': { path: 'thread', expect: seen('[role="menuitem"]'), steps: [{ js: button('Thread actions') }] },
  'command-palette': { path: 'thread', expect: seen('[data-slot="command-dialog-popup"]'), steps: [{ key: 'k', modifiers: 2 }] },
  'tooltip': { path: 'thread', expect: seen('[data-slot="tooltip-popup"]'),
    steps: [{ hover: 'button[aria-label="Toggle right panel"]' }, { wait: 1400 }] },
  'files-panel': { path: 'thread', expect: seen('[data-workspace-area="panel"]'),
    steps: [{ js: button('Toggle right panel') }, { wait: 900 }, { js: panelSurface('Files') }, { wait: 1500 }] },
  'diff-panel': { path: 'thread', expect: seen('[data-workspace-area="panel"]'),
    steps: [{ js: button('Toggle right panel') }, { wait: 900 }, { js: panelSurface('Diff') }, { wait: 2000 }] },
  'terminal': { path: 'thread', expect: seen('[data-thread-terminal-drawer]'), steps: [{ js: button('Toggle terminal drawer') }, { wait: 1800 }] },
  'delete-dialog': { path: 'thread', expect: seen('[data-slot="alert-dialog-popup"]'),
    steps: [{ js: button('Thread actions') }, { wait: 700 }, { js: click('[role="menuitem"]', '/^Delete/') }, { wait: 900 }] },
  'settings': { path: '/settings/general', expect: seen('[data-slot="settings-group"]') },
  // These two show other themes' swatches and provider brand colours on purpose: no colour probe.
  'appearance': { path: '/settings/appearance', probe: false, expect: `document.body.innerText.includes('Color scheme')` },
  'usage': { path: '/usage', probe: false, expect: seen('[data-slot="dialog-popup"]') },
  'pull-requests': { path: '/pull-requests', expect: seen('[data-workspace-area="pull-requests"]') },
}

const PROBE = `(()=>{
  // Colours become [OKLab L, a, b, alpha]. A canvas normalises any CSS colour without touching the page's
  // styles; it keeps modern formats as they are, so oklab, oklch and color(srgb) are parsed here.
  const ctx = new OffscreenCanvas(1, 1).getContext('2d'), memo = new Map();
  const fromSrgb = (r, g, b) => { const f = v => { v /= 255; return v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4 };
    const R = f(r), G = f(g), B = f(b); const l = Math.cbrt(.4122214708*R+.5363325363*G+.0514459929*B), m = Math.cbrt(.2119034982*R+.6806995451*G+.1073969566*B), s = Math.cbrt(.0883024619*R+.2817188376*G+.6299787005*B);
    return [ .2104542553*l+.7936177850*m-.0040720468*s, 1.9779984951*l-2.4285922050*m+.4505937099*s, .0259040371*l+.7827717662*m-.8086757660*s ] };
  const num = t => t.endsWith('%') ? parseFloat(t) / 100 : parseFloat(t);
  const col = v => { if (memo.has(v)) return memo.get(v); let out = null;
    ctx.fillStyle = '#010203'; ctx.fillStyle = v; const f = ctx.fillStyle;
    if (f !== '#010203' || v.replace(/\\s/g, '') === '#010203') {
      const p = (f.match(/\\(([^)]*)\\)/) || [, ''])[1].replace(/,/g, ' ').replace('/', ' ').trim().split(/\\s+/);
      if (f[0] === '#') out = [...fromSrgb(...[1, 3, 5].map(i => parseInt(f.slice(i, i + 2), 16))), 1];
      else if (f.startsWith('rgb')) out = [...fromSrgb(+p[0], +p[1], +p[2]), p[3] ? num(p[3]) : 1];
      else if (f.startsWith('oklab')) out = [num(p[0]), +p[1], +p[2], p[3] ? num(p[3]) : 1];
      else if (f.startsWith('oklch')) { const h = +p[2] * Math.PI / 180; out = [num(p[0]), +p[1] * Math.cos(h), +p[1] * Math.sin(h), p[3] ? num(p[3]) : 1] }
      else if (f.startsWith('color(')) out = [...fromSrgb(num(p[1]) * 255, num(p[2]) * 255, num(p[3]) * 255), p[4] ? num(p[4]) : 1] }
    if (out && out.some(Number.isNaN)) out = null;
    memo.set(v, out); return out };
  const dist = (a, b) => Math.hypot(a[0]-b[0], a[1]-b[1], a[2]-b[2]);
  const root = getComputedStyle(document.documentElement), role = n => col(root.getPropertyValue('--app-theme-' + n).trim());

  // The theme's colours: its roles (T3 exposes them as --app-theme-*) and the literals in its stylesheet.
  // T3's own tokens are left out, or its fixed colours would never be flagged.
  const palette = [col('#000'), col('#fff')];
  for (const sh of document.styleSheets) { let rules; try { rules = sh.cssRules } catch { continue }
    for (const r of rules) if (r.style) for (const n of r.style) if (n.startsWith('--app-theme-')) { const c = col(root.getPropertyValue(n).trim()); if (c && c[3] > 0) palette.push(c) } }
  for (const sh of document.adoptedStyleSheets || []) for (const lit of [...sh.cssRules].map(r => r.cssText).join(' ').match(/#[0-9a-f]{3,8}\\b|rgba?\\([^)]*\\)/gi) || []) { const c = col(lit); if (c) palette.push(c) }
  const accents = [role('accent'), role('message-action')].filter(Boolean), text = role('text');
  const far = c => Math.min(...palette.map(p => dist(p, c)));

  const colours = new Map(), edges = new Map();
  const note = (map, what, value, el, d) => { const k = what + ' ' + value; const cur = map.get(k) || { what, value, distance: +d.toFixed(3), count: 0,
    sample: (el.getAttribute('data-slot') || el.tagName.toLowerCase()) + ' ' + (el.textContent || '').trim().slice(0, 40) }; cur.count++; map.set(k, cur) };
  const SHADOW_COLOURS = /(?:rgba?|oklab|oklch|color)\\([^)]*\\)|#[0-9a-f]{3,8}\\b/gi;
  const edgesOf = cs => { const out = [];
    for (const side of ['Top', 'Right', 'Bottom', 'Left']) if (parseFloat(cs['border' + side + 'Width']) > 0 && cs['border' + side + 'Style'] !== 'none') out.push(['border', cs['border' + side + 'Color']]);
    if (cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0) out.push(['outline', cs.outlineColor]);
    for (const m of (cs.boxShadow || '').match(SHADOW_COLOURS) || []) out.push(['shadow', m]);
    return out };

  for (const el of document.querySelectorAll('body *')) {
    // Brand marks, media and code (its syntax colours come from T3's code theme) are not the theme's.
    if (el.closest('svg,img,canvas,video,pre,code,.chat-markdown-codeblock,[data-pierre-icon],[data-provider-icon]')) continue;
    const b = el.getBoundingClientRect(); if (b.width < 2 || b.height < 2 || b.bottom < 0 || b.top > innerHeight || b.right < 0 || b.left > innerWidth) continue;
    const cs = getComputedStyle(el); if (cs.visibility === 'hidden' || +cs.opacity === 0) continue;
    const fill = col(cs.backgroundColor);
    const colour = (what, value) => { const c = col(value); if (!c || c[3] < .06) return; const d = far(c); if (d > .08) note(colours, what, value, el, d) };
    colour('background', cs.backgroundColor);
    if ([...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) colour('text', cs.color);
    const all = edgesOf(cs);
    for (const pseudo of ['::before', '::after']) { const ps = getComputedStyle(el, pseudo); if (ps.content !== 'none') for (const [w, v] of edgesOf(ps)) all.push([w + pseudo, v]) }
    for (const [what, value] of all) { const c = col(value); if (!c || c[3] < .06) continue;
      if (fill && fill[3] > .5 && dist(fill, c) < .03) continue;  // a solid button's border is its fill
      const accent = accents.some(a => dist(a, c) < .05) && (!text || dist(text, c) > .1);
      const d = far(c);
      if (accent) note(edges, 'accent ' + what, value, el, d); else if (d > .08) note(edges, what, value, el, d) }
  }
  const top = m => [...m.values()].sort((a, b) => b.distance * b.count - a.distance * a.count).slice(0, 12);
  return { colours: top(colours), edges: top(edges), themeId: document.documentElement.getAttribute('data-theme-id') };
})()`

// Replace private text (a machine name, say) on the page just before a screenshot. Screenshots only.
const REDACT = map => `(()=>{const m=${JSON.stringify(map)};const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
  let n;while((n=w.nextNode()))for(const[k,v]of Object.entries(m))if(n.nodeValue.includes(k))n.nodeValue=n.nodeValue.split(k).join(v);return true})()`

const themes = cfg.themeFiles.map(f => JSON.parse(readFileSync(f, 'utf8')))
const appearance = Object.fromEntries(themes.map(t => [t.id, t.appearance]))
const ids = cfg.themes || themes.map(t => t.id)
const surfaces = cfg.surfaces || Object.keys(SURFACES)
const out = cfg.outDir || 'screens'
mkdirSync(out, { recursive: true })

const report = { failures: [], themes: {} }
const fail = message => { report.failures.push(message); console.log(`FAIL ${message}`) }
const page = await launch({ profileDir: cfg.profileDir || '.capture-profile', width: W, height: H, port: cfg.port || 9335 })
try {
  await page.go(`${cfg.origin}/pair#token=${cfg.token}`, 4000)
  await page.go(`${cfg.origin}/settings/appearance`, 3000)
  await page.js(`localStorage.removeItem('t3code:themes:v1'); true`)
  await page.go(`${cfg.origin}/settings/appearance`, 3000)
  if (!await page.js(button('Add theme'))) throw new Error('No Add theme button: is the token valid?')
  await sleep(1200)
  await page.upload('[role="dialog"] input[type=file]', cfg.themeFiles)
  await sleep(2500)
  const installed = await page.js(`JSON.parse(localStorage.getItem('t3code:themes:v1')||'[]').map(t=>t.id)`)
  for (const id of ids) if (!installed.includes(id)) fail(`${id}: not installed by Add theme`)
  console.log(`installed ${installed.length} of ${themes.length} themes`)

  for (const id of ids.filter(i => installed.includes(i))) {
    mkdirSync(join(out, id), { recursive: true })
    report.themes[id] = {}
    for (const s of surfaces) {
      const spec = SURFACES[s]
      await page.js(`localStorage.setItem('t3code:theme-halves:v1', ${JSON.stringify(JSON.stringify({ [appearance[id]]: id }))}); localStorage.setItem('t3code:theme-appearance-mode', ${JSON.stringify(appearance[id])}); true`)
      await page.go(cfg.origin + (spec.path === 'thread' ? cfg.thread : spec.path), 3200)
      if (spec.path === 'thread') await page.js(RESET)
      await page.mouse(W - 5, H - 5)  // park the pointer away from hover states
      for (const step of spec.steps || []) {
        if (step.js && await page.js(step.js).catch(() => false) === false) fail(`${id}/${s}: a step found nothing to act on`)
        if (step.key) await page.key(step.key, { modifiers: step.modifiers || 0 })
        if (step.type) await page.type(step.type)
        if (step.enter) await page.enter()
        if (step.hover) {
          const at = await page.js(`(()=>{const b=document.querySelector(${JSON.stringify(step.hover)})?.getBoundingClientRect();return b?[b.x+b.width/2,b.y+b.height/2]:null})()`)
          if (at) await page.mouse(at[0], at[1]); else fail(`${id}/${s}: nothing to hover`)
        }
        await sleep(step.wait || 700)
      }
      if (!await page.js(spec.expect).catch(() => false)) fail(`${id}/${s}: the surface did not open`)
      const probe = await page.js(PROBE)
      if (probe.themeId && probe.themeId !== id) fail(`${id}/${s}: T3 shows theme "${probe.themeId}"`)
      report.themes[id][s] = spec.probe === false ? { colours: [], edges: probe.edges } : { colours: probe.colours, edges: probe.edges }
      if (cfg.redact) await page.js(REDACT(cfg.redact))
      await page.shot(join(out, id, `${s}.${cfg.format || 'png'}`), cfg.format, cfg.quality)
    }
    console.log(`${id}: ${surfaces.length} surfaces`)
  }
} finally {
  writeFileSync(join(out, 'report.json'), JSON.stringify(report, null, 1))
  page.close()
}
if (report.failures.length) { console.log(`\n${report.failures.length} failures (see report.json)`); process.exitCode = 1 }
