"""Compute every number the HTML report shows from results/run1 (adjudicated results.csv), write report/data.json.

python3.12 report/make_data.py

Vocabulary used throughout (one question, one model, one language = one "item"):
  V = the drawing's answer       (right on the true and no-numbers charts)
  T = the lying text's answer    (what the conflict chart's printed text says; a specific wrong answer elsewhere)
  O = anything else
Each item has a state on three images: none (no numbers), true (consistent), lie (conflict).
"Switched to the text" = T on the lie image, not T on the true image. Only the printed text differs between the two.
"About the drawing" = every question except the 11 "how much is X?" (kind read_value) questions, the notebook's pre-run
headline rule ("number questions are kept out of the headline numbers").
"""
import ast
import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "results" / "run1"
sys.path.insert(0, str(ROOT / "common"))
from scoring import match  # noqa: E402

MODELS, LANGS = ["224", "448"], ["en", "tr"]
df = pd.read_csv(RUN / "results.csv", keep_default_na=False).astype({"model": str})
for c in ("visual", "text", "en_visual", "en_text"):
    df[c] = df[c].apply(ast.literal_eval)
specs = {p.parent.name: json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "stimuli").glob("s*/spec.json"))}
A = pd.read_csv(RUN / "answers.csv", keep_default_na=False).astype({"model": str})
f = float
GROUP_LABEL = {"name": "Which one is biggest / smallest?", "direction": "Up or down? Higher or lower?", "yesno": "Yes / no",
               "number": "How much is X?"}


def group(answer_type, kind):
    """By what the question asks: read_value = "how much is X?"; argmax/argmin = "which one?" (also when the answer is a
    year); trend, relation and s11's "how many stocks went up?" = direction."""
    if kind == "read_value":
        return "number"
    if answer_type == "yesno":
        return "yesno"
    if kind in ("argmax", "argmin"):
        return "name"
    return "direction"


def lst(v, ev, lang):                       # Turkish rows accept the English answer too (the notebook's rule)
    return v + (ev if lang == "tr" else [])


def norm(a):
    return a.strip().lower() if isinstance(a, str) else a


# ---------- one row per item, with its state on the three images
key = ["model", "lang", "qid"]
C = df[df.cond == "consistent"].set_index(key)
X = df[df.cond == "conflict"].set_index(key)
N = df[df.cond == "nonumbers"].set_index(key)
I = C[["stimulus", "mechanism", "conflict_has_truth", "answer_type", "kind", "pair", "cue_px", "prompt", "answer", "outcome"]].rename(
    columns={"answer": "a_true", "outcome": "o_true"})
I = I.join(X[["answer", "outcome", "text", "en_text"]].rename(columns={"answer": "a_lie", "outcome": "o_lie"}))
I = I.join(N[["answer", "outcome"]].rename(columns={"answer": "a_none", "outcome": "o_none"})).reset_index()
I["group"] = [group(a, k) for a, k in zip(I.answer_type, I.kind)]
I["draw"] = I.group.ne("number")
I["T"] = [lst(t, et, l) for t, et, l in zip(I.text, I.en_text, I.lang)]


def state_plain(a, o, T, lang):              # true / none images: right = V, the lie's answer = T
    if not isinstance(o, str):
        return None
    return "V" if o == "correct" else "T" if match(a, T, lang) else "O"


I["s_lie"] = I.o_lie.map({"visual": "V", "text": "T"}).fillna("O")
assert not (I.o_lie == "both").any()
I["s_true"] = [state_plain(a, o, T, l) for a, o, T, l in zip(I.a_true, I.o_true, I["T"], I.lang)]
I["s_none"] = [state_plain(a, o, T, l) for a, o, T, l in zip(I.a_none, I.o_none, I["T"], I.lang)]
# A hand override (adjudication.csv) was applied to one row only. The same answer string must get the same state on
# every image of an item, so copy the lying image's state to an identical answer on the true / no-numbers image.
# This touches exactly one item: 224 / tr / s11_q1, 'tltwy' on all three images.
same_true = [norm(a) == norm(b) and s != t for a, b, s, t in zip(I.a_true, I.a_lie, I.s_true, I.s_lie)]
same_none = [isinstance(s, str) and norm(a) == norm(b) and s != t for a, b, s, t in zip(I.a_none, I.a_lie, I.s_none, I.s_lie)]
fixed = I[pd.Series(same_true) | pd.Series(same_none)][key].drop_duplicates().values.tolist()
assert fixed == [["224", "tr", "s11_q1"]], fixed
I.loc[same_true, "s_true"] = I.loc[same_true, "s_lie"]
I.loc[same_none, "s_none"] = I.loc[same_none, "s_lie"]
I["sw"] = I.s_lie.eq("T") & I.s_true.ne("T")          # switched to the text
I["has_none"] = I.s_none.notna()

