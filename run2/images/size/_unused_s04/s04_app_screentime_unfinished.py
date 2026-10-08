"""Run 2 size sweep for s04_app_screentime: the per-app duration labels ("2h 30m") at 4 sizes.

python3.12 run2/size_sweep/s04_app_screentime.py

Where make.py sets the cue size: ONE CSS rule in page(),
    .time { width: 190px; flex: none; text-align: right; font-size: 28px; font-weight: 700; ... }
and each label is <span class="time">2h 30m</span> inside a baseline-aligned flex row (.line) of app name, time, chevron.
Changing .time's font-size directly would change the .line box (its height and shared baseline) and so move the app
names, bars and chevrons. So for k != 2 this script leaves the .time box at 28 px and wraps the label text in an inner
<span class="cue"> that carries the new size:
    .time .cue { font-size: FSpx; line-height: 0; position: relative; top: DYpx; }
  - line-height 0: the inner span adds a zero-height inline box (inside the 28 px strut), so the line box, the shared
    baseline and every other element keep their run-1 position; the glyphs simply overflow the line box (visible).
  - top DY: keeps the label's ink centred where make.py put it. In run 1 the 24 px ink (incl. the 'h' ascender) sits
    exactly midway between the row's separator line and its bar (19-20 px clear on each side); a bigger label grown
    only upwards from the baseline would cross the separator at 2x, so the label grows equally up and down instead.
    DY = round((INK_RATIO * fs - INK0) / 2), INK_RATIO measured from Chrome's own ink heights (see notes).
  - .time width 190 -> WIDE px (box only, right edge unchanged at x=806): at 2x the label is ~210 px wide, and an
    over-long line in a right-aligned box start-aligns and would spill right into the chevron. .app is flex:1 and
    left-aligned, so its narrower box moves no pixel.
k = 2 is NOT patched: it renders make.page() byte for byte, so it is the run-1 stimulus.

Writes only to run2/images/size/, run2/build/size/ (through common/lib.py render_html with redirected folders)
and run2/size_sweep/ (check images + s04_app_screentime.json). English, consistent + conflict only.
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
SID = "s04_app_screentime"
OUT = ROOT / "run2" / "size_sweep"
CHECK = OUT / "check"
RUN1 = ROOT / "images"

sys.path.insert(0, str(ROOT / "common"))
import lib  # noqa: E402

lib.IMAGES = ROOT / "run2" / "images" / "size"
lib.BUILD = ROOT / "run2" / "build" / "size"

_spec = importlib.util.spec_from_file_location("s04_make", ROOT / "stimuli" / SID / "make.py")
make = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(make)          # main loop is behind __name__ == "__main__": nothing is rendered or written

CONDS = ("consistent", "conflict")
LANG = "en"
FS0 = 28                                 # .time font-size in make.py (px)
FACTORS = {1: 0.6, 2: 1.0, 3: 1.5, 4: 2.0}           # k -> target share of the original digit height
FS = {k: round(FS0 * f, 1) for k, f in FACTORS.items()}   # 16.8, 28, 42, 56 px
INK0 = 24                                # run-1 label ink height incl. 'h' ascender (rows 396..419 in row 1)
INK_RATIO = float("nan")                 # set after the trial render (see notes)
WIDE = 300                               # .time box width for patched sizes (was 190)
TIME_RULE = ".time { width: 190px; flex: none; text-align: right; font-size: 28px;"
TIME_SPAN = re.compile(r'<span class="time">([^<]*)</span>')

# layout of the list (from make.py CSS, checked against the run-1 pixels in check_layout())
ROW0, ROW_H, N = 376, 88, 5              # first row top, row height, rows
SEP = [ROW0 + ROW_H * i for i in range(1, N)]          # 1 px separator (border-top of .main) of rows 2..5
BAR_TOP = [ROW0 + 63 + ROW_H * i for i in range(N)]    # 16 px bars: rows 439..454, 527..542, ...
BAR_H = 16
TIME_RIGHT = 806                         # .time right edge (= chevron box left edge)
APP_MAX_X, CHEV_MIN_X = 227, 828         # app-name ink right edge, chevron ink left edge (run 1)
ZONE_X = (300, 818)                      # label column: right of every app name, left of the chevrons


def dy(fs):
    if fs == FS0:
        return 0
    return int(round((INK_RATIO * fs - INK0) / 2))


def html(cond, k, dy_px=None):
    h = make.page(cond, LANG)
    if k == 2:
        return h
    fs = FS[k]
    d = dy(fs) if dy_px is None else dy_px
    assert h.count(TIME_RULE) == 1, ".time rule not found exactly once in make.py's HTML"
    assert len(TIME_SPAN.findall(h)) == N, "expected 5 time spans"
    h = h.replace(TIME_RULE, TIME_RULE.replace("width: 190px;", f"width: {WIDE}px;"))
    h = h.replace("</style>", f"  .time .cue {{ font-size: {fs:g}px; line-height: 0; position: relative; top: {d}px; }}\n</style>", 1)
    return TIME_SPAN.sub(r'<span class="time"><span class="cue">\1</span></span>', h)


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


NONUM = None


def text_mask(a):
    """Where the cue text is drawn: in the label column, pixels that differ from run 1's nonumbers image (same page
    with every time label blanked, all other pixels identical to consistent: asserted in check_layout())."""
    m = np.abs(a - NONUM).max(axis=2) > 24
    z = np.zeros_like(m)
    z[ROW0:ROW0 + N * ROW_H, ZONE_X[0]:ZONE_X[1]] = True
    return m & z


def label_boxes(a):
    """Per row: ink bbox (y0, y1, x0, x1) of the cue text, from text_mask (any pixel > 24 from the blank page)."""
    m = text_mask(a)
    out = []
    for i in range(N):
        y0 = ROW0 + ROW_H * i
        ys, xs = np.where(m[y0:y0 + ROW_H])
        out.append((int(ys.min()) + y0, int(ys.max()) + y0, int(xs.min()), int(xs.max())))
    return out


def main():
    global NONUM
    for d in (lib.IMAGES, lib.BUILD, CHECK / "448", CHECK / "224", CHECK / "diff"):
        d.mkdir(parents=True, exist_ok=True)
    NONUM = load(RUN1 / f"{SID}_nonumbers_{LANG}.png")
    trial = "--trial" in sys.argv
    imgs = {}
    for k in FACTORS:
        for cond in CONDS:
            p = lib.render_html(html(cond, k, 0 if trial else None), img_name(cond, k))
            imgs[cond, k] = load(p)
    if trial:
        for k in FACTORS:
            for cond in CONDS:
                print(k, FS[k], cond, label_boxes(imgs[cond, k]),
                      "cue_px", cue_px(imgs["consistent", k], imgs["conflict", k]) if cond == "conflict" else "")
        return


if __name__ == "__main__":
    main()
