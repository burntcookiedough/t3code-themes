"""Measures how strong each scene's reading veil must be for chat text to read over the art.

Renders every still in headless Chrome at two window sizes, takes the pixels under the chat column
(T3's 256px sidebar, then the Comfortable column centred in the rest), lays the veil (the scene's
glass tint at alpha a) over them, and finds the smallest a at which the body text colour reaches
4.5:1 on 99.5% of those pixels and 3:1 on all of them. Writes veils.json, which build.py reads.

    python tune_veils.py          # after dump-scenes (python build.py does that)
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build      # noqa: E402
import scenemin   # noqa: E402
from verify import CHROME, data_url  # noqa: E402

SIZES = [(1707, 960), (1280, 800)]
SIDEBAR, COLUMN = 256, 760   # px; the column is a little wider than Comfortable's text, for margin
FLOOR, CEIL = 0.30, 0.85

PAGE = """<!doctype html><meta charset="utf-8"><pre id="out">running</pre><script>
const jobs = %s, sizes = %s, SIDEBAR = %d, COLUMN = %d, FLOOR = %s, CEIL = %s;
const lin = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
const lum = (r, g, b) => 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
const ratio = (a, b) => (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
const load = src => new Promise((ok, bad) => { const i = new Image(); i.onload = () => ok(i); i.onerror = bad; i.src = src; });
(async () => {
  const out = {};
  for (const j of jobs) {
    const img = await load(j.src);
    let need = FLOOR;
    for (const [w, h] of sizes) {
      const c = document.createElement('canvas'); c.width = w; c.height = h;
      const g = c.getContext('2d'); g.drawImage(img, 0, 0, w, h);
      const x0 = Math.round(SIDEBAR + (w - SIDEBAR - COLUMN) / 2), y0 = 60, y1 = h - 140;
      const px = g.getImageData(x0, y0, COLUMN, y1 - y0).data;
      const counts = new Map();
      for (let i = 0; i < px.length; i += 4) { const k = (px[i] << 16) | (px[i+1] << 8) | px[i+2]; counts.set(k, (counts.get(k) || 0) + 1); }
      const total = px.length / 4, T = lum(...j.text);
      for (let a = FLOOR; a <= CEIL + 1e-9; a += 0.01) {
        let fail45 = 0, fail3 = 0;
        for (const [k, n] of counts) {
          const r = ((k >> 16) & 255) * (1 - a) + j.tint[0] * a, gg = ((k >> 8) & 255) * (1 - a) + j.tint[1] * a,
                b = (k & 255) * (1 - a) + j.tint[2] * a;
          const cr = ratio(T, lum(r, gg, b));
          if (cr < 4.5) fail45 += n;
          if (cr < 3) fail3 += n;
        }
        if (fail45 / total <= 0.005 && fail3 === 0) { need = Math.max(need, a); break; }
        if (a + 0.01 > CEIL + 1e-9) need = Math.max(need, CEIL + 0.01);
      }
    }
    out[j.id] = Math.round(need * 100) / 100;
  }
  document.getElementById('out').textContent = JSON.stringify(out);
})();
</script>"""


def main():
    scenes = json.load(open(os.path.join(HERE, "build", "scenes.json"), encoding="utf-8"))
    jobs = []
    for s in scenes:
        p = build.palette(s)
        mini = scenemin.minify(scenemin.reference_still(s["svg"]))
        jobs.append({"id": s["id"], "src": data_url(mini), "text": list(build.rgb(p["text"])),
                     "tint": list(build.rgb(p["tint"]))})
    page = os.path.join(HERE, "build", "veils.html")
    with open(page, "w", encoding="utf-8") as fh:
        fh.write(PAGE % (json.dumps(jobs), json.dumps(SIZES), SIDEBAR, COLUMN, FLOOR, CEIL))
    dom = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=120000",
                          "--force-device-scale-factor=1", "--dump-dom", "file:///" + page.replace("\\", "/")],
                         capture_output=True, text=True, encoding="utf-8", timeout=600).stdout
    veils = json.loads(dom.split('<pre id="out">', 1)[1].split("</pre>", 1)[0])
    too_much = {k: v for k, v in veils.items() if v > CEIL}
    with open(os.path.join(HERE, "veils.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(dict(sorted(veils.items())), fh, indent=2)
        fh.write("\n")
    for k, v in sorted(veils.items(), key=lambda kv: -kv[1]):
        print(f"{k:20} veil {v:.2f}")
    if too_much:
        print("Needs more than the ceiling:", too_much)
        sys.exit(1)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
