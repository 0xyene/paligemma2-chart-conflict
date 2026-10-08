"""The short version of the analysis: one question, three steps. report.txt has every cut; this is the spine.

python3.12 common/simple.py results/run1        # reads results.csv (already scored + hand-adjudicated); writes simple.txt and simple.png

Question: when the printed text and the drawing disagree, which one does the model follow?
  Step 1  control     can it read the chart when nothing disagrees?
  Step 2  main        same question on the consistent vs the conflict image (only the text differs):
                      did the answer stay, switch to what the text says, or switch to something else?
  Step 3  resolution  does mix-448 follow the text more than mix-224? checked chart by chart.
"""
import io
import sys
from math import comb
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scoring import match, tokens

run = Path(sys.argv[1]).resolve()
df = pd.read_csv(run / "results.csv", dtype={"model": str})
for col in ["text", "en_text"]:
    df[col] = df[col].apply(eval)                     # stored as python list literals
GROUP = {"number": "a number", "name": "which one / trend", "direction": "which one / trend",
         "judgement": "which one / trend", "yesno": "yes / no"}
df["group"] = df.answer_type.map(GROUP)
out = io.StringIO()
say = lambda *a: print(*a, file=out)

# step 1
acc = df[df.cond == "consistent"].assign(right=lambda d: d.outcome == "correct")
say("STEP 1 — control: share right when text and drawing agree")
say((acc.pivot_table(index="lang", columns="model", values="right", aggfunc="mean") * 100).round(0).astype(int).to_string())
say("→ about half to two thirds. Conflict answers on charts it can't read are partly noise; keep that in mind.\n")

# step 2
key = ["model", "lang", "qid"]
J = (df[df.cond == "consistent"].set_index(key)[["answer", "stimulus", "group"]]
     .join(df[df.cond == "conflict"].set_index(key)[["answer", "text", "en_text"]], rsuffix="_x").reset_index())
changed = [tokens(a) != tokens(b) for a, b in zip(J.answer, J.answer_x)]
to_text = [c and match(b, t + (et if l == "tr" else []), l)
           for c, b, t, et, l in zip(changed, J.answer_x, J.text, J.en_text, J.lang)]
J["result"] = ["switched to text" if t else "switched to other" if c else "stayed" for c, t in zip(changed, to_text)]
COLS = ["stayed", "switched to text", "switched to other"]
ORDER = ["a number", "which one / trend", "yes / no"]
tab = (J.groupby(["group", "model"]).result.value_counts(normalize=True).unstack(fill_value=0)
       .reindex(columns=COLS, fill_value=0).mul(100).round(0).astype(int)
       .join(J.groupby(["group", "model"]).size().rename("n")).reindex(ORDER, level=0))
say("STEP 2 — main: consistent vs conflict image, same question (% of answers)")
say(tab.to_string())
say("→ 'a number': it reads the printed label (any reader would; you can't get 120 from a bar's height).")
say("→ 'which one / trend': the text mostly doesn't move the answer, but 448 switches to it about 1 time in 5.")
say("→ 'yes / no': says yes ~75% of the time no matter what, so it rarely switches. Low switching here is a yes-habit, not evidence.\n")

# step 3
per = J.assign(t=J.result == "switched to text").pivot_table(index="stimulus", columns="model", values="t", aggfunc="mean")
up, down = int((per["448"] > per["224"]).sum()), int((per["448"] < per["224"]).sum())
tie = len(per) - up - down
p = min(1.0, 2 * sum(comb(up + down, k) for k in range(max(up, down), up + down + 1)) / 2 ** (up + down))
say("STEP 3 — resolution: share of answers that switched to the text, per chart")
say((per * 100).round(0).astype(int).sort_values("448", ascending=False).to_string())
say(f"→ mix-448 switched to the text more on {up} charts, less on {down}, tied on {tie}  (sign test p = {p:.3f}).")
say("→ Higher resolution = reads the printed numbers more. The most solid result in the run.")

text = out.getvalue()
(run / "simple.txt").write_text(text, encoding="utf-8")
print(text)

# figure: step 2
colors = {"stayed": "#9aa0a6", "switched to text": "#eb6834", "switched to other": "#d9dcdf"}
fig, ax = plt.subplots(figsize=(8, 3.6))
rows = [(g, m) for g in ORDER for m in ["224", "448"]]
for i, (g, m) in enumerate(rows):
    left = 0
    for c in COLS:
        v = tab.loc[(g, m), c]
        ax.barh(i, v, left=left, color=colors[c], label=c if i == 0 else None, edgecolor="white")
        if v >= 8:
            ax.text(left + v / 2, i, f"{v}%", ha="center", va="center", fontsize=9,
                    color="white" if c != "switched to other" else "#333")
        left += v
ax.set_yticks(range(len(rows)), [f"{g}  ·  mix-{m}" for g, m in rows])
ax.invert_yaxis()
ax.set_xlim(0, 100)
ax.set_xlabel("% of answers, consistent → conflict image (only the printed text differs)")
ax.legend(ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.0), frameon=False)
for s in ["top", "right"]:
    ax.spines[s].set_visible(False)
fig.tight_layout()
fig.savefig(run / "simple.png", dpi=200)
