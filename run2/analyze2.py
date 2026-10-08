"""Analyse run 2 (see run2/PREDICTIONS.md, written before the run).

python3.12 run2/analyze2.py [answers_run2.csv] [out_dir]
  defaults: run2/results/answers_run2.csv and run2/results/

Writes report2.txt, results2.json, e2_resolution.png, e3_size.png and unmatched2.csv (answers the matcher could not place,
for a judge pass like run 1's).
Uses the run-1 definitions: per item (model, lang, question) the state on the true image is V (right), T (the lying text's
answer) or O; on the lying image V / T / O from the cue the answer followed; "switched" = T on lie and not T on true;
"drawing questions" = every question except the 11 "how much is X?" (kind read_value) ones.
"""
import ast
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
R2 = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "common"))
from scoring import classify, match, tokens  # noqa: E402

ANS = Path(sys.argv[1]) if len(sys.argv) > 1 else R2 / "results" / "answers_run2.csv"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else R2 / "results"
OUT.mkdir(parents=True, exist_ok=True)
Q2 = pd.DataFrame(json.loads((R2 / "bundle" / "questions2.json").read_text(encoding="utf-8")))
A = pd.read_csv(ANS, keep_default_na=False).astype({"model": str})
lines = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    lines.append(s)


def norm(a):
    return a.strip().lower() if isinstance(a, str) else a


def lst(v, ev, lang):
    return list(v) + (list(ev) if lang == "tr" else [])


def boot(d, fn, reps=4000, seed=0):
    rng = np.random.default_rng(seed)
    parts = [g for _, g in d.groupby("stimulus")]
    vals = [fn(pd.concat([parts[i] for i in rng.integers(0, len(parts), len(parts))])) for _ in range(reps)]
    return [float(v) for v in np.nanpercentile(vals, [2.5, 97.5])]


def items(rows, key=("model", "lang", "qid"), adj=None):
    """rows: one row per (model, image, prompt) with cond consistent/conflict, answer, visual/text lists, kind, stimulus.
    Returns one row per item with s_true, s_lie, sw, draw (same rules as the report, incl. same-answer -> same state)."""
    key = list(key)
    r = rows.copy()
    r["V"] = [lst(v, ev, l) for v, ev, l in zip(r.visual, r.en_visual, r.lang)]
    r["T"] = [lst(t, et, l) for t, et, l in zip(r.text, r.en_text, r.lang)]
    t = r[r.cond == "consistent"].set_index(key)
    x = r[r.cond == "conflict"].set_index(key)
    it = t[["stimulus", "kind", "mechanism", "answer", "V", "T"]].rename(columns={"answer": "a_true"}).join(
        x[["answer"]].rename(columns={"answer": "a_lie"}), how="inner").reset_index()
    if "o_true" in r:     # run 1: adjudicated outcomes
        it = it.join(t[["o_true"]], on=key).join(x[["o_lie"]], on=key)
    else:
        it["o_true"] = ["correct" if match(a, v, l) else "wrong" for a, v, l in zip(it.a_true, it["V"], it.lang)]
        it["o_lie"] = [classify(a, v, tt, l) for a, v, tt, l in zip(it.a_lie, it["V"], it["T"], it.lang)]
    if adj:              # run-2 judge verdicts for answers the matcher couldn't place: (lang, qid, answer) -> drawing / text
        vt = [adj.get((l, q, norm(a))) for l, q, a in zip(it.lang, it.qid, it.a_true)]
        vl = [adj.get((l, q, norm(a))) for l, q, a in zip(it.lang, it.qid, it.a_lie)]
        it["o_true"] = ["correct" if v == "drawing" else o for v, o in zip(vt, it.o_true)]
        it["o_lie"] = [{"drawing": "visual", "text": "text"}.get(v, o) for v, o in zip(vl, it.o_lie)]
    it["s_true"] = ["V" if o == "correct" else "T" if match(a, tt, l) else "O" for a, o, tt, l in zip(it.a_true, it.o_true, it["T"], it.lang)]
    if adj:
        it["s_true"] = ["T" if v == "text" and s != "V" else s for v, s in zip(vt, it.s_true)]
    it["s_lie"] = it.o_lie.map({"visual": "V", "text": "T"}).fillna("O")
    same = [norm(a) == norm(b) for a, b in zip(it.a_true, it.a_lie)]
    it.loc[same, "s_true"] = it.loc[same, "s_lie"]
    it["sw"] = it.s_lie.eq("T") & it.s_true.ne("T")
    it["draw"] = it.kind.ne("read_value")
    return it