out = {"meta": {
    "charts": len(specs), "images": 84, "questions": sum(len(s["questions"]) for s in specs.values()),
    "answers": len(A), "rows_per_model": int(len(A) / 2), "items_per_model": int(len(I) / 2),
    "draw_items": int(I[I.model == "448"].draw.sum()), "draw_questions": int(I[(I.model == "448") & (I.lang == "en")].draw.sum()),
    "sec_per_answer": {m: f(A[A.model == m].seconds.median()) for m in MODELS},
    "minutes": {m: round(float(A[A.model == m].seconds.sum() / 60), 1) for m in MODELS},
}}
out["paper"] = [["ChartQA (augmented)", 74.4, 89.2], ["ChartQA (human)", 42.0, 54.0], ["DocVQA", 39.9, 73.6],
                ["InfoVQA", 25.2, 37.5], ["AI2D", 74.7, 76.0]]


def boot(d, fn, reps=4000, seed=0):
    """95% interval, resampling whole charts (answers from one chart are not independent)."""
    rng = np.random.default_rng(seed)
    parts = [g for _, g in d.groupby("stimulus")]
    vals = [fn(pd.concat([parts[i] for i in rng.integers(0, len(parts), len(parts))])) for _ in range(reps)]
    return [f(v) for v in np.nanpercentile(vals, [2.5, 97.5])]


def rate(d, col="sw"):
    return f(d[col].mean()) if len(d) else float("nan")


# ---------- 1. can it read the charts?
acc = {}
for m in MODELS:
    for l in LANGS:
        d = I[(I.model == m) & (I.lang == l)]
        acc[f"{m}_{l}"] = {"true_all": f(d.s_true.eq("V").mean()),
                           "true": f(d[d.has_none].s_true.eq("V").mean()), "none": f(d[d.has_none].s_none.eq("V").mean()),
                           "n_all": int(len(d)), "n": int(d.has_none.sum())}
out["accuracy"] = acc

YES, NO = ["yes", "evet"], ["no", "hayır", "^değil"]
yn = df[df.answer_type == "yesno"].copy()
yn["said"] = [("yes" if match(a, YES, l) else "no" if match(a, NO, l) else "?") for a, l in zip(yn.answer, yn.lang)]
out["yes_rate"] = {m: {c: f(yn[(yn.model == m) & (yn.cond == c)].said.eq("yes").mean()) for c in ("nonumbers", "consistent", "conflict")}
                   for m in MODELS}


def pair_pattern(g):
    """Two opposite questions ("more?" / "fewer?"). drawing = both match the drawing, text = both match the text."""
    if len(g) != 2 or (g.said == "?").any():
        return "unclear"
    if g.said.nunique() == 1:
        return "yes-yes" if g.said.iloc[0] == "yes" else "no-no"
    vis = all(match(a, lst(v, ev, l), l) for a, v, ev, l in zip(g.answer, g.visual, g.en_visual, g.lang))
    return "drawing" if vis else "text"


P = pd.DataFrame([{"model": k[0], "cond": k[1], "lang": k[2], "pair": k[3], "stimulus": k[4], "pattern": pair_pattern(g)}
                  for k, g in yn.groupby(["model", "cond", "lang", "pair", "stimulus"])])
out["pairs"] = {m: {c: [{"stimulus": r.stimulus, "lang": r.lang, "pattern": r.pattern} for r in
                        P[(P.model == m) & (P.cond == c)].sort_values(["stimulus", "lang"]).itertuples()]
                    for c in ("nonumbers", "consistent", "conflict")} for m in MODELS}
