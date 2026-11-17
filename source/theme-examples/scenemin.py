"""Turns one theme-examples scene into a still, small SVG for a T3 Code theme.

reference_still() is the scene exactly as Anthropic composes it for reduced motion: the scene's own
`@media (prefers-reduced-motion: reduce)` rules made unconditional. minify() shrinks that still
without changing what it draws; verify.py renders both in Chrome and compares them pixel by pixel.
"""
import re
import xml.etree.ElementTree as ET
from decimal import Decimal

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
Q = "{" + SVG_NS + "}"


def _block_end(s, open_brace):
    depth = 0
    for k in range(open_brace, len(s)):
        if s[k] == "{":
            depth += 1
        elif s[k] == "}":
            depth -= 1
            if depth == 0:
                return k
    raise ValueError("unbalanced braces")


REDUCED = re.compile(r"@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{")


def reference_still(svg):
    """The scene's reduced-motion rules, made unconditional: Anthropic's own resting picture."""
    m = REDUCED.search(svg)
    if not m or REDUCED.search(svg, m.end()):
        raise ValueError("expected exactly one reduced-motion rule")
    close = _block_end(svg, m.end() - 1)
    return svg[:m.start()] + svg[m.end():close] + svg[close + 1:]


# ---------------------------------------------------------------- CSS

def _drop_at_blocks(css, name):
    out, i = [], 0
    while True:
        j = css.find(name, i)
        if j < 0:
            return "".join(out) + css[i:]
        out.append(css[i:j])
        i = _block_end(css, css.index("{", j)) + 1


def _clean_decls(decls, keep):
    kept = []
    for d in decls.split(";"):
        d = d.strip()
        if not d or ":" not in d:
            continue
        prop, val = d.split(":", 1)
        prop, val = prop.strip(), re.sub(r"\s+", " ", val.strip())
        if keep(prop, val):
            kept.append(f"{prop}:{val}")
    return ";".join(kept)


def _not_motion(prop, val):
    return not prop.startswith("animation") and prop not in ("will-change",)


def minify_css(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = _drop_at_blocks(css, "@keyframes")
    rules = []
    for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        body = _clean_decls(body, _not_motion)
        sel = re.sub(r"\s*,\s*", ",", re.sub(r"\s+", " ", sel.strip()))
        if body:
            rules.append(f"{sel}{{{body}}}")
    return "".join(rules)


def css_rules(css):
    return [(sel, body) for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css)]


def hidden_classes(css):
    """(hidden, first_only): classes a simple rule hides outright (opacity:0), and classes hidden
    except where `.cls:first-child` shows them again. Any other rule that sets a visible opacity on
    a class (.a .pose, .pose.b, ...) may show it, so such a class is in neither set."""
    hidden, shown, first = set(), set(), set()
    for sel, body in css_rules(css):
        decl = dict(d.split(":", 1) for d in body.split(";") if ":" in d)
        for part in sel.split(","):
            part = part.strip()
            m = re.fullmatch(r"\.([\w-]+)", part)
            f = re.fullmatch(r"\.([\w-]+):first-child", part)
            if m and decl.get("opacity", "").strip() in ("0", "0.0"):
                hidden.add(m.group(1))
            elif f and "opacity" in decl:
                first.add(f.group(1))
            elif "opacity" in decl:
                shown.update(re.findall(r"\.([\w-]+)", part))
    return hidden - shown - first, (hidden & first) - shown


def used_custom_props(css):
    return set(re.findall(r"var\((--[\w-]+)", css))


# ---------------------------------------------------------------- numbers and paths