def share(d, col="sw"):
    return float(d[col].mean()) if len(d) else float("nan")


# ---------- run-1 reference items (adjudicated results.csv)
R1 = pd.read_csv(ROOT / "results" / "run1" / "results.csv", keep_default_na=False).astype({"model": str})
for c in ("visual", "text", "en_visual", "en_text"):
    R1[c] = R1[c].apply(ast.literal_eval)
R1 = R1[R1.cond.isin(["consistent", "conflict"])].rename(columns={"outcome": "o"})
R1["o_true"] = R1.o
R1["o_lie"] = R1.o
I1 = items(R1)
I1raw = items(R1.drop(columns=["o_true", "o_lie"]))   # same answers, raw matcher (run-2 answers have no hand overrides yet)

# ---------- run-2 judge pass (run2/results/adjudication2.json, written after the run; same rubric and rule as run 1)
ADJ = {}
_adj = OUT / "adjudication2.json"
if _adj.exists():
    for r in json.loads(_adj.read_text(encoding="utf-8"))["items"]:
        if r["verdict"] in ("drawing", "text"):
            ADJ[(r["lang"], r["qid"], norm(r["answer"]))] = r["verdict"]

# ---------- run-2 rows
D = A.merge(Q2, on=["image", "prompt"], how="left", suffixes=("", "_q"))
assert D.exp_q.eq(D.exp).all() if "exp_q" in D else True, "answer rows don't match questions2.json"
missing = int(Q2.models.map(len).sum()) - len(A)
say(f"run 2: {len(A)} answers ({missing} missing of {int(Q2.models.map(len).sum())}) · by test {A.groupby(['exp', 'model']).size().to_dict()}")
out = {"n_answers": int(len(A)), "missing": missing}

# ================= E2c: control
c = D[D.exp == "E2c"]
if len(c):
    r1a = R1[R1.model == "448"].set_index(["image", "prompt"]).answer
    same = [norm(r1a.get((o, p))) == norm(a) for o, p, a in zip(c.orig_image, c.prompt, c.answer)]
    say(f"\nE2c control (mix-448, 896→448 bicubic, en): {sum(same)} of {len(same)} answers identical to run 1 ({np.mean(same):.0%}); prediction ≥ 95%")
    out["E2c"] = {"n": len(same), "same": int(sum(same))}

