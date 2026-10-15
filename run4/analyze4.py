"""Analyse run 4: E4 concrete comparisons + F model size (+ precision / hardware controls).

python3.12 run4/build4.py            # recreates run4/bundle/ (questions4.json), not in the repo
python3.12 run4/analyze4.py [answers_run4.csv] [out_dir]
  defaults: run4/results/answers_run4.csv and run4/results/

Writes report4.txt, results4.json, e4_compare.png, e5_ladder.png, f_size.png.
Model keys: 224 / 448 = 3B float32 (runs 1-3 setup), 224bf / 448bf = 3B bfloat16, 10b-* / 28b-* = bfloat16.
E4 "flip" questions = cmp_big_max ("is the number on the biggest mark the largest?") and cmp_small_min ("…on the smallest
mark the smallest?"): right answer yes on all 11 agreeing charts, no on all 11 lying ones -> 22 per cell.
E5 = the "no" ladder: L0 object / L1 text / L2 drawing questions with mostly NO answers, L3 = E4's comparisons.
"False yes" = share of yes when the right answer is no, on the AGREEING charts (on lying charts L2/L3 are cue conflicts).
Composition (E4, lying charts): for each chart x {biggest, smallest} mark, did the model name the mark right (drawing), quote
its printed number (text), and then answer the flip question right ("no")?
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd
from scipy import stats

R4 = Path(__file__).resolve().parent
ANS = Path(sys.argv[1]) if len(sys.argv) > 1 else R4 / "results" / "answers_run4.csv"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else R4 / "results"
OUT.mkdir(parents=True, exist_ok=True)
Q = pd.DataFrame(json.loads((R4 / "bundle" / "questions4.json").read_text(encoding="utf-8")))
A = pd.read_csv(ANS, keep_default_na=False).astype({"model": str})
ORDER = [m for m in ["224", "448", "224bf", "448bf", "10b-224", "10b-448", "28b-448"] if m in set(A.model)]
NAME = {"224": "3B-224 fp32", "448": "3B-448 fp32", "224bf": "3B-224", "448bf": "3B-448", "10b-224": "10B-224",
        "10b-448": "10B-448", "28b-448": "28B-448"}
lines, res = [], {}


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


NUM = re.compile(r"[-−]?\d+(?:[.,]\d+)?")


def nums(s):
    return [float(x.replace("−", "-").replace(",", ".")) for x in NUM.findall(str(s))]


def read_kind(answer, right, drawn):
    a, r, d = nums(answer), nums(right), nums(drawn)
    if r and a[:len(r)] == r:
        return "label"
    if d and a[:len(d)] == d:
        return "drawing"
    return "other"


def names_ok(answer, names):
    t = answer.lower()
    return any(re.search(rf"(?<![a-z0-9]){re.escape(n)}(?![a-z0-9])", t) for n in names)


M = A.merge(Q.drop(columns=["exp"]), on=["image", "prompt"], how="inner")
say(f"run 4: {len(A)} answers, {len(M)} matched to questions; models: " + ", ".join(f"{NAME[m]} ({(A.model == m).sum()})" for m in ORDER))
yesno = ~M.qtype.isin(["which_big", "which_small", "read_big", "read_small"])
M["level"] = M["level"].where(M["level"].astype(str).str.startswith("L"), "") if "level" in M else ""
M.loc[(M.exp == "E4") & M.qtype.str.startswith(("cmp", "any")), "level"] = "L3"
M.loc[yesno, "yn"] = M.loc[yesno, "answer"].map(yn)
codable = yesno & (M.yn == "other")
M.loc[codable, "yn"] = [yn_sentence(a, q) for a, q in zip(M.loc[codable, "answer"], M.loc[codable, "qtype"])]
sys.path.insert(0, str(R4.parent / "judge"))
import adj  # noqa: E402
JUDGED = {"yesno": 0, "which": 0, "read": 0}
if adj.available():
    for i, r in M[yesno].iterrows():
        v = adj.lookup("yesno", r.image, r.prompt, r.answer)
        if v is not None:
            M.at[i, "yn"] = v if v in ("yes", "no") else "other"
            JUDGED["yesno"] += 1

# ---------- controls
say("\nCONTROLS")
r3p = R4.parent / "run3" / "results" / "answers_run3.csv"
if r3p.exists():
    R3 = pd.read_csv(r3p, keep_default_na=False).astype({"model": str}).set_index(["model", "image", "prompt"]).answer
    res["control_hw"] = {}
    for k in ("224", "448"):
        f = M[(M.model == k) & (M.exp == "F")]
        same = int(sum(R3.get((k, i, p)) == a for i, p, a in zip(f.image, f.prompt, f.answer)))
        res["control_hw"][k] = [same, len(f)]
        say(f"  {NAME[k]} on this GPU vs run 3 on the T4: {same}/{len(f)} answers identical")
res["control_dtype"] = {}
for k in ("224", "448"):
    if k + "bf" in ORDER:
        a = M[M.model == k].set_index(["image", "prompt"]).answer
        b = M[M.model == k + "bf"].set_index(["image", "prompt"]).answer
        j = a.index.intersection(b.index)
        same = int((a[j] == b[j]).sum())
        res["control_dtype"][k] = [same, len(j)]
        say(f"  3B-{k} float32 vs bfloat16: {same}/{len(j)} answers identical")

# ---------- E4
E = M[M.exp == "E4"]
say("\nE4 · CONCRETE COMPARISONS (English, 11 charts)")
say("flip questions ('number on the biggest mark is the largest?' + 'on the smallest mark the smallest?'): share of yes,")
say("right answer = yes on agreeing, no on lying; p = Fisher exact, two-sided")
res["e4_flip"] = {}
for m in ORDER:
    f = E[(E.model == m) & E.qtype.isin(["cmp_big_max", "cmp_small_min"])]
    c, l = f[f.cond == "consistent"], f[f.cond == "conflict"]
    cy, ly = int((c.yn == "yes").sum()), int((l.yn == "yes").sum())
    p = stats.fisher_exact([[cy, len(c) - cy], [ly, len(l) - ly]])[1]
    res["e4_flip"][m] = {"consistent": [cy, len(c)], "conflict": [ly, len(l)], "p": p}
    say(f"  {NAME[m]:12s} yes {cy:2d}/{len(c)} → {ly:2d}/{len(l)}   p = {fp(p)}")

say("\nall 6 comparison questions: share right (agreeing / lying); a model that always says yes gets 22/66 and 38/66 here")
res["e4_cmp_right"] = {}
for m in ORDER:
    f = E[(E.model == m) & E.qtype.str.startswith(("cmp", "any"))]
    r = {cd: [int((g.yn == g.right).sum()), len(g)] for cd, g in f.groupby("cond")}
    res["e4_cmp_right"][m] = r
    say(f"  {NAME[m]:12s} agreeing {r['consistent'][0]}/{r['consistent'][1]} · lying {r['conflict'][0]}/{r['conflict'][1]} · "
        f"yes-share {(f.yn == 'yes').mean():.0%}")

say("\nexact-opposite pairs: 'is the number on the biggest mark the largest?' vs 'is any number larger than it?' (and the")
say("same for the smallest mark). caught = 'no' then 'yes' on a lying chart; false alarm = the same on an agreeing chart;")
say("yes/yes = says both, i.e. contradicts itself")
res["e4_pairs"] = {}
for m in ORDER:
    out = {}
    for cond in ("conflict", "consistent"):
        g = E[(E.model == m) & (E.cond == cond)].set_index(["stimulus", "qtype"]).yn
        caught = both_yes = n = 0
        for sid in E.stimulus.unique():
            for q1, q2 in (("cmp_big_max", "any_more_big"), ("cmp_small_min", "any_less_small")):
                if (sid, q1) in g.index and (sid, q2) in g.index:
                    a1, a2 = g[(sid, q1)], g[(sid, q2)]
                    n += 1
                    caught += a1 == "no" and a2 == "yes"
                    both_yes += a1 == "yes" and a2 == "yes"
        out[cond] = {"caught": int(caught), "yes_yes": int(both_yes), "n": n}
    res["e4_pairs"][m] = out
    p = stats.fisher_exact([[out["conflict"]["caught"], out["conflict"]["n"] - out["conflict"]["caught"]],
                            [out["consistent"]["caught"], out["consistent"]["n"] - out["consistent"]["caught"]]])[1]
    res["e4_pairs"][m]["p"] = p
    say(f"  {NAME[m]:12s} caught {out['conflict']['caught']}/{out['conflict']['n']} lying vs false alarm "
        f"{out['consistent']['caught']}/{out['consistent']['n']} agreeing (p {fp(p)}) · yes/yes {out['conflict']['yes_yes']} lying, "
        f"{out['consistent']['yes_yes']} agreeing")

say("\nthe two parts on the same images")
W = E[E.qtype.str.startswith("which")].copy()
def which_item(r):
    """the item the answer names: the judges' verdict if they decoded it, else the rule match"""
    v = adj.lookup("which", r.image, r.prompt, r.answer)
    if v is not None:
        JUDGED["which"] += 1
        return v if v != "none" else None
    hits = [n for n in r.allnames if names_ok(r.answer, [n])]
    return r.canon[hits[0]] if len(hits) == 1 else None


