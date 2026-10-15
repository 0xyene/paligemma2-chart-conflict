"""Analyse run 3: does the model notice when the printed numbers contradict the drawing?

python3.12 run3/analyze3.py [answers_run3.csv] [out_dir]
  defaults: run3/results/answers_run3.csv and run3/results/

Writes report3.txt, results3.json and run3_yes.png.
Per (model, question) it compares the share of "yes" on the 22 consistent images with the 22 lying ones (Fisher exact,
two-sided). A model that compares numbers with the drawing says "yes" to *match* less, and to *contradict* / *mistake* more,
on the lying charts. Equal shares = the answer does not depend on whether the chart lies.
"Caught" (per image) = answered *match* no AND *contradict* yes, i.e. both polarities say "these disagree"; its rate on the
consistent images is the false-alarm rate it has to beat.
"""
import json
import sys
from pathlib import Path

import pandas as pd
from scipy import stats

R3 = Path(__file__).resolve().parent
ANS = Path(sys.argv[1]) if len(sys.argv) > 1 else R3 / "results" / "answers_run3.csv"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else R3 / "results"
OUT.mkdir(parents=True, exist_ok=True)
Q = pd.DataFrame(json.loads((R3 / "bundle" / "questions3.json").read_text(encoding="utf-8")))
A = pd.read_csv(ANS, keep_default_na=False).astype({"model": str})
QTYPES = ["match", "mismatch", "error"]
lines = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    lines.append(s)


def fp(p):
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def yn(a):
    w = a.lower().strip().split()
    w = w[0].strip(".,!?") if w else ""
    return "yes" if w in ("yes", "evet") else "no" if w in ("no", "hayır", "hayir") else "other"


def yn_sentence(a, qtype):
    """Second pass for full-sentence answers (mostly Turkish). Only unambiguous verdicts; everything else stays "other"."""
    t = a.lower()
    if qtype == "error":
        if "hata yok" in t or "hiçbir hata" in t or "no mistake" in t:
            return "no"
        if "hata var" in t or "hatalar gösteril" in t or "incorrect" in t or "sahte" in t or "düzgün değil" in t:
            return "yes"
    if qtype == "match":
        if "uyuşmuyor" in t:
            return "no"
        if "uyuşuyor" in t:
            return "yes"
    if qtype == "mismatch":
        if "çelişmiyor" in t:
            return "no"
        if "çelişiyor" in t:
            return "yes"
    return "other"


M = A.merge(Q, on=["image", "prompt"], how="inner")
missing = len(Q) * A.model.nunique() - len(M)
M["yn"] = M.answer.map(yn)
M["yn_strict"] = M.yn
coded = M.yn == "other"
M.loc[coded, "yn"] = [yn_sentence(a, q) for a, q in zip(M.loc[coded, "answer"], M.loc[coded, "qtype"])]
sys.path.insert(0, str(R3.parent / "judge"))
import adj  # noqa: E402
judged = changed = 0
if adj.available():
    for i, r in M.iterrows():
        v = adj.lookup("yesno", r.image, r.prompt, r.answer)
        if v is not None:
            new = v if v in ("yes", "no") else "other"
            judged += 1
            changed += new != M.at[i, "yn"]
            M.at[i, "yn"] = new
M["ok"] = M.yn == M.right
say(f"run 3: {len(M)} answers ({M.model.nunique()} models), {missing} missing; parsed:",
    " · ".join(f"{k} {v}" for k, v in M.yn.value_counts().items()))
say(f"sentence answers coded: {int((coded & (M.yn != 'other')).sum())} of {int(coded.sum())} "
    f"(e.g. 'Resimde hata var.' = yes, 'Sayılar çubuklarla çelişiyor.' = yes); counts below include them")
if judged:
    say(f"judge pass (judge/adjudication.json, two judges, both must agree): {judged} answers decoded, {changed} changed vs the rule coding")
other = M[M.yn == "other"]
if len(other):
    say("not yes/no:", "; ".join(f"[{r.model}] {r.prompt.split(' ', 2)[2]} → {r.answer!r}" for r in other.head(10).itertuples()))