# ================= E2: mix-448 on 224-detail images
e = D[D.exp == "E2"]
if len(e):
    for col in ("visual", "text", "en_visual", "en_text"):
        e[col] = e[col].apply(lambda v: v if isinstance(v, list) else ast.literal_eval(v))
    I2raw = items(e.assign(model="448d"))
    I2 = items(e.assign(model="448d"), adj=ADJ)
    ref = {"mix-448 (run 1)": I1raw[I1raw.model == "448"], "mix-448 on 224-detail (run 2)": I2raw, "mix-224 (run 1)": I1raw[I1raw.model == "224"],
           "mix-448 (run 1, adjudicated)": I1[I1.model == "448"], "mix-448 on 224-detail (run 2, adjudicated)": I2,
           "mix-224 (run 1, adjudicated)": I1[I1.model == "224"]}
    say("\nE2 · same weights, less detail. Share of items that switched to the lying text (raw matcher for all three main rows,")
    say("so they compare like for like; the adjudicated rows, run 2 included after its judge pass, are the report's numbers)")
    say(f"{'':44s} {'drawing q':>12s} {'how much':>10s} {'all':>8s} {'right on true':>14s}")
    e2 = {}
    for name, d in ref.items():
        dr, hm = d[d.draw], d[~d.draw]
        e2[name] = {"draw": share(dr), "draw_n": int(len(dr)), "draw_count": int(dr.sw.sum()), "draw_ci": boot(dr, share),
                    "howmuch_lie": float(hm.s_lie.eq("T").mean()), "howmuch_n": int(len(hm)), "all": share(d),
                    "howmuch_ci": boot(hm.assign(x=hm.s_lie.eq("T").astype(float)), lambda z: z.x.mean()),
                    "right_true": float(d.s_true.eq("V").mean())}
        say(f"{name:44s} {e2[name]['draw']:>11.0%}  {e2[name]['howmuch_lie']:>9.0%} {e2[name]['all']:>8.0%} {e2[name]['right_true']:>13.0%}"
            f"   (drawing {e2[name]['draw_count']}/{e2[name]['draw_n']}, 95% {e2[name]['draw_ci'][0]:.0%}–{e2[name]['draw_ci'][1]:.0%})")
    # chart-level comparisons, paired by chart
    def per_chart(d, col="sw", draw_only=False):
        d = d[d.draw] if draw_only else d
        return d.groupby("stimulus")[col].mean()
    for other in ("mix-448 (run 1)", "mix-224 (run 1)"):
        for draw_only in (False, True):
            a, b = per_chart(I2, draw_only=draw_only), per_chart(ref[other], draw_only=draw_only)
            more, less = int((a > b + 1e-12).sum()), int((a < b - 1e-12).sum())
            p = stats.binomtest(more, more + less).pvalue if more + less else 1.0
            tag = "drawing q" if draw_only else "all q"
            say(f"  charts, degraded-448 vs {other} ({tag}): more {more}, less {less}, tied {len(a) - more - less}, sign test p = {p:.3f}")
            e2[f"vs {other} {tag}"] = {"more": more, "less": less, "tie": int(len(a) - more - less), "p": float(p)}
    # where does it land? share of the 448→224 gap closed by degrading
    g448, g224, gd = e2["mix-448 (run 1)"]["draw"], e2["mix-224 (run 1)"]["draw"], e2["mix-448 on 224-detail (run 2)"]["draw"]
    if abs(g448 - g224) > 1e-9:
        frac = (g448 - gd) / (g448 - g224)
        say(f"  degrading closes {frac:.0%} of the 448–224 gap on drawing questions (0% = checkpoint explains it, 100% = detail does)")
        e2["gap_closed_draw"] = float(frac)
    h448, h224, hd = (e2[k]["howmuch_lie"] for k in ("mix-448 (run 1)", "mix-224 (run 1)", "mix-448 on 224-detail (run 2)"))
    if abs(h448 - h224) > 1e-9:
        e2["gap_closed_howmuch"] = float((h448 - hd) / (h448 - h224))
        say(f"  on 'how much' lie-quoting it closes {e2['gap_closed_howmuch']:.0%} of the gap")
    a448, a224, ad = (e2[k]["draw"] for k in ("mix-448 (run 1, adjudicated)", "mix-224 (run 1, adjudicated)", "mix-448 on 224-detail (run 2, adjudicated)"))
    e2["gap_closed_draw_adj"] = float((a448 - ad) / (a448 - a224))
    say(f"  adjudicated rows: degrading closes {e2['gap_closed_draw_adj']:.0%} of the gap on drawing questions")
    # paired by item, resampled by chart: degraded − mix-224 and mix-448 − degraded, drawing questions, adjudicated
    k = ["lang", "qid"]
    P = I2[I2.draw].set_index(k)[["stimulus", "sw"]].rename(columns={"sw": "d"})
    P = P.join(I1[(I1.model == "448") & I1.draw].set_index(k).sw.rename("h")).join(I1[(I1.model == "224") & I1.draw].set_index(k).sw.rename("l")).reset_index()
    for c in ("d", "h", "l"):
        P[c] = P[c].astype(float)
    for name, fn in (("degraded − mix-224", lambda x: (x.d - x.l).mean()), ("mix-448 − degraded", lambda x: (x.h - x.d).mean())):
        lo, hi = boot(P, fn)
        e2[f"diff {name}"] = {"est": float(fn(P)), "ci": [lo, hi]}
        say(f"  drawing q, {name}: {fn(P):+.1%} (chart bootstrap 95% {lo:+.1%} to {hi:+.1%})")
    out["E2"] = e2
    I2.to_csv(OUT / "e2_items.csv", index=False)