import build4  # noqa: E402
W["allnames"] = [build4.C[sid]["names"] + [a for v in build4.C[sid].get("alias", {}).values() for a in v] for sid in W.stimulus]
W["canon"] = [{**{n: n for n in build4.C[sid]["names"]}, **{a: k for k, v in build4.C[sid].get("alias", {}).items() for a in v}}
              for sid in W.stimulus]
W["named"] = [which_item(r) for r in W.itertuples()]
W["ok"] = W.named == W.item
TXT = {}
for sid, c in build4.C.items():
    vis, lie, *_ = build4.values(sid)
    TXT[(sid, "which_big")], TXT[(sid, "which_small")] = c["names"][lie.index(max(lie))], c["names"][lie.index(min(lie))]
W["text_item"] = [TXT[(sid, q)] for sid, q in zip(W.stimulus, W.qtype)]
R = E[E.qtype.str.startswith("read")].copy()
def read_answer(r):
    v = adj.lookup("read", r.image, r.prompt, r.answer)
    if v is not None:
        JUDGED["read"] += 1
        return v if v != "none" else ""
    return r.answer


R["kind"] = [read_kind(read_answer(r), r.right, r.drawn) for r in R.itertuples()]
res["e4_parts"] = {}
for m in ORDER:
    w, r = W[W.model == m], R[(R.model == m) & (R.cond == "conflict")]
    rc = R[(R.model == m) & (R.cond == "consistent")]
    res["e4_parts"][m] = {"which_ok": [int(w.ok.sum()), len(w)], "read_ok_agreeing": [int((rc.kind == "label").sum()), len(rc)],
                          "read_lying": {k: int((r.kind == k).sum()) for k in ("label", "drawing", "other")}}
    say(f"  {NAME[m]:12s} names the biggest/smallest mark {int(w.ok.sum())}/{len(w)} · reads the number (agreeing) "
        f"{int((rc.kind == 'label').sum())}/{len(rc)} · on lying charts quotes printed {int((r.kind == 'label').sum())}, "
        f"drawn {int((r.kind == 'drawing').sum())}, other {int((r.kind == 'other').sum())} of {len(r)}")