T_ = df[df.lang == "tr"]
out["in_english"] = {m: {"yesno": f(T_[(T_.model == m) & (T_.answer_type == "yesno")].in_english.astype(str).eq("True").mean()),
                         "other": f(T_[(T_.model == m) & (T_.answer_type != "yesno")].in_english.astype(str).eq("True").mean())}
                     for m in MODELS}

# ---------- 2. where the answers go when the numbers lie (3 × 3 flows)
SUBSETS = {"all": lambda d: d, "nonum": lambda d: d[d.draw], "name": lambda d: d[d.group == "name"],
           "direction": lambda d: d[d.group == "direction"], "yesno": lambda d: d[d.group == "yesno"],
           "number": lambda d: d[d.group == "number"]}
flows = {}
for m in MODELS:
    for s, fn in SUBSETS.items():
        d = fn(I[I.model == m])
        flows[f"{m}_{s}"] = {a: {b: int(((d.s_true == a) & (d.s_lie == b)).sum()) for b in "VTO"} for a in "VTO"}
out["flows"] = flows

head = {}
for m in MODELS:
    d = I[I.model == m]
    h = {}
    for s in ("all", "nonum"):
        e = SUBSETS[s](d)
        v = e[e.s_true == "V"]
        into, outof = int(e.sw.sum()), int(((e.s_true == "T") & (e.s_lie != "T")).sum())
        strict = e.sw & e.s_none.ne("T")
        h[s] = {"n": int(len(e)), "sw": rate(e), "sw_ci": boot(e, rate), "sw_count": into,
                "fromV_n": int(len(v)), "fromV_T": int((v.s_lie == "T").sum()), "fromV_O": int((v.s_lie == "O").sum()),
                "fromV_rate": f((v.s_lie == "T").mean()), "into_T": into, "out_of_T": outof,
                "p_into_vs_out": f(stats.binomtest(into, into + outof).pvalue),
                "strict_count": int(strict.sum()), "strict": f(strict.mean())}
    e = d[d.draw & ~d.qid.isin(["s06_q3a", "s06_q3b"])]          # s06's freezing questions need the readout (spec: nonumbers=false)
    h["nonum_no_s06freeze"] = {"n": int(len(e)), "sw_count": int(e.sw.sum()), "sw": rate(e)}
    head[m] = h
out["head"] = head

# the test planned before the run (notebook §4): conflict answers on units the model got right from the DRAWING ALONE.
# unit = a non-yes/no drawing question, or a yes/no pair scored as a pair
plan = {}
for m in MODELS:
    o = I[(I.model == m) & I.draw & (I.group != "yesno") & I.s_none.eq("V")]
    ok_pairs = P[(P.model == m) & (P.cond == "nonumbers") & (P.pattern == "drawing")][["lang", "pair"]]
    px = P[(P.model == m) & (P.cond == "conflict")].merge(ok_pairs, on=["lang", "pair"])
    plan[m] = {"units": int(len(o) + len(px)), "text": int(o.s_lie.eq("T").sum() + px.pattern.eq("text").sum()),
               "drawing": int(o.s_lie.eq("V").sum() + px.pattern.eq("drawing").sum())}
out["planned"] = plan

# ---------- 3. the text's pull by question type: how often it gives the lie's answer on each image
pull = {}
for m in MODELS:
    rows = []
    for g in ["name", "direction", "yesno", "number"]:
        d = I[(I.model == m) & (I.group == g)]
        w = d[d.has_none]
        rows.append({"group": g, "label": GROUP_LABEL[g], "n": int(len(d)), "n_twin": int(len(w)),
                     "T_none": f(w.s_none.eq("T").mean()) if len(w) else None,
                     "T_true": f(d.s_true.eq("T").mean()), "T_lie": f(d.s_lie.eq("T").mean()),
                     "T_lie_count": int(d.s_lie.eq("T").sum()), "T_true_count": int(d.s_true.eq("T").sum()), "sw": rate(d)})
    w = I[(I.model == m) & I.has_none & I.draw]
    rows.append({"group": "twin", "label": "Questions asked in all three versions", "n": int(len(w)), "n_twin": int(len(w)),
                 "T_none": f(w.s_none.eq("T").mean()), "T_true": f(w.s_true.eq("T").mean()), "T_lie": f(w.s_lie.eq("T").mean()),
                 "sw": rate(w)})
    pull[m] = rows