def fmt(n):
    """Shortest exact decimal: 0.5 -> .5, -0.5 -> -.5, 12.0 -> 12."""
    n = Decimal(n).normalize()
    s = format(n, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    if s.startswith("0."):
        s = s[1:]
    elif s.startswith("-0."):
        s = "-" + s[2:]
    return "0" if s in ("", "-0") else s


def join_nums(nums):
    out = ""
    for s in nums:
        if out and not (s.startswith("-") or (s.startswith(".") and "." in _last_num(out))):
            out += " "
        out += s
    return out


def _last_num(s):
    """The last number token of a path text: '-.1-11' -> '-11', '11.3.9' -> '.9'."""
    nums = re.findall(r"-?(?:\d+\.\d*|\.\d+|\d+)", s)
    return nums[-1] if nums and re.search(r"[\d.]$", s) else ""


TOKEN = re.compile(r"[A-Za-z]|-?(?:\d+\.?\d*|\.\d+)(?:e-?\d+)?")
SIMPLE = set("MmLlHhVvZz")
ARGS = {"M": 2, "L": 2, "H": 1, "V": 1, "Z": 0}


def parse_simple_path(d):
    """[(cmd, [abs numbers])] for paths of M/L/H/V/Z only, else None. Numbers are Decimals."""
    toks = TOKEN.findall(d)
    if not toks or any(t.isalpha() and t not in SIMPLE for t in toks):
        return None
    cmds, i, cx, cy, sx, sy, cmd = [], 0, Decimal(0), Decimal(0), Decimal(0), Decimal(0), None
    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            cmd, i = t, i + 1
            if cmd in "Zz":
                cmds.append(("Z", []))
                cx, cy = sx, sy
                continue
        elif cmd is None:
            return None
        up, rel = cmd.upper(), cmd.islower()
        n = ARGS[up]
        vals = [Decimal(v) for v in toks[i:i + n]]
        if len(vals) < n:
            return None
        i += n
        if up == "M":
            x, y = (cx + vals[0], cy + vals[1]) if rel else (vals[0], vals[1])
            cmds.append(("M", [x, y]))
            cx, cy, sx, sy = x, y, x, y
            cmd = "l" if rel else "L"  # implicit lineto after moveto
        elif up == "L":
            x, y = (cx + vals[0], cy + vals[1]) if rel else (vals[0], vals[1])
            cmds.append(("L", [x, y]))
            cx, cy = x, y
        elif up == "H":
            x = cx + vals[0] if rel else vals[0]
            cmds.append(("H", [x]))
            cx = x
        elif up == "V":
            y = cy + vals[0] if rel else vals[0]
            cmds.append(("V", [y]))
            cy = y
    return cmds


def rects_of(cmds):
    """If the path is only axis-aligned closed rectangles, return [(x, y, w, h)], else None."""
    rects, i = [], 0
    while i < len(cmds):
        seq = cmds[i:i + 5]
        if (len(seq) == 5 and [c for c, _ in seq] == ["M", "H", "V", "H", "Z"]):
            (x, y), (x2,), (y2,), (x3,) = seq[0][1], seq[1][1], seq[2][1], seq[3][1]
            if x3 == x and x2 > x and y2 > y:
                rects.append((x, y, x2 - x, y2 - y))
                i += 5
                continue
        return None
    return rects


def merge_rects(rects):
    """Join rectangles that touch edge to edge in a row (same y and height). Same pixels, fewer bytes."""
    rows = {}
    for x, y, w, h in rects:
        rows.setdefault((y, h), []).append((x, w))
    out = []
    for (y, h), cells in rows.items():
        cells.sort()
        cur = None
        for x, w in cells:
            if cur and x == cur[0] + cur[1]:
                cur = (cur[0], cur[1] + w)
            elif cur and x < cur[0] + cur[1]:  # overlap: keep the union
                cur = (cur[0], max(cur[0] + cur[1], x + w) - cur[0])
            else:
                if cur:
                    out.append((cur[0], y, cur[1], h))
                cur = (x, w)
        out.append((cur[0], y, cur[1], h))
    out.sort(key=lambda r: (r[1], r[0]))
    return out


def rects_to_cmds(rects):
    cmds = []
    for x, y, w, h in rects:
        cmds += [("M", [x, y]), ("H", [x + w]), ("V", [y + h]), ("H", [x]), ("Z", [])]
    return cmds


def emit(cmds):
    """Shortest text for absolute commands, choosing absolute or relative per command."""
    out, prev, cx, cy, sx, sy = [], None, Decimal(0), Decimal(0), Decimal(0), Decimal(0)
    for c, v in cmds:
        if c == "Z":
            out.append("z")
            prev, cx, cy = "z", sx, sy
            continue
        if c == "M":
            a = ("M", [v[0], v[1]])
            r = ("m", [v[0] - cx, v[1] - cy])
        elif c == "L":
            a, r = ("L", v), ("l", [v[0] - cx, v[1] - cy])
        elif c == "H":
            a, r = ("H", v), ("h", [v[0] - cx])
        else:
            a, r = ("V", v), ("v", [v[0] - cy])
        if not out:
            r = a  # a path must start with an absolute moveto
        best = None
        for letter, nums in (a, r):
            body = join_nums([fmt(n) for n in nums])
            # Repeating the previous command letter may be omitted, except after M/m.
            text = body if (letter == prev and letter not in "Mm") else letter + body
            if out and not text[0].isalpha() and not text.startswith("-") and not (
                    text.startswith(".") and "." in _last_num(out[-1])):
                text = " " + text
            if best is None or len(text) < len(best[0]):
                best = (text, letter)
        out.append(best[0])
        prev = best[1]
        if c == "M":
            cx, cy, sx, sy = v[0], v[1], v[0], v[1]
        elif c == "L":
            cx, cy = v
        elif c == "H":
            cx = v[0]
        else:
            cy = v[0]
    return "".join(out)


def rects_as_strokes(rects):
    """{height: path text}: each rectangle drawn as a butt-capped horizontal line through its middle,
    stroke-width = its height. The stroke covers exactly the rectangle."""
    by_h = {}
    for x, y, w, h in rects:
        by_h.setdefault(h, []).append((x, y, w))
    out = {}
    for h, rs in by_h.items():
        rs.sort(key=lambda r: (r[1], r[0]))
        cmds = []
        for x, y, w in rs:
            cmds += [("M", [x, y + h / 2]), ("H", [x + w])]
        out[h] = emit(cmds)
    return out


def shrink_path(d, may_merge):
    cmds = parse_simple_path(d)
    if cmds is None:
        return re.sub(r"\s+", " ", d.strip())
    if may_merge:
        rects = rects_of(cmds)
        if rects:
            cmds = rects_to_cmds(merge_rects(rects))
    text = emit(cmds)
    return text if len(text) <= len(d) else d


# ---------------------------------------------------------------- the tree

def _strokes(el, parents):
    for e in [el] + parents:
        if e.get("stroke") not in (None, "none") or re.search(r"(^|;)\s*stroke\s*:", e.get("style") or ""):
            return True
        if e.get("fill-rule") == "evenodd" or "evenodd" in (e.get("style") or ""):
            return True
    return False


CULL_MARGIN = Decimal(40)  # wider than any stroke or glyph in the scenes
OFFSTAGE = {f"{Q}{t}" for t in ("defs", "pattern", "mask", "clipPath", "symbol", "marker")}


def subpaths(cmds):
    out, cur = [], []
    for c in cmds:
        if c[0] == "M" and cur:
            out.append(cur)
            cur = []
        cur.append(c)
    if cur:
        out.append(cur)
    return out


def bbox(sub):
    xs = [v[0] for c, v in sub if c in "MLH"]
    ys = [v[-1] for c, v in sub if c in "MLV"]
    return min(xs), min(ys), max(xs), max(ys)


def outside(box, w, h):
    x0, y0, x1, y1 = box
    m = CULL_MARGIN
    return x1 < -m or y1 < -m or x0 > w + m or y0 > h + m


def lattice_order(dots):
    """Sort dots along the rows of the lattice they sit on. A stroke is painted once for the whole
    path, so the order of its subpaths never changes what is drawn."""
    from collections import Counter
    near = Counter()
    for i, a in enumerate(dots):
        best = None
        for b in dots[max(0, i - 40):i + 40]:
            if b is a:
                continue
            dx, dy = b[0] - a[0], b[1] - a[1]
            d2 = dx * dx + dy * dy
            if best is None or d2 < best[0]:
                best = (d2, dx, dy)
        if best:
            dx, dy = best[1], best[2]
            if dx < 0 or (dx == 0 and dy < 0):
                dx, dy = -dx, -dy
            near[(round(float(dx)), round(float(dy)))] += 1
    if not near:
        return dots
    (sx, sy), _ = near.most_common(1)[0]
    norm = (sx * sx + sy * sy) ** 0.5 or 1.0
    ux, uy = sx / norm, sy / norm
    along = lambda p: float(p[0]) * ux + float(p[1]) * uy
    across = lambda p: float(p[0]) * -uy + float(p[1]) * ux
    return sorted(dots, key=lambda p: (round(across(p) / 2), along(p)))


def dots_never_touch(paths):
    """True when every path is round dots (`M x y h0`) of a known width and no two dots overlap."""
    dots = []
    widest = 0.0
    for p in paths:
        m = re.search(r"(?:--w|stroke-width):\s*([\d.]+)(?:px)?", p.get("style") or "")
        cmds = parse_simple_path(p.get("d") or "")
        if not m or not cmds:
            return False
        w = float(m.group(1))
        widest = max(widest, w)
        for s in subpaths(cmds):
            if len(s) != 2 or s[1][0] != "H" or s[1][1][0] != s[0][1][0]:
                return False
            dots.append((float(s[0][1][0]), float(s[0][1][1])))
    reach = widest + 0.5  # two dots touch when their centres are closer than (w1 + w2) / 2
    cells = {}
    for x, y in dots:
        cells.setdefault((int(x // reach), int(y // reach)), []).append((x, y))
    for (cx, cy), here in cells.items():
        for nx in (cx - 1, cx, cx + 1):
            for ny in (cy - 1, cy, cy + 1):
                for a in here:
                    for b in cells.get((nx, ny), ()):
                        if a is not b and (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 < reach * reach:
                            return False
    return True


def merge_sibling_paths(root, css):
    """Join sibling paths that paint the same way into one path.

    Only where it cannot show: every path in the group is a plain stroke or fill of one inherited
    paint, with no class, id, transform or blend of its own, and either fully opaque or proven not
    to overlap. Opaque paint of one colour looks the same whether two shapes are one path or two,
    in any order. An even-odd fill rule anywhere would turn overlaps into holes, so it stops a merge.
    """
    if re.search(r"evenodd", css):
        return
    up = {c: p for p in root.iter() for c in p}
    for parent in root.iter():
        kids = [c for c in parent if c.tag == f"{Q}path"]
        if len(kids) < 2 or len(kids) != len(parent):
            continue
        if any(set(c.attrib) - {"d", "style"} for c in kids):
            continue
        styles = {c.get("style") or "" for c in kids}
        if any(re.search(r"opacity|blend|transform|filter|mask|clip|fill|stroke:|dasharray", s) for s in styles):
            continue
        chain, a = [], parent
        while a is not None:
            chain.append(a)
            a = up.get(a)
        if any("evenodd" in (e.get("fill-rule") or "") + (e.get("style") or "") for e in chain):
            continue
        translucent = any(e.get(k) not in (None, "1") or re.search(k + r"\s*:", e.get("style") or "")
                          for e in chain for k in ("fill-opacity", "stroke-opacity"))
        if translucent and not dots_never_touch(kids):
            continue  # translucent paint shows where shapes overlap, so separate paths must stay separate
        groups = {}
        for c in kids:
            groups.setdefault(c.get("style") or "", []).append(c)
        for same in groups.values():
            if len(same) < 2:
                continue
            first = same[0]
            first.set("d", " ".join(c.get("d") for c in same))
            for c in same[1:]:
                parent.remove(c)


def dot_runs(cmds):
    """Split a path of round-capped dots (`M x y h0`) into evenly spaced runs and loose dots.

    A run of n dots becomes one line drawn with `stroke-dasharray: 0 L`, which puts a round dot every
    L along it: the same dots, a fraction of the text. Returns (runs_cmds, loose_cmds, L) or None.
    """
    subs = subpaths(cmds)
    dots = []
    for s in subs:
        if len(s) != 2 or s[1][0] != "H" or s[1][1][0] != s[0][1][0]:
            return None
        dots.append(s[0][1])
    if len(dots) < 6:
        return None
    dots = lattice_order(dots)
    steps = [((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) for a, b in zip(dots, dots[1:])]
    lengths = sorted(float(x) ** 0.5 for x in steps)
    median = lengths[len(lengths) // 2]
    if median <= 0:
        return None
    # The lattice step: the mean of the steps near the median. Positions are rounded to 0.1, so a
    # single step is off by up to ~0.14; the mean over many is far closer to the true spacing.
    near = [x for x in lengths if abs(x - median) <= 0.03 * median]
    L = Decimal(str(round(sum(near) / len(near), 3)))
    runs, loose, i = [], [], 0
    while i < len(dots):
        j = i
        if i + 1 < len(dots):
            dx, dy = dots[i + 1][0] - dots[i][0], dots[i + 1][1] - dots[i][1]
            while (j + 1 < len(dots)
                   and abs(dots[j + 1][0] - dots[j][0] - dx) <= Decimal("0.15")
                   and abs(dots[j + 1][1] - dots[j][1] - dy) <= Decimal("0.15")):
                j += 1
        n = j - i + 1
        if n >= 3:
            (x0, y0), (x1, y1) = dots[i], dots[j]
            span = ((x1 - x0) ** 2 + (y1 - y0) ** 2).sqrt()
            if abs(span - (n - 1) * L) <= Decimal("0.3"):
                ux, uy = (x1 - x0) / span, (y1 - y0) / span
                reach = (n - Decimal("0.5")) * L  # half a step past the last dot, so it is always drawn
                ex = (x0 + ux * reach).quantize(Decimal("0.01"))
                ey = (y0 + uy * reach).quantize(Decimal("0.01"))
                runs += [("M", [x0, y0]), ("L", [ex, ey])]
                i = j + 1
                continue
        for x, y in dots[i:j + 1]:
            loose += [("M", [x, y]), ("H", [x])]
        i = j + 1
    return (runs, loose, L) if runs else None


NUMBER = re.compile(r"(?<![\w#.-])-?(?:\d+\.\d*|\.\d+|\d+)(?![\d.])")


def short_numbers(s):
    return NUMBER.sub(lambda m: fmt(m.group(0)) if len(fmt(m.group(0))) <= len(m.group(0)) else m.group(0), s)


NUMERIC_ATTRS = {"x", "y", "width", "height", "cx", "cy", "r", "rx", "ry", "x1", "y1", "x2", "y2", "fx", "fy",
                 "offset", "opacity", "fill-opacity", "stroke-opacity", "stop-opacity", "stroke-width",
                 "font-size", "transform", "viewBox", "stroke-dashoffset", "stroke-dasharray", "style",
                 "patternTransform", "gradientTransform"}
DEFAULTS = {"rect": {"x": "0", "y": "0"}, "stop": {"offset": "0"}, "circle": {"cx": "0", "cy": "0"},
            "ellipse": {"cx": "0", "cy": "0"}}


def compact_patterns(root):
    """Single-cell dither patterns: share one base through `href` and draw on an 8x8 grid."""
    eighth = Decimal("0.125")
    cands = []
    for p in root.iter(f"{Q}pattern"):
        a = dict(p.attrib)
        a.pop("id", None)
        if a != {"width": "1", "height": "1", "patternUnits": "userSpaceOnUse"} or not len(p):
            continue
        ok = all(c.tag == f"{Q}rect" and set(c.attrib) <= {"x", "y", "width", "height", "fill"} and all(
            (Decimal(c.get(k, "0")) / eighth) == (Decimal(c.get(k, "0")) / eighth).to_integral_value()
            for k in ("x", "y", "width", "height")) for c in p)
        if ok:
            cands.append(p)
    if len(cands) < 4:
        return
    base = cands[0]
    base.set("viewBox", "0 0 8 8")
    for p in cands:
        if p is not base:
            for k in ("width", "height", "patternUnits"):
                del p.attrib[k]
            p.set("href", "#" + base.get("id"))
        for c in p:
            for k in ("x", "y", "width", "height"):
                if k in c.attrib:
                    c.set(k, fmt(Decimal(c.get(k)) / eighth))


def group_pattern_fills(root):
    """Patterns whose cells share one fill colour move under a <g fill> in <defs>: a pattern's
    content inherits from the pattern's ancestors, so each cell can drop its own fill."""
    defs = root.find(f"{Q}defs")
    if defs is None:
        return
    by_fill = {}
    for p in list(defs):
        if p.tag != f"{Q}pattern" or not len(p):
            continue
        fills = {c.get("fill") for c in p}
        if len(fills) == 1 and None not in fills and all(c.tag in (f"{Q}rect", f"{Q}path") for c in p):
            by_fill.setdefault(fills.pop(), []).append(p)
    for fill, pats in by_fill.items():
        if len(pats) < 3:
            continue
        g = ET.Element(f"{Q}g", {"fill": fill})
        for p in pats:
            defs.remove(p)
            for c in p:
                del c.attrib["fill"]
            g.append(p)
        defs.append(g)


def short_ids(root, css):
    """Rename ids to one or two letters and update every url(#id) and href. Ids a stylesheet
    selects by name keep theirs."""
    styled = set(re.findall(r"#([A-Za-z][\w-]*)", css))
    ids = [e.get("id") for e in root.iter() if e.get("id") and e.get("id") not in styled]
    letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    names = (letters[i] if i < 52 else letters[i // 52 - 1] + letters[i % 52] for i in range(10 ** 4))
    taken = styled
    rename = {}
    for old in ids:
        new = next(n for n in names if n not in taken)
        rename[old] = new
    if not rename:
        return
    ref = re.compile(r"(url\(['\"]?#|^#)([A-Za-z][\w-]*)")  # url(#a), url('#a'), href and xlink:href '#a'
    for e in root.iter():
        for k, v in list(e.attrib.items()):
            if k == "id" and v in rename:
                e.set(k, rename[v])
            elif "#" in v:
                e.set(k, ref.sub(lambda m: m.group(1) + rename.get(m.group(2), m.group(2)), v))


def rect_as_path(el):
    a = el.attrib
    if not ({"width", "height"} <= set(a)) or set(a) & {"rx", "ry", "id", "class"}:
        return None
    try:
        x, y, w, h = (Decimal(a.get(k, "0")) for k in ("x", "y", "width", "height"))
    except Exception:
        return None
    return emit([("M", [x, y]), ("H", [x + w]), ("V", [y + h]), ("H", [x]), ("Z", [])])


def minify(still):
    root = ET.fromstring(still)
    vb = [Decimal(v) for v in (root.get("viewBox") or "0 0 0 0").split()]
    stage_w, stage_h = vb[2], vb[3]
    style_el = root.find(f".//{Q}style")
    css = minify_css(style_el.text or "") if style_el is not None else ""
    hidden, first_only = hidden_classes(css)
    # Merging rectangles changes outlines, so it is only done where nothing can stroke them.
    css_strokes_paths = "stroke" in css
    inline_styles = " ".join(re.findall(r"style=\"([^\"]*)\"", still))
    used_vars = used_custom_props(css) | used_custom_props(inline_styles)
    dashed = {c for sel, body in css_rules(css) if "dasharray" in body for c in re.findall(r"\.([\w-]+)", sel)}
    moved = {c for sel, body in css_rules(css) if "transform" in body for c in re.findall(r"\.([\w-]+)", sel)}
    round_caps = bool(re.search(r"stroke-linecap:round", css))
    # A rect drawn as a path would pick up the scene's own path{...} rules, so convert only where
    # the CSS names neither element type.
    css_names_rect = bool(re.search(r"(^|[},\s>+~])(rect|path)\b", css))

    def transformed(e):
        return bool(e.get("transform")) or "transform" in (e.get("style") or "") or bool(
            moved & set((e.get("class") or "").split()))

    paint_classes = {c for sel, body in css_rules(css) if re.search(r"fill|stroke|paint", body)
                     for c in re.findall(r"\.([\w-]+)", sel)}
    user_space_patterns = {p.get("id") for p in root.iter(f"{Q}pattern") if p.get("patternUnits") == "userSpaceOnUse"}

    def strokable(child, ancestors):
        """Whether this filled path may be drawn as strokes without anything else changing."""
        fill = child.get("fill") or ""
        m = re.fullmatch(r"url\(#([\w-]+)\)", fill)
        if not (re.fullmatch(r"#[0-9a-fA-F]{3,8}|[a-z]+", fill) and fill != "none") \
                and not (m and m.group(1) in user_space_patterns):
            return False
        if set(child.attrib) - {"d", "fill", "fill-opacity", "transform", "opacity"}:
            return False
        if paint_classes & set((child.get("class") or "").split()):
            return False
        for a in ancestors:
            if any(k.startswith(("stroke", "fill-opacity", "paint-order", "vector-effect")) for k in a.attrib):
                return False
            if re.search(r"stroke|fill-opacity", a.get("style") or ""):
                return False
            if paint_classes & set((a.get("class") or "").split()):
                return False
        return True

    def as_strokes(parent, child):
        cmds = parse_simple_path(child.get("d"))
        rects = rects_of(cmds) if cmds else None
        if not rects:
            return
        groups = rects_as_strokes(rects)
        made = []
        for h, d in groups.items():
            attrs = {k: v for k, v in child.attrib.items() if k not in ("d", "fill", "fill-opacity")}
            attrs.update({"d": d, "stroke": child.get("fill"), "stroke-width": fmt(h)})
            if child.get("fill-opacity"):
                attrs["stroke-opacity"] = child.get("fill-opacity")
            made.append(ET.Element(child.tag, attrs))
        if sum(len(serialize(e)) for e in made) < len(serialize(child)):
            i = list(parent).index(child)
            parent.remove(child)
            for k, e in enumerate(made):
                parent.insert(i + k, e)

    def walk(el, parents, offstage, moving):
        kids = list(el)
        for child in kids:
            classes = set((child.get("class") or "").split())
            st = child.get("style") or ""
            if classes & first_only and child is not kids[0] and not re.search(r"opacity:\s*[.1-9]", st):
                el.remove(child)
                continue
            if classes & hidden or child.get("opacity") == "0" or re.search(r"(^|;)\s*opacity:\s*0(;|$)", st):
                if not re.search(r"(^|;)\s*opacity:\s*[.1-9]", st):
                    el.remove(child)
                    continue
            if st:
                kept = _clean_decls(st, lambda p, v: _not_motion(p, v) and (not p.startswith("--") or p in used_vars))
                if kept:
                    child.set("style", kept)
                else:
                    del child.attrib["style"]
            chain = [child, el] + parents
            c_off = offstage or child.tag in OFFSTAGE
            c_moving = moving or transformed(child)
            if child.tag == f"{Q}path" and child.get("d"):
                # Dash patterns follow the exact path text, so dashed paths are left as they are.
                if not any("dasharray" in (e.get("style") or "") or e.get("stroke-dasharray")
                           or dashed & set((e.get("class") or "").split()) for e in chain):
                    cmds = parse_simple_path(child.get("d"))
                    if cmds is not None and not c_off and not c_moving and stage_w:
                        cmds = [c for s in subpaths(cmds) if not outside(bbox(s), stage_w, stage_h) for c in s]
                        if not cmds:
                            el.remove(child)
                            continue
                        child.set("d", emit(cmds))
                    runs = dot_runs(cmds) if (cmds and round_caps) else None
                    if runs:
                        run_cmds, loose, L = runs
                        if loose:
                            twin = ET.Element(child.tag, dict(child.attrib))
                            twin.set("d", emit(loose))
                            el.insert(list(el).index(child) + 1, twin)
                        child.set("d", emit(run_cmds))
                        child.set("style", ";".join(x for x in (child.get("style"), f"stroke-dasharray:0 {fmt(L)}") if x))
                    else:
                        may_merge = not css_strokes_paths and not _strokes(child, [el] + parents)
                        child.set("d", shrink_path(child.get("d"), may_merge))
                        if may_merge and not css_names_rect and strokable(child, [el] + parents):
                            as_strokes(el, child)
            elif child.tag == f"{Q}text" and not len(child) and child.text and " " in (child.get("x") or "") \
                    and not c_off and not c_moving:
                xs = [Decimal(v) for v in child.get("x").split()]
                ys = [Decimal(v) for v in (child.get("y") or "0").split()]
                chars = list(child.text)
                y_list = len(ys) > 1
                if len(xs) == len(chars) and (not y_list or len(ys) == len(chars)) \
                        and not (set(child.attrib) & {"dx", "dy", "rotate", "textLength"}):
                    ys_full = ys if y_list else [ys[0]] * len(xs)
                    keep = [(x, y, ch) for x, y, ch in zip(xs, ys_full, chars)
                            if -CULL_MARGIN <= x <= stage_w + CULL_MARGIN]
                    if not keep:
                        el.remove(child)
                        continue
                    xs, ys_full, chars = ([k[i] for k in keep] for i in range(3))
                    # One translate for what every glyph shares: the x fraction (all at .5) and the
                    # top row, so each position is written with fewer digits.
                    frac = {x - x.to_integral_value(rounding="ROUND_FLOOR") for x in xs}
                    tx = frac.pop() if len(frac) == 1 else Decimal(0)
                    ty = min(ys_full).to_integral_value(rounding="ROUND_FLOOR") if y_list else Decimal(0)
                    plain = " ".join(fmt(x) for x in xs) + (" ".join(fmt(y) for y in ys_full) if y_list else "")
                    moved_x = [x - tx for x in xs]
                    moved_y = [y - ty for y in ys_full]
                    shifted = " ".join(fmt(x) for x in moved_x) + (" ".join(fmt(y) for y in moved_y) if y_list else "")
                    if (tx or ty) and not child.get("transform") and len(shifted) + 20 < len(plain):
                        xs, ys_full = moved_x, moved_y
                        child.set("transform", f"translate({fmt(tx)}{' ' + fmt(ty) if ty else ''})")
                    child.set("x", " ".join(fmt(x) for x in xs))
                    if y_list:
                        child.set("y", " ".join(fmt(y) for y in ys_full))
                    child.text = "".join(chars)
            walk(child, [el] + parents, c_off, c_moving)
            if child.tag == f"{Q}g" and len(child) == 0 and not (child.text or "").strip():
                el.remove(child)

    for e in root.iter():  # motion and unused variables out first, so alike paths look alike
        if e.get("style"):
            kept = _clean_decls(e.get("style"),
                                lambda p, v: _not_motion(p, v) and (not p.startswith("--") or p in used_vars))
            if kept:
                e.set("style", kept)
            else:
                del e.attrib["style"]
    merge_sibling_paths(root, css)
    walk(root, [], False, False)
    compact_patterns(root)
    group_pattern_fills(root)
    short_ids(root, css)
    for e in root.iter():
        tag = e.tag.replace(Q, "")
        for k, v in DEFAULTS.get(tag, {}).items():
            if e.get(k) == v:
                del e.attrib[k]
        for k in list(e.attrib):
            if k in NUMERIC_ATTRS:
                e.set(k, short_numbers(e.get(k)))
    if root.get("width") == "100%" and root.get("height") == "100%":
        del root.attrib["width"], root.attrib["height"]
    if not css_names_rect:
        for parent in root.iter():
            for i, c in enumerate(list(parent)):
                if c.tag == f"{Q}rect":
                    d = rect_as_path(c)
                    if d is not None:
                        attrs = {k: v for k, v in c.attrib.items() if k not in ("x", "y", "width", "height")}
                        p = ET.Element(f"{Q}path", {"d": d, **attrs})
                        p.tail = c.tail
                        parent.remove(c)
                        parent.insert(i, p)
    if style_el is not None:
        style_el.text = short_numbers(css)
    return serialize(root)


def _esc_text(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _esc_attr(s):
    return _esc_text(s).replace("'", "&apos;")


TEXTY = {f"{Q}text", f"{Q}tspan", f"{Q}style"}


def serialize(el, inside_text=False):
    tag = el.tag.replace(Q, "")
    attrs = "".join(f" {k}='{_esc_attr(re.sub(chr(10) + '|' + chr(9), ' ', v))}'" for k, v in el.attrib.items())
    if el.tag == f"{Q}svg" and "xmlns" not in attrs:
        attrs = f" xmlns='{SVG_NS}'" + attrs
    keep_ws = inside_text or el.tag in TEXTY
    text = el.text or ""
    if not keep_ws:
        text = text.strip()
    inner = (text if el.tag == f"{Q}style" else _esc_text(text)) + "".join(
        serialize(c, keep_ws) + (_tail(c, keep_ws)) for c in el)
    return f"<{tag}{attrs}/>" if not inner else f"<{tag}{attrs}>{inner}</{tag}>"


def _tail(c, keep_ws):
    t = c.tail or ""
    return _esc_text(t if keep_ws else t.strip())


def to_css_url(svg):
    """A data: URL T3 accepts: no backslash (T3 drops the declaration), no line break, no double quote."""
    if "\n" in svg or "\r" in svg:
        svg = svg.replace("\r", "").replace("\n", " ")
    enc = (svg.replace("%", "%25").replace("#", "%23").replace("\\", "%5C").replace('"', "%22"))
    # A raw "</style" would end the stylesheet wherever this CSS sits inside an HTML <style> tag.
    enc = re.sub(r"<(?=/style)", "%3C", enc, flags=re.I)
    return f'url("data:image/svg+xml,{enc}")'
