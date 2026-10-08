"""Write run2/chart_conflict_run2.ipynb (Colab) for the run-2 follow-up tests. Same setup and generation code as run 1."""
import json
from pathlib import Path

R2 = Path(__file__).resolve().parent


def md(s):
    return {"cell_type": "markdown", "metadata": {}, "source": s.strip("\n")}


def code(s):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": s.strip("\n")}


cells = [
    md("""
# PaliGemma 2 chart cue conflict: run 2 (follow-up tests)

Three follow-up tests for run 1 ("Bars or Labels?"). The predictions were written down before this run, in `run2/PREDICTIONS.md`.

- **E1 · scale-reading probe:** can the model read flipped axis ticks and a reversed legend at all?
- **E2 · same weights, less detail:** mix-448 on images degraded to the detail mix-224 sees. Is the resolution effect about pixels or about the checkpoint? Plus a control that should reproduce run 1.
- **E3 · digit-size sweep:** the cue text at four sizes on five charts, everything else pixel-identical.

**Before running** (same as run 1)
1. Runtime → Change runtime type → **T4 GPU**.
2. The `HF_TOKEN` secret from run 1, with notebook access switched on for this notebook (🔑 sidebar).
3. Runtime → **Run all**, and upload `chart_conflict_run2_bundle.zip` when asked (or drag it into the Files sidebar first).
4. At the end the last cell downloads `run2_outputs.zip`. Send that file back.

About 25–35 minutes on a T4. If it stops, run all again: it skips what is already answered.
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
if not Path("questions2.json").exists():
    if not Path("chart_conflict_run2_bundle.zip").exists() and IN_COLAB:
        files.upload()   # pick chart_conflict_run2_bundle.zip
    zipfile.ZipFile("chart_conflict_run2_bundle.zip").extractall(".")

Q = pd.DataFrame(json.loads(Path("questions2.json").read_text(encoding="utf-8")))
print(len(Q), "rows ·", Q.image.nunique(), "images")
print(pd.crosstab(Q.exp, Q.models.map(lambda m: "+".join(m))))
"""),
    md("""
## Run
Greedy decoding, max 16 new tokens, exactly as run 1. Answers are appended to `answers_run2.csv` as they come in; with
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
    OUT = Path("/content/drive/MyDrive/chart_conflict/answers_run2.csv")
    OUT.parent.mkdir(parents=True, exist_ok=True)
else:
    OUT = Path("answers_run2.csv")
done = set()
if OUT.exists():
    prev = pd.read_csv(OUT, keep_default_na=False)
    done = set(zip(prev.model.astype(str), prev.image, prev.prompt))

for key in MODELS:
    todo = [r for r in Q.itertuples() if key in r.models and (key, r.image, r.prompt) not in done]
    if not todo:
        continue
    model, proc = load(key)
    ask(model, proc, Image.open(f"images/{todo[0].image}").convert("RGB"), "caption en")   # warm-up
    for i, r in enumerate(todo):
        t0 = time.perf_counter()
        answer = ask(model, proc, Image.open(f"images/{r.image}").convert("RGB"), r.prompt)
        pd.DataFrame([{"model": key, "exp": r.exp, "image": r.image, "prompt": r.prompt, "answer": answer,
                       "seconds": round(time.perf_counter() - t0, 2)}]).to_csv(OUT, mode="a", header=not OUT.exists(), index=False)
        if i % 25 == 0:
            print(f"[{key}] {i + 1}/{len(todo)}  {r.exp} {r.image} | {r.prompt} → {answer}")
    del model
    free()
A = pd.read_csv(OUT, keep_default_na=False).astype({"model": str})
print("answers:", len(A), "of", int(Q.models.map(len).sum()))
"""),
    md("""
## Quick look
The full analysis runs locally (`python3.12 run2/analyze2.py <answers_run2.csv>`). Two checks you can read right away:
the control should repeat run 1's mix-448 answers, and the scale-reading probe shows what the model reads off the axes.
"""),
    code("""
R1 = pd.read_csv("run1_answers.csv", keep_default_na=False).astype({"model": str})
r1 = R1[R1.model == "448"].set_index(["image", "prompt"]).answer
ctl = A[A.exp == "E2c"].merge(Q[Q.exp == "E2c"][["image", "prompt", "orig_image"]], on=["image", "prompt"])
same = [r1.get((o, p), None) == a for o, p, a in zip(ctl.orig_image, ctl.prompt, ctl.answer)]
print(f"control: {sum(same)} of {len(same)} answers identical to run 1 (prediction: at least 95%)")

e1 = A[A.exp == "E1"].merge(Q[Q.exp == "E1"][["image", "prompt", "stimulus", "cond", "lang", "qid"]], on=["image", "prompt"])
pd.set_option("display.max_rows", 200)
print(e1.pivot_table(index=["stimulus", "qid"], columns=["model", "cond", "lang"], values="answer", aggfunc="first").to_string())
"""),
    code("""
import shutil
shutil.copy(OUT, "answers_run2.csv") if OUT != Path("answers_run2.csv") else None
with zipfile.ZipFile("run2_outputs.zip", "w", zipfile.ZIP_DEFLATED) as z:
    z.write("answers_run2.csv")
if IN_COLAB:
    files.download("run2_outputs.zip")
"""),
]

nb = {"cells": cells, "metadata": {"accelerator": "GPU", "colab": {"provenance": []},
                                   "kernelspec": {"display_name": "Python 3", "name": "python3"}, "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 0}
(R2 / "chart_conflict_run2.ipynb").write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print("wrote", R2 / "chart_conflict_run2.ipynb", len(cells), "cells")
