// Runs Anthropic's theme-examples scene code, unchanged, and prints every theme with its SVG as JSON.
// Node 22.6+:  node --experimental-strip-types dump-scenes.mts > build/scenes.json
import { mkdirSync, readFileSync, readdirSync, copyFileSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const vendor = join(here, 'vendor', 'theme-examples', 'hooks')
const work = join(here, 'build', 'hooks')
mkdirSync(join(work, 'scenes'), { recursive: true })
for (const f of readdirSync(join(vendor, 'scenes'))) copyFileSync(join(vendor, 'scenes', f), join(work, 'scenes', f))
// Node's ESM loader needs file extensions; the plugin's imports leave them off.
const themes = readFileSync(join(vendor, 'themes.ts'), 'utf8').replace(/from '(\.\/scenes\/[\w-]+)'/g, "from '$1.ts'")
writeFileSync(join(work, 'themes.ts'), themes)

const { THEMES } = await import(pathToFileURL(join(work, 'themes.ts')).href)
const out = THEMES.map((t: any) => ({ id: t.id, title: t.title, blurb: t.blurb, window: t.window, twin: t.twin ?? null, glass: t.glass, svg: t.scene() }))
process.stdout.write(JSON.stringify(out))