# ================= E1: scale-reading probe
p1 = D[D.exp == "E1"].copy()
if len(p1):
    def num(a):
        for t in tokens(a):
            try:
                return float(t)
            except ValueError:
                continue
        return None

    def e1_class(r):
        ex = r.expect if isinstance(r.expect, dict) else ast.literal_eval(r.expect)
        if r.probe_kind == "read":
            x = num(r.answer)
            if x is None:
                return "other"
            if x == float(ex[r.cond]):
                return "right"
            if r.cond == "conflict" and x == float(ex["consistent"]):
                return "habit"
            return "other"
        if r.probe_kind == "read_word":
            if match(r.answer, ex[r.cond][r.lang], r.lang):
                return "right"
            if r.cond == "conflict" and match(r.answer, ex["consistent"][r.lang], r.lang):
                return "habit"
            return "other"
        x = num(r.answer)                                   # through
        if x is None:
            return "other"
        ds, da = abs(x - ex["shape"]), abs(x - ex["axis"])
        if r.cond == "consistent":
            return "right" if ds <= ex["tol"] else "other"
        if da <= ex["tol"] and da < ds:
            return "axis"
        if ds <= ex["tol"] and ds <= da:
            return "shape"
        return "other"

    p1["e1"] = p1.apply(e1_class, axis=1)
    p1["probe_group"] = p1.probe_kind.map({"read": "read", "read_word": "read", "through": "through"})
    say("\nE1 · scale-reading probe (s02 flipped y axis, s12 reversed x axis, s10 reversed legend)")
    tab = p1.pivot_table(index=["stimulus", "qid", "probe_kind"], columns=["model", "cond", "lang"], values="answer", aggfunc="first")
    say(tab.to_string())
    say("\nclassified: reading questions (right / habit = the normal-axis label / other)")
    say(pd.crosstab([p1[p1.probe_group == "read"].model, p1[p1.probe_group == "read"].cond], p1[p1.probe_group == "read"].e1).to_string())
    say("read-through questions on the flipped version (axis = used the printed scale, shape = read the mark on a normal scale)")
    th = p1[(p1.probe_group == "through")]
    say(pd.crosstab([th.model, th.cond], th.e1).to_string())
    out["E1"] = {m: {g: {c: p1[(p1.model == m) & (p1.probe_group == g) & (p1.cond == c)].e1.value_counts().to_dict()
                         for c in ("consistent", "conflict")} for g in ("read", "through")} for m in ("224", "448")}
    out["E1_rows"] = p1[["model", "stimulus", "qid", "probe_kind", "cond", "lang", "prompt", "answer", "e1"]].to_dict("records")

# ================= E3: digit-size sweep
s3 = D[D.exp == "E3"].copy()
if len(s3):
    for col in ("visual", "text", "en_visual", "en_text"):
        s3[col] = s3[col].apply(lambda v: v if isinstance(v, list) else ast.literal_eval(v))
    s3["model_k"] = s3.model + "_k" + s3.size_k.astype(int).astype(str)
    I3raw = items(s3.assign(model=s3.model_k))
    I3 = items(s3.assign(model=s3.model_k), adj=ADJ)
    I3["model_k"] = I3.model
    I3["base_model"] = I3.model.str.split("_k").str[0]
    I3["k"] = I3.model.str.split("_k").str[1].astype(int)
    px = s3.drop_duplicates(["stimulus", "size_k"]).set_index(["stimulus", "size_k"]).size_cue_px
    I3["cue_px"] = [int(px[(s, k)]) for s, k in zip(I3.stimulus, I3.k)]
    say("\nE3 · digit-size sweep (en). Per chart and size: drawing questions switched / how-much lie quoted")
    rows3 = []
    for (m, sid, k), g in I3.groupby(["base_model", "stimulus", "k"]):
        dr, hm = g[g.draw], g[~g.draw]
        rows3.append({"model": m, "stimulus": sid, "k": int(k), "cue_px": int(g.cue_px.iloc[0]),
                      "eff_px": float(g.cue_px.iloc[0] * int(m) / 896), "draw_sw": int(dr.sw.sum()), "draw_n": int(len(dr)),
                      "hm_lie": int(hm.s_lie.eq("T").sum()), "hm_n": int(len(hm)), "right_true": float(g.s_true.eq("V").mean())})
    T3 = pd.DataFrame(rows3)
    say(T3.to_string(index=False))
    for m in ("224", "448"):
        t = T3[T3.model == m]
        if not len(t):
            continue
        byk = t.groupby("k")[["draw_sw", "draw_n", "hm_lie", "hm_n"]].sum()
        say(f"  {m}: pooled over charts by size level k: drawing " + ", ".join(f"k{k} {r.draw_sw}/{r.draw_n}" for k, r in byk.iterrows())
            + " · how-much " + ", ".join(f"k{k} {r.hm_lie}/{r.hm_n}" for k, r in byk.iterrows()))
        # within-chart trend: Spearman of switch share vs size, computed per chart and averaged (chart = block)
        rhos = []
        for sid, g in t.groupby("stimulus"):
            y = (g.draw_sw / g.draw_n.clip(lower=1)).to_numpy()
            if np.ptp(y) > 0:
                rhos.append(stats.spearmanr(g.k, y).statistic)
            else:
                rhos.append(0.0)
        up = int(sum(r > 0 for r in rhos)); down = int(sum(r < 0 for r in rhos))
        say(f"  {m}: within-chart trend of drawing switches with size: {up} charts up, {down} down, {len(rhos) - up - down} flat; mean ρ = {np.mean(rhos):.2f}")
    out["E3"] = T3.to_dict("records")
    I3.to_csv(OUT / "e3_items.csv", index=False)

