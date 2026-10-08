"""Run-2 cue-size sweep for s14_spreadsheet_databars (English, consistent + conflict only).

Where the cue size lives: stimuli/s14_spreadsheet_databars/make.py, page() CSS rule
    .val { position: absolute; right: 18px; top: 50%; transform: translateY(-50%); font-size: 26px; font-weight: 700; ... }
The same .val class is also used by the Total cell ("1,800", <td class="db totv">), which is NOT a cue and must not change.
So the sweep leaves that rule alone and appends ONE override that only reaches the five region value spans:
    td.db:not(.totv) .val { font-size: <N>px; }
(specificity 0,3,1 > 0,1,0). Nothing else in the HTML changes: bars, row heights, right offset (18 px), vertical centring
(top 50% + translateY(-50%)) and every other string are untouched. k=2 is the unpatched run-1 HTML.

Outputs (only inside the allowed folders):
    run2/images/size/<sid>_<cond>_en_s<k>.png   run2/build/size/<same>.html
    run2/size_sweep/check/{448,224}/...png, check/diff/...png, check/*sheet*.png
    run2/size_sweep/s14_spreadsheet_databars.json
Run: python3.12 run2/size_sweep/s14_spreadsheet_databars.py
"""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
SID = "s14_spreadsheet_databars"
CONDS = ("consistent", "conflict")
LANG = "en"
OUT = ROOT / "run2" / "size_sweep"
CHECK = OUT / "check"
IMG_DIR = ROOT / "run2" / "images" / "size"
BUILD_DIR = ROOT / "run2" / "build" / "size"

sys.path.insert(0, str(ROOT / "common"))
import lib  # noqa: E402

lib.IMAGES = IMG_DIR          # render_html reads these globals at call time
lib.BUILD = BUILD_DIR

_spec = importlib.util.spec_from_file_location(f"{SID}_make", ROOT / "stimuli" / SID / "make.py")
mk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mk)   # safe: make.py's render loop is behind __main__

ORIG_FS = 26                                   # .val font-size in make.py (digit height measured 20 px at 896)
ORIG_RULE = "font-size: 26px; font-weight: 700;\n          color: #202124; font-variant-numeric: tabular-nums; }}"
# k -> font-size of the five region value spans (None = original HTML). Measured cue_px = 12 / 20 / 28 / 36 px
# = 0.6x / 1x / 1.4x / 1.8x of the 20 px run-1 digit height (15.6 px gave 13, so k=1 uses 15 px).
# 46.8 px still leaves >= 11 px above/below the digits in the 59 px cells and >= 42 px between the East bar and its label.
FONT = {1: 15, 2: None, 3: 36.4, 4: 46.8}

# ---------- geometry of the cue cells (column B, rows 4..8), read off the run-1 image ----------
COLB_X0, COLB_X1 = 243, 680                    # column-B interior (border pixels at x=242 and x=680)
ROWS = [(372, 431), (432, 491), (492, 551), (552, 611), (612, 671)]   # interiors of rows 4..8 (half-open)
BAR_X0 = COLB_X0 + mk.BAR_LEFT                 # 255
BAR_END = [BAR_X0 + mk.bar_px(v) for v in mk.VISUAL]                 # exclusive right edge of each data bar


def image_name(cond, k):
    return f"{SID}_{cond}_{LANG}_s{k}"


def html_for(cond, k):
    base = mk.page(cond, LANG)
    fs = FONT[k]
    if fs is None:
        return base
    css = f"  td.db:not(.totv) .val {{ font-size: {fs:g}px; }}\n"
    assert base.count("</style>") == 1
    out = base.replace("</style>", css + "</style>")
    assert out.replace(css, "") == base          # the only change is the one override line
    return out


def load(p):
    return np.asarray(Image.open(p).convert("RGB")).astype(int)


def cue_px_pair(a, b):
    """common/collect.py cue_px(), verbatim, on an arbitrary consistent/conflict pair."""
    changed = np.abs(a - b).max(axis=2) > 24
    blobs, _ = ndimage.label(ndimage.binary_dilation(changed, structure=np.ones((3, 15), bool)))
    hs = []
    for sl in ndimage.find_objects(blobs):
        rows = np.where(changed[sl].any(axis=1))[0]
        if len(rows) and changed[sl].sum() >= 20:
            hs.append(int(rows[-1] - rows[0] + 1))
    return int(np.median(hs)) if hs else 0


