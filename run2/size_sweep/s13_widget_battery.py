"""Run-2 cue-size sweep for s13_widget_battery (radial battery rings, centre percentages = cue text).

Only the cue text changes between sizes:
  * size  = the `.pct` CSS rule's `font-size: 40px` (make.py page(), the one place the centre-label size is set)
  * place = the centre <text>'s own baseline `y="115.0"` (SVG coords of the 164-px ring), nudged up only for the
            two larger sizes so the label stays clear of the ring stroke (inner edge r = 64) and the device glyph.
Rings, glyphs, device names, app grid, dock: untouched. English only, consistent + conflict only.

The ring interior caps the label: a 2-digit label is 82 px wide at 40 px, the interior is 128 px across and the
device glyph sits above the label, so 1.8x (148 px wide) cannot fit at all; 1.4x leaves ~3 px and 1.35x (54 px)
~4.5 px to the ring, which at the model's 224-px input fuses "88%" with the dark Phone ring. k=4 is therefore 1.3x
(52 px, ~6 px clearance at 896 = a visible gap at 224) and k=3 sits halfway between 1x and that (46 px).

Writes run2/images/size/<sid>_<cond>_en_s<k>.png (+ HTML in run2/build/size/), 448/224 bicubic previews and diff
overlays in run2/size_sweep/check/, and run2/size_sweep/s13_widget_battery.json.
Run: python3.12 run2/size_sweep/s13_widget_battery.py
"""
import importlib.util
import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]            # .../chart-conflict
SID = "s13_widget_battery"
LANG = "en"
CONDS = ("consistent", "conflict")
HERE = ROOT / "run2" / "size_sweep"
CHECK = HERE / "check"

sys.path.insert(0, str(ROOT / "common"))
import lib  # noqa: E402

lib.IMAGES = ROOT / "run2" / "images" / "size"          # render_html reads these globals at call time
lib.BUILD = ROOT / "run2" / "build" / "size"

_spec = importlib.util.spec_from_file_location(f"{SID}_make", ROOT / "stimuli" / SID / "make.py")
mk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mk)                            # __main__ guard: nothing is rendered or written here

# ---------- the sweep ----------
ORIG_FONT, ORIG_Y = 40, 115.0                            # make.py: .pct font-size 40px, <text y = s/2 + 33>
SIZES = [  # k, font-size px, baseline y (SVG units of the 164-px ring)
    (1, 24, 115.0),    # 0.6x, original baseline
    (2, 40, 115.0),    # 1x = run 1, HTML not touched at all
    (3, 46, 107.0),    # 1.15x, nudged up 8 px to centre it between glyph and ring (at y=115: ~7 px to the ring)
    (4, 52, 106.5),    # 1.3x = largest that keeps a visible gap to ring and glyph at 224 px; nudged up 8.5 px
]
CSS_OLD = "font-size: 40px; font-weight: 700; fill: #1d1e29;"   # unique to the .pct rule
TXT_OLD = 'y="115.0" text-anchor="middle" class="pct"'          # the 4 centre labels


def html_for(cond, font, y):
    html = mk.page(cond, LANG)
    assert html.count(CSS_OLD) == 1 and html.count(TXT_OLD) == 4, "make.py changed, patch targets not found"
    if font != ORIG_FONT:
        html = html.replace(CSS_OLD, CSS_OLD.replace("40px", f"{font}px"))
    if y != ORIG_Y:
        html = html.replace(TXT_OLD, TXT_OLD.replace("115.0", f"{y:.1f}"))
    return html


def img_name(cond, k):
    return f"{SID}_{cond}_{LANG}_s{k}"


def load(p):
    return np.asarray(Image.open(p).convert("RGB")).astype(int)


# ---------- geometry of the page (from make.py's CSS; verified on the run-1 images) ----------
RING_CX = [157 + 194 * i for i in range(4)]   # widget left 40 + rings padding 20 + (194-164)/2 + 82 + 194 i
RING_CY = 223                                 # widget top 70 + 24 padding + title + 14 margin -> svg top 141, +82
R_IN = 64.0                                   # stroke inner edge: r 73 - 18/2
YY, XX = np.mgrid[0:lib.SIZE, 0:lib.SIZE]


def ring_dist():
    """Per-pixel distance to the nearest ring centre and the index of that ring."""
    d = np.stack([np.hypot(XX + 0.5 - cx, YY + 0.5 - RING_CY) for cx in RING_CX])
    return d.min(axis=0), d.argmin(axis=0)


RDIST, RIDX = ring_dist()
NONUM = load(ROOT / "images" / f"{SID}_nonumbers_{LANG}.png")    # run 1, same drawing with empty centre text
GLYPH_BOTTOM = []                                                # lowest glyph-ink row per ring (run-1 nonumbers)
for i, cx in enumerate(RING_CX):
    dark = (NONUM.mean(axis=2) < 200) & (RDIST < R_IN - 1) & (RIDX == i) & (YY < RING_CY)
    GLYPH_BOTTOM.append(int(np.where(dark.any(axis=1))[0].max()))
LABEL_ZONE = (RDIST < R_IN - 0.5) & (YY > max(GLYPH_BOTTOM) + 1)   # ring interior below the device glyph


def text_ink(img):
    """Pixels where the cue text is drawn = differs from the run-1 no-numbers image (whole widget)."""
    return np.abs(img - NONUM).max(axis=2) > 24


