"""Write chart_conflict_experiment.ipynb (Colab). The scoring cell is copied from common/scoring.py so both stay identical."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCORING = (ROOT / "common" / "scoring.py").read_text(encoding="utf-8")


def md(s):
    return {"cell_type": "markdown", "metadata": {}, "source": s.strip("\n")}


def code(s):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": s.strip("\n")}


cells = [
    md("""
# PaliGemma 2: charts that contradict themselves

Runs `google/paligemma2-3b-mix-224` and `google/paligemma2-3b-mix-448` on 14 chart stimuli
(newspaper, slide, phone app, dashboard, paper figure, sketch, map, spreadsheet …).
Each chart comes in three versions with the **same drawing**:

- **consistent**: the printed numbers agree with the drawing
- **conflict**: only the text changes (value labels, axis ticks, legend, readouts) so that it contradicts the drawing
- **no numbers**: that text is removed — how well the model reads the drawing alone

…in English and Turkish. The question: does the model answer from **what the marks look like** or from **what the text says**?

**Before running**
1. Runtime → Change runtime type → **T4 GPU**.
2. Logged in to Hugging Face, accept the Gemma license on [mix-224](https://huggingface.co/google/paligemma2-3b-mix-224) and [mix-448](https://huggingface.co/google/paligemma2-3b-mix-448).
3. Colab sidebar 🔑 → secret `HF_TOKEN` (read token), notebook access on.
4. Runtime → Run all, and upload `chart_conflict_bundle.zip` when asked (or drag it into the Files sidebar first).
"""),
    code("""
import sys
IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    !pip install -q -U transformers accelerate

import gc, json, time, zipfile
from pathlib import Path

import matplotlib.pyplot as plt
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
# T4: no native bfloat16 and float16 is unstable for Gemma 2 → float32 (3B x 4 bytes ≈ 12 GB, fits in 15 GB)
DTYPE = torch.bfloat16 if DEVICE == "cuda" and torch.cuda.get_device_capability()[0] >= 8 else torch.float32
print(DEVICE, DTYPE)
"""),
    code("""
MODELS = {
    "224": "google/paligemma2-3b-mix-224",
    "448": "google/paligemma2-3b-mix-448",
}

def load(key):
    proc = AutoProcessor.from_pretrained(MODELS[key])
    model = PaliGemmaForConditionalGeneration.from_pretrained(MODELS[key], dtype=DTYPE, device_map=DEVICE).eval()
    return model, proc

def free():
    # call after `del model`; only one 3B model fits on the T4 at a time
    gc.collect()
    if DEVICE == "cuda":
        torch.cuda.empty_cache()
"""),
    md("""
## 1. Stimuli
`questions.json` has one row per (image, prompt): 14 stimuli × 3 versions × 2 languages × their questions
(the no-numbers version only gets the questions that can be answered from the drawing alone).
`visual` = answers that follow the drawing, `text` = answers that follow the printed text of the conflict version.
"""),
    code("""
if not Path("questions.json").exists():
    if not Path("chart_conflict_bundle.zip").exists() and IN_COLAB:
        files.upload()   # pick chart_conflict_bundle.zip
    zipfile.ZipFile("chart_conflict_bundle.zip").extractall(".")

Q = pd.DataFrame(json.loads(Path("questions.json").read_text(encoding="utf-8")))
print(Q.stimulus.nunique(), "stimuli ·", Q.image.nunique(), "images ·", len(Q), "rows per model")
print(Q.groupby("mechanism").stimulus.nunique().to_dict())

def show_pair(stimulus, lang="en"):
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.4))
    for ax, cond in zip(axes, ["consistent", "conflict", "nonumbers"]):
        ax.imshow(Image.open(f"images/{stimulus}_{cond}_{lang}.png")); ax.axis("off"); ax.set_title(f"{cond} · {lang}")
    plt.show()

show_pair(Q.stimulus.iloc[0])
"""),
    md("""
## 2. Scoring
- **consistent** and **no numbers** images → `correct` if the answer matches what the drawing shows, else `wrong`.
- **conflict** image → which cue the answer followed: `visual`, `text`, `both` or `neither`.
  For `axis` and `legend` stimuli the conflict chart is misleading but internally consistent, so `text` is the right answer there.
  For `label` and `readout` stimuli the chart contradicts itself and there is no right answer, only a preference.
