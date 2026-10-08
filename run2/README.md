# Run 2: follow-up tests

Three tests that answer open questions from run 1. Predictions are in [PREDICTIONS.md](PREDICTIONS.md),
written before the run.

| Test | Question | Models | Answers |
|---|---|---|---|
| E1 scale-reading probe | Can it read flipped axis ticks and a reversed legend at all? | 224 + 448 | 80 |
| E2 same weights, less detail | Is 448's extra text-following about pixels or about the checkpoint? | 448 | 280 |
| E2c control | Does the 896→448 resize reproduce run 1? | 448 | 140 |
| E3 digit-size sweep | Does label size alone change switching, within one chart? | 224 + 448 | see `build2.py` output |

## Run it (about 30 minutes on a free T4)
1. Open `chart_conflict_run2.ipynb` in Colab (File → Upload notebook). Runtime → Change runtime type → T4 GPU.
2. In the 🔑 sidebar, switch on notebook access for your `HF_TOKEN` secret (same token as run 1).
3. Runtime → Run all. Upload `chart_conflict_run2_bundle.zip` when asked, allow Drive access (answers are saved to
   `MyDrive/chart_conflict/answers_run2.csv`, so a disconnect loses nothing; Run all again to resume).
4. The last cell downloads `run2_outputs.zip`. Put it in this folder (or send it back).

## Analyse
```
unzip run2/run2_outputs.zip -d run2/results
python3.12 run2/analyze2.py run2/results/answers_run2.csv
```
Writes `results/report2.txt`, `results2.json`, two figures, and `unmatched2.csv` for a judge pass on near-miss answers.

## Rebuild
```
python3.12 run2/size_sweep/<sid>.py      # one per swept chart, renders into run2/images/size/
python3.12 run2/build2.py                 # bundle: images + questions2.json + run-1 answers for the control check
python3.12 run2/make_notebook2.py         # notebook
```