out["pull"] = pull

yv = I[(I.group == "yesno") & (I.s_true == "V")].copy()
yv["lie_says_yes"] = [t[0] in ("yes", "evet") for t in yv.text]
out["yes_lie"] = {m: {k: {"n": int(len(g)), "sw": int(g.sw.sum())} for k, g in
                      (("yes", yv[(yv.model == m) & yv.lie_says_yes]), ("no", yv[(yv.model == m) & ~yv.lie_says_yes]))}
                  for m in MODELS}

# ---------- 4. per chart (all questions and drawing questions)
charts = []
for sid, s in specs.items():
    d = I[I.stimulus == sid]
    row = {"id": sid, "short": sid.split("_")[0], "title": s["title"]["en"], "style": s["style"], "chart": s["chart"],
           "mechanism": s["mechanism"], "truth": bool(s["conflict_has_truth"]), "cue_px": int(d.cue_px.iloc[0]),
           "summary": s["conflict_summary"]}
    for m in MODELS:
        e = d[d.model == m]
        dr = e[e.draw]
        row[m] = {"n": int(len(e)), "sw": rate(e), "sw_count": int(e.sw.sum()), "right_true": f(e.s_true.eq("V").mean()),
                  "dn": int(len(dr)), "dsw": rate(dr), "dsw_count": int(dr.sw.sum()), "eff_px": f(row["cue_px"] * int(m) / 896)}
    charts.append(row)
out["charts"] = charts


def scale_lane(mech):
    return mech in ("axis", "legend")


def perm_p(vals_by_chart, scale_ids):
    """Exact one-sided chart-level permutation test: share of 3-chart subsets whose mean switch rate is <= the scale charts'."""
    obs = np.mean([vals_by_chart[c] for c in scale_ids])
    ids = list(vals_by_chart)
    subs = list(combinations(ids, len(scale_ids)))
    return f(np.mean([np.mean([vals_by_chart[c] for c in s]) <= obs + 1e-12 for s in subs]))


# value text (labels, readouts: the lie is wrong) vs scale text (axis ticks, legend: the text is the truth); drawing questions
role = {}
for m in MODELS:
    d = I[(I.model == m) & I.draw]
    val, scale = d[~d.mechanism.map(scale_lane)], d[d.mechanism.map(scale_lane)]
    by_chart = {c["id"]: c[m]["dsw"] for c in charts}
    scale_ids = [c["id"] for c in charts if scale_lane(c["mechanism"])]
    small = d[(d.mechanism == "label") & (d.cue_px <= 24)]
    small_by = small.groupby("stimulus").sw.sum()
    elig = scale[scale.s_true != "T"]
    hm = I[(I.model == m) & (I.group == "number")]
    sc_all = I[(I.model == m) & I.mechanism.map(scale_lane)]
    tick = I[(I.model == m) & I.stimulus.isin(["s02_magazine_line_inverted", "s12_textbook_scatter"]) & I.has_none]
    role[m] = {
        "value": {"n": int(len(val)), "sw_count": int(val.sw.sum()), "sw": rate(val),
                  "charts": int(val.stimulus.nunique()), "charts_moved": int((val.groupby("stimulus").sw.sum() > 0).sum())},
        "scale": {"n": int(len(scale)), "sw_count": int(scale.sw.sum()), "charts": len(scale_ids),
                  "eligible": int(len(elig)), "already_T": int((scale.s_true == "T").sum())},
        "scale_all": {"n": int(len(sc_all)), "sw_count": int(sc_all.sw.sum()), "eligible": int((sc_all.s_true != "T").sum()),
                      "already_T": int((sc_all.s_true == "T").sum()), "lie_V": int(sc_all.s_lie.eq("V").sum()),
                      "lie_T": int(sc_all.s_lie.eq("T").sum()),
                      "lie_T_same_as_true": int((sc_all.s_lie.eq("T") & (sc_all.a_lie.map(norm) == sc_all.a_true.map(norm))).sum())},
        "perm_p": perm_p(by_chart, scale_ids),
        "value_small": {"n": int(len(small)), "sw_count": int(small.sw.sum()), "charts": int(small.stimulus.nunique()),
                        "zero_charts": int((small_by == 0).sum()), "s11": int(small_by.get("s11_finance_watchlist", 0)),
                        "px": [int(small.cue_px.min()), int(small.cue_px.max())]},
        "scale_px": [int(scale.cue_px.min()), int(scale.cue_px.max())],
        "howmuch": {"n": int(len(hm)), "lie": int(hm.s_lie.eq("T").sum()), "true": int(hm.s_true.eq("T").sum())},
        "tick_removed": {"n": int(len(tick)), "unchanged": int((tick.a_none.map(norm) == tick.a_true.map(norm)).sum())},
        "s10_right_true": f(I[(I.model == m) & (I.stimulus == "s10_report_tilemap")].s_true.eq("V").mean()),
    }
