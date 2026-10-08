"""Run 2 size sweep for s06_tv_thermometers: the big readout digits under the thermometer tubes at 4 sizes.

python3.12 run2/size_sweep/s06_tv_thermometers.py

Only the cue text changes. In make.py the readout is drawn by ONE canvas call inside card():
    if (label) txt(label, cx, 745, '700 64px ' + DIN, INK, 'center');     // cap height 0.712 em -> centred in the 68 px box
This script patches exactly that substring of the page HTML (asserted to occur once): the font size 64px -> fs and
the baseline 745 -> the baseline that keeps the cap height centred in the 68 px readout box (top 688), i.e. the same
rule make.py used for 64 px (722 + 0.356 * fs, = 745 at fs 64, so k=4 is byte-identical to run 1's HTML).
Everything else (tubes, mercury, notch, readout boxes, names, header, ticker, fonts.load calls) is untouched.

Writes only to run2/images/size/, run2/build/size/ (through common/lib.py render_html with redirected folders)
and run2/size_sweep/ (check images + s06_tv_thermometers.json). English, consistent + conflict only.
"""
import sys

sys.dont_write_bytecode = True          # importing make.py / lib must not drop __pycache__ into stimuli/ or common/

import importlib.util  # noqa: E402
import json  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from scipy import ndimage  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SID = "s06_tv_thermometers"
OUT = ROOT / "run2" / "size_sweep"
CHECK = OUT / "check"
RUN1 = ROOT / "images"

sys.path.insert(0, str(ROOT / "common"))
import lib  # noqa: E402

lib.IMAGES = ROOT / "run2" / "images" / "size"
lib.BUILD = ROOT / "run2" / "build" / "size"

_spec = importlib.util.spec_from_file_location("s06_make", ROOT / "stimuli" / SID / "make.py")
make = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(make)          # main loop is behind __name__ == "__main__": nothing is rendered or written

CONDS = ("consistent", "conflict")
LANG = "en"
FS0, BASE0 = 64, 745                    # original readout font size (px) and baseline (y)
BOX_TOP, BOX_H, BOX_HW = 688, 68, 76    # readout box: rr(cx - 76, 688, 152, 68, 14)
ORIG_CALL = f"if (label) txt(label, cx, {BASE0}, '700 {FS0}px ' + DIN, INK, 'center');"
FACTORS = {1: 0.4, 2: 0.6, 3: 0.8, 4: 1.0}          # k -> target share of the original digit height
FS = {k: round(FS0 * f) for k, f in FACTORS.items()}  # 26, 38, 51, 64 px
CX = [40 + i * (192 + 16) + 96 for i in range(4)]     # card centres, from card(): x0 + i*(cw+gap) + cw/2
PAPER = np.array([0xf2, 0xf1, 0xf6])
# from looking at all 8 renders, check/448, check/224 and the diff overlays (2026-10-07)
VISUAL_NOTES = ("visual check: all readouts sit centred inside their own unchanged white box under their own tube at every "
                "size, no clipping or overlap (largest text 76 px wide in a 152 px box); conflict shows -3,24,12,31 under "
                "Avlen,Berim,Covra,Dimel at every k = run 1's lie; at 448 all sizes legible; at 224 s1 digits are ~5 px "
                "tall and the minus of -3 is faint but present, s2+ clearly legible")


def baseline(fs):
    """make.py's rule: cap height 0.712 em centred in the 68 px box (gives 745 for 64 px)."""
    return round(BOX_TOP + BOX_H / 2 + 0.712 * fs / 2)


def html(cond, k):
    h = make.page(cond, LANG)
    assert h.count(ORIG_CALL) == 1, "readout call not found exactly once in make.py's HTML"
    return h.replace(ORIG_CALL, f"if (label) txt(label, cx, {baseline(FS[k])}, '700 {FS[k]}px ' + DIN, INK, 'center');")


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


INNER = 14   # box corner radius: text must stay inside the box minus its rounded corners


def text_mask(a):
    """Where readout text is drawn: inside each readout box (corners excluded), pixels that are not box PAPER."""
    m = np.zeros(a.shape[:2], bool)
    for cx in CX:
        y0, y1, x0, x1 = BOX_TOP + 2, BOX_TOP + BOX_H - 2, cx - BOX_HW + INNER, cx + BOX_HW - INNER
        sub = np.abs(a[y0:y1, x0:x1] - PAPER).max(axis=2) > 24
        # clipping/overflow guard: no text pixel on the border of the searched rectangle
        assert not (sub[0].any() or sub[-1].any() or sub[:, 0].any() or sub[:, -1].any()), f"text touches box edge at cx={cx}"
        m[y0:y1, x0:x1] = sub
    return m