say("\nlying charts, 'which has the tallest / shortest mark?' (a drawing question): the drawing's item vs the numbers' item")
res["e4_which_lying"] = {}
for m in ORDER:
    w = W[(W.model == m) & (W.cond == "conflict")]
    d, t = int((w.named == w.item).sum()), int((w.named == w.text_item).sum())
    res["e4_which_lying"][m] = {"drawing": d, "numbers": t, "n": len(w)}
    say(f"  {NAME[m]:12s} drawing's item {d}/{len(w)} · numbers' item {t}/{len(w)} · other {len(w) - d - t}")
res["e4_which_agreeing"] = {m: [int(W[(W.model == m) & (W.cond == "consistent")].ok.sum()), int(((W.model == m) & (W.cond == "consistent")).sum())] for m in ORDER}
say("\ncomposition, lying charts: mark named right AND printed number quoted → flip question answered right ('no')?")
res["e4_composition"] = {}
for m in ORDER:
    rows = []
    for (sid, cond), g in E[(E.model == m) & (E.cond == "conflict")].groupby(["stimulus", "cond"]):
        for side, cq in (("big", "cmp_big_max"), ("small", "cmp_small_min")):
            wq = W[(W.model == m) & (W.stimulus == sid) & (W.cond == cond) & (W.qtype == f"which_{side}")]
            rq = R[(R.model == m) & (R.stimulus == sid) & (R.cond == cond) & (R.qtype == f"read_{side}")]
            cmpq = g[g.qtype == cq]
            if len(wq) and len(rq) and len(cmpq):
                rows.append({"stim": sid, "side": side, "has_both": bool(wq.ok.iloc[0]) and rq.kind.iloc[0] == "label",
                             "cmp_right": cmpq.yn.iloc[0] == "no"})
    d = pd.DataFrame(rows)
    hb = d[d.has_both]
    res["e4_composition"][m] = {"has_both": len(hb), "of": len(d), "cmp_right_given_both": int(hb.cmp_right.sum()),
                                "cmp_right_overall": int(d.cmp_right.sum())}
    say(f"  {NAME[m]:12s} has both facts on {len(hb)}/{len(d)} marks; of those, said 'no' (right) on {int(hb.cmp_right.sum())}")