# ---------- unmatched answers for a judge pass
um = []
for name, d in (("E2", locals().get("I2raw")), ("E3", locals().get("I3raw"))):     # raw matcher: this is the judge input
    if d is None:
        continue
    for r in d.itertuples():
        if r.s_true == "O":
            um.append({"exp": name, "model": r.model, "lang": r.lang, "qid": r.qid, "image_cond": "consistent", "answer": r.a_true})
        if r.s_lie == "O":
            um.append({"exp": name, "model": r.model, "lang": r.lang, "qid": r.qid, "image_cond": "conflict", "answer": r.a_lie})
pd.DataFrame(um).to_csv(OUT / "unmatched2.csv", index=False)
say(f"\n{len(um)} answers scored 'something else' → unmatched2.csv (check for near-misses before quoting)")

# ================= added after seeing the run-2 answers (not in PREDICTIONS.md; reported as such)
say("\nADDED AFTER SEEING THE ANSWERS (not pre-registered)")
post = {}
r1a = {(m, i, p): norm(a) for m, i, p, a in zip(R1.model, R1.image, R1.prompt, R1.answer)}
if len(e):
    # which model does degraded mix-448 answer like, where the two run-1 models gave different answers?
    g = e.assign(a448=[r1a.get(("448", o, p)) for o, p in zip(e.orig_image, e.prompt)],
                 a224=[r1a.get(("224", o, p)) for o, p in zip(e.orig_image, e.prompt)], a=e.answer.map(norm))
    dis = g[g.a448 != g.a224]
    post["E2_agree"] = {"n": int(len(g)), "differ": int(len(dis)), "like448": int((dis.a == dis.a448).sum()),
                        "like224": int((dis.a == dis.a224).sum()), "neither": int(((dis.a != dis.a448) & (dis.a != dis.a224)).sum()),
                        "same448_all": int((g.a == g.a448).sum()), "same224_all": int((g.a == g.a224).sum())}
    # same comparison on scored outcomes (V / T / O, adjudicated) instead of exact strings ("27" vs "27%" count as the same)
    kk = ["lang", "qid"]
    hh, ll, dd = I1[I1.model == "448"].set_index(kk), I1[I1.model == "224"].set_index(kk), I2.set_index(kk)
    J = pd.concat([pd.DataFrame({"h": hh[c], "l": ll[c], "d": dd[c]}).dropna() for c in ("s_true", "s_lie")])
    Jd = J[J.h != J.l]
    post["E2_agree_outcome"] = {"n": int(len(J)), "differ": int(len(Jd)), "like448": int((Jd.d == Jd.h).sum()), "like224": int((Jd.d == Jd.l).sum()),
                                "neither": int(((Jd.d != Jd.h) & (Jd.d != Jd.l)).sum())}
    say(f"E2: on scored outcomes the run-1 models differed on {len(Jd)} of {len(J)} pairs; degraded mix-448 matched mix-448 {post['E2_agree_outcome']['like448']}, "
        f"mix-224 {post['E2_agree_outcome']['like224']}, neither {post['E2_agree_outcome']['neither']}")
    # share of the gap closed, with a chart bootstrap
    Pg = dd[dd.draw][["stimulus"]].assign(D=dd[dd.draw].sw.astype(float), H=hh[hh.draw].sw.astype(float), L=ll[ll.draw].sw.astype(float)).reset_index()
    rng = np.random.default_rng(0); parts = [x for _, x in Pg.groupby("stimulus")]; vals = []
    for _ in range(10000):
        b = pd.concat([parts[i] for i in rng.integers(0, len(parts), len(parts))])
        den = b.H.mean() - b.L.mean()
        if den > 0:
            vals.append((b.H.mean() - b.D.mean()) / den)
    post["E2_gap_ci"] = [float(v) for v in np.percentile(vals, [2.5, 97.5])]
    say(f"E2: share of the drawing-question gap closed 95% chart-bootstrap interval {post['E2_gap_ci'][0]:.0%} to {post['E2_gap_ci'][1]:.0%}")
    # answer habits on the degraded images
    hab = {}
    for name, a in (("448d", e.answer), ("448", R1[(R1.model == "448") & R1.image.isin(set(e.orig_image))].answer),
                    ("224", R1[(R1.model == "224") & R1.image.isin(set(e.orig_image))].answer)):
        a = a.map(norm)
        hab[name] = {"n": int(len(a)), "yes": int((a == "yes").sum()), "no": int((a == "no").sum()), "unanswerable": int((a == "unanswerable").sum())}
    post["E2_habits"] = hab
    say("E2: answer habits (all 280 E2 image-question pairs): " + " · ".join(f"{k} yes {v['yes']} no {v['no']} unanswerable {v['unanswerable']}" for k, v in hab.items()))
    say(f"E2: run-1 mix-448 and mix-224 answered differently on {len(dis)} of {len(g)} (image, question) pairs; there degraded mix-448 "
        f"gave mix-448's answer {post['E2_agree']['like448']} times, mix-224's {post['E2_agree']['like224']}, something else {post['E2_agree']['neither']}")
    # reading accuracy on the true image, drawing questions (adjudicated)
    acc = {}
    for name, d in (("448", I1[I1.model == "448"]), ("448d", I2), ("224", I1[I1.model == "224"])):
        dr = d[d.draw]
        acc[name] = {"right": int(dr.s_true.eq("V").sum()), "n": int(len(dr)), "ci": boot(dr.assign(r=dr.s_true.eq("V").astype(float)), lambda x: x.r.mean()),
                     "hm_right": int(d[~d.draw].s_true.eq("V").sum()), "hm_n": int((~d.draw).sum()),
                     "hm_ci": boot(d[~d.draw].assign(r=d[~d.draw].s_true.eq("V").astype(float)), lambda x: x.r.mean())}
    k = ["lang", "qid"]
    PA = I2[I2.draw].set_index(k)[["stimulus"]].assign(d=I2[I2.draw].set_index(k).s_true.eq("V").astype(float))
    PA = PA.join(I1[(I1.model == "448") & I1.draw].set_index(k).s_true.eq("V").astype(float).rename("h")).join(
        I1[(I1.model == "224") & I1.draw].set_index(k).s_true.eq("V").astype(float).rename("l")).reset_index()
    for name, fn in (("mix-448 − degraded", lambda x: (x.h - x.d).mean()), ("degraded − mix-224", lambda x: (x.d - x.l).mean())):
        acc[f"diff {name}"] = {"est": float(fn(PA)), "ci": boot(PA, fn)}
    post["E2_accuracy"] = acc
    say("E2: right on the true chart, drawing questions: " + " · ".join(f"{k} {acc[k]['right']}/{acc[k]['n']} ({acc[k]['right'] / acc[k]['n']:.0%})" for k in ("448", "448d", "224"))
        + " | how much: " + " · ".join(f"{k} {acc[k]['hm_right']}/{acc[k]['hm_n']}" for k in ("448", "448d", "224")))
    for name in ("mix-448 − degraded", "degraded − mix-224"):
        v = acc[f"diff {name}"]
        say(f"   accuracy, drawing q, {name}: {v['est']:+.1%} (chart bootstrap 95% {v['ci'][0]:+.1%} to {v['ci'][1]:+.1%})")
