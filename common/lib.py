"""Shared helpers for every stimulus' make.py.

Typical make.py:
    from lib import render_html, finish, CONDS, LANGS
    for cond in CONDS:
        for lang in LANGS:
            render_html(page(cond, lang), name(SID, cond, lang))
    finish(SPEC)          # validates spec.json, writes 448/224 previews, diff overlays, 2x2 sheet
"""
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scoring import match  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BUILD, IMAGES, CHECK, SHEETS = ROOT / "build", ROOT / "images", ROOT / "check", ROOT / "sheets"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SIZE = 896
CONDS = ("consistent", "conflict", "nonumbers")   # nonumbers = same drawing, cue strings removed
LANGS = ("en", "tr")
KINDS = {"trend", "argmax", "argmin", "compare", "threshold", "read_value", "count", "relation"}
MECHANISMS = {"label": False, "readout": False, "axis": True, "legend": True}   # -> conflict_has_truth


def name(sid, cond, lang):
    return f"{sid}_{cond}_{lang}"


# ---------- number formatting ----------
def fmt_num(x, lang, decimals=0, sign=False):
    s = f"{abs(x):.{decimals}f}"
    if lang == "tr":
        s = s.replace(".", ",")
    if x < 0:
        s = "−" + s          # real minus sign, not a hyphen
    elif sign and x > 0:
        s = "+" + s
    return s


def fmt_pct(x, lang, decimals=0, sign=False):
    n = fmt_num(abs(x), lang, decimals)
    pre = "−" if x < 0 else ("+" if sign and x > 0 else "")
    return f"{pre}%{n}" if lang == "tr" else f"{pre}{n}%"