def box_crop(a, i):
    """Box interior without its anti-aliased edge rows and rounded corners (those blend with the per-card background)."""
    cx = CX[i]
    return a[BOX_TOP + 2:BOX_TOP + BOX_H - 2, cx - BOX_HW + INNER:cx + BOX_HW - INNER]


def permutation_ok(cons, conf):
    """Conflict box i must show exactly the readout that consistent shows on the card whose value is CONFLICT[i]."""
    worst = 0
    for i, v in enumerate(make.CONFLICT):
        j = make.VISUAL.index(v)
        worst = max(worst, int(np.abs(box_crop(conf, i) - box_crop(cons, j)).max()))
    return worst


def text_bbox(a, i):
    m = text_mask(a)[BOX_TOP:BOX_TOP + BOX_H, CX[i] - BOX_HW:CX[i] + BOX_HW]
    ys, xs = np.where(m)
    return int(ys.min()) + BOX_TOP, int(ys.max()) + BOX_TOP, int(xs.min()) + CX[i] - BOX_HW, int(xs.max()) + CX[i] - BOX_HW


def main():
    for d in (lib.IMAGES, lib.BUILD, CHECK / "448", CHECK / "224", CHECK / "diff"):
        d.mkdir(parents=True, exist_ok=True)

    # ---- render ----
    imgs = {}
    for k in FACTORS:
        for cond in CONDS:
            p = lib.render_html(html(cond, k), img_name(cond, k))
            imgs[cond, k] = load(p)
            for res in (448, 224):
                Image.open(p).convert("RGB").resize((res, res), Image.BICUBIC).save(CHECK / str(res) / p.name)

    problems, notes = [], []

    # ---- 1. original size == run 1 ----
    assert html("consistent", 4) == make.page("consistent", LANG) and html("conflict", 4) == make.page("conflict", LANG)
    run1_diff = {}
    for cond in CONDS:
        r1 = load(RUN1 / f"{SID}_{cond}_{LANG}.png")
        run1_diff[cond] = int(np.abs(imgs[cond, 4] - r1).max())
    identical = all(v <= 2 for v in run1_diff.values())
    if not identical:
        problems.append(f"original-size re-render differs from run 1: max abs diff {run1_diff}")

    # ---- 2. changed pixels vs the original size lie inside the cue-text regions ----
    dil = np.ones((7, 7), bool)          # dilate text masks by 3 px
    outside, changed_n = {}, {}
    for k in FACTORS:
        for cond in CONDS:
            a, b = imgs[cond, 4], imgs[cond, k]
            changed = np.abs(a - b).max(axis=2) > 24
            region = ndimage.binary_dilation(text_mask(a) | text_mask(b), structure=dil)
            n = int(changed.sum())
            out = int((changed & ~region).sum())
            outside[f"s{k}_{cond}"] = round(out / n, 6) if n else 0.0
            changed_n[f"s{k}_{cond}"] = n
            # overlay: changed pixels red, region outline blue, on a faded copy
            faded = (255 - (255 - b) * 0.35).astype(np.uint8)
            faded[region & ~ndimage.binary_erosion(region)] = (40, 90, 230)
            faded[changed] = (230, 30, 30)
            Image.fromarray(faded).save(CHECK / "diff" / f"{img_name(cond, k)}_vs_s4.png")
    outside_share = max(outside.values())
    if outside_share > 0:
        problems.append(f"changed pixels outside cue-text regions: {outside}")
    # extra: nothing at all changes outside the four readout boxes
    boxes = np.zeros((896, 896), bool)
    for cx in CX:
        boxes[BOX_TOP:BOX_TOP + BOX_H, cx - BOX_HW:cx + BOX_HW] = True
    outside_boxes = {f"s{k}_{c}": int(np.abs(imgs[c, 4] - imgs[c, k])[~boxes].max()) for k in FACTORS for c in CONDS}

    # ---- 3. digit height per size, as collect.py measures it ----
    cpx = {k: cue_px(imgs["consistent", k], imgs["conflict", k]) for k in FACTORS}
    r1_cpx = cue_px(load(RUN1 / f"{SID}_consistent_{LANG}.png"), load(RUN1 / f"{SID}_conflict_{LANG}.png"))
    seq = [cpx[k] for k in sorted(cpx)]
    if not all(x < y for x, y in zip(seq, seq[1:])):
        problems.append(f"cue_px not strictly increasing: {seq}")
    if cpx[4] != r1_cpx:
        problems.append(f"cue_px at original size {cpx[4]} != run-1 {r1_cpx}")

    # ---- 4. same lie as run 1 (pixel-level permutation check) + text placement ----
    perm = {k: permutation_ok(imgs["consistent", k], imgs["conflict", k]) for k in FACTORS}
    perm_r1 = permutation_ok(load(RUN1 / f"{SID}_consistent_{LANG}.png"), load(RUN1 / f"{SID}_conflict_{LANG}.png"))
    if any(v > 2 for v in perm.values()) or perm_r1 > 2:
        problems.append(f"conflict permutation check failed: {perm}, run1 {perm_r1}")
    bbox = {f"s{k}_{c}": [text_bbox(imgs[c, k], i) for i in range(4)] for k in FACTORS for c in CONDS}

    # contact sheet for eyeballing: rows = sizes, cols = consistent/conflict (448 px tiles) + readout strip crops at 896
    t = 448
    sheet = Image.new("RGB", (2 * t + 12, 4 * (t + 28)), "white")
    dr = ImageDraw.Draw(sheet)
    for r, k in enumerate(sorted(FACTORS)):
        for c, cond in enumerate(CONDS):
            x, y = c * (t + 12), r * (t + 28)
            dr.text((x + 4, y + 6), f"s{k}  {FS[k]}px  cue_px={cpx[k]}  {cond}", fill=(20, 20, 20))
            sheet.paste(Image.open(CHECK / "448" / f"{img_name(cond, k)}.png"), (x, y + 28))
    sheet.save(CHECK / f"{SID}_sheet.png")
    strip = Image.new("RGB", (896, 8 * 90), "white")
    for r, k in enumerate(sorted(FACTORS)):
        for c, cond in enumerate(CONDS):
            crop = Image.fromarray(imgs[cond, k][BOX_TOP - 11:BOX_TOP - 11 + 90].astype(np.uint8))   # rows 677..766
            strip.paste(crop, (0, (2 * r + c) * 90))
    strip.save(CHECK / f"{SID}_readout_strips.png")

    sizes = []
    for k in sorted(FACTORS):
        sizes.append({"k": k,
                      "param": f"readout font-size {FS[k]}px (canvas '700 {FS[k]}px DIN Condensed'), baseline y={baseline(FS[k])}",
                      "cue_px": cpx[k], "original": k == 4,
                      "consistent": str(lib.IMAGES / f"{img_name('consistent', k)}.png"),
                      "conflict": str(lib.IMAGES / f"{img_name('conflict', k)}.png")})
    notes.append(f"cue_px by k: {seq} (run-1 cue_px {r1_cpx}); targets 0.4/0.6/0.8/1.0 x {r1_cpx} = "
                 f"{[round(r1_cpx * f, 1) for f in FACTORS.values()]}; ratios {[round(v / cpx[4], 3) for v in seq]}")
    notes.append(f"run-1 max abs diff at original size: {run1_diff}; k=4 HTML is byte-identical to make.page()")
    notes.append(f"changed-pixel share outside dilated (3 px) text masks: {outside}; max abs diff outside the 4 readout boxes: "
                 f"{outside_boxes}; changed pixel counts {changed_n}")
    notes.append(f"conflict box i == consistent box of value CONFLICT[i] (max abs diff) per k: {perm}, run 1: {perm_r1}")
    notes.append("baseline re-centred per size with make.py's own rule (722 + 0.356*fs) so the smaller numbers stay "
                 "centred in the unchanged readout boxes")
    notes.append(f"text bboxes (y0,y1,x0,x1) per card: {bbox}")
    notes.append(VISUAL_NOTES)
    result = {"sid": SID, "ok": not problems, "script": str(Path(__file__).resolve()), "sizes": sizes,
              "identical_to_run1": identical, "outside_text_share": outside_share,
              "notes": " | ".join(problems + notes)}
    (OUT / f"{SID}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    main()