# ---------- E5
say("\nE5 · THE 'NO' LADDER (English, agreeing charts; L3 = E4 comparisons)")
say("false yes = said yes where the right answer is no · true yes = said yes where it is yes")
L = M[(M.level.isin(["L0", "L1", "L2", "L3"])) & (M.cond == "consistent")]
res["e5"] = {}
for m in ORDER:
    row = {}
    for lv in ("L0", "L1", "L2", "L3"):
        g = L[(L.model == m) & (L.level == lv)]
        no_q, yes_q = g[g.right == "no"], g[g.right == "yes"]
        row[lv] = {"false_yes": [int((no_q.yn == "yes").sum()), len(no_q)], "true_yes": [int((yes_q.yn == "yes").sum()), len(yes_q)],
                   "other": int((g.yn == "other").sum())}
    res["e5"][m] = row
    say(f"  {NAME[m]:12s} " + " · ".join(f"{lv} false yes {r['false_yes'][0]:2d}/{r['false_yes'][1]:<2d} true yes {r['true_yes'][0]:2d}/{r['true_yes'][1]:<2d}"
                                       for lv, r in row.items()))
say("by question (false yes on agreeing charts, all models pooled):")
for (lv, qt), g in L[L.right == "no"].groupby(["level", "qtype"]):
    say(f"  {lv} {qt:15s} " + " · ".join(f"{NAME[m]} {int((g[g.model == m].yn == 'yes').sum())}/{int((g.model == m).sum())}" for m in ORDER))
lie = M[(M.exp == "E5") & (M.cond == "conflict") & (M.level == "L2") & (M.right == "no")]
say("L2 on LYING charts (the printed numbers point to the wrong item): false yes " + " · ".join(
    f"{NAME[m]} {int((lie[lie.model == m].yn == 'yes').sum())}/{int((lie.model == m).sum())}" for m in ORDER))
res["e5_l2_lying"] = {m: [int((lie[lie.model == m].yn == "yes").sum()), int((lie.model == m).sum())] for m in ORDER}

say(f"\njudge pass (judge/adjudication.json, two judges, both must agree): decoded {JUDGED['yesno']} yes/no, "
    f"{JUDGED['which']} 'which', {JUDGED['read']} 'read' answers" if adj.available() else "\nno judge pass applied")

# ---------- F
F = M[M.exp == "F"]
say("\nF · RUN 3 QUESTIONS BY MODEL (en + tr, 11 charts): share of yes, agreeing → lying (n = 22 each)")
res["f"] = {}
for m in ORDER:
    parts = []
    res["f"][m] = {}
    for qt in ("match", "mismatch", "error"):
        s = F[(F.model == m) & (F.qtype == qt)]
        c, l = s[s.cond == "consistent"], s[s.cond == "conflict"]
        cy, ly = int((c.yn == "yes").sum()), int((l.yn == "yes").sum())
        p = stats.fisher_exact([[cy, len(c) - cy], [ly, len(l) - ly]])[1]
        res["f"][m][qt] = {"consistent": [cy, len(c)], "conflict": [ly, len(l)], "p": p, "other": int((s.yn == "other").sum())}
        parts.append(f"{qt} {cy:2d}→{ly:2d} (p {fp(p)})")
    w = F[(F.model == m) & F.qtype.isin(["match", "mismatch"])].pivot_table(
        index=["image", "cond"], columns="qtype", values="yn", aggfunc="first").reset_index()
    w["caught"] = (w["match"] == "no") & (w["mismatch"] == "yes")
    cl, ca = int(w[w.cond == "conflict"].caught.sum()), int(w[w.cond == "consistent"].caught.sum())
    res["f"][m]["caught"] = {"lying": cl, "agreeing": ca}
    say(f"  {NAME[m]:12s} " + " · ".join(parts) + f" · caught {cl}/22 vs false alarm {ca}/22")
