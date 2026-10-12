"""Write run3/chart_conflict_run3.ipynb (Colab) for run 3, the numbers-match probe. Same setup and generation code as run 1."""
import json
from pathlib import Path

R3 = Path(__file__).resolve().parent


def md(s):
    return {"cell_type": "markdown", "metadata": {}, "source": s.strip("\n")}


def code(s):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": s.strip("\n")}


cells = [
    md("""
# PaliGemma 2 chart cue conflict: run 3 (do the numbers match the drawing?)

Run 1 ("Bars or Labels?") showed which cue the model follows when the printed numbers lie about the drawing. It never asked
the model whether it *notices* the lie. Run 3 asks it directly, on the same images.

- 11 charts where the lying version contradicts itself (value labels or readouts), consistent + lying, en + tr = 44 images.
- 3 yes/no questions per image: *do the numbers match the bars?*, *do the numbers contradict the bars?*, *is there a mistake in this chart?*
  Two polarities, so a model that just says "yes" (run 1: about 75% of yes/no answers) scores no better than chance.
- Both models, 264 answers.

**Before running** (same as runs 1 and 2)
1. Runtime → Change runtime type → **T4 GPU**.
2. The `HF_TOKEN` secret, with notebook access switched on for this notebook (🔑 sidebar).
3. Runtime → **Run all**, and upload `chart_conflict_run3_bundle.zip` when asked (or drag it into the Files sidebar first).
4. The last cell downloads `run3_outputs.zip`. Put it in `chart-conflict/run3/`.

About 10 minutes on a T4, most of it loading the two models. If it stops, run all again: it skips what is already answered.
"""),
    code("""
import sys
IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    !pip install -q -U transformers accelerate

import gc, json, time, zipfile
from pathlib import Path

import pandas as pd
import torch
from PIL import Image
from transformers import AutoProcessor, PaliGemmaForConditionalGeneration

if IN_COLAB:
    from google.colab import files, userdata
    from huggingface_hub import login
    login(userdata.get("HF_TOKEN"))

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
assert DEVICE == "cuda" or not IN_COLAB, "Runtime → Change runtime type → T4 GPU"
# same dtype rule as run 1: float32 on a T4, bfloat16 on A100/H100
DTYPE = torch.bfloat16 if DEVICE == "cuda" and torch.cuda.get_device_capability()[0] >= 8 else torch.float32
print(DEVICE, DTYPE, torch.cuda.get_device_name(0) if DEVICE == "cuda" else "")
"""),
    code("""
MODELS = {"224": "google/paligemma2-3b-mix-224", "448": "google/paligemma2-3b-mix-448"}

def load(key):
    proc = AutoProcessor.from_pretrained(MODELS[key])
    model = PaliGemmaForConditionalGeneration.from_pretrained(MODELS[key], dtype=DTYPE, device_map=DEVICE).eval()
    return model, proc

def free():
    gc.collect()
    if DEVICE == "cuda":
        torch.cuda.empty_cache()
"""),
    code("""
if not Path("questions3.json").exists():
    if not Path("chart_conflict_run3_bundle.zip").exists() and IN_COLAB:
        files.upload()   # pick chart_conflict_run3_bundle.zip
    zipfile.ZipFile("chart_conflict_run3_bundle.zip").extractall(".")

Q = pd.DataFrame(json.loads(Path("questions3.json").read_text(encoding="utf-8")))
print(len(Q), "rows ·", Q.image.nunique(), "images")
print(pd.crosstab(Q.qtype, [Q.cond, Q.lang]))
"""),
    md("""
## Run
Greedy decoding, max 16 new tokens, exactly as run 1. Answers are appended to `answers_run3.csv` as they come in; with
`SAVE_TO_DRIVE = True` the file lives in `MyDrive/chart_conflict/` so a recycled machine doesn't lose it.
"""),
    code("""
@torch.inference_mode()
def ask(model, proc, image, prompt, max_new_tokens=16):
    inputs = proc(text=prompt, images=image, return_tensors="pt").to(model.dtype).to(model.device)
    n_in = inputs["input_ids"].shape[-1]
    out = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
    return proc.decode(out[0, n_in:], skip_special_tokens=True).strip()

SAVE_TO_DRIVE = True
if SAVE_TO_DRIVE and IN_COLAB:
    from google.colab import drive
    drive.mount("/content/drive")
    OUT = Path("/content/drive/MyDrive/chart_conflict/answers_run3.csv")
    OUT.parent.mkdir(parents=True, exist_ok=True)
else:
    OUT = Path("answers_run3.csv")
done = set()
if OUT.exists():
    prev = pd.read_csv(OUT, keep_default_na=False)
    done = set(zip(prev.model.astype(str), prev.image, prev.prompt))

for key in MODELS:
    todo = [r for r in Q.itertuples() if (key, r.image, r.prompt) not in done]
    if not todo:
        continue
    model, proc = load(key)
    ask(model, proc, Image.open(f"images/{todo[0].image}").convert("RGB"), "caption en")   # warm-up
    for i, r in enumerate(todo):
        t0 = time.perf_counter()
        answer = ask(model, proc, Image.open(f"images/{r.image}").convert("RGB"), r.prompt)
        pd.DataFrame([{"model": key, "image": r.image, "prompt": r.prompt, "answer": answer,
                       "seconds": round(time.perf_counter() - t0, 2)}]).to_csv(OUT, mode="a", header=not OUT.exists(), index=False)
        if i % 25 == 0:
            print(f"[{key}] {i + 1}/{len(todo)}  {r.image} | {r.prompt} → {answer}")
    del model
    free()
A = pd.read_csv(OUT, keep_default_na=False).astype({"model": str})
print("answers:", len(A), "of", len(Q) * len(MODELS))
"""),
    md("""
## Quick look
Share of "yes" per question, on the consistent and on the lying charts (22 images each: 11 charts × en/tr). If the model
compared numbers with the drawing, *match* would drop and *contradict* / *mistake* would rise on the lying charts. Equal
rates mean the answer doesn't depend on whether the chart lies. Full analysis: `python3.12 run3/analyze3.py`.
"""),
    code("""
def yn(a):
    w = a.lower().strip().split()
    w = w[0].strip(".,!?") if w else ""
    return "yes" if w in ("yes", "evet") else "no" if w in ("no", "hayır", "hayir") else "other"

M = A.merge(Q, on=["image", "prompt"])
M["yn"] = M.answer.map(yn)
M["right_ans"] = M.yn == M.right
print(M.yn.value_counts().to_string(), "\\n")
print("share of yes:")
print(M.assign(yes=M.yn == "yes").pivot_table(index=["model", "qtype"], columns="cond", values="yes", aggfunc="mean")
      [["consistent", "conflict"]].round(2).to_string(), "\\n")
print("right answers:")
print(M.pivot_table(index=["model", "qtype"], columns="cond", values="right_ans", aggfunc="mean")[["consistent", "conflict"]].round(2).to_string())
"""),
    code("""
import shutil
shutil.copy(OUT, "answers_run3.csv") if OUT != Path("answers_run3.csv") else None
with zipfile.ZipFile("run3_outputs.zip", "w", zipfile.ZIP_DEFLATED) as z:
    z.write("answers_run3.csv")
if IN_COLAB:
    files.download("run3_outputs.zip")
"""),
]

nb = {"cells": cells, "metadata": {"accelerator": "GPU", "colab": {"provenance": []},
                                   "kernelspec": {"display_name": "Python 3", "name": "python3"}, "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 0}
(R3 / "chart_conflict_run3.ipynb").write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print("wrote", R3 / "chart_conflict_run3.ipynb", len(cells), "cells")