if len(p1):
    # a scale version counts as read when every numeric reading probe on it is right
    rd = p1[p1.probe_kind == "read"].assign(ok=lambda x: x.e1.eq("right"))
    ver = rd.groupby(["model", "stimulus", "lang", "cond"]).ok.all().reset_index()
    post["E1_versions"] = {m: {c: [int(ver[(ver.model == m) & (ver.cond == c)].ok.sum()), int(((ver.model == m) & (ver.cond == c)).sum())]
                               for c in ("consistent", "conflict")} for m in ("224", "448")}
    tot = {c: [int(ver[ver.cond == c].ok.sum()), int((ver.cond == c).sum())] for c in ("consistent", "conflict")}
    post["E1_versions"]["both"] = tot
    disc = ver.pivot_table(index=["model", "stimulus", "lang"], columns="cond", values="ok", aggfunc="first")
    b, c_ = int((disc.consistent & ~disc.conflict).sum()), int((~disc.consistent & disc.conflict).sum())
    post["E1_versions"]["mcnemar"] = {"normal_only": b, "flipped_only": c_, "p": float(stats.binomtest(b, b + c_).pvalue) if b + c_ else 1.0}
    say(f"E1: scale versions read right end to end (all numeric reading probes right): normal {tot['consistent'][0]}/{tot['consistent'][1]}, "
        f"flipped {tot['conflict'][0]}/{tot['conflict'][1]} (pairs: normal only {b}, flipped only {c_}; exact McNemar p = {post['E1_versions']['mcnemar']['p']:.3f}, "
        f"descriptive, 3 charts)")
    ax = ver[ver.stimulus != "s10_report_tilemap"]
    post["E1_axes"] = {c: [int(ax[ax.cond == c].ok.sum()), int((ax.cond == c).sum())] for c in ("consistent", "conflict")}
    pv = rd.pivot_table(index=["model", "qid", "lang"], columns="cond", values="answer", aggfunc="first")
    post["E1_changed"] = [int((pv.consistent.map(norm) != pv.conflict.map(norm)).sum()), int(len(pv))]
    say(f"E1: axes only (s02, s12): read end to end normal {post['E1_axes']['consistent']}, flipped {post['E1_axes']['conflict']}; "
        f"answers that changed when the labels flipped {post['E1_changed'][0]} of {post['E1_changed'][1]}")
    say("E1: the word probe (s10, 'what word is at the top of the legend?') failed on both versions: answers name the page title or a club, so it is left out")
