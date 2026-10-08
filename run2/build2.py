"""Build the run-2 bundle: run2/chart_conflict_run2_bundle.zip = images/ + questions2.json.

python3.12 run2/build2.py

Three tests (see run2/PREDICTIONS.md, written before the run):
  E1  scale-reading probe on s02 / s10 / s12 (true and flipped versions, en + tr, both models)
  E2  mix-448 on true and lying images degraded to 224-px detail (896 -> 224 -> 448, bicubic), en + tr
      E2c control: mix-448 on 896 -> 448 bicubic images (en), should reproduce run 1
  E3  digit-size sweep: cue text at 4 sizes on 5 charts (built by run2/size_sweep/*.py), en, both models
Every row says which models answer it (`models`). Run-1 question rows are reused unchanged for E2 / E2c / E3, so scoring is
exactly the run-1 scoring.
"""
import json
import shutil
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
R2 = Path(__file__).resolve().parent
OUT_IMG = R2 / "bundle" / "images"
Q1 = json.loads((ROOT / "questions.json").read_text(encoding="utf-8"))
rows = []


def put(src, name):
    dst = OUT_IMG / name
    if not dst.exists():
        shutil.copyfile(src, dst)
    return name


if (R2 / "bundle").exists():
    shutil.rmtree(R2 / "bundle")
OUT_IMG.mkdir(parents=True)

# ---------- E2 / E2c: same pixels the smaller model saw, at mix-448's input size
BIC = Image.Resampling.BICUBIC
for q in Q1:
    if q["cond"] not in ("consistent", "conflict"):
        continue
    src = ROOT / "images" / q["image"]
    stem = q["image"].removesuffix(".png")
    deg = f"{stem}_d224.png"
    if not (OUT_IMG / deg).exists():
        Image.open(src).convert("RGB").resize((224, 224), BIC).resize((448, 448), BIC).save(OUT_IMG / deg)
    rows.append({**q, "exp": "E2", "orig_image": q["image"], "image": deg, "models": ["448"]})
    if q["lang"] == "en":
        ctl = f"{stem}_r448.png"
        if not (OUT_IMG / ctl).exists():
            Image.open(src).convert("RGB").resize((448, 448), BIC).save(OUT_IMG / ctl)
        rows.append({**q, "exp": "E2c", "orig_image": q["image"], "image": ctl, "models": ["448"]})

# ---------- E1: scale-reading probe. kind "read" = read a scale label; "through" = a value that needs the scale.
# For "read": right[cond] is the label actually printed there; on the flipped version `habit` is the normal-axis label.
# For "through": `shape` = value from the mark's position on a normal scale, `axis` = value using the printed (flipped) scale.
PROBES = [
    ("s02_magazine_line_inverted", [
        ("s02_p1", "read", "what number is at the top of the y-axis?", "y ekseninin en üstündeki sayı kaç?", {"consistent": "600", "conflict": "0"}),
        ("s02_p2", "read", "what number is at the bottom of the y-axis?", "y ekseninin en altındaki sayı kaç?", {"consistent": "0", "conflict": "600"}),
        ("s02_p3", "through", "how many bicycle thefts were reported in 2025?", "2025'te kaç bisiklet hırsızlığı bildirildi?", {"shape": 520, "axis": 80, "tol": 100}),
        ("s02_p4", "through", "how many bicycle thefts were reported in 2018?", "2018'de kaç bisiklet hırsızlığı bildirildi?", {"shape": 180, "axis": 420, "tol": 100}),
    ]),
    ("s12_textbook_scatter", [
        ("s12_p1", "read", "what number is at the left end of the x-axis?", "x ekseninin en solundaki sayı kaç?", {"consistent": "0", "conflict": "14"}),
        ("s12_p2", "read", "what number is at the right end of the x-axis?", "x ekseninin en sağındaki sayı kaç?", {"consistent": "14", "conflict": "0"}),
        ("s12_p3", "through", "how many km from school does the student with the lowest score live?",
         "en düşük puanı alan öğrenci okula kaç km uzaklıkta oturuyor?", {"shape": 13.5, "axis": 0.5, "tol": 2.5}),
    ]),
    ("s10_report_tilemap", [
        ("s10_p1", "read", "what number is at the top of the legend?", "lejantın en üstündeki sayı kaç?", {"consistent": "80", "conflict": "10"}),
        ("s10_p2", "read_word", "what word is at the top of the legend?", "lejantın en üstündeki kelime ne?",
         {"consistent": {"en": ["polluted"], "tr": ["kirli", "polluted"]}, "conflict": {"en": ["clean"], "tr": ["temiz", "clean"]}}),
        ("s10_p3", "through", "what is the pm2.5 value in glenrock?", "glenrock'ta pm2,5 değeri kaç?", {"shape": 80, "axis": 10, "tol": 15}),
    ]),
]
meta1 = {q["stimulus"]: q for q in Q1}
for sid, probes in PROBES:
    for cond in ("consistent", "conflict"):
        for lang in ("en", "tr"):
            img = put(ROOT / "images" / f"{sid}_{cond}_{lang}.png", f"{sid}_{cond}_{lang}.png")
            for pid, kind, en, tr, exp in probes:
                rows.append({"exp": "E1", "image": img, "stimulus": sid, "mechanism": meta1[sid]["mechanism"], "cond": cond,
                             "lang": lang, "qid": pid, "probe_kind": kind, "prompt": f"answer {lang} {en if lang == 'en' else tr}",
                             "expect": exp, "models": ["224", "448"]})

# ---------- E3: digit-size sweep (images rendered by run2/size_sweep/<sid>.py, described in <sid>.json)
SWEEP = R2 / "size_sweep"
swept = []
for js in sorted(SWEEP.glob("s*.json")):
    info = json.loads(js.read_text(encoding="utf-8"))
    sid = info["sid"]
    for s in info["sizes"]:
        for cond in ("consistent", "conflict"):
            src = Path(s[cond])
            src = src if src.is_absolute() else ROOT / src
            img = put(src, src.name)
            for q in Q1:
                if q["stimulus"] == sid and q["cond"] == cond and q["lang"] == "en":
                    rows.append({**q, "exp": "E3", "orig_image": q["image"], "image": img, "size_k": s["k"], "size_cue_px": s["cue_px"],
                                 "size_original": s["original"], "models": ["224", "448"]})
    swept.append(sid)

shutil.copyfile(ROOT / "results" / "run1" / "answers.csv", R2 / "bundle" / "run1_answers.csv")   # for the notebook's control check
(R2 / "bundle" / "questions2.json").write_text(json.dumps(rows, ensure_ascii=False, indent=0), encoding="utf-8")
zp = R2 / "chart_conflict_run2_bundle.zip"
zp.unlink(missing_ok=True)
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted((R2 / "bundle").rglob("*")):
        if f.is_file():
            z.write(f, f.relative_to(R2 / "bundle"))

per_model = {m: sum(m in r["models"] for r in rows) for m in ("224", "448")}
by_exp = {}
for r in rows:
    by_exp[r["exp"]] = by_exp.get(r["exp"], 0) + len(r["models"])
print(f"rows {len(rows)} · answers per model {per_model} · answers by test {by_exp}")
print(f"size sweep charts: {swept or 'none yet'}")
print(f"images {len(list(OUT_IMG.iterdir()))} · bundle {zp.stat().st_size / 1e6:.1f} MB")
est = per_model["448"] * 2.53 + per_model["224"] * 0.78
print(f"estimated generation time on a T4: {est / 60:.0f} min (+ ~5 min model loading)")
