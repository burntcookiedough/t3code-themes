"""Contact sheet of captured surfaces: one PNG per theme, every surface as a labelled thumbnail.

    python tools/capture/sheet.py <screens-dir> [theme ...]   ->  <screens-dir>/<theme>.sheet.png
"""
import os
import subprocess
import sys

CHROMES = [os.environ.get("CHROME", ""), r"C:\Program Files\Google\Chrome\Application\chrome.exe",
           r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
           "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/usr/bin/google-chrome", "/usr/bin/chromium"]
CHROME = next(p for p in CHROMES if p and os.path.exists(p))
COLS, TW, TH = 4, 568, 320


def sheet(folder, theme):
    shots = sorted(f for f in os.listdir(os.path.join(folder, theme)) if f.endswith(".png"))
    cells = "".join(
        f"<div><img src='file:///{os.path.abspath(os.path.join(folder, theme, f)).replace(os.sep, '/')}'><b>{f[:-4]}</b></div>"
        for f in shots)
    rows = -(-len(shots) // COLS)
    html = os.path.join(folder, f"{theme}.sheet.html")
    with open(html, "w", encoding="utf-8") as fh:
        fh.write(f"<!doctype html><style>body{{margin:0;background:#111;display:grid;grid-template-columns:repeat({COLS},{TW}px);"
                 f"gap:3px;width:{COLS * (TW + 3)}px}}div{{position:relative}}img{{width:{TW}px;height:{TH}px;display:block}}"
                 f"b{{position:absolute;left:4px;bottom:4px;font:13px sans-serif;color:#fff;background:#000c;padding:2px 6px}}</style>{cells}")
    out = os.path.join(folder, f"{theme}.sheet.png")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                    f"--window-size={COLS * (TW + 3)},{rows * (TH + 3)}", f"--screenshot={os.path.abspath(out)}",
                    "file:///" + os.path.abspath(html).replace(os.sep, "/")], capture_output=True, timeout=120, check=True)
    if not os.path.isfile(out):
        raise RuntimeError(f"Chrome did not write {out}")
    return out


def compare(folder, surface, crop, cols=4, scale=1.0):
    """One surface across every theme, cropped to x,y,w,h (screenshot pixels), as one sheet."""
    x, y, w, h = crop
    themes = sorted(d for d in os.listdir(folder) if os.path.exists(os.path.join(folder, d, f"{surface}.png")))
    tw, th = int(w * scale), int(h * scale)
    cells = "".join(
        f"<div style=\"width:{tw}px;height:{th}px;background:url('file:///{os.path.abspath(os.path.join(folder, t, surface + '.png')).replace(os.sep, '/')}') "
        f"-{x * scale}px -{y * scale}px / {1707 * scale}px auto no-repeat\"><b>{t}</b></div>" for t in themes)
    rows = -(-len(themes) // cols)
    name = f"compare-{surface}-{x}-{y}"
    html = os.path.join(folder, name + ".html")
    with open(html, "w", encoding="utf-8") as fh:
        fh.write(f"<!doctype html><style>body{{margin:0;background:#111;display:grid;grid-template-columns:repeat({cols},{tw}px);"
                 f"gap:3px}}div{{position:relative}}b{{position:absolute;left:4px;bottom:4px;font:12px sans-serif;"
                 f"color:#fff;background:#000c;padding:2px 6px}}</style>{cells}")
    out = os.path.join(folder, name + ".png")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                    f"--window-size={cols * (tw + 3)},{rows * (th + 3)}", f"--screenshot={os.path.abspath(out)}",
                    "file:///" + os.path.abspath(html).replace(os.sep, "/")], capture_output=True, timeout=120, check=True)
    if not os.path.isfile(out):
        raise RuntimeError(f"Chrome did not write {out}")
    return out


if __name__ == "__main__":
    folder = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[2] == "--compare":
        # sheet.py <dir> --compare <surface> x,y,w,h [scale] [cols]
        crop = tuple(int(v) for v in sys.argv[4].split(","))
        print(compare(folder, sys.argv[3], crop, int(sys.argv[6]) if len(sys.argv) > 6 else 4,
                      float(sys.argv[5]) if len(sys.argv) > 5 else 1.0))
        sys.exit(0)
    themes = sys.argv[2:] or sorted(d for d in os.listdir(folder) if os.path.isdir(os.path.join(folder, d)))
    for t in themes:
        print(sheet(folder, t))
