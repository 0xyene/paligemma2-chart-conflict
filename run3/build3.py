"""Build the run-3 bundle: run3/chart_conflict_run3_bundle.zip = images/ + questions3.json.

python3.12 run3/build3.py

Run 3 asks the model directly whether the numbers on a chart agree with the drawing (runs 1–2 supported the
conclusion "it doesn't compare the numbers to the drawing" only indirectly).
Charts: the 11 `label` / `readout` stimuli, where the lying version contradicts itself. The 3 `axis` / `legend` stimuli
(s02, s10, s12) are left out: their flipped scale is unusual but internally consistent, so "do the numbers match?" has no
clean right answer there.
Images: run-1 images unchanged, consistent + conflict, en + tr = 44. Both models.
Three yes/no questions per image, two polarities so the model's yes-habit (about 75% "yes" in run 1) cannot pass as detection:
  match     "do the numbers on the chart match the <marks>?"         right answer yes on consistent, no on conflict
  mismatch  "do the numbers on the chart contradict the <marks>?"    no on consistent, yes on conflict
  error     "is there a mistake in this chart?"                       no on consistent, yes on conflict
"""
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R3 = Path(__file__).resolve().parent

# stimulus: (English marks, Turkish "<marks> + with" form)
MARKS = {
    "s01_newspaper_bars": ("bars", "çubuklarla"),
    "s03_slide_donut": ("slices", "dilimlerle"),
    "s04_app_screentime": ("bars", "çubuklarla"),
    "s05_poster_pictogram": ("tree icons", "ağaç simgeleriyle"),
    "s06_tv_thermometers": ("thermometer fills", "termometrelerin doluluğuyla"),
    "s07_dashboard_gauges": ("gauges", "göstergelerle"),
    "s08_paper_grouped_bars": ("bars", "çubuklarla"),
    "s09_notebook_sketch": ("line", "çizgiyle"),
    "s11_finance_watchlist": ("sparklines", "mini grafiklerle"),
    "s13_widget_battery": ("rings", "halkalarla"),
    "s14_spreadsheet_databars": ("bars", "çubuklarla"),
}


def prompts(sid, lang):
    en, tr = MARKS[sid]
    if lang == "en":
        return {"match": f"answer en do the numbers on the chart match the {en}?",
                "mismatch": f"answer en do the numbers on the chart contradict the {en}?",
                "error": "answer en is there a mistake in this chart?"}
    return {"match": f"answer tr grafikteki sayılar {tr} uyuşuyor mu?",
            "mismatch": f"answer tr grafikteki sayılar {tr} çelişiyor mu?",
            "error": "answer tr bu grafikte bir hata var mı?"}


def main():
    meta = {q["stimulus"]: q for q in json.loads((ROOT / "questions.json").read_text(encoding="utf-8"))}
    bundle = R3 / "bundle"
    if bundle.exists():
        shutil.rmtree(bundle)
    (bundle / "images").mkdir(parents=True)
    rows = []
    for sid in MARKS:
        assert meta[sid]["mechanism"] in ("label", "readout"), sid
        for cond in ("consistent", "conflict"):
            for lang in ("en", "tr"):
                img = f"{sid}_{cond}_{lang}.png"
                shutil.copyfile(ROOT / "images" / img, bundle / "images" / img)
                for qtype, prompt in prompts(sid, lang).items():
                    # the right answer: "match" is yes only when the chart agrees with itself
                    right = ("yes" if cond == "consistent" else "no") if qtype == "match" else ("no" if cond == "consistent" else "yes")
                    rows.append({"image": img, "stimulus": sid, "mechanism": meta[sid]["mechanism"], "cond": cond,
                                 "lang": lang, "qtype": qtype, "prompt": prompt, "right": right})
    (bundle / "questions3.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    zp = R3 / "chart_conflict_run3_bundle.zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(bundle.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(bundle))
    n_img = len({r["image"] for r in rows})
    print(f"wrote {zp.name}: {n_img} images, {len(rows)} questions, {len(rows) * 2} answers with both models "
          f"({zp.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