oth = M[yesno & (M.yn == "other")]
if len(oth):
    say(f"\nyes/no questions answered with something else: {len(oth)} (by model: "
        + ", ".join(f"{NAME[k]} {v}" for k, v in oth.model.value_counts().items()) + ")")
    for r in oth.head(8).itertuples():
        say(f"  [{NAME[r.model]}] {r.prompt.split(' ', 2)[2]} → {r.answer!r}")

(OUT / "report4.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
(OUT / "results4.json").write_text(json.dumps(res, indent=1), encoding="utf-8")

# ---------- figures
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

AG, LI = "#9aa5b1", "#1baf7a"


def paired(ax, labels, pairs, n):
    for i, (a, b) in enumerate(pairs):
        for j, (v, col) in enumerate(((a, AG), (b, LI))):
            ax.bar(i + (j - 0.5) * 0.36, v / n, 0.34, color=col, label=("numbers agree" if j == 0 else "numbers lie") if i == 0 else None)
            ax.text(i + (j - 0.5) * 0.36, v / n + 0.02, str(v), ha="center", fontsize=8)
    ax.set_xticks(range(len(labels)), labels, fontsize=8)
    ax.set_ylim(0, 1.12)
    ax.spines[["top", "right"]].set_visible(False)


bf = [m for m in ORDER if m not in ("224", "448")] or ORDER
fig, ax = plt.subplots(figsize=(1.3 * len(bf) + 1.5, 3.4))
paired(ax, [NAME[m] for m in bf], [(res["e4_flip"][m]["consistent"][0], res["e4_flip"][m]["conflict"][0]) for m in bf], 22)
ax.set_ylabel('share of "yes"')
ax.set_title('"Is the number on the biggest mark the largest?" + "…smallest mark the smallest?"', fontsize=9)
fig.legend(*ax.get_legend_handles_labels(), frameon=False, fontsize=8, loc="upper center", ncol=2)
fig.tight_layout(rect=(0, 0, 1, 0.9))
fig.savefig(OUT / "e4_compare.png", dpi=200)

fig, axes = plt.subplots(1, 3, figsize=(3.2 * 3, 3.4), sharey=True)
for ax, qt, title in zip(axes, ("match", "mismatch", "error"), ("numbers match the drawing?", "numbers contradict the drawing?", "mistake in this chart?")):
    paired(ax, [NAME[m] for m in bf], [(res["f"][m][qt]["consistent"][0], res["f"][m][qt]["conflict"][0]) for m in bf], 22)
    ax.set_title(title, fontsize=9)
    ax.tick_params(axis="x", labelrotation=30)
axes[0].set_ylabel('share of "yes"')
fig.legend(*axes[0].get_legend_handles_labels(), frameon=False, fontsize=8, loc="upper center", ncol=2)
fig.tight_layout(rect=(0, 0, 1, 0.9))
fig.savefig(OUT / "f_size.png", dpi=200)
COLS = {"224": "#2a78d6", "448": "#eb6834", "224bf": "#2a78d6", "448bf": "#eb6834", "10b-224": "#1baf7a", "10b-448": "#eda100",
        "28b-448": "#e87ba4"}
fig, ax = plt.subplots(figsize=(7.6, 3.6))
for m in ORDER:
    ys = [res["e5"][m][lv]["false_yes"][0] / max(res["e5"][m][lv]["false_yes"][1], 1) for lv in ("L0", "L1", "L2", "L3")]
    ax.plot(range(4), ys, marker="o", lw=2, ms=6, color=COLS[m], ls="--" if m in ("224", "448") else "-", label=NAME[m])
ax.set_xticks(range(4), ["L0 object\n(a dog?)", "L1 text\n(about car sales?)", "L2 drawing\n(january tallest?)", "L3 comparison\n(any number larger?)"], fontsize=8)
ax.set_ylim(-0.03, 1.05)
ax.set_ylabel('"yes" when the answer is no')
ax.set_title("Where does the model stop saying no? (agreeing charts)", fontsize=9)
ax.spines[["top", "right"]].set_visible(False)
ax.legend(frameon=False, fontsize=7, loc="upper left", bbox_to_anchor=(1.01, 1))
fig.tight_layout()
fig.savefig(OUT / "e5_ladder.png", dpi=200)
say(f"\nwrote {OUT / 'report4.txt'}, results4.json, e4_compare.png, e5_ladder.png, f_size.png")
