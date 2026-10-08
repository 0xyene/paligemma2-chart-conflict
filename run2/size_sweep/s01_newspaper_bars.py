"""Run 2 size sweep for s01_newspaper_bars: the value labels above the bars at 4 sizes.

python3.12 run2/size_sweep/s01_newspaper_bars.py

Only the cue text changes. In make.py the labels are SVG <text class="val"> elements, sized by ONE CSS rule:
    .val { font-family: "Helvetica Neue", Arial, sans-serif; font-size: 25px; font-weight: 700; fill: #1a1a1a; }
This script patches exactly that rule's font-size in the page HTML (asserted to occur once): 25px -> fs.
k=2 (25px) is byte-identical to run 1's HTML.
At k=4 the Jan and Jun labels would run past the SVG's left/right edge (the inline <svg> clips its overflow), so those two
<text> elements get their x nudged inward by NUDGE px. Nothing else moves; bars, axis, months, titles, body text, fonts
are untouched.

Writes only to run2/images/size/, run2/build/size/ (through common/lib.py render_html with redirected folders)
and run2/size_sweep/ (check images + s01_newspaper_bars.json). English, consistent + conflict only.
"""
import sys

sys.dont_write_bytecode = True          # importing make.py / lib must not drop __pycache__ into stimuli/ or common/

import importlib.util  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from scipy import ndimage  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SID = "s01_newspaper_bars"
OUT = ROOT / "run2" / "size_sweep"
CHECK = OUT / "check"
RUN1 = ROOT / "images"

sys.path.insert(0, str(ROOT / "common"))
import lib  # noqa: E402

lib.IMAGES = ROOT / "run2" / "images" / "size"
lib.BUILD = ROOT / "run2" / "build" / "size"

_spec = importlib.util.spec_from_file_location("s01_make", ROOT / "stimuli" / SID / "make.py")
make = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(make)          # main loop is behind __name__ == "__main__": nothing is rendered or written

CONDS = ("consistent", "conflict")
LANG = "en"
FS0 = 25                                            # original .val font size (px)
FS = {1: 15, 2: 25, 3: 37.5, 4: 50}                 # 0.6x, 1x, 1.5x, 2x the font size -> digit height scales with it
NUDGE = {4: 6}                                      # k -> px the Jan label moves right and the Jun label moves left
VAL_RULE = re.compile(r'(\.val \{ font-family: "Helvetica Neue", Arial, sans-serif; font-size: )25px(; font-weight: 700;)')
VAL_TEXT = re.compile(r'<text x="([0-9.]+)"( y="[0-9.]+" text-anchor="middle" class="val">)([^<]*)</text>')

# SVG geometry, copied from make.bars_svg (read-only) to place the analytic text boxes
W, H, BASE, TOP, BW = 470, 410, 366, 52, 46
SLOT = W / len(make.VISUAL)
SCALE = (BASE - TOP) / max(make.VISUAL)
CX = [SLOT * i + (SLOT - BW) / 2 + BW / 2 for i in range(len(make.VISUAL))]   # label x centres (svg units)
BY = [BASE - v * SCALE - 12 for v in make.VISUAL]                               # label baselines (svg units)
BAR_RGB = np.array([0x1f, 0x3a, 0x5f])


def fs_css(fs):
    return f"{fs:g}px"


def html(cond, k):
    h = make.page(cond, LANG)
    h, n = VAL_RULE.subn(lambda m: m.group(1) + fs_css(FS[k]) + m.group(2), h)
    assert n == 1, ".val font-size rule not found exactly once in make.py's HTML"
    d = NUDGE.get(k, 0)
    if d:
        texts = VAL_TEXT.findall(h)
        assert len(texts) == len(make.VISUAL), texts
        i = [0]

        def nudge(m):
            j = i[0]
            i[0] += 1
            x = float(m.group(1)) + (d if j == 0 else -d if j == len(make.VISUAL) - 1 else 0)
            return f'<text x="{x:.1f}"{m.group(2)}{m.group(3)}</text>'
        h = VAL_TEXT.sub(nudge, h)
    return h


def label_texts(h):
    return [t[2] for t in VAL_TEXT.findall(h)]


def img_name(cond, k):
    return f"{SID}_{cond}_{LANG}_s{k}"


def load(p):
    return np.asarray(Image.open(p).convert("RGB")).astype(int)


