// Trace real installed themes while the panel/sidebar toggle. Never injects CSS.
// node tools/capture/perf.mjs <config.json> — see THEME-GUIDE §10.
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs'
import { join } from 'node:path'
import { launch, sleep } from './cdp.mjs'

const cfg = JSON.parse(readFileSync(process.argv[2], 'utf8'))
const repeats = cfg.repeats ?? 3, cycles = cfg.cycles ?? 1, settle = cfg.settleMs ?? 900
const animationMs = cfg.animationMs ?? 200
if (![repeats, cycles, settle].every(n => Number.isInteger(n) && n > 0)) throw new Error('Invalid trace timing')
if (!Number.isInteger(animationMs) || animationMs <= 0 || animationMs > 400 || settle <= animationMs) throw new Error('Invalid animation duration')
mkdirSync(cfg.outDir, { recursive: true })
const page = await launch({ profileDir: cfg.profileDir, port: cfg.port ?? 9337, width: 1707, height: 960 })
const report = { repeats, cycles, settleMs: settle, animationMs, viewport: [1707, 960], results: [] }
let events = [], complete
page.on('Tracing.dataCollected', p => events.push(...p.value))
page.on('Tracing.tracingComplete', () => complete?.())
const toggle = label => page.js(`(()=>{const b=document.querySelector('button[aria-label="${label}"]');if(!b)return false;b.click();return true})()`)
async function trace(label) {
  events = []
  await page.send('Tracing.start', { traceConfig: { includedCategories: ['devtools.timeline', 'disabled-by-default-devtools.timeline', 'cc', 'viz', 'blink', 'gpu'] } })
  try {
    for (let i = 0; i < cycles * 2; i++) {
      if (!await toggle(label)) throw new Error(`Missing toggle: ${label}`)
      await sleep(settle)
    }
  } finally {
    const finished = new Promise(resolve => { complete = resolve })
    await page.send('Tracing.end')
    await finished
  }
  const sums = {}
  for (const e of events) if (e.ph === 'X' && e.dur) sums[e.name] = (sums[e.name] || 0) + e.dur / 1000
  const sum = (...names) => +names.reduce((n, name) => n + (sums[name] || 0), 0).toFixed(2)
  return { raster: sum('RasterTask'), paint: sum('Paint', 'PaintImage'), layout: sum('Layout', 'UpdateLayoutTree'),
    layers: sum('UpdateLayer', 'Layerize'),
    // Like the reference experiment: inclusive event durations overlap; this is not wall time or CPU time.
    tracedWork: +Object.values(sums).reduce((a, b) => a + b, 0).toFixed(2) }
}
const median = samples => Object.fromEntries(Object.keys(samples[0]).map(key =>
  [key, samples.map(s => s[key]).sort((a, b) => a - b)[Math.floor(samples.length / 2)]]))
try {
  await page.go(`${cfg.origin}/pair#token=${cfg.token}`, 4000)
  // Change only this throwaway browser's client preference; fresh profiles default to instant panes.
  await page.js(`(()=>{const k='t3code:client-settings:v1';const s=JSON.parse(localStorage.getItem(k)||'{}');s.panelAnimationDurationMs=${animationMs};localStorage.setItem(k,JSON.stringify(s));return true})()`)
  // Alternate baseline/current per theme to reduce drift. Each file is imported through Add theme.
  const runs = cfg.runs.map(run => ({ ...run, themes: run.themeFiles.map(file => ({ file, ...JSON.parse(readFileSync(file, 'utf8')) })) }))
  for (const id of runs[0].themes.map(t => t.id)) for (const run of runs) {
    const theme = run.themes.find(t => t.id === id)
    if (!theme) throw new Error(`${run.label}: missing ${id}`)
    await page.go(`${cfg.origin}/settings/appearance`, 2000)
    await page.js(`localStorage.removeItem('t3code:themes:v1');true`)
    await page.go(`${cfg.origin}/settings/appearance`, 2000)
    if (!await page.js(`(()=>{const b=[...document.querySelectorAll('button')].find(b=>b.textContent.trim()==='Add theme');if(!b)return false;b.click();return true})()`)) throw new Error('No Add theme button')
    await sleep(1200)
    await page.upload('[role="dialog"] input[type=file]', [theme.file])
    let confirmed = false
    for (let n = 0; n < 40 && !confirmed; n++) {
      await sleep(250)
      confirmed = await page.js(`(()=>{const b=[...document.querySelectorAll('[role="dialog"] button')].filter(b=>b.textContent.trim()==='Add theme').at(-1);if(!b||b.disabled)return false;b.click();return true})()`)
    }
    if (!confirmed) throw new Error(`No import confirmation: ${id}`)
    await sleep(2500)
    const imported = await page.js(`JSON.parse(localStorage.getItem('t3code:themes:v1')||'[]').find(t=>t.id===${JSON.stringify(id)})`)
    if (!imported) throw new Error(`Import failed: ${id}`)
    if (imported.css !== theme.css) throw new Error(`Imported CSS differs: ${id}`)
    await page.js(`localStorage.setItem('t3code:theme-halves:v1',${JSON.stringify(JSON.stringify({ [theme.appearance]: id }))});localStorage.setItem('t3code:theme-appearance-mode',${JSON.stringify(theme.appearance)});true`)
    await page.go(cfg.origin + cfg.thread, 3500)
    const state = await page.js(`(()=>{const w=document.querySelector('[data-slot="sidebar-wrapper"]');return {
      theme:document.documentElement.getAttribute('data-theme-id'),animated:document.querySelector('[data-panel-animations="true"]')!==null,
      duration:w&&getComputedStyle(w).getPropertyValue('--panel-animation-duration').trim(),
      reducedMotion:matchMedia('(prefers-reduced-motion: reduce)').matches,noTransitions:!!document.querySelector('.no-transitions'),
      sceneLayer:w&&getComputedStyle(w,'::before').willChange}})()`)
    if (state.theme !== id || !state.animated || state.reducedMotion || state.noTransitions) throw new Error(`Invalid trace state: ${JSON.stringify(state)}`)
    if (await page.js(`!!document.querySelector('[data-workspace-area="panel"]')`)) { await toggle('Toggle right panel'); await sleep(settle) }
    if (await page.js(`!!document.querySelector('[data-thread-terminal-drawer]')`)) { await toggle('Toggle terminal drawer'); await sleep(settle) }
    if (await page.js(`!!document.querySelector('[data-slot="sidebar-wrapper"][data-sidebar-state="collapsed"]')`)) { await toggle('Toggle main sidebar'); await sleep(settle) }
    // Warm both interactions before measuring; all samples start with the panel closed.
    for (const label of ['Toggle right panel', 'Toggle main sidebar']) for (let n = 0; n < 2; n++) { if (!await toggle(label)) throw new Error(`Missing ${label}`); await sleep(settle) }
    const panel = [], sidebar = []
    for (let n = 0; n < repeats; n++) {
      panel.push(await trace('Toggle right panel'))
      sidebar.push(await trace('Toggle main sidebar'))
    }
    const result = { theme: id, run: run.label, state, panel: { median: median(panel), samples: panel }, sidebar: { median: median(sidebar), samples: sidebar } }
    report.results.push(result)
    writeFileSync(join(cfg.outDir, 'perf.json'), JSON.stringify(report, null, 2))
    console.log(JSON.stringify({ theme: id, run: run.label, panel: result.panel.median, sidebar: result.sidebar.median }))
  }
} finally { page.close() }
