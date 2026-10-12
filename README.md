# Chart cue conflict — PaliGemma 2

Does the model read a chart from **what the marks look like** or from **what the text says**?
14 charts × {consistent, conflict, no numbers} × {en, tr} = 84 images, each chart with 4–6 questions.

- `consistent`: numbers agree with the drawing
- `conflict`: the drawing is pixel-identical, only the text (labels / axis / legend / readout) contradicts it
- `nonumbers`: the same drawing with that text removed — how well the model reads the drawing alone

Every sheet with its questions and expected answers (generated from the specs): [QUESTIONS.md](QUESTIONS.md). Original plan and rules: [DESIGN.md](DESIGN.md).

## Results

Run 1 (792 answers) and follow-up runs 2 (820 answers) and 3 (264 answers), all on a free Colab T4 with `google/paligemma2-3b-mix-224` and `-mix-448`, greedy decoding.

- **Questions about the drawing** ("which is biggest?", "up or down?"): the lying text changed **18%** of mix-448's answers and **7%** of mix-224's.
- **"How much is X?"**: mix-448 quoted the printed (lying) number **91%** of the time, mix-224 **55%**. The model reads the numbers but doesn't check them against the drawing.
- **Scales:** on the 3 charts where the text sets the scale (axis ticks, a legend), the text was never used, even when it was the truth.
- **Run 2:** given images cut to mix-224's level of detail, mix-448 still followed the text nearly as often as before, so the 448–224 gap is mostly not about image detail.
- **Run 3:** asked directly ("do the numbers on the chart match the bars?", "…contradict the bars?", "is there a mistake in this chart?"), neither model answered differently on agreeing and lying charts: e.g. mix-448 said the numbers match on **16/22** agreeing and **16/22** lying charts.

Full write-up with every answer: [Bars or Labels?](https://claude.ai/artifact/XAcHHgbQzEBZNpTUEQpNYy). Numbers: `results/run1/report.txt`, `run2/results/report2.txt`, `run3/results/report3.txt`. Run 2 design and the predictions written before it: `run2/README.md`, `run2/PREDICTIONS.md`. Run 3: `run3/README.md`.

## Files

| path | what |
|---|---|
| `images/` | the 84 stimuli (896 × 896 PNG) |
| `sheets/<id>.png` | comparison per chart (consistent / conflict / no numbers × en / tr) |
| `questions.json` / `.csv` | one row per (image, prompt) with the `visual` and `text` answer lists, `answer_type`, `cue_px`, … |
| `chart_conflict_bundle.zip` | images + questions.json — upload this to Colab (built by `common/collect.py`, not in the repo) |
| `chart_conflict_experiment.ipynb` | Colab notebook: runs mix-224 and mix-448, scores, makes the figure |
| `common/scoring.py`, `common/answers.py` | answer matching (same code in the notebook) and shared accept lists |
| `stimuli/<id>/make.py` | builds one chart (HTML/SVG/Canvas via headless Chrome, matplotlib, PIL) + its `spec.json` |
| `check/448`, `check/224` | what the model actually sees after resizing (generated, not in the repo) |
| `check/diff` | red = pixels that differ from consistent (`<id>_<lang>.png` conflict, `…_nonumbers.png`): only the cue text (generated, not in the repo) |

## Rebuild

Generated files are not in the repo: `build/` (HTML renders, plus macOS system fonts that can't be redistributed), `check/`, the `.zip` bundles, `run2/bundle/` and `run3/bundle/`. These commands recreate them (macOS + Chrome for the HTML charts).

```bash
python3.12 common/collect.py --rebuild
```

```bash
python3.12 common/make_notebook.py
```

## Run

Colab → upload `chart_conflict_experiment.ipynb` → T4 GPU → Run all → upload `chart_conflict_bundle.zip` when asked.