def cue_px(a, b):
    """common/collect.py cue_px(), on an in-memory consistent/conflict pair."""
    changed = np.abs(a - b).max(axis=2) > 24
    blobs, _ = ndimage.label(ndimage.binary_dilation(changed, structure=np.ones((3, 15), bool)))
    hs = []
    for sl in ndimage.find_objects(blobs):
        rows = np.where(changed[sl].any(axis=1))[0]
        if len(rows) and changed[sl].sum() >= 20:
            hs.append(int(rows[-1] - rows[0] + 1))
    return int(np.median(hs)) if hs else 0


def svg_origin(img):
    """Page position of the SVG's (0,0): the 470 px axis line (svg y 365..366, x 0..470) is the only 470 px dark run."""
    dark = img.max(axis=2) < 80
    for r in range(img.shape[0]):
        row = np.concatenate([[0], dark[r].astype(int), [0]])
        st, en = np.where(np.diff(row) == 1)[0], np.where(np.diff(row) == -1)[0]
        for s, e in zip(st, en):
            if e - s == W:
                return int(s), int(r - 365)
    raise RuntimeError("axis line not found")


def label_boxes(k, x0, y0):
    """Analytic page-pixel boxes [y0, y1, x0, x1) where each label's ink can be, at size k (measured at 25px: ink is
    +-0.85 em wide around the centre and 0.77 em tall above the baseline; a 1 px margin is added)."""
    fs, d = FS[k], NUDGE.get(k, 0)
    out = []
    for i, (cx, by) in enumerate(zip(CX, BY)):
        cx = cx + (d if i == 0 else -d if i == len(CX) - 1 else 0)
        out.append((int(np.floor(y0 + by - 0.80 * fs - 1)), int(np.ceil(y0 + by + 2)),
                    int(np.floor(x0 + cx - 0.88 * fs - 1)), int(np.ceil(x0 + cx + 0.88 * fs + 1))))
    return out


def box_mask(boxes):
    m = np.zeros((lib.SIZE, lib.SIZE), bool)
    for a, b, c, d in boxes:
        m[a:b, c:d] = True
    return m


