"""Write run4/chart_conflict_run4.ipynb (Colab, A100) for run 4: E4 concrete comparisons + F model size."""
import json
from pathlib import Path

R4 = Path(__file__).resolve().parent


def md(s):
    return {"cell_type": "markdown", "metadata": {}, "source": s.strip("\n")}


def code(s):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": s.strip("\n")}


cells = [
    md("""
# PaliGemma 2 chart cue conflict: run 4 (concrete comparisons + bigger models)

Run 3 asked "do the numbers on the chart match the bars?" and neither 3B model answered differently on agreeing and lying
charts. Two things could explain that, and run 4 tests both.

- **E4 · concrete comparisons** (English, 22 images). The same comparison asked the concrete way, e.g. *"is the number above
  the tallest bar the largest of the six numbers?"*, plus its two parts on the same image: *which month has the tallest
  bar?* (drawing) and *what number is written above the June bar?* (text). Does it fail to compare even when it has both facts?
- **E5 · the "no" ladder** (same 22 images). Easy questions whose right answer is mostly *no*, getting harder: an object that
  isn't there (*"is there a dog?"*), the text (*"is this chart about car sales?"*), the drawing (*"does January have the tallest
  bar?"*), then E4's comparisons. Where does the model stop saying no? A few *yes* questions keep "always no" from passing.
- **F · model size.** Run 3's 132 questions on PaliGemma 2 **10B** (and **28B** if the GPU has ≥ 70 GB).
- **Controls.** 3B in float32 with TF32 off (should repeat run 3's T4 answers), and 3B in bfloat16, so 3B vs 10B compare in the
  same precision (10B doesn't fit in float32).

**Before running**
1. Runtime → Change runtime type → **A100 GPU** (High-RAM if offered). An L4 also works but is slower, and 28B is skipped.
2. The `HF_TOKEN` secret with notebook access on (🔑 sidebar). The first code cell checks access to every model and prints
   the page to accept the licence on if one is missing.
3. Drag `chart_conflict_run4_bundle.zip` into the 📁 Files sidebar (the upload button breaks on files this size), then
   Runtime → **Run all**.
4. The last cell downloads `run4_outputs.zip`. Answers are also saved to `MyDrive/chart_conflict/answers_run4.csv` as they come
   in, so a disconnect loses nothing: Run all again and it skips what is done.

About 45–60 minutes on an A100 (3,564 answers), much of it downloading the 10B weights (~20 GB each).
"""),
    code("""
import sys
IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    !pip install -q -U transformers accelerate

import gc, json, shutil, time, zipfile
from pathlib import Path

import pandas as pd
import torch
from PIL import Image
from transformers import AutoProcessor, PaliGemmaForConditionalGeneration

if IN_COLAB:
    from google.colab import userdata
    from huggingface_hub import login
    login(userdata.get("HF_TOKEN"))

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
assert DEVICE == "cuda" or not IN_COLAB, "Runtime → Change runtime type → A100 GPU"
# float32 runs must do the same math as the T4 in runs 1-3: no TF32 on newer GPUs
torch.backends.cuda.matmul.allow_tf32 = False
torch.backends.cudnn.allow_tf32 = False
GPU_GB = torch.cuda.get_device_properties(0).total_memory / 1e9 if DEVICE == "cuda" else 0
print(DEVICE, torch.cuda.get_device_name(0) if DEVICE == "cuda" else "", f"{GPU_GB:.0f} GB")

# key: (checkpoint, dtype). 3B in float32 = runs 1-3 setup; the bf16 rows make the 3B vs 10B/28B comparison like for like.
MODELS = {
    "224":       ("google/paligemma2-3b-mix-224", torch.float32),
    "448":       ("google/paligemma2-3b-mix-448", torch.float32),
    "224bf":     ("google/paligemma2-3b-mix-224", torch.bfloat16),
    "448bf":     ("google/paligemma2-3b-mix-448", torch.bfloat16),
    "10b-224":   ("google/paligemma2-10b-mix-224", torch.bfloat16),
    "10b-448":   ("google/paligemma2-10b-mix-448", torch.bfloat16),
    "28b-448":   ("google/paligemma2-28b-mix-448", torch.bfloat16),
}
if GPU_GB < 70:
    MODELS.pop("28b-448")
    print("28B skipped: needs a GPU with at least 70 GB (this one has", round(GPU_GB), "GB)")
if 0 < GPU_GB < 30:
    print("note: 10B in bfloat16 needs ~21 GB; on a 24 GB L4 it fits but is slow")

if IN_COLAB:
    from huggingface_hub import model_info
    missing = []
    for repo in sorted({r for r, _ in MODELS.values()}):
        try:
            model_info(repo)
        except Exception as e:
            missing.append(repo)
            print("NO ACCESS:", repo, "→ accept the licence at https://huggingface.co/" + repo, f"({type(e).__name__})")
    assert not missing, "accept the licence(s) above with the account your HF_TOKEN belongs to, then Run all again"
    print("access OK:", ", ".join(sorted({r for r, _ in MODELS.values()})))
"""),
    code("""
if not Path("questions4.json").exists():
    assert Path("chart_conflict_run4_bundle.zip").exists(), "drag chart_conflict_run4_bundle.zip into the Files sidebar first"
    zipfile.ZipFile("chart_conflict_run4_bundle.zip").extractall(".")

Q = pd.DataFrame(json.loads(Path("questions4.json").read_text(encoding="utf-8")))
print(len(Q), "questions ·", Q.image.nunique(), "images ·", len(MODELS), "model settings →", len(Q) * len(MODELS), "answers")
print(Q.groupby(["exp", "qtype"]).size().to_string())
"""),
    md("""
## Run
Greedy decoding, max 16 new tokens, as in runs 1–3. One model at a time; a finished 10B/28B is deleted from disk before the
next one downloads.
"""),
    code("""
def load(key):
    repo, dtype = MODELS[key]
    proc = AutoProcessor.from_pretrained(repo)
    model = PaliGemmaForConditionalGeneration.from_pretrained(repo, dtype=dtype, device_map=DEVICE).eval()
    return model, proc

@torch.inference_mode()
def ask(model, proc, image, prompt, max_new_tokens=16):
    inputs = proc(text=prompt, images=image, return_tensors="pt").to(model.dtype).to(model.device)
    n_in = inputs["input_ids"].shape[-1]
    out = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
    return proc.decode(out[0, n_in:], skip_special_tokens=True).strip()

def drop_from_disk(repo):
    if IN_COLAB and "-3b-" not in repo:
        shutil.rmtree(Path.home() / ".cache/huggingface/hub" / ("models--" + repo.replace("/", "--")), ignore_errors=True)

SAVE_TO_DRIVE = True
if SAVE_TO_DRIVE and IN_COLAB:
    from google.colab import drive
    drive.mount("/content/drive")
    OUT = Path("/content/drive/MyDrive/chart_conflict/answers_run4.csv")
    OUT.parent.mkdir(parents=True, exist_ok=True)
else:
    OUT = Path("answers_run4.csv")
done = set()
if OUT.exists():
    prev = pd.read_csv(OUT, keep_default_na=False)
    done = set(zip(prev.model.astype(str), prev.image, prev.prompt))

images = {}
def img(name):
    if name not in images:
        images[name] = Image.open(f"images/{name}").convert("RGB")
    return images[name]

for key in MODELS:
    todo = [r for r in Q.itertuples() if (key, r.image, r.prompt) not in done]
    if not todo:
        continue
    t_load = time.perf_counter()
    model, proc = load(key)
    print(f"[{key}] loaded in {time.perf_counter() - t_load:.0f}s, {len(todo)} questions")
    ask(model, proc, img(todo[0].image), "caption en")   # warm-up
    for i, r in enumerate(todo):
        t0 = time.perf_counter()
        answer = ask(model, proc, img(r.image), r.prompt)
        pd.DataFrame([{"model": key, "exp": r.exp, "image": r.image, "prompt": r.prompt, "answer": answer,
                       "seconds": round(time.perf_counter() - t0, 2)}]).to_csv(OUT, mode="a", header=not OUT.exists(), index=False)
        if i % 50 == 0:
            print(f"[{key}] {i + 1}/{len(todo)}  {r.image} | {r.prompt} → {answer}")
    del model
    gc.collect()
    if DEVICE == "cuda":
        torch.cuda.empty_cache()
    drop_from_disk(MODELS[key][0])
A = pd.read_csv(OUT, keep_default_na=False).astype({"model": str})
print("answers:", len(A), "of", len(Q) * len(MODELS))
"""),
    md("""
## Quick look
The full analysis runs locally (`python3.12 run4/analyze4.py`). Three checks you can read right away:
1. **Control:** 3B float32 on this GPU vs run 3 on the T4 (should be identical or nearly).
2. **E4:** share of "yes" to *"is the number on the biggest mark the largest?"* and *"…on the smallest mark the smallest?"*.
   The right answer is yes on every agreeing chart and no on every lying one. A model that compares drops on the lying charts.
3. **E5:** share of "yes" where the right answer is *no*, per difficulty level (agreeing charts).
4. **F:** run 3's *"do the numbers match?"* per model, agreeing vs lying.
"""),
    code("""
def yn(a):
    w = a.lower().strip().split()
    w = w[0].strip(".,!?") if w else ""
    return "yes" if w in ("yes", "evet") else "no" if w in ("no", "hayır", "hayir") else "other"

M = A.merge(Q.drop(columns=["exp"]), on=["image", "prompt"])
M["yn"] = M.answer.map(yn)
R3 = pd.read_csv("run3_answers.csv", keep_default_na=False).astype({"model": str}).set_index(["model", "image", "prompt"]).answer
for k in ("224", "448"):
    f = M[(M.model == k) & (M.exp == "F")]
    same = sum(R3.get((k, i, p)) == a for i, p, a in zip(f.image, f.prompt, f.answer))
    print(f"control mix-{k} float32: {same} of {len(f)} answers identical to run 3 (T4)")

flip = M[M.qtype.isin(["cmp_big_max", "cmp_small_min"])]
print("\\nE4: share of yes, 'number on the biggest mark is the largest' + 'on the smallest mark is the smallest' (n = 22 per cell)")
print(flip.assign(yes=flip.yn == "yes").pivot_table(index="model", columns="cond", values="yes", aggfunc="mean")
      [["consistent", "conflict"]].reindex(list(MODELS)).round(2).to_string())
lad = M[(M.cond == "consistent") & (M.right == "no") & (M.exp.isin(["E4", "E5"]))].copy()
lad["level"] = lad["level"].where(lad.exp == "E5", "L3")
lad = lad[(lad.exp == "E5") | lad.qtype.str.startswith(("cmp", "any"))]
print("\\nE5: share of yes where the answer is NO (agreeing charts) · L0 object, L1 text, L2 drawing, L3 comparison")
print(lad.assign(yes=lad.yn == "yes").pivot_table(index="model", columns="level", values="yes", aggfunc="mean")
      .reindex(list(MODELS)).round(2).to_string())
m3 = M[(M.exp == "F") & (M.qtype == "match")]
print("\\nF: share of yes, 'do the numbers match?' (n = 22 per cell)")
print(m3.assign(yes=m3.yn == "yes").pivot_table(index="model", columns="cond", values="yes", aggfunc="mean")
      [["consistent", "conflict"]].reindex(list(MODELS)).round(2).to_string())
"""),
    code("""
shutil.copy(OUT, "answers_run4.csv") if OUT != Path("answers_run4.csv") else None
with zipfile.ZipFile("run4_outputs.zip", "w", zipfile.ZIP_DEFLATED) as z:
    z.write("answers_run4.csv")
if IN_COLAB:
    from google.colab import files
    files.download("run4_outputs.zip")
"""),
]

nb = {"cells": cells, "metadata": {"accelerator": "GPU", "colab": {"provenance": [], "gpuType": "A100"},
                                   "kernelspec": {"display_name": "Python 3", "name": "python3"}, "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 0}
(R4 / "chart_conflict_run4.ipynb").write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print("wrote", R4 / "chart_conflict_run4.ipynb", len(cells), "cells")
