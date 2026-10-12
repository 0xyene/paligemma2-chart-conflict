# Run 3: do the numbers match the drawing?

Runs 1–2 supported the conclusion "the model doesn't compare the numbers to the drawing" only indirectly, because the
model was never asked. Run 3 asks it directly, on the run-1 images.

- 11 charts whose lying version contradicts itself (`label` / `readout`). s02 / s10 / s12 are left out: their flipped
  scale is misleading but consistent, so "do they match?" has no clean right answer.
- consistent + lying × en + tr = 44 images, both models, 3 yes/no questions each = 264 answers:
  *do the numbers on the chart match the bars?* · *…contradict the bars?* · *is there a mistake in this chart?*
  (the mark word changes per chart: slices, tree icons, gauges, line, rings…). Two polarities, because run 1's
  yes/no answers were about 75% "yes".

## Result (Colab T4, float32, 12 Oct 2026)
No detection: for every model × question the share of "yes" is the same on agreeing and lying charts (all Fisher p ≥ 0.7). "Caught" (match *no* and contradict *yes* on one image): mix-224 2/22 lying vs 2/22 agreeing, mix-448 0/22 vs 1/22. Full numbers: `results/report3.txt`, figure `results/run3_yes.png`. 56 answers were sentences (mostly Turkish); 33 are coded by `yn_sentence` in `analyze3.py`, usually the same sentence on both versions of a chart.

## Run it (about 10 minutes on a free T4)
1. Open `chart_conflict_run3.ipynb` in Colab, Runtime → T4 GPU, `HF_TOKEN` secret on.
2. Run all, upload `chart_conflict_run3_bundle.zip` when asked (answers go to `MyDrive/chart_conflict/answers_run3.csv`).
3. The last cell downloads `run3_outputs.zip`; put it here.

## Analyse
```
python3.12 run3/build3.py          # recreates run3/bundle/ (questions3.json), not in the repo
unzip run3/run3_outputs.zip -d run3/results
python3.12 run3/analyze3.py
```
Writes `results/report3.txt`, `results3.json`, `run3_yes.png` (share of "yes", agreeing vs lying charts).

## Rebuild
```
python3.12 run3/build3.py
python3.12 run3/make_notebook3.py
```