out["role"] = role
out["s12_q5_true"] = [a for a in I[I.qid == "s12_q5"].sort_values(["model", "lang"]).a_true]

# ---------- 5. resolution: same items, both models
def mcnemar(sub):
    w = sub.pivot_table(index=["lang", "qid"], columns="model", values="sw", aggfunc="first").astype(bool)
    b, c = int((w["448"] & ~w["224"]).sum()), int((~w["448"] & w["224"]).sum())
    return {"only448": b, "only224": c, "both": int((w["448"] & w["224"]).sum()), "neither": int((~w["448"] & ~w["224"]).sum()),
            "p": f(stats.binomtest(b, b + c).pvalue)}


def sign(col):
    cs = [(c["448"][col], c["224"][col]) for c in charts]
    more, less = sum(a > b + 1e-12 for a, b in cs), sum(a < b - 1e-12 for a, b in cs)
    return {"more": more, "less": less, "tie": len(cs) - more - less, "p": f(stats.binomtest(more, more + less).pvalue)}


def diff_ci(sub):
    def fn(x):
        return f(x[x.model == "448"].sw.mean() - x[x.model == "224"].sw.mean())
    return {"diff": fn(sub), "ci": boot(sub, fn)}


res = {"all": mcnemar(I), "nonum": mcnemar(I[I.draw]), "charts": sign("sw"), "charts_nonum": sign("dsw"),
       "diff_all": diff_ci(I), "diff_nonum": diff_ci(I[I.draw])}
size = {}
for m in MODELS:
    pm = [(c["cue_px"], c[m]["sw"]) for c in charts if not scale_lane(c["mechanism"])]
    rm = stats.spearmanr([p[0] for p in pm], [p[1] for p in pm])
    size[m] = {"rho": f(rm.statistic), "p": f(rm.pvalue), "n": len(pm)}
pts = [(c[m]["eff_px"], c[m]["sw"]) for c in charts for m in MODELS if not scale_lane(c["mechanism"])]
size["pooled_rho"] = f(stats.spearmanr([p[0] for p in pts], [p[1] for p in pts]).statistic)
size["pooled_n"] = len(pts)
res["size"] = size
out["resolution"] = res

# ---------- 6. language: same items, English vs Turkish, drawing questions
lang = {}
for m in MODELS:
    d = I[(I.model == m) & I.draw]
    w = d.pivot_table(index="qid", columns="lang", values="sw", aggfunc="first").astype(bool)
    b, c = int((w.en & ~w.tr).sum()), int((~w.en & w.tr).sum())
    lang[m] = {l: {"n": int((d.lang == l).sum()), "count": int(d[d.lang == l].sw.sum()), "rate": rate(d[d.lang == l])} for l in LANGS}
    lang[m].update({"only_en": b, "only_tr": c, "p": f(stats.binomtest(b, b + c).pvalue) if b + c else 1.0})
out["language"] = lang