res = {"n_answers": int(len(M)), "missing": int(missing), "yes": {}, "caught": {}}
say("\nshare of yes (consistent → lying), n = 22 images per cell; p = Fisher exact, two-sided")
for model in sorted(M.model.unique()):
    for qt in QTYPES:
        s = M[(M.model == model) & (M.qtype == qt)]
        c = s[s.cond == "consistent"]
        l = s[s.cond == "conflict"]
        cy, ly = int((c.yn == "yes").sum()), int((l.yn == "yes").sum())
        p = stats.fisher_exact([[cy, len(c) - cy], [ly, len(l) - ly]])[1]
        res["yes"][f"{model}_{qt}"] = {"consistent": [cy, len(c)], "conflict": [ly, len(l)], "p": p,
                                       "by_lang": {lg: [int((s[(s.cond == cd) & (s.lang == lg)].yn == "yes").sum()) for cd in ("consistent", "conflict")]
                                                   for lg in ("en", "tr")}}
        say(f"  mix-{model} {qt:8s} {cy:2d}/{len(c)} → {ly:2d}/{len(l)}   p = {fp(p)}   right answers {int(s.ok.sum())}/{len(s)}")

say("\ncaught = match 'no' AND contradict 'yes' on the same image")
W = M[M.qtype.isin(["match", "mismatch"])].pivot_table(index=["model", "image", "cond", "lang", "stimulus"], columns="qtype",
                                                       values="yn", aggfunc="first").reset_index()
W["caught"] = (W["match"] == "no") & (W["mismatch"] == "yes")
for model in sorted(W.model.unique()):
    w = W[W.model == model]
    lie, ok = w[w.cond == "conflict"], w[w.cond == "consistent"]
    p = stats.fisher_exact([[int(lie.caught.sum()), len(lie) - int(lie.caught.sum())], [int(ok.caught.sum()), len(ok) - int(ok.caught.sum())]])[1]
    res["caught"][model] = {"lying": [int(lie.caught.sum()), len(lie)], "consistent_false_alarm": [int(ok.caught.sum()), len(ok)], "p": p,
                            "charts": sorted(lie[lie.caught].stimulus.unique().tolist())}
    say(f"  mix-{model}: lying {int(lie.caught.sum())}/{len(lie)} · consistent (false alarm) {int(ok.caught.sum())}/{len(ok)}   p = {fp(p)}"
        + (f"   caught on: {', '.join(res['caught'][model]['charts'])}" if lie.caught.any() else ""))

say("\nanswer pattern per image (match / contradict):")
for model in sorted(W.model.unique()):
    w = W[W.model == model]
    tab = w.assign(pattern=w["match"] + "/" + w["mismatch"]).pivot_table(index="pattern", columns="cond", values="image", aggfunc="count", fill_value=0)
    say(f"  mix-{model}\n" + "\n".join("    " + l for l in tab.to_string().splitlines()))

(OUT / "report3.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
(OUT / "results3.json").write_text(json.dumps(res, indent=1), encoding="utf-8")

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

labels = {"match": "numbers match\nthe drawing?", "mismatch": "numbers contradict\nthe drawing?", "error": "mistake in\nthis chart?"}
models = sorted(M.model.unique())
fig, axes = plt.subplots(1, len(models), figsize=(4.2 * len(models), 3.4), sharey=True, squeeze=False)
for ax, model in zip(axes[0], models):
    for i, qt in enumerate(QTYPES):
        r = res["yes"][f"{model}_{qt}"]
        for j, (cond, col) in enumerate((("consistent", "#9aa5b1"), ("conflict", "#d1495b"))):
            k, n = r[cond]
            ax.bar(i + (j - 0.5) * 0.36, k / n, 0.34, color=col, label=("numbers agree" if j == 0 else "numbers lie") if i == 0 else None)
            ax.text(i + (j - 0.5) * 0.36, k / n + 0.02, f"{k}/{n}", ha="center", fontsize=8)
    ax.set_xticks(range(3), [labels[q] for q in QTYPES], fontsize=8)
    ax.set_title(f"mix-{model}", fontsize=10)
    ax.set_ylim(0, 1.1)
    ax.spines[["top", "right"]].set_visible(False)
axes[0][0].set_ylabel('share of "yes"')
fig.legend(*axes[0][0].get_legend_handles_labels(), frameon=False, fontsize=8, loc="upper center", ncol=2)
fig.tight_layout(rect=(0, 0, 1, 0.93))
fig.savefig(OUT / "run3_yes.png", dpi=200)
say(f"\nwrote {OUT / 'report3.txt'}, results3.json, run3_yes.png")
