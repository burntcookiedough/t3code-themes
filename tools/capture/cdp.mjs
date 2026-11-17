// A tiny Chrome DevTools Protocol driver: launch headless Chrome, run JavaScript, click, press keys,
// take screenshots. No dependencies; needs Node 22+ (global WebSocket and fetch).
import { spawn } from 'node:child_process'
import { existsSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'

const CHROMES = [
  process.env.CHROME,
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
].filter(Boolean)

export const sleep = ms => new Promise(r => setTimeout(r, ms))

export async function launch({ profileDir, width = 1707, height = 960, port = 9333 }) {
  const chrome = CHROMES.find(p => existsSync(p))
  if (!chrome) throw new Error('No Chrome or Edge found; set CHROME to its path')
  const proc = spawn(chrome, ['--headless=new', `--remote-debugging-port=${port}`, `--user-data-dir=${resolve(profileDir)}`  /* Chrome needs an absolute profile path */,
    `--window-size=${width},${height}`, '--hide-scrollbars', '--force-device-scale-factor=1', 'about:blank'], { stdio: 'ignore' })
  let ws
  for (let i = 0; i < 300 && !ws; i++) {  // a brand-new profile can take a while on first launch
    try {
      const page = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(t => t.type === 'page')
      if (page) ws = new WebSocket(page.webSocketDebuggerUrl)
    } catch {}
    if (!ws) await sleep(150)
  }
  if (!ws) { proc.kill(); throw new Error(`Chrome did not start (port ${port}, profile ${profileDir})`) }
  await new Promise(r => ws.addEventListener('open', r, { once: true }))
  let id = 0
  const waiting = new Map(), listeners = new Map()
  ws.addEventListener('message', e => {
    const m = JSON.parse(e.data)
    if (m.id && waiting.has(m.id)) { waiting.get(m.id)(m); waiting.delete(m.id) }
    else if (m.method) for (const fn of listeners.get(m.method) || []) fn(m.params)
  })
  const send = (method, params = {}) => new Promise(res => { const i = ++id; waiting.set(i, res); ws.send(JSON.stringify({ id: i, method, params })) })
  await send('Page.enable'); await send('Runtime.enable'); await send('DOM.enable')
  await send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: false })

  const page = {
    send,
    on(method, fn) { listeners.set(method, [...(listeners.get(method) || []), fn]) },
    async js(expression) {
      const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true })
      if (r.result?.exceptionDetails) throw new Error(r.result.exceptionDetails.exception?.description || r.result.exceptionDetails.text)
      return r.result?.result?.value
    },
    async go(url, wait = 3000) {
      const r = await send('Page.navigate', { url })
      const failed = r.error?.message || r.result?.errorText
      if (failed) throw new Error(`Could not open ${url}: ${failed}`)
      await sleep(wait)
    },
    async shot(file, format = 'png', quality = 90) {
      const r = await send('Page.captureScreenshot', format === 'png' ? { format } : { format, quality })
      writeFileSync(file, Buffer.from(r.result.data, 'base64'))
    },
    async key(key, { code, modifiers = 0, text } = {}) {
      const base = { key, code: code || key, modifiers, windowsVirtualKeyCode: key.length === 1 ? key.toUpperCase().charCodeAt(0) : undefined }
      await send('Input.dispatchKeyEvent', { type: 'keyDown', ...base, ...(text ? { text } : {}) })
      await send('Input.dispatchKeyEvent', { type: 'keyUp', ...base })
    },
    async type(text) { await send('Input.insertText', { text }) },
    async enter() {
      const k = { key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13, nativeVirtualKeyCode: 13 }
      await send('Input.dispatchKeyEvent', { type: 'keyDown', ...k, text: '\r' })
      await send('Input.dispatchKeyEvent', { type: 'keyUp', ...k })
    },
    async mouse(x, y, { click = false } = {}) {
      await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y })
      if (click) {
        await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 })
        await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 })
      }
    },
    async upload(selector, files) {
      const doc = await send('DOM.getDocument', { depth: -1 })
      const q = await send('DOM.querySelector', { nodeId: doc.result.root.nodeId, selector })
      if (!q.result?.nodeId) throw new Error(`No element for ${selector}`)
      await send('DOM.setFileInputFiles', { nodeId: q.result.nodeId, files })
    },
    close() { try { ws.close() } catch {} proc.kill() },
  }
  return page
}