def main():
    for d in (lib.IMAGES, lib.BUILD, CHECK / "448", CHECK / "224", CHECK / "diff"):
        d.mkdir(parents=True, exist_ok=True)

    # ---- render ----
    imgs, htmls = {}, {}
    for k in FS:
        for cond in CONDS:
            htmls[cond, k] = html(cond, k)
            p = lib.render_html(htmls[cond, k], img_name(cond, k))
            imgs[cond, k] = load(p)
            for res in (448, 224):
                Image.open(p).convert("RGB").resize((res, res), Image.BICUBIC).save(CHECK / str(res) / p.name)

    problems, notes = [], []
    nonum = load(RUN1 / f"{SID}_nonumbers_{LANG}.png")      # run-1 drawing with the label strings blanked (read only)
    x0, y0 = svg_origin(nonum)

    # ---- 1. original size == run 1 ----
    for cond in CONDS:
        assert htmls[cond, 2] == make.page(cond, LANG), "k=2 HTML must be byte-identical to make.page()"
        run1_html = ROOT / "build" / f"{SID}_{cond}_{LANG}.html"
        if run1_html.read_text(encoding="utf-8") != htmls[cond, 2]:
            problems.append(f"make.page({cond}) differs from run 1's build HTML")
    run1_diff = {c: int(np.abs(imgs[c, 2] - load(RUN1 / f"{SID}_{c}_{LANG}.png")).max()) for c in CONDS}
    identical = all(v <= 2 for v in run1_diff.values())
    if not identical:
        problems.append(f"original-size re-render differs from run 1: max abs diff {run1_diff}")

    # ---- 2. changed pixels vs the original size lie inside the cue-text regions ----
    dil = np.ones((7, 7), bool)                       # dilate the text boxes by 3 px
    boxes = {k: label_boxes(k, x0, y0) for k in FS}
    region_k = {k: ndimage.binary_dilation(box_mask(boxes[k]), structure=dil) for k in FS}
    outside, changed_n, ink_out = {}, {}, {}
    for k in FS:
        region = region_k[k] | region_k[2]
        for cond in CONDS:
            a, b = imgs[cond, 2], imgs[cond, k]
            changed = np.abs(a - b).max(axis=2) > 24
            n, out = int(changed.sum()), int((changed & ~region).sum())
            outside[f"s{k}_{cond}"] = round(out / n, 6) if n else 0.0
            changed_n[f"s{k}_{cond}"] = n
            # stronger: the size-k image equals run 1's blank-label drawing everywhere outside its own text boxes
            ink_out[f"s{k}_{cond}"] = int(np.abs(b - nonum)[~region_k[k]].max())
            faded = (255 - (255 - b) * 0.35).astype(np.uint8)
            faded[region & ~ndimage.binary_erosion(region)] = (40, 90, 230)
            faded[changed] = (230, 30, 30)
            Image.fromarray(faded).save(CHECK / "diff" / f"{img_name(cond, k)}_vs_s2.png")
    outside_share = max(outside.values())
    if outside_share > 0:
        problems.append(f"changed pixels outside cue-text regions: {outside}")
    if max(ink_out.values()) > 2:
        problems.append(f"image differs from run-1 blank-label drawing outside the text boxes: {ink_out}")

    # ---- 3. digit height per size, as collect.py measures it ----
    cpx = {k: cue_px(imgs["consistent", k], imgs["conflict", k]) for k in FS}
    r1_cpx = cue_px(load(RUN1 / f"{SID}_consistent_{LANG}.png"), load(RUN1 / f"{SID}_conflict_{LANG}.png"))
    seq = [cpx[k] for k in sorted(cpx)]
    if not all(x < y for x, y in zip(seq, seq[1:])):
        problems.append(f"cue_px not strictly increasing: {seq}")
    if cpx[2] != r1_cpx:
        problems.append(f"cue_px at original size {cpx[2]} != run-1 {r1_cpx}")

    # ---- 4. placement (clipping / overlap / ownership) and the lie ----
    bar = np.abs(nonum - BAR_RGB).max(axis=2) < 40   # bar fill pixels
    svg_box = (y0, y0 + H, x0, x0 + W)
    place = {}
    yy, xx = np.mgrid[0:lib.SIZE, 0:lib.SIZE]
    for k in FS:
        # pixel -> label id: the label box (dilated 3 px) it lies in, the nearest box centre where boxes overlap
        idmap, best = np.full((lib.SIZE, lib.SIZE), -1), np.full((lib.SIZE, lib.SIZE), np.inf)
        for i, (a, b, c, d) in enumerate(boxes[k]):
            inside = (yy >= a - 3) & (yy < b + 3) & (xx >= c - 3) & (xx < d + 3)
            dist = np.hypot((yy - (a + b) / 2) / (b - a), (xx - (c + d) / 2) / (d - c))
            take = inside & (dist < best)
            idmap[take], best[take] = i, dist[take]
        for cond in CONDS:
            ink = np.abs(imgs[cond, k] - nonum).max(axis=2) > 8          # every label pixel incl. anti-aliasing
            per = []
            for i in range(len(boxes[k])):
                li = ink & (idmap == i)
                ys, xs = np.where(li)
                others = ink & (idmap != i)
                dist_other = ndimage.distance_transform_edt(~others)[li].min() if others.any() else 999
                dist_bar = ndimage.distance_transform_edt(~bar)[li].min()
                # own bar = the bar right below the label centre
                cxp = int(round(x0 + CX[i]))
                own_top = y0 + int(round(BASE - make.VISUAL[i] * SCALE))
                per.append(dict(i=i, bbox=[int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())],
                                margin_svg=int(min(ys.min() - svg_box[0], xs.min() - svg_box[2],
                                                   svg_box[3] - 1 - xs.max(), svg_box[1] - 1 - ys.max())),
                                gap_other_label=round(float(dist_other), 1), gap_bar=round(float(dist_bar), 1),
                                over_own_bar=bool(xs.min() <= cxp <= xs.max()), gap_own_bar=int(own_top - ys.max() - 1)))
            place[f"s{k}_{cond}"] = per
            for p in per:
                if p["margin_svg"] < 1 or p["gap_other_label"] < 2 or p["gap_bar"] < 2 or not p["over_own_bar"]:
                    problems.append(f"placement s{k} {cond} label {p['i']}: {p}")
    # the lie: printed strings in the HTML, and pixel template matching (conflict label i looks like consistent label j)
    lie = {}
    for k in FS:
        want = {c: [lib.fmt_num(v, LANG) for v in make.LABELS[c]] for c in CONDS}
        got = {c: label_texts(htmls[c, k]) for c in CONDS}
        if got != want:
            problems.append(f"s{k} label strings {got} != {want}")
        g = {c: imgs[c, k].mean(axis=2) for c in CONDS}
        crops = {}
        for c in CONDS:
            ink = np.abs(imgs[c, k] - nonum).max(axis=2) > 24
            crops[c] = []
            for (a, b, cc, d) in boxes[k]:
                ys, xs = np.where(ink[a:b, cc:d])
                crops[c].append(g[c][a + ys.min():a + ys.max() + 1, cc + xs.min():cc + xs.max() + 1])
        match = []
        for i, ci in enumerate(crops["conflict"]):
            scores = []
            for cj in crops["consistent"]:
                hh, ww = max(ci.shape[0], cj.shape[0]), max(ci.shape[1], cj.shape[1])
                pa = np.full((hh, ww), 246.0)
                pb = np.full((hh, ww), 246.0)
                pa[:ci.shape[0], :ci.shape[1]] = ci
                pb[:cj.shape[0], :cj.shape[1]] = cj
                scores.append(float(np.abs(pa - pb).mean()))
            match.append(int(np.argmin(scores)))
        expect = [make.VISUAL.index(v) for v in make.LABELS["conflict"]]
        lie[f"s{k}"] = match
        if match != expect:
            problems.append(f"s{k}: conflict labels look like consistent labels {match}, expected {expect}")

    # contact sheet: rows = sizes, cols = consistent/conflict (448 px tiles); chart crops at 896 for clipping checks
    t = 448
    sheet = Image.new("RGB", (2 * t + 12, 4 * (t + 28)), "white")
    dr = ImageDraw.Draw(sheet)
    for r, k in enumerate(sorted(FS)):
        for c, cond in enumerate(CONDS):
            x, y = c * (t + 12), r * (t + 28)
            dr.text((x + 4, y + 6), f"s{k}  {fs_css(FS[k])}  cue_px={cpx[k]}  {cond}", fill=(20, 20, 20))
            sheet.paste(Image.open(CHECK / "448" / f"{img_name(cond, k)}.png"), (x, y + 28))
    sheet.save(CHECK / f"{SID}_sheet.png")
    cw, ch = W + 40, H + 30
    crops_img = Image.new("RGB", (2 * cw, 4 * ch), "white")
    for r, k in enumerate(sorted(FS)):
        for c, cond in enumerate(CONDS):
            crop = imgs[cond, k][y0 - 20:y0 - 20 + ch, x0 - 20:x0 - 20 + cw].astype(np.uint8)
            crops_img.paste(Image.fromarray(crop), (c * cw, r * ch))
    crops_img.save(CHECK / f"{SID}_chart_crops.png")

    sizes = []
    for k in sorted(FS):
        sizes.append({"k": k,
                      "param": f".val font-size {fs_css(FS[k])}" + (f"; Jan/Jun label x nudged {NUDGE[k]} px inward"
                                                                     if NUDGE.get(k) else ""),
                      "cue_px": cpx[k], "original": k == 2,
                      "consistent": str(lib.IMAGES / f"{img_name('consistent', k)}.png"),
                      "conflict": str(lib.IMAGES / f"{img_name('conflict', k)}.png")})
    notes.append(f"cue_px by k: {seq} (run-1 cue_px {r1_cpx}); targets 0.6/1/1.5/2 x {r1_cpx} = "
                 f"{[round(r1_cpx * f, 1) for f in (0.6, 1, 1.5, 2)]}; ratios {[round(v / cpx[2], 3) for v in seq]}")
    notes.append(f"run-1 max abs diff at original size: {run1_diff}; k=2 HTML is byte-identical to make.page() "
                 f"and to run 1's build HTML")
    notes.append(f"changed-pixel share outside the analytic label boxes dilated 3 px: {outside}; changed pixel counts "
                 f"{changed_n}; max abs diff vs run-1 nonumbers image outside each size's own label boxes: {ink_out}")
    notes.append(f"conflict label i best matches consistent label j (pixel template match) per k: {lie}; "
                 f"expected {[make.VISUAL.index(v) for v in make.LABELS['conflict']]} (values reversed, same as run 1)")
    worst = {key: dict(min_margin_svg=min(p["margin_svg"] for p in v), min_gap_other_label=min(p["gap_other_label"] for p in v),
                       min_gap_bar=min(p["gap_bar"] for p in v), gap_own_bar=sorted({p["gap_own_bar"] for p in v}))
             for key, v in place.items()}
    notes.append(f"placement (px, ink incl. anti-aliasing): {worst}")
    result = {"sid": SID, "ok": not problems, "script": str(Path(__file__).resolve()), "sizes": sizes,
              "identical_to_run1": identical, "outside_text_share": outside_share,
              "notes": " | ".join(problems + notes)}
    (OUT / f"{SID}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    main()
