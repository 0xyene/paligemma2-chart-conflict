"""Two run-4 counts used in the blog post that analyze4.py does not print.

usage: python3.12 run4/extra4.py      -> run4/results/extra4.txt
1. Lying charts, "which has the tallest / shortest mark?": the drawing's item, split by chart type (value labels vs readouts).
2. Composition: on lying charts, marks where the model named the right mark AND read its printed number, yet said yes to
   "is the number on that mark the largest / smallest?" (right answer: no). How many of those also said yes to the exact
   opposite ("is any number larger / smaller than it?")?
analyze4.py runs into a temporary folder, so results/ is not touched.
"""
import contextlib
import io
import json
import runpy
import sys
import tempfile
from pathlib import Path

R4 = Path(__file__).resolve().parent
sys.path.insert(0, str(R4))
tmp = tempfile.mkdtemp(prefix="extra4-")
sys.argv = [str(R4 / "analyze4.py"), str(R4 / "results" / "answers_run4.csv"), tmp]
with contextlib.redirect_stdout(io.StringIO()):
    ns = runpy.run_path(str(R4 / "analyze4.py"), run_name="__main__")
E, W, R, NAME = ns["E"], ns["W"], ns["R"], ns["NAME"]
MODELS = ["224bf", "448bf", "10b-224", "10b-448"]  # the bfloat16 runs, as in the post
mech = {sid: json.loads((R4.parent / "stimuli" / sid / "spec.json").read_text())["mechanism"] for sid in W.stimulus.unique()}
W["mech"] = W.stimulus.map(mech)
out = [f"chart types: {', '.join(f'{k} {sum(v == k for v in mech.values())}' for k in ('label', 'readout'))} (run-3 charts)", ""]

out.append("1. 'which has the tallest / shortest mark?' -> the drawing's item (true chart -> lying chart)")
for m in MODELS:
    cells = []
    for mk in ("label", "readout", None):
        n = {}
        for cond in ("consistent", "conflict"):
            w = W[(W.model == m) & (W.cond == cond) & ((W.mech == mk) if mk else True)]
            n[cond] = (int((w.named == w.item).sum()), len(w))
        cells.append(f"{mk or 'all'} {n['consistent'][0]}/{n['consistent'][1]} -> {n['conflict'][0]}/{n['conflict'][1]}")
    out.append(f"  {NAME[m]:8s} " + " | ".join(cells))

out += ["", "2. lying charts, both facts (right mark + its printed number) but yes to the flip question: also yes to the opposite?"]
OPP = {"big": ("cmp_big_max", "any_more_big"), "small": ("cmp_small_min", "any_less_small")}
tot = [0, 0, 0]
for m in MODELS:
    both = agree = yy = 0
    for sid in sorted(E.stimulus.unique()):
        for side, (cq, oq) in OPP.items():
            def sel(df, q):
                return df[(df.model == m) & (df.stimulus == sid) & (df.cond == "conflict") & (df.qtype == q)]
            w, r, c, o = sel(W, f"which_{side}"), sel(R, f"read_{side}"), sel(E, cq), sel(E, oq)
            if not (len(w) and len(r) and len(c) and len(o)):
                continue
            if bool(w.ok.iloc[0]) and r.kind.iloc[0] == "label":
                both += 1
                if c.yn.iloc[0] == "yes":
                    agree += 1
                    yy += o.yn.iloc[0] == "yes"
    tot = [tot[0] + both, tot[1] + agree, tot[2] + yy]
    out.append(f"  {NAME[m]:8s} both facts {both}/22 · flip answered yes (wrong) {agree} · of those, yes to the opposite too {yy}")
out.append(f"  all four  both facts {tot[0]} · flip yes {tot[1]} · also yes to the opposite {tot[2]}")

(R4 / "results" / "extra4.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