# ---------- 7. wrong "which one?" answers: what it says when it can't read the chart
REAL = {"samsung", "nokia", "berlin", "amsterdam", "istanbul", "konya", "instagram", "k-nearest neighbor"}
wr = df[(df.answer_type == "name") & df.outcome.isin(["wrong", "neither"])].copy()
wr["a"] = wr.answer.str.lower().str.strip()
real = wr[wr.a.isin(REAL)]
out["wrong_names"] = {
    "total": int(len(wr)), "real_count": int(len(real)),
    "real_world": [{"answer": a, "count": int(len(g)), "chart": sid.split("_")[0],
                    "models": sorted(g.model.unique().tolist()), "langs": sorted(g.lang.unique().tolist())}
                   for (a, sid), g in real.groupby(["a", "stimulus"])],
}
s07 = df[(df.stimulus == "s07_dashboard_gauges") & (df.answer_type == "name")]
out["wrong_names"]["alpha"] = {"n": int(len(s07)), "alpha": int(s07.answer.str.lower().eq("alpha-01").sum()),
                               "right": int(s07.outcome.isin(["correct", "visual"]).sum())}
oo = I[(I.s_true == "O") & (I.s_lie == "O")]
out["wrong_names"]["o_same"] = {"n": int(len(oo)), "same": int((oo.a_true.map(norm) == oo.a_lie.map(norm)).sum())}

# ---------- 8. the explorer: every question, both models, both languages, three images
def show(v):
    return v[0] if v else ""


ex = []
for sid, s in specs.items():
    qs = []
    for q in s["questions"]:
        d = I[I.qid == q["qid"]]
        cells = {f"{r.model}_{r.lang}": {"none": [r.a_none, r.s_none] if isinstance(r.s_none, str) else None,
                                         "true": [r.a_true, r.s_true], "lie": [r.a_lie, r.s_lie]} for r in d.itertuples()}
        qs.append({"qid": q["qid"], "group": d.group.iloc[0], "pair": q["pair"],
                   "en": q["prompt"]["en"].removeprefix("answer en "), "tr": q["prompt"]["tr"].removeprefix("answer tr "),
                   "V": {l: show(q["visual"][l]) for l in LANGS}, "T": {l: show(q["text"][l]) for l in LANGS}, "cells": cells})
    ex.append({"id": sid, "short": sid.split("_")[0], "title": s["title"]["en"], "mechanism": s["mechanism"],
               "truth": bool(s["conflict_has_truth"]), "summary": s["conflict_summary"], "questions": qs})
out["explorer"] = ex

adj = json.loads((RUN / "adjudicate_items.json").read_text())
out["judging"] = {"distinct": len(adj), "rows": int(sum(x["rows"] for x in adj))}

# ---------- run 2 (run2/results/results2.json from run2/analyze2.py; predictions in run2/PREDICTIONS.md, written before the run)
R2J = json.loads((Path(__file__).resolve().parents[1] / "run2" / "results" / "results2.json").read_text(encoding="utf-8"))
e2, post = R2J["E2"], R2J["post"]
row = {"448": "mix-448 (run 1, adjudicated)", "448d": "mix-448 on 224-detail (run 2, adjudicated)", "224": "mix-224 (run 1, adjudicated)"}
r2 = {"e2c": R2J["E2c"], "e3_repeat": post["E3_repeat"], "n_answers": R2J["n_answers"], "missing": R2J["missing"]}
r2["e2"] = {k: {"draw_count": e2[v]["draw_count"], "draw_n": e2[v]["draw_n"], "draw": e2[v]["draw"], "draw_ci": e2[v]["draw_ci"],
                "hm_lie": e2[v]["howmuch_lie"], "hm_n": e2[v]["howmuch_n"], "hm_lie_ci": e2[v]["howmuch_ci"],
                "acc_right": post["E2_accuracy"][k]["right"], "acc_n": post["E2_accuracy"][k]["n"], "acc_ci": post["E2_accuracy"][k]["ci"],
                "hm_right": post["E2_accuracy"][k]["hm_right"], "hm_acc_ci": post["E2_accuracy"][k]["hm_ci"]}
            for k, v in row.items()}
r2["e2_diff"] = {"sw_vs224": e2["diff degraded − mix-224"], "sw_vs448": e2["diff mix-448 − degraded"],
                 "acc_vs448": post["E2_accuracy"]["diff mix-448 − degraded"], "acc_vs224": post["E2_accuracy"]["diff degraded − mix-224"]}
r2["e2_charts"] = {"vs448_draw": e2["vs mix-448 (run 1) drawing q"], "vs224_draw": e2["vs mix-224 (run 1) drawing q"],
                   "vs448_all": e2["vs mix-448 (run 1) all q"], "vs224_all": e2["vs mix-224 (run 1) all q"]}
