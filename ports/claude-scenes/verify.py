"""Proves the minified stills draw what Anthropic's reduced-motion stills draw.

Renders both versions of every scene in headless Chrome at two window sizes, compares them pixel by
pixel and prints the share of pixels that differ visibly (any channel off by more than 24 of 255).

    python verify.py build/scenes.json [scene-id ...]

Exits 1 when any scene has more than LIMIT percent of its pixels visibly different.
"""
import json
import os
import subprocess
import sys
import urllib.parse

CHROME = next(p for p in (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
) if os.path.exists(p))

SIZES = [(1707, 960), (1280, 800)]
LIMIT = 0.2  # percent of pixels

PAGE = """<!doctype html><meta charset="utf-8"><body><pre id="out">running</pre><script>
const pairs = %s, sizes = %s;
const load = src => new Promise((ok, bad) => { const i = new Image(); i.onload = () => ok(i); i.onerror = () => bad(new Error('load')); i.src = src; });
const px = (img, w, h) => { const c = document.createElement('canvas'); c.width = w; c.height = h;
  const g = c.getContext('2d'); g.drawImage(img, 0, 0, w, h); return g.getImageData(0, 0, w, h).data; };
(async () => {
  const res = {};
  for (const p of pairs) {
    try {
      const [a, b] = await Promise.all([load(p.ref), load(p.min)]);
      res[p.id] = sizes.map(([w, h]) => { const A = px(a, w, h), B = px(b, w, h); let bad = 0, sum = 0;
        for (let i = 0; i < A.length; i += 4) { const d = Math.max(Math.abs(A[i]-B[i]), Math.abs(A[i+1]-B[i+1]), Math.abs(A[i+2]-B[i+2]));
          sum += d; if (d > 24) bad++; }
        return { size: w + 'x' + h, visiblyDifferent: +(100 * bad / (w * h)).toFixed(4), meanDiff: +(sum / (w * h)).toFixed(3) }; });
    } catch (e) { res[p.id] = String(e); }
  }
  document.getElementById('out').textContent = JSON.stringify(res);
})();
</script>"""


def data_url(svg):
    return "data:image/svg+xml," + urllib.parse.quote(svg, safe="")


def main(pairs_path):
    pairs = json.load(open(pairs_path, encoding="utf-8"))
    only = sys.argv[2:]
    if only:
        pairs = [p for p in pairs if p["id"] in only]
    if pairs and "svg" in pairs[0]:  # build/scenes.json from dump-scenes.mts: minify here
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import scenemin
        built = []
        for t in pairs:
            ref = scenemin.reference_still(t["svg"])
            mini = scenemin.minify(ref)
            print(f"{t['id']:20} {len(ref):6} -> {len(scenemin.to_css_url(mini)):6} as a CSS url")
            built.append({"id": t["id"], "ref": ref, "min": mini})
        pairs = built
    rows = [{"id": p["id"], "ref": data_url(p["ref"]), "min": data_url(p["min"])} for p in pairs]
    page = os.path.join(os.path.dirname(os.path.abspath(pairs_path)), "verify.html")
    with open(page, "w", encoding="utf-8") as fh:
        fh.write(PAGE % (json.dumps(rows), json.dumps(SIZES)))
    dom = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=60000",
                          "--force-device-scale-factor=1", "--dump-dom", "file:///" + page.replace("\\", "/")],
                         capture_output=True, text=True, encoding="utf-8", timeout=300).stdout
    out = dom.split('<pre id="out">', 1)[1].split("</pre>", 1)[0]
    result = json.loads(out)
    worst = 0.0
    for p in pairs:
        r = result[p["id"]]
        if isinstance(r, str):
            print(f"{p['id']:20} ERROR {r}")
            worst = 100.0
            continue
        worst = max(worst, *(x["visiblyDifferent"] for x in r))
        print(f"{p['id']:20} " + "  ".join(f"{x['size']}: {x['visiblyDifferent']:.4f}% px differ, mean {x['meanDiff']}" for x in r))
    return worst


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    w = main(sys.argv[1])
    print(f"worst: {w:.4f}% of pixels visibly different (limit {LIMIT}%)")
    sys.exit(1 if w > LIMIT else 0)