def text_pixels(img, blank):
    """Where the cue text is drawn: pixels differing from the run-1 nonumbers image (same drawing, value strings blank),
    looked for only in column B of rows 4..8 to the right of each bar. Returns (mask, per-row bbox, stray pixel count)."""
    d = np.abs(img - blank).max(axis=2)
    mask = np.zeros(d.shape, bool)
    boxes, stray = [], 0
    for (y0, y1), bx in zip(ROWS, BAR_END):
        zone = np.zeros(d.shape, bool)
        zone[y0:y1, bx + 2:COLB_X1] = True
        m = (d > 8) & zone
        mask |= m
        # anything that differs in the rest of column B of this row (bars / left padding) would be a non-text change
        rest = np.zeros(d.shape, bool)
        rest[y0:y1, COLB_X0:COLB_X1] = True
        stray += int(((d > 24) & rest & ~zone).sum())
        ys, xs = np.where((d > 24) & zone)
        boxes.append(None if not len(ys) else (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())))
    return mask, boxes, stray


def main():
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    for sub in ("448", "224", "diff"):
        (CHECK / sub).mkdir(parents=True, exist_ok=True)

    # the source must still be the run-1 source: unpatched HTML == run-1 build HTML, and the rule we override exists
    for cond in CONDS:
        assert mk.page(cond, LANG) == (ROOT / "build" / f"{lib.name(SID, cond, LANG)}.html").read_text(encoding="utf-8"), cond
    assert ".val {{ position: absolute; right: {NUM_RIGHT}px;" in Path(_spec.origin).read_text() and \
           ORIG_RULE in Path(_spec.origin).read_text(), "make.py .val rule changed"
    # the lie is the run-1 lie: same permutation as spec.json (the sweep only changes font-size, never the strings)
    sj = json.loads((ROOT / "stimuli" / SID / "spec.json").read_text(encoding="utf-8"))
    assert mk.LABELS["conflict"] == sj["data"]["conflict_labels"] and mk.LABELS["consistent"] == sj["data"]["visual"]
    for k in FONT:
        for cond in CONDS:
            h = html_for(cond, k)
            assert all(f'<span class="val">{v}</span>' in h for v in mk.LABELS[cond]), (cond, k)

    paths = {}
    for k in sorted(FONT):
        for cond in CONDS:
            paths[cond, k] = lib.render_html(html_for(cond, k), image_name(cond, k))

    img = {key: load(p) for key, p in paths.items()}
    blank = load(ROOT / "images" / f"{lib.name(SID, 'nonumbers', LANG)}.png")
    notes = []

    # 1. original size vs run 1
    run1_diff = {}
    for cond in CONDS:
        r1 = load(ROOT / "images" / f"{lib.name(SID, cond, LANG)}.png")
        run1_diff[cond] = int(np.abs(img[cond, 2] - r1).max())
    identical = all(v <= 2 for v in run1_diff.values())

    # text masks + per-label boxes
    tmask, boxes, stray = {}, {}, {}
    for key in img:
        tmask[key], boxes[key], stray[key] = text_pixels(img[key], blank)

    # 2. changed pixels vs the original-size render must sit inside the (dilated) cue-text regions
    outside = {}
    for k in sorted(FONT):
        for cond in CONDS:
            changed = np.abs(img[cond, k] - img[cond, 2]).max(axis=2) > 24
            region = ndimage.binary_dilation(tmask[cond, k] | tmask[cond, 2], iterations=3)
            n = int(changed.sum())
            outside[cond, k] = (float((changed & ~region).sum() / n) if n else 0.0, n)
            ov = (255 - (255 - img[cond, k]) * 0.35).astype(np.uint8)
            ov[changed & region] = (230, 30, 30)
            ov[changed & ~region] = (30, 30, 230)
            Image.fromarray(ov).save(CHECK / "diff" / f"{image_name(cond, k)}_vs_s2.png")
    outside_share = max(v[0] for v in outside.values())

    # 3. digit height like collect.py, per size
    cue = {k: cue_px_pair(img["consistent", k], img["conflict", k]) for k in sorted(FONT)}
    cue_ok = all(cue[a] < cue[b] for a, b in zip(sorted(FONT), sorted(FONT)[1:]))

    # geometry checks (clipping / overlap): every label inside its own row, right of its own bar, nothing stray
    geom = []
    for (cond, k), bb in boxes.items():
        for i, (b, (y0, y1), bx) in enumerate(zip(bb, ROWS, BAR_END)):
            if b is None:
                geom.append(f"{cond} s{k} row{4 + i}: no text found")
                continue
            x0, yt, x1, yb = b
            if yt - y0 < 3 or (y1 - 1) - yb < 3:
                geom.append(f"{cond} s{k} row{4 + i}: text within 3 px of the row border ({yt}-{yb} in {y0}-{y1 - 1})")
            if x0 - bx < 10:
                geom.append(f"{cond} s{k} row{4 + i}: text {x0 - bx} px from the bar end")
            if COLB_X1 - 1 - x1 < 3:
                geom.append(f"{cond} s{k} row{4 + i}: text touches the right border")
        if stray[cond, k]:
            geom.append(f"{cond} s{k}: {stray[cond, k]} changed px in column B outside the text zones")

    # downscales the model sees + tiled sheets at native pixels for viewing
    for key, p in paths.items():
        im = Image.open(p).convert("RGB")
        for res in (448, 224):
            im.resize((res, res), Image.BICUBIC).save(CHECK / str(res) / p.name)
    for cond in CONDS:
        sh = Image.new("RGB", (896, 896), "white")
        for j, k in enumerate(sorted(FONT)):
            sh.paste(Image.open(CHECK / "448" / f"{image_name(cond, k)}.png"), ((j % 2) * 448, (j // 2) * 448))
        sh.save(CHECK / f"sheet448_{cond}.png")
    sh = Image.new("RGB", (896, 448), "white")
    for i, cond in enumerate(CONDS):
        for j, k in enumerate(sorted(FONT)):
            sh.paste(Image.open(CHECK / "224" / f"{image_name(cond, k)}.png"), (j * 224, i * 224))
    sh.save(CHECK / "sheet224.png")
    crop = (230, 360, 690, 680)                                   # column B rows 3..8 at full resolution
    cw, chh = crop[2] - crop[0], crop[3] - crop[1]
    sh = Image.new("RGB", (cw * 2 + 10, chh * 4 + 30), "white")
    for i, cond in enumerate(CONDS):
        for j, k in enumerate(sorted(FONT)):
            sh.paste(Image.open(paths[cond, k]).crop(crop), (i * (cw + 10), j * (chh + 10)))
    sh.save(CHECK / "crops_full.png")

    for cond in CONDS:
        if run1_diff[cond] > 2:
            notes.append(f"original-size {cond} differs from run 1 by max {run1_diff[cond]}")
    notes += geom
    ok = identical and cue_ok and outside_share == 0.0 and not geom and len(set(cue.values())) == 4
    min_gap_bar = min(b[i][0] - BAR_END[i] for b in boxes.values() for i in range(5))
    min_gap_row = min(min(b[i][1] - ROWS[i][0], ROWS[i][1] - 1 - b[i][3]) for b in boxes.values() for i in range(5))
    notes.insert(0, (
        "Cue size = make.py page() CSS '.val { ... font-size: 26px }'; .val is shared with the Total cell (1,800), so the "
        "sweep appends one override 'td.db:not(.totv) .val { font-size: Npx }' that reaches only the 5 region values "
        "(Total, bars, row heights, right:18px alignment and vertical centring untouched; no position nudge needed). "
        f"k=2 is the unpatched HTML: identical to run 1 (max abs diff {run1_diff}); unpatched HTML also equals build/*.html. "
        f"cue_px {[cue[k] for k in sorted(FONT)]}. Changed px vs s2 all inside the dilated text mask (3 px). "
        f"Closest label-to-bar gap {min_gap_bar} px, closest label-to-row-border {min_gap_row} px. "
        "Conflict permutation unchanged at every size (N260 S330 E180 W420 C610). At 224 px the s1 labels are ~3 px tall "
        "and no longer legible (expected at the small end); s2-s4 readable at 224."))

    sizes = []
    for k in sorted(FONT):
        fs = FONT[k] if FONT[k] is not None else ORIG_FS
        sizes.append({
            "k": k,
            "param": f"font-size {fs:g}px (.val in region rows 4-8 only{'; original, unpatched HTML' if FONT[k] is None else ''})",
            "cue_px": cue[k],
            "original": FONT[k] is None,
            "consistent": str(paths["consistent", k]),
            "conflict": str(paths["conflict", k]),
        })
    res = {
        "sid": SID,
        "ok": ok,
        "script": str(Path(__file__).resolve()),
        "sizes": sizes,
        "identical_to_run1": identical,
        "outside_text_share": round(outside_share, 6),
        "notes": "; ".join(notes),
        "_details": {
            "run1_max_abs_diff": run1_diff,
            "changed_px_vs_s2": {f"{c}_s{k}": v[1] for (c, k), v in outside.items()},
            "outside_share": {f"{c}_s{k}": round(v[0], 6) for (c, k), v in outside.items()},
            "label_boxes_x0y0x1y1": {f"{c}_s{k}": b for (c, k), b in boxes.items()},
            "bar_end_x": BAR_END,
        },
    }
    return res


if __name__ == "__main__":
    r = main()
    details = r.pop("_details")
    (OUT / f"{SID}.json").write_text(json.dumps(r, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(r, indent=1, ensure_ascii=False))
    print(json.dumps(details))
