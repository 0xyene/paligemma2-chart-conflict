# Run 4: concrete comparisons (E4), the "no" ladder (E5) and bigger models (F)

Run 3 asked "do the numbers on the chart match the bars?" and neither 3B model answered differently on agreeing and lying
charts. That leaves two explanations open, and run 4 tests both:

- **E4 · can't compare, or can't parse the question?** The same comparison asked concretely, in English, on the 11 run-3 charts
  (agreeing + lying = 22 images), 10 questions per image:
  - 6 yes/no comparisons, e.g. *"is the number above the tallest bar the largest of the six numbers above the bars?"* and its
    exact opposite *"among the six numbers above the bars, is any larger than the number above the tallest bar?"* (same for the
    smallest mark), plus *"…the smallest?"* / *"…the largest?"* cross-checks. Right answers are computed from
    `stimuli/<id>/spec.json`. The exact-opposite pairs separate a yes-habit (yes to both) from trusting the drawing (consistent
    answers, never catches the lie) from comparing (no, then yes, on lying charts only).
  - the two parts on the same image: *"which month has the tallest bar?"* (drawing only) and *"what number is written above the
    June bar?"* (text only). Composition = on lying charts, does it get both parts right and still say the numbers agree?
- **E5 · the "no" ladder** (same 22 images, 11 questions each, 7 with the answer *no*). Where does the model stop saying no?
  L0 object (*"is there a dog in this image?"*), L1 text (*"is this chart about car sales?"*, *"is december one of the months on
  the chart?"*), L2 drawing (*"does january have the tallest bar?"*), L3 = E4's comparisons. Some *yes* questions
  (*"are there any numbers in this image?"*, *"does june have the tallest bar?"*) so "always no" can't pass. If "no" holds at
  L0–L2 and breaks only at L3, run 3's flat result is about comparing, not a general yes-habit.
- **F · model size.** Run 3's 132 questions (en + tr) on PaliGemma 2 10B mix-224 / mix-448, and 28B mix-448 when the GPU has ≥ 70 GB.
- **Controls.** 3B in float32 with TF32 off (should repeat run 3's T4 answers) and 3B in bfloat16 (10B and 28B only fit in
  bfloat16, so size is compared bf16 vs bf16).

## Run it (Colab Pro, A100, about 45–60 minutes, 3,564 answers)
1. Open `chart_conflict_run4.ipynb` in Colab, Runtime → **A100 GPU**, `HF_TOKEN` secret on.
2. Accept the licence for the 10B (and 28B) checkpoints on Hugging Face if the first cell says NO ACCESS.
3. Drag `chart_conflict_run4_bundle.zip` into the Files sidebar, then Run all. Answers go to `MyDrive/chart_conflict/answers_run4.csv`.
4. The last cell downloads `run4_outputs.zip`; put it here.

## Analyse
```
python3.12 run4/build4.py          # recreates run4/bundle/ (questions4.json), not in the repo
unzip run4/run4_outputs.zip -d run4/results
python3.12 run4/analyze4.py
```
Writes `results/report4.txt`, `results4.json`, `e4_compare.png`, `e5_ladder.png`, `f_size.png`.

## Rebuild
```
python3.12 run4/build4.py
python3.12 run4/make_notebook4.py
```