r2["e2_gap"] = {"draw": e2["gap_closed_draw_adj"], "draw_raw": e2["gap_closed_draw"], "howmuch": e2["gap_closed_howmuch"]}
r2["e2_agree"] = post["E2_agree"]
r2["e2_agree_outcome"] = post["E2_agree_outcome"]
r2["e2_gap_ci"] = post["E2_gap_ci"]
r2["e2_habits"] = post["E2_habits"]
r2["e1_axes"] = post["E1_axes"]
r2["e1_changed"] = post["E1_changed"]
# E3: which question kinds switched at mix-448 (threshold questions exist only on s06 and s13)
I3 = pd.read_csv(Path(__file__).resolve().parents[1] / "run2" / "results" / "e3_items.csv", keep_default_na=False)
I3 = I3[I3.draw.astype(str).eq("True") & I3.sw.astype(str).eq("True")]
r2["e3_kinds"] = {m: {"threshold": int(((I3.base_model.astype(str) == m) & (I3.kind == "threshold")).sum()),
                      "rank": int(((I3.base_model.astype(str) == m) & I3.kind.isin(["argmax", "argmin"])).sum()),
                      "rank_s01_s14": int(((I3.base_model.astype(str) == m) & I3.kind.isin(["argmax", "argmin"]) & I3.stimulus.isin(["s01_newspaper_bars", "s14_spreadsheet_databars"])).sum()),
                      "all": int((I3.base_model.astype(str) == m).sum())} for m in ("224", "448")}
r2["e1_versions"] = post["E1_versions"]
# E1 answer grid: numeric reading probes, answers per model/language on the normal and the flipped version
PROBE_NAME = {"s02_p1": "top of the y-axis", "s02_p2": "bottom of the y-axis", "s12_p1": "left end of the x-axis",
              "s12_p2": "right end of the x-axis", "s10_p1": "top of the legend"}
PRINTED = {"s02_p1": ("600", "0"), "s02_p2": ("0", "600"), "s12_p1": ("0", "14"), "s12_p2": ("14", "0"), "s10_p1": ("80", "10")}
grid = []
for pid, name in PROBE_NAME.items():
    cells = {}
    for r in R2J["E1_rows"]:
        if r["qid"] == pid:
            cells[f'{r["cond"]}_{r["model"]}_{r["lang"]}'] = [r["answer"], {"right": "P", "habit": "U"}.get(r["e1"], "O")]
    grid.append({"qid": pid, "chart": pid.split("_")[0], "name": name, "printed": {"consistent": PRINTED[pid][0], "conflict": PRINTED[pid][1]}, "cells": cells})
r2["e1_grid"] = grid
r2["e1_through"] = {m: R2J["E1"][m]["through"] for m in ("224", "448")}
r2["e1_word"] = sorted({r["answer"] for r in R2J["E1_rows"] if r["qid"] == "s10_p2"})
# E3: per chart × size × model
r2["e3"] = [{k: r[k] for k in ("model", "stimulus", "k", "cue_px", "eff_px", "draw_sw", "draw_n", "hm_lie", "hm_n")} for r in R2J["E3"]]
sweep = {json.loads(p.read_text())["sid"]: json.loads(p.read_text()) for p in (Path(__file__).resolve().parents[1] / "run2" / "size_sweep").glob("s*.json")}
r2["e3_original_k"] = {sid: next(s["k"] for s in info["sizes"] if s["original"]) for sid, info in sweep.items()}
r2["e3_pooled"] = {m: {str(k): {"draw_sw": sum(r["draw_sw"] for r in R2J["E3"] if r["model"] == m and r["k"] == k),
                                "draw_n": sum(r["draw_n"] for r in R2J["E3"] if r["model"] == m and r["k"] == k),
                                "hm_lie": sum(r["hm_lie"] for r in R2J["E3"] if r["model"] == m and r["k"] == k),
                                "hm_n": sum(r["hm_n"] for r in R2J["E3"] if r["model"] == m and r["k"] == k)} for k in (1, 2, 3, 4)}
                   for m in ("224", "448")}