if len(s3):
    o3 = s3[s3.size_original.astype(bool)]
    same3 = [r1a.get((m, o, p)) == norm(a) for m, o, p, a in zip(o3.model, o3.orig_image, o3.prompt, o3.answer)]
    post["E3_repeat"] = {"n": len(same3), "same": int(sum(same3))}
    say(f"E3: original-size images (pixel-identical to run 1): {sum(same3)} of {len(same3)} answers identical to run 1 (both models)")
out["post"] = post

# ---------- figures
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    if "E2" in out:
        fig, ax = plt.subplots(figsize=(6.4, 3.2))
        names = ["mix-224 (run 1)", "mix-448 on 224-detail (run 2)", "mix-448 (run 1)"]
        for i, n in enumerate(names):
            v, lo, hi = out["E2"][n]["draw"], *out["E2"][n]["draw_ci"]
            ax.errorbar(v, i, xerr=[[v - lo], [hi - v]], fmt="o", color=["#8d929a", "#eb6834", "#2a78d6"][i], capsize=4, ms=8)
        ax.set_yticks(range(3), names); ax.set_xlim(0, 0.5); ax.set_xlabel("drawing questions that switched to the lying text")
        ax.grid(axis="x", alpha=.3); fig.tight_layout(); fig.savefig(OUT / "e2_resolution.png", dpi=160); plt.close(fig)
    if "E3" in out:
        T3 = pd.DataFrame(out["E3"])
        fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
        for ax, m in zip(axes, ("224", "448")):
            for sid, g in T3[T3.model == m].groupby("stimulus"):
                ax.plot(g.eff_px, (g.draw_sw + g.hm_lie) / (g.draw_n + g.hm_n), marker="o", label=sid.split("_")[0])
            ax.set_title(f"mix-{m}"); ax.set_xlabel("digit height in the model's input (px)"); ax.grid(alpha=.3)
        axes[0].set_ylabel("share switched to the text (all q)"); axes[1].legend(fontsize=8)
        fig.tight_layout(); fig.savefig(OUT / "e3_size.png", dpi=160); plt.close(fig)
except Exception as ex:      # figures are a convenience
    say(f"(figures skipped: {ex})")

(OUT / "results2.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
(OUT / "report2.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\nwrote", OUT / "report2.txt", "and results2.json")