def cue_px(a, b):
    """Exact copy of common/collect.py cue_px(), applied to a given consistent/conflict pair."""
    changed = np.abs(a - b).max(axis=2) > 24
    blobs, _ = ndimage.label(ndimage.binary_dilation(changed, structure=np.ones((3, 15), bool)))
    hs = []
    for sl in ndimage.find_objects(blobs):
        rows = np.where(changed[sl].any(axis=1))[0]
        if len(rows) and changed[sl].sum() >= 20:
            hs.append(int(rows[-1] - rows[0] + 1))
    return int(np.median(hs)) if hs else 0


def clearance(img):
    """Min clearance (px) of the text ink to the ring stroke inner edge and to the device glyph, over the 4 rings."""
    ink = text_ink(img)
    ring_c, glyph_c = [], []
    for i in range(4):
        m = ink & (RIDX == i) & (RDIST < R_IN + 10) & (YY > RING_CY - 60)
        ring_c.append(R_IN - RDIST[m].max())
        glyph_c.append(np.where(m.any(axis=1))[0].min() - GLYPH_BOTTOM[i] - 1)
    return round(float(min(ring_c)), 1), int(min(glyph_c))


def labels(html):
    return re.findall(r'class="pct">(.*?)</text>', html)


def main():
    lib.IMAGES.mkdir(parents=True, exist_ok=True)
    lib.BUILD.mkdir(parents=True, exist_ok=True)
    for res in (448, 224):
        (CHECK / str(res)).mkdir(parents=True, exist_ok=True)
    (CHECK / "diff").mkdir(parents=True, exist_ok=True)

    imgs, notes, ok = {}, [], True
    expect = {"consistent": ["88%", "9%", "54%", "31%"], "conflict": ["9%", "88%", "31%", "54%"]}
    for k, font, y in SIZES:
        for cond in CONDS:
            html = html_for(cond, font, y)
            assert labels(html) == expect[cond], (cond, labels(html))       # same lie as run 1
            out = lib.render_html(html, img_name(cond, k))
            imgs[(k, cond)] = load(out)
            im = Image.open(out).convert("RGB")
            for res in (448, 224):
                im.resize((res, res), Image.BICUBIC).save(CHECK / str(res) / out.name)

    # 1. original size == run 1
    run1_diff = {c: int(np.abs(imgs[(2, c)] - load(ROOT / "images" / f"{SID}_{c}_{LANG}.png")).max()) for c in CONDS}
    identical = all(v <= 2 for v in run1_diff.values())
    ok &= identical
    notes.append(f"s2 vs run-1 max abs diff {run1_diff}")

    # 2. changed pixels vs the original-size render must lie in the cue-text regions
    #    region = (text ink of size k  U  text ink of size 2) restricted to the ring interior below the glyph,
    #             U where consistent and conflict differ at that size, dilated by 3 px
    outside_max, sizes = 0.0, []
    for k, font, y in SIZES:
        cd = (np.abs(imgs[(k, "consistent")] - imgs[(k, "conflict")]).max(axis=2) > 24)
        shares = {}
        for cond in CONDS:
            a, o = imgs[(k, cond)], imgs[(2, cond)]
            changed = np.abs(a - o).max(axis=2) > 24
            region = ((text_ink(a) | text_ink(o)) & LABEL_ZONE) | (cd & LABEL_ZONE)
            region = ndimage.binary_dilation(region, iterations=3)
            n = int(changed.sum())
            shares[cond] = float((changed & ~region).sum() / n) if n else 0.0
            if k != 2:
                ov = (255 - (255 - a) * 0.35).astype(np.uint8)
                ov[changed & region] = (230, 30, 30)
                ov[changed & ~region] = (20, 120, 255)
                Image.fromarray(ov).save(CHECK / "diff" / f"{img_name(cond, k)}_vs_s2.png")
        outside_max = max(outside_max, *shares.values())
        px = cue_px(imgs[(k, "consistent")], imgs[(k, "conflict")])
        rc = {c: clearance(imgs[(k, c)]) for c in CONDS}
        ring_min = min(v[0] for v in rc.values())
        glyph_min = min(v[1] for v in rc.values())
        notes.append(f"s{k}: font {font}px y {y:g} cue_px {px} ring clearance {ring_min} px glyph gap {glyph_min} px "
                     f"outside share {max(shares.values()):.4f}")
        if ring_min < 5 or glyph_min < 5:                # >= 1.25 px at the 224-px model input
            ok = False
            notes.append(f"s{k}: label too close to ring/glyph")
        param = f"font-size {font}px (.pct)" + (f", baseline y {y:g} (was 115)" if y != ORIG_Y else "")
        sizes.append({"k": k, "param": param, "cue_px": px, "original": k == 2,
                      "consistent": str(lib.IMAGES / f"{img_name('consistent', k)}.png"),
                      "conflict": str(lib.IMAGES / f"{img_name('conflict', k)}.png")})
    ok &= outside_max <= 0.001

    # 3. cue_px distinct and increasing with k
    pxs = [s["cue_px"] for s in sizes]
    mono = all(b > a for a, b in zip(pxs, pxs[1:]))
    ok &= mono
    notes.append(f"cue_px {pxs} {'strictly increasing' if mono else 'NOT increasing'}")

    result = {"sid": SID, "ok": bool(ok), "script": str(Path(__file__).resolve()), "sizes": sizes,
              "identical_to_run1": bool(identical), "outside_text_share": round(outside_max, 6),
              "notes": "; ".join(notes)}
    (HERE / f"{SID}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