- PaliGemma often answers Turkish prompts in English (`yes` instead of `evet`). The cue it followed doesn't depend on the
  language, so Turkish rows accept the Turkish **or** English answers; `in_english` flags those rows and gets its own table.
- After reading the answers, near-misses (e.g. `t.lwy` for the ticker TLWY) can be decided by hand in `adjudication.csv`
  (`model, image, prompt, outcome, reason`); every override is printed, so nothing changes silently.

Matching is whole-word and case-insensitive; numbers compare by value; Turkish words may carry a suffix
(`haziranda` = `haziran`) but not a negation (`azalmadı` ≠ `azal`). In the lists, `=` means exact match and `^` whole answer only.
"""),
    code(SCORING),
    md("""
## 3. Run both models
Greedy decoding, so every run gives the same answer. Answers are appended to `answers.csv` as they come in, and the cell
skips what's already answered: if it stops, run it again and it continues. With `SAVE_TO_DRIVE = True` the file lives in your
Google Drive (`MyDrive/chart_conflict/`), so it also survives Colab recycling the machine — otherwise a recycled machine loses it.
"""),
    code("""
@torch.inference_mode()
def ask(model, proc, image, prompt, max_new_tokens=16):
    inputs = proc(text=prompt, images=image, return_tensors="pt").to(model.dtype).to(model.device)
    n_in = inputs["input_ids"].shape[-1]
    out = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
    return proc.decode(out[0, n_in:], skip_special_tokens=True).strip()

SAVE_TO_DRIVE = True   # keep answers.csv in Google Drive (asks for Drive access once); False = local file only
if SAVE_TO_DRIVE and IN_COLAB:
    from google.colab import drive
    drive.mount("/content/drive")
    OUT = Path("/content/drive/MyDrive/chart_conflict/answers.csv")
    OUT.parent.mkdir(parents=True, exist_ok=True)
else:
    OUT = Path("answers.csv")
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
        row = pd.DataFrame([{"model": key, "image": r.image, "prompt": r.prompt, "answer": answer,
                             "seconds": round(time.perf_counter() - t0, 2)}])
        row.to_csv(OUT, mode="a", header=not OUT.exists(), index=False)
        if i % 25 == 0:
            print(f"[{key}] {i + 1}/{len(todo)}  {r.image} | {r.prompt} → {answer}")
    del model
    free()
print("answers:", len(pd.read_csv(OUT)))
"""),
    md("""
## 4. Results
- Conflict rows are shown **only where the model got the consistent twin right** (same model, language, question):
  if it can't answer the consistent chart, its conflict answer says nothing about cue preference.
- The **no-numbers** version says whether the model can read the drawing at all. The strongest result is the conflict table
  restricted to questions it answered right *from the drawing alone*: a `text` answer there means the text overrode a drawing
  the model demonstrably can read.
- **Number questions (`read_value`) are kept out of the headline numbers.** The conflict labels are the consistent labels
  shuffled, so the drawing's number is still printed on *another* mark in the conflict image: a `visual` hit there means
  "took the label of the mark with the right size rank" or "read the wrong mark's label". They get their own table.