adj2 = json.loads((Path(__file__).resolve().parents[1] / "run2" / "results" / "adjudication2.json").read_text(encoding="utf-8"))["items"]
r2["judging"] = {"new": len(adj2), "changed": sum(a["verdict"] != "neither" for a in adj2), "agree": sum(a["judge_A"] == a["judge_B"] for a in adj2)}
out["run2"] = r2

(Path(__file__).parent / "data.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, allow_nan=False), encoding="utf-8")

# ---------- cross-checks against the notebook's own report (results/run1/report.txt) and the earlier summaries
rep = (RUN / "report.txt").read_text(encoding="utf-8")
assert "en     0.54  0.64" in rep and round(acc["448_en"]["true_all"], 2) == 0.64 and round(acc["224_tr"]["true_all"], 2) == 0.43, acc
assert round(out["yes_rate"]["448"]["consistent"], 2) == 0.75
assert flows["448_all"]["V"] == {"V": 45, "T": 36, "O": 3} and flows["224_all"]["V"] == {"V": 46, "T": 18, "O": 4}, flows
assert head["448"]["all"]["sw_count"] == 41 and head["224"]["all"]["sw_count"] == 19
assert head["448"]["nonum"]["sw_count"] == 21 and head["224"]["nonum"]["sw_count"] == 8
assert (head["448"]["nonum"]["strict_count"], head["224"]["nonum"]["strict_count"]) == (12, 7)
assert res["all"]["only448"] == 22 and res["all"]["only224"] == 0 and res["nonum"]["only448"] == 13 and res["nonum"]["only224"] == 0
assert (res["charts"]["more"], res["charts"]["less"]) == (9, 0) and (res["charts_nonum"]["more"], res["charts_nonum"]["less"]) == (7, 0)
assert (plan["448"]["text"], plan["448"]["units"], plan["224"]["text"], plan["224"]["units"]) == (6, 33, 2, 25), plan
assert role["448"]["scale_all"]["sw_count"] == 0 and role["224"]["scale_all"]["sw_count"] == 0
assert role["448"]["scale_all"]["eligible"] + role["224"]["scale_all"]["eligible"] == 41
assert (role["448"]["value"]["sw_count"], role["448"]["value"]["n"], role["448"]["value"]["charts_moved"]) == (21, 92, 8)
assert (role["448"]["value_small"]["sw_count"], role["448"]["value_small"]["n"]) == (7, 52)
assert abs(role["448"]["perm_p"] - 20 / 364) < 1e-9
# run 2: the adjudicated run-1 rows analyze2 uses must be the report's own numbers
assert (r2["e2"]["448"]["draw_count"], r2["e2"]["224"]["draw_count"]) == (head["448"]["nonum"]["sw_count"], head["224"]["nonum"]["sw_count"]) == (21, 8)
assert r2["e2"]["448d"]["draw_count"] == 18 and r2["e2c"] == {"n": 140, "same": 140} and r2["e3_repeat"] == {"n": 80, "same": 80}
assert (r2["e2_agree"]["differ"], r2["e2_agree"]["like448"], r2["e2_agree"]["like224"]) == (118, 75, 7)
assert r2["e1_versions"]["both"] == {"consistent": [8, 12], "conflict": [1, 12]}
assert (r2["e2"]["448"]["acc_right"], r2["e2"]["448d"]["acc_right"], r2["e2"]["224"]["acc_right"]) == (65, 55, 55)
assert r2["judging"] == {"new": 30, "changed": 2, "agree": 30}
assert r2["e2_agree_outcome"]["differ"] == 83 and (r2["e2_agree_outcome"]["like448"], r2["e2_agree_outcome"]["like224"]) == (63, 16)
assert r2["e1_axes"] == {"consistent": [6, 8], "conflict": [1, 8]} and r2["e1_changed"] == [10, 20]
assert r2["e3_kinds"]["448"] == {"threshold": 12, "rank": 11, "rank_s01_s14": 0, "all": 23}, r2["e3_kinds"]
print("data.json written; cross-checks pass")
print(json.dumps({"head": head, "planned": plan, "role": role, "resolution": res, "language": lang}, indent=1)[:6000])
print(json.dumps(out["wrong_names"], ensure_ascii=False)[:1200], out["s12_q5_true"], out["judging"])