# ---------- rendering ----------
def render_html(html, image_name, size=SIZE):
    """Write build/<image_name>.html and screenshot it to images/<image_name>.png (size x size)."""
    BUILD.mkdir(exist_ok=True)
    IMAGES.mkdir(exist_ok=True)
    src, out = BUILD / f"{image_name}.html", IMAGES / f"{image_name}.png"
    src.write_text(html, encoding="utf-8")
    # Own throwaway profile, and never wait for Chrome to exit: a headless Chrome on the user's real profile once hung for
    # 25 h and blocked their Chrome (2026-10-05); with a fresh profile Chrome writes the PNG in ~1 s but then keeps running.
    # So: wait until the PNG exists and its size is stable, then kill everything started with this profile.
    out.unlink(missing_ok=True)
    profile = tempfile.mkdtemp(prefix="chart-conflict-chrome-")
    proc = subprocess.Popen([CHROME, "--headless=new", f"--user-data-dir={profile}", "--no-first-run",
                             "--no-default-browser-check", "--disable-component-update", "--disable-gpu", "--hide-scrollbars",
                             "--force-device-scale-factor=1", "--allow-file-access-from-files", "--virtual-time-budget=4000",
                             f"--window-size={size},{size}", f"--screenshot={out}", src.as_uri()],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        deadline, last = time.time() + 60, -1
        while time.time() < deadline:
            if out.exists() and out.stat().st_size > 0 and out.stat().st_size == last:
                break
            last = out.stat().st_size if out.exists() else -1
            if proc.poll() is not None and not out.exists():
                raise RuntimeError(f"Chrome exited without writing {out.name}")
            time.sleep(0.3)
        else:
            raise TimeoutError(f"Chrome did not write {out.name} within 60 s")
    finally:
        proc.kill()
        subprocess.run(["pkill", "-f", profile], capture_output=True)
        shutil.rmtree(profile, ignore_errors=True)
    with Image.open(out) as im:
        assert im.size == (size, size), f"{out.name}: got {im.size}, expected {size}x{size}"
    return out


def save_image(img, image_name):
    """For stimuli drawn with matplotlib/PIL: save a PIL image as images/<image_name>.png."""
    IMAGES.mkdir(exist_ok=True)
    img = img.convert("RGB")
    assert img.size == (SIZE, SIZE), f"{image_name}: got {img.size}"
    out = IMAGES / f"{image_name}.png"
    img.save(out)
    return out


# ---------- validation ----------
def validate(spec):
    err = []
    sid = spec["id"]
    for k in ("id", "title", "chart", "style", "tech", "mechanism", "conflict_summary", "data", "questions"):
        if k not in spec:
            err.append(f"missing key {k}")
    if spec.get("mechanism") not in MECHANISMS:
        err.append(f"mechanism must be one of {sorted(MECHANISMS)}")
    else:
        spec["conflict_has_truth"] = MECHANISMS[spec["mechanism"]]
    for cond in CONDS:
        for lang in LANGS:
            if not (IMAGES / f"{name(sid, cond, lang)}.png").exists():
                err.append(f"image missing: {name(sid, cond, lang)}.png")
    qids, pairs = set(), {}
    if not any(q.get("nonumbers", True) for q in spec.get("questions", [])):
        err.append("no question applies to the nonumbers version")
    for q in spec.get("questions", []):
        if not isinstance(q.get("nonumbers"), bool):
            err.append(f"{q.get('qid')}: set \"nonumbers\": true/false (can the question be answered from the drawing alone?)")
        qid = q.get("qid", "?")
        if qid in qids or not qid.startswith(sid.split("_")[0] + "_"):
            err.append(f"{qid}: duplicate or not prefixed with {sid.split('_')[0]}_")
        qids.add(qid)
        if q.get("kind") not in KINDS:
            err.append(f"{qid}: kind {q.get('kind')!r} not in {sorted(KINDS)}")
        for lang in LANGS:
            p = q["prompt"].get(lang, "")
            if not p.startswith(f"answer {lang} ") or p != p.lower():
                err.append(f"{qid}: prompt[{lang}] must be lowercase and start with 'answer {lang} '")
            vis, txt = q["visual"].get(lang, []), q["text"].get(lang, [])
            if not vis or not txt:
                err.append(f"{qid}: empty accept list for {lang}")
            for v in vis:
                if match(v, txt, lang):
                    err.append(f"{qid} [{lang}]: visual answer {v!r} would also match the text list {txt}")
            for t in txt:
                if match(t, vis, lang):
                    err.append(f"{qid} [{lang}]: text answer {t!r} would also match the visual list {vis}")
        vis_m, txt_m = q["visual"]["tr"] + q["visual"]["en"], q["text"]["tr"] + q["text"]["en"]   # TR rows accept both
        for v in vis_m:
            if match(v, txt_m, "tr"):
                err.append(f"{qid} [tr+en]: visual answer {v!r} would also match a text answer")
        if q.get("pair"):
            pairs.setdefault(q["pair"], []).append(q)
    for pid, qs in pairs.items():
        yn = [(q["visual"]["en"][0], q["text"]["en"][0]) for q in qs]
        if len(qs) != 2 or sorted(yn) != [("no", "yes"), ("yes", "no")]:
            err.append(f"pair {pid}: needs exactly 2 yes/no questions with opposite answers, got {yn}")
        if len({q.get("nonumbers") for q in qs}) > 1:
            err.append(f"pair {pid}: both questions must have the same nonumbers flag")
    if err:
        raise SystemExit(f"[{sid}] spec problems:\n  - " + "\n  - ".join(err))


# ---------- checks ----------
def previews(sid):
    """What the model sees: bicubic downsizes to 448 and 224 (PaliGemma's processor resamples bicubic)."""
    for res in (448, 224):
        d = CHECK / str(res)
        d.mkdir(parents=True, exist_ok=True)
        for p in IMAGES.glob(f"{sid}_*.png"):
            Image.open(p).convert("RGB").resize((res, res), Image.BICUBIC).save(d / p.name)


def diffcheck(sid):
    """Overlays vs the consistent image, changed pixels in red on a faded copy:
    check/diff/<sid>_<lang>.png (conflict) and <sid>_<lang>_nonumbers.png. Returns changed share per lang and version."""
    d = CHECK / "diff"
    d.mkdir(parents=True, exist_ok=True)
    out = {}
    for lang in LANGS:
        a = np.asarray(Image.open(IMAGES / f"{name(sid, 'consistent', lang)}.png").convert("RGB")).astype(int)
        for cond, suffix in (("conflict", ""), ("nonumbers", "_nonumbers")):
            b = np.asarray(Image.open(IMAGES / f"{name(sid, cond, lang)}.png").convert("RGB")).astype(int)
            changed = np.abs(a - b).max(axis=2) > 24
            faded = (255 - (255 - b) * 0.35).astype(np.uint8)
            faded[changed] = (230, 30, 30)
            Image.fromarray(faded).save(d / f"{sid}_{lang}{suffix}.png")
            out[f"{cond}_{lang}"] = round(float(changed.mean()), 4)
    return out


def _font(size):
    for f in ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


def sheet(sid):
    """Comparison sheet: rows en/tr, columns consistent/conflict/nonumbers, each tile 448 px."""
    SHEETS.mkdir(exist_ok=True)
    t, head = 448, 34
    canvas = Image.new("RGB", (len(CONDS) * (t + 12) - 12, 2 * (t + head) + 6), "white")
    draw = ImageDraw.Draw(canvas)
    for r, lang in enumerate(LANGS):
        for c, cond in enumerate(CONDS):
            x, y = c * (t + 12), r * (t + head + 6)
            label = {"nonumbers": "no numbers"}.get(cond, cond)
            color = {"consistent": (20, 20, 20), "conflict": (180, 30, 30)}.get(cond, (90, 90, 90))
            draw.text((x + 4, y + 6), f"{label} · {lang}", fill=color, font=_font(20))
            canvas.paste(Image.open(IMAGES / f"{name(sid, cond, lang)}.png").convert("RGB").resize((t, t), Image.LANCZOS), (x, y + head))
    canvas.save(SHEETS / f"{sid}.png")


def finish(spec):
    validate(spec)
    stim_dir = ROOT / "stimuli" / spec["id"]
    stim_dir.mkdir(parents=True, exist_ok=True)
    (stim_dir / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    previews(spec["id"])
    share = diffcheck(spec["id"])
    sheet(spec["id"])
    nn = sum(q["nonumbers"] for q in spec["questions"])
    print(f"[{spec['id']}] ok · {len(spec['questions'])} questions ({nn} also on nonumbers) · changed pixels vs consistent: {share}")
    print(f"  look at: sheets/{spec['id']}.png, check/448/{spec['id']}_*.png, check/diff/{spec['id']}_*.png (incl. *_nonumbers.png)")