- Cue text size differs between charts (`cue_px`, digit height at 896 px; at 224 px it's a quarter). The per-chart figure is
  sorted by it, so "big text wins" can be told apart from "this kind of cue wins".
"""),
    code("""
A = pd.read_csv(OUT, keep_default_na=False).astype({"model": str})
df = A.merge(Q, on=["image", "prompt"], how="inner")
assert len(df) == len(A), "some answers don't match a question row"

def lists(r):
    # Turkish prompts: accept the Turkish or the English answer (the cue is the same; the language is reported separately)
    return (r.visual + r.en_visual, r.text + r.en_text) if r.lang == "tr" else (r.visual, r.text)

def outcome(r):
    vis, txt = lists(r)
    if r.cond in ("consistent", "nonumbers"):
        return "correct" if match(r.answer, vis, r.lang) else "wrong"
    return classify(r.answer, vis, txt, r.lang)

df["outcome"] = df.apply(outcome, axis=1)
df["in_english"] = [l == "tr" and not match(a, v + t, "tr") and match(a, ev + et, "tr")
                    for a, l, v, t, ev, et in zip(df.answer, df.lang, df.visual, df.text, df.en_visual, df.en_text)]
if Path("adjudication.csv").exists():                     # manual decisions on near-misses, documented with a reason
    adj = pd.read_csv("adjudication.csv", keep_default_na=False).astype({"model": str})
    key = ["model", "image", "prompt"]
    df = df.merge(adj[key + ["outcome", "reason"]].rename(columns={"outcome": "adjudicated"}), on=key, how="left")
    hit = df.adjudicated.fillna("").ne("")
    print(f"adjudication.csv: {int(hit.sum())} outcomes overridden by hand")
    for r in df[hit].itertuples():
        print(f"  [{r.model}] {r.image} | {r.prompt} → {r.answer!r}: {r.outcome} → {r.adjudicated} ({r.reason})")
    df.loc[hit, "outcome"] = df.loc[hit, "adjudicated"]
    df = df.drop(columns=["adjudicated"])
ctrl = df[df.cond == "consistent"].set_index(["model", "lang", "qid"]).outcome.eq("correct").rename("ctrl_ok")
df = df.join(ctrl, on=["model", "lang", "qid"])
df["ctrl_ok"] = df.ctrl_ok.fillna(False).astype(bool)
draw = df[df.cond == "nonumbers"].set_index(["model", "lang", "qid"]).outcome.eq("correct").rename("draw_ok")
df = df.join(draw, on=["model", "lang", "qid"])          # NaN where the question isn't asked without numbers
df.to_csv("results.csv", index=False)

C = df[df.cond == "consistent"]
print("control: share correct on CONSISTENT charts (all questions)")
print(C.assign(ok=C.outcome.eq("correct")).pivot_table(index="lang", columns="model", values="ok", aggfunc="mean").round(2), "\\n")
both = df[df.cond.isin(["consistent", "nonumbers"]) & df.qid.isin(df[df.cond == "nonumbers"].qid)]
print("do the numbers help? share correct, same questions with and without the printed numbers")
print(both.assign(ok=both.outcome.eq("correct")).pivot_table(index=["lang", "cond"], columns="model", values="ok", aggfunc="mean").round(2), "\\n")

CUES = ["visual", "text", "both", "neither"]
X = df[df.cond == "conflict"]
keep = X[X.ctrl_ok & (X.kind != "read_value")]           # headline set
share = lambda d, by: (d.groupby(by).outcome.value_counts(normalize=True).unstack(fill_value=0)
                        .reindex(columns=CUES, fill_value=0).round(2))
n = lambda d, by: d.groupby(by).size().rename("n")
print("CONFLICT charts, headline (consistent twin right, number questions excluded): which cue did the answer follow?")
print(share(keep, ["model", "lang"]).join(n(keep, ["model", "lang"])), "\\n")
print("same, all rows (no ctrl_ok filter, number questions excluded)")
print(share(X[X.kind != "read_value"], ["model", "lang"]), "\\n")
print("by answer type")
print(share(keep, ["answer_type", "model"]).join(n(keep, ["answer_type", "model"])), "\\n")
print("by mechanism — descriptive only: few charts per mechanism and different cue sizes (see per-chart figure)")
print(share(keep, ["mechanism", "model"]).join(n(keep.drop_duplicates(["stimulus", "model"]), ["mechanism", "model"]).rename("charts")), "\\n")
R = X[X.ctrl_ok & (X.kind == "read_value")]
print("NUMBER questions: 'visual' = the label of the mark with the drawing's size rank (or a misread neighbour), 'text' = own label")
print(share(R, ["model", "lang"]).join(n(R, ["model", "lang"])), "\\n")
T = df[df.lang == "tr"]
print("Turkish prompts answered in English (share of all Turkish rows), by answer type")
print(T.pivot_table(index="answer_type", columns="model", values="in_english", aggfunc="mean").round(2))
"""),
    md("""
### Yes/no questions: scored per pair
A model with a yes-bias says "yes" to both halves of a pair ("more?" and "fewer?"). Scored question by question, it then looks
like it follows the drawing on one half and the text on the other; filtered by "consistent twin right", it keeps mostly the
questions whose drawing answer is "yes", which inflates `visual`. So yes/no questions are scored **per pair**:
`visual` / `text` = the two answers are opposite and match that cue, `same` = the same answer to both halves (no information about the cue),
`unclear` = an answer that isn't yes/no. On consistent and no-numbers charts, `correct` = both halves right.
"""),
    code("""
YES, NO = ["yes", "evet"], ["no", "hayır", "^değil"]
yn = df[df.answer_type == "yesno"].copy()
yn["said"] = [("yes" if match(a, YES, l) else "no" if match(a, NO, l) else "?") for a, l in zip(yn.answer, yn.lang)]
print("share of yes/no prompts answered 'yes' (half would be right on consistent charts):")
print(yn.assign(y=yn.said.eq("yes")).pivot_table(index=["cond", "lang"], columns="model", values="y", aggfunc="mean").round(2), "\\n")

def pair_outcome(g):
    model, lang, cond, stimulus, pair = g.name
    if len(g) != 2 or (g.said == "?").any():
        return "unclear"
    if g.said.nunique() == 1:
        return "same"
    extra = lambda en: en if lang == "tr" else []
    vis_ok = all(match(a, v + extra(ev), lang) for a, v, ev in zip(g.answer, g.visual, g.en_visual))
    txt_ok = all(match(a, t + extra(et), lang) for a, t, et in zip(g.answer, g.text, g.en_text))
    if cond != "conflict":
        return "correct" if vis_ok else "wrong"
    return "visual" if vis_ok else "text" if txt_ok else "unclear"

P = (yn.groupby(["model", "lang", "cond", "stimulus", "pair"]).apply(pair_outcome, include_groups=False)
     .rename("pair_outcome").reset_index())
pshare = lambda d, cols: (d.groupby(["model", "lang"]).pair_outcome.value_counts(normalize=True).unstack(fill_value=0)
                          .reindex(columns=cols, fill_value=0).round(2).join(d.groupby(["model", "lang"]).size().rename("pairs")))
print("CONSISTENT charts, per pair: correct = both halves right, same = same answer to both")
print(pshare(P[P.cond == "consistent"], ["correct", "same", "wrong", "unclear"]), "\\n")
print("NO-NUMBERS charts, per pair")
print(pshare(P[P.cond == "nonumbers"], ["correct", "same", "wrong", "unclear"]), "\\n")
ok_pairs = P[(P.cond == "consistent") & (P.pair_outcome == "correct")][["model", "lang", "pair"]]
PX = P[P.cond == "conflict"]
print("CONFLICT charts, per pair (all pairs): which cue did the two answers follow?")
print(pshare(PX, ["visual", "text", "same", "unclear"]), "\\n")
print("…only pairs answered right on the consistent chart (same model, language)")
print(pshare(PX.merge(ok_pairs, on=["model", "lang", "pair"]), ["visual", "text", "same", "unclear"]))
"""),
    md("""
### Did the answer change when only the text changed?
The simplest measure, with almost no assumptions: consistent and conflict images differ **only** in the printed text, so any change
in the answer between the two is caused by the text. `changed` = the answer differs; `to_text` = it changed to the conflict text's
answer. A model that ignores the text never changes (a constant "yes" never changes either, so this isn't fooled by a yes-bias).
"""),
    code("""
key = ["model", "lang", "qid"]
J = (df[df.cond == "consistent"].set_index(key)[["answer", "stimulus", "mechanism", "answer_type", "kind"]]
     .join(df[df.cond == "conflict"].set_index(key)[["answer", "text", "en_text"]], rsuffix="_x").reset_index())
J["changed"] = [tokens(a) != tokens(b) for a, b in zip(J.answer, J.answer_x)]
J["to_text"] = [ch and match(b, t + (et if l == "tr" else []), l)
                for ch, b, t, et, l in zip(J.changed, J.answer_x, J.text, J.en_text, J.lang)]
flip = lambda by: J.groupby(by).agg(n=("changed", "size"), changed=("changed", "mean"), to_text=("to_text", "mean")).round(2)
print("answer changed between consistent and conflict (only the text differs):")
print(flip(["model"]), "\\n")
print("…number questions excluded"); print(J[J.kind != "read_value"].groupby("model").agg(n=("changed", "size"), changed=("changed", "mean"), to_text=("to_text", "mean")).round(2), "\\n")
print("…by answer type"); print(flip(["answer_type", "model"]), "\\n")
print("…by mechanism"); print(flip(["mechanism", "model"]), "\\n")
print("…by chart (448)"); print(J[J.model == "448"].groupby("stimulus").agg(n=("changed", "size"), changed=("changed", "mean"), to_text=("to_text", "mean")).round(2))
"""),
    code("""
# the other question types (names, directions, judgements, counts) have no yes-bias problem: scored per question
O = X[~X.answer_type.isin(["yesno"]) & (X.kind != "read_value")]
print("CONFLICT charts, non-yes/no questions (number questions excluded), all rows")
print(share(O, ["model", "lang"]).join(n(O, ["model", "lang"])), "\\n")
print("…only where the consistent twin was answered right")
print(share(O[O.ctrl_ok], ["model", "lang"]).join(n(O[O.ctrl_ok], ["model", "lang"])), "\\n")
print("…by answer type (consistent twin right)")
print(share(O[O.ctrl_ok], ["answer_type", "model"]).join(n(O[O.ctrl_ok], ["answer_type", "model"])), "\\n")
tr = O[O.ctrl_ok & O.visual_dir.notna()]
print("trend questions, split by the DRAWING's direction (a 'things go up' prior shows up as more 'visual' when it rises)")
print(share(tr, ["visual_dir", "model"]).join(n(tr, ["visual_dir", "model"])))
"""),
    code("""
# HEADLINE: one unit = one non-yes/no question, or one yes/no PAIR (so a yes-bias can't masquerade as a cue);
# only units the model got right on the consistent chart
units = pd.concat([
    O[O.ctrl_ok][["model", "lang", "stimulus", "mechanism", "cue_px", "outcome"]],
    PX.merge(ok_pairs, on=["model", "lang", "pair"]).merge(
        df[["stimulus", "mechanism", "cue_px"]].drop_duplicates(), on="stimulus")
      .rename(columns={"pair_outcome": "outcome"})[["model", "lang", "stimulus", "mechanism", "cue_px", "outcome"]],
], ignore_index=True)
units["outcome"] = units.outcome.replace({"unclear": "neither"})
UC = ["visual", "text", "same", "neither", "both"]
ushare = lambda d, by: (d.groupby(by).outcome.value_counts(normalize=True).unstack(fill_value=0)
                         .reindex(columns=UC, fill_value=0).round(2))
print("HEADLINE — conflict charts, units the model got right on the consistent chart")
print("(unit = a non-yes/no question or a yes/no pair; same = same answer to both halves of a pair)")
print(ushare(units, ["model", "lang"]).join(units.groupby(["model", "lang"]).size().rename("units")), "\\n")
draw_pairs = P[(P.cond == "nonumbers") & (P.pair_outcome == "correct")][["model", "lang", "pair"]]
units_draw = pd.concat([
    O[O.draw_ok.eq(True)][["model", "lang", "stimulus", "outcome"]],
    PX.merge(draw_pairs, on=["model", "lang", "pair"]).rename(columns={"pair_outcome": "outcome"})[["model", "lang", "stimulus", "outcome"]],
], ignore_index=True)
units_draw["outcome"] = units_draw.outcome.replace({"unclear": "neither"})
print("…only units the model answered right from the DRAWING ALONE (no-numbers version):")
print("  'text' here = the text overrode a drawing the model demonstrably can read")
print(ushare(units_draw, ["model", "lang"]).join(units_draw.groupby(["model", "lang"]).size().rename("units")), "\\n")
print("by mechanism — descriptive only (few charts per mechanism, different cue sizes)")
print(ushare(units, ["mechanism", "model"]).join(units.groupby(["mechanism", "model"]).size().rename("units")))

# 95% intervals: resample whole charts (units of one chart, en + tr, aren't independent)
import numpy as np
def chart_ci(d, col, reps=4000, seed=0):
    rng = np.random.default_rng(seed)
    by = {k: (g.outcome == col).to_numpy() for k, g in d.groupby("stimulus")}
    keys = list(by)
    stats = [np.concatenate([by[k] for k in rng.choice(keys, len(keys))]).mean() for _ in range(reps)]
    return np.percentile(stats, [2.5, 97.5])
print("\\npooled over en + tr, with 95% intervals from resampling charts:")
for key in MODELS:
    d = units[units.model == key]
    parts = [f"{c} {(d.outcome == c).mean():.0%} [{chart_ci(d, c)[0]:.0%}–{chart_ci(d, c)[1]:.0%}]" for c in ("visual", "text")]
    print(f"  mix-{key}: " + " · ".join(parts) + f"  ({len(d)} units from {d.stimulus.nunique()} charts)")

COLORS = {"visual": "#2a78d6", "text": "#eb6834", "same": "#8a7fd6", "neither": "#e1e0d9", "both": "#b4b2a9"}

def stacked(ax, table, title):
    left = pd.Series(0.0, index=table.index)
    labels = [" · ".join(map(str, i)) if isinstance(i, tuple) else str(i) for i in table.index]
    for col in COLORS:
        ax.barh(labels, table[col], left=left, color=COLORS[col], label=col, height=0.62, edgecolor="white", linewidth=2)
        for y, (l, v) in enumerate(zip(left, table[col])):
            if v >= 0.1:
                ax.text(l + v / 2, y, f"{v:.0%}", ha="center", va="center", fontsize=8,
                        color="white" if col in ("visual", "text", "same") else "#333")
        left += table[col]
    ax.set_xlim(0, 1); ax.invert_yaxis(); ax.set_title(title, loc="left", fontsize=11)
    ax.spines[["top", "right"]].set_visible(False); ax.tick_params(axis="both", labelsize=8)

units["chart"] = units.apply(lambda r: f"{r.stimulus.split('_')[0]} {r.mechanism} · {r.cue_px}px", axis=1)
order = units.drop_duplicates("chart").sort_values("cue_px", ascending=False).chart.tolist()
fig = plt.figure(figsize=(14, 7.5))
gs = fig.add_gridspec(2, 2, height_ratios=[1, 3.2])
ax0 = fig.add_subplot(gs[0, :])
stacked(ax0, ushare(units, ["model", "lang"]), "Conflict charts: which cue the answer followed (units right on the consistent chart)")
for k, key in enumerate(MODELS):
    ax = fig.add_subplot(gs[1, k])
    stacked(ax, ushare(units[units.model == key], ["chart"]).reindex(order).dropna(), f"mix-{key}: per chart, largest cue text first")
ax0.legend(ncol=5, loc="upper right", bbox_to_anchor=(1, 1.45), frameon=False, fontsize=9)
fig.tight_layout()
fig.savefig("cue_following.png", dpi=150, bbox_inches="tight")
plt.show()
"""),
    code("""
# every answer side by side, for reading through
wide = df.pivot_table(index=["stimulus", "qid", "lang", "prompt"], columns=["model", "cond"], values="answer", aggfunc="first")
wide
"""),
    md("""
## 5. Check the scores by eye
The match is a first pass. Read `wide` above; where an answer was scored wrongly, fix `results.csv` and re-run section 4 from it.
"""),
    code("""
with zipfile.ZipFile("chart_conflict_outputs.zip", "w") as z:
    for f, arc in [(OUT, "answers.csv"), (Path("results.csv"), "results.csv"), (Path("cue_following.png"), "cue_following.png")]:
        if Path(f).exists():
            z.write(f, arc)
print(zipfile.ZipFile("chart_conflict_outputs.zip").namelist())
if IN_COLAB:
    files.download("chart_conflict_outputs.zip")
"""),
]

nb = {"cells": cells, "metadata": {"accelerator": "GPU", "colab": {"provenance": []},
                                   "kernelspec": {"display_name": "Python 3", "name": "python3"},
                                   "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 0}
for c in nb["cells"]:
    c["source"] = c["source"].splitlines(keepends=True)
out = ROOT / "chart_conflict_experiment.ipynb"
out.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print("wrote", out.name, "·", len(cells), "cells")
