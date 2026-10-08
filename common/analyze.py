"""Run the notebook's own analysis cells locally on a finished run, so local and Colab numbers come from the same code.

python3.12 common/analyze.py results/run1        # needs results/run1/answers.csv; reads results/run1/adjudication.csv if present
Writes report.txt, results.csv and cue_following.png into the run folder.
"""
import contextlib
import io
import json
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parents[1]
run = Path(sys.argv[1]).resolve()
assert (run / "answers.csv").exists(), f"no answers.csv in {run}"

nb = json.loads((ROOT / "chart_conflict_experiment.ipynb").read_text(encoding="utf-8"))
cells = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
SCORING = next(i for i, c in enumerate(cells) if "def classify(" in c)
FIRST = next(i for i, c in enumerate(cells) if "@torch.inference_mode()" in c) + 1      # after the GPU run cell
LAST = next(i for i, c in enumerate(cells) if "wide = df.pivot_table" in c)              # stop before the wide table

g = {"IN_COLAB": False}
exec("import gc, json, time, zipfile\nfrom pathlib import Path\nimport matplotlib.pyplot as plt\nimport pandas as pd\n"
     "from PIL import Image", g)
exec(cells[SCORING], g)                                              # scoring (same code as common/scoring.py)
g["Q"] = g["pd"].DataFrame(json.loads((ROOT / "questions.json").read_text(encoding="utf-8")))
g["OUT"] = run / "answers.csv"
g["MODELS"] = {"224": "google/paligemma2-3b-mix-224", "448": "google/paligemma2-3b-mix-448"}
g["plt"].show = lambda *a, **k: None

os.chdir(run)
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    for i in range(FIRST, LAST):
        exec(cells[i], g)
(run / "report.txt").write_text(buf.getvalue(), encoding="utf-8")
print(buf.getvalue())
