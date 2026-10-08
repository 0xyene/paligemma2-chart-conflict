# Run 2: follow-up tests and predictions

Written on 2026-10-08, **before** any run-2 answer exists. Run 1 (2026-10-07) results are in `results/run1/` and the
report "Bars or Labels?". Each test below answers one objection raised in the pre-mentor review. The predictions are
stated now so the run can confirm or falsify them; anything decided after seeing run-2 answers will be marked as such.

Same models (`paligemma2-3b-mix-224`, `mix-448`), greedy decoding, prompt format `answer en …` / `answer tr …`,
scoring with `common/scoring.py`. "Switched to the text" and "questions about the drawing" mean what they mean in the report.

## E1 · Can it read the scale at all? (scale-reading probe)

**Why:** run 1 found that flipped axes and a reversed legend never moved an answer (0 of 41 that could switch). That could
mean the model *can't read* tick labels, or that it *reads them but doesn't apply them* to the marks.

**What:** on s02 (flipped y axis), s12 (reversed x axis) and s10 (reversed legend), true and flipped versions, English and
Turkish, both models: pure reading questions ("what number is at the top of the y-axis?") and read-through questions
("how many bicycle thefts were reported in 2025?", which needs the axis).

**Predictions**
- If it reads but doesn't apply the scale: reading questions right on both versions (it says 0 at the top of the flipped
  axis), read-through answers follow the shape (about 520 thefts in 2025 on the flipped chart, where the truth is 80).
- If it can't read the scale: reading questions answered from habit (600 at the top of the flipped axis), read-through
  answers follow the shape.
- Expected from run 1 (the model answered 14, 14, 10 and 14 km for a 2 km answer on the true s12 chart): weak reading
  on s12 at both resolutions; better reading on s02 at 448 than at 224.

## E2 · Is the resolution effect about pixels or about the checkpoint?

**Why:** mix-448 followed the text more than mix-224 (9 : 0 charts), but they are different checkpoints, so pixel detail
and weights are confounded.

**What:** mix-448 on every true and lying image after throwing away detail: 896 → 224 → 448 px (bicubic), so it sees what
mix-224 saw, at its own input size. Control: mix-448 on 896 → 448 px images made the same way (English), which should
reproduce run 1's mix-448 answers.

**Predictions**
- Control: at least 95% of answers identical to run 1 (same model, same pixels up to the resizer).
- If detail drives the effect: on degraded images mix-448 switches about as often as mix-224 did (drawing questions about
  7%, "how much" lie-quoting about 55%).
- If the checkpoint drives it: it stays near its own run-1 level (drawing questions about 18%, "how much" about 91%).
- A result in between means both matter.

## E3 · Does label size alone change switching? (digit-size sweep)

**Why:** in run 1 digit size was tangled with chart type: the biggest digits were the two readout charts.

**What:** three label charts (s01 newspaper bars, s13 battery widget, s14 spreadsheet) and the s06 thermometer readouts, re-rendered with only the cue text at four sizes (one of them the original), marks pixel-identical.
True and lying versions, English, all questions, both models.

**Predictions**
- If size drives switching: within each chart, switching to the text rises with label size, most clearly at mix-224 and
  on "how much" questions (legibility), and shrinking s06's readouts lowers its switching.
- If chart type drives it: switching stays flat across sizes within a chart.

**Change before the run (2026-10-08):** s04 (screen-time app) was planned but dropped: its labels sit in a shared
flex row, and a bigger label couldn't be rendered without moving other elements in the time available. Sizes as built
(digit height in px at 896): s01 12 / 19 / 29 / 38, s13 17 / 27 / 33 / 37, s14 12 / 20 / 28 / 36, s06 19 / 28 / 38 / 47
(original sizes: 19, 27, 20, 47). The original-size images are pixel-identical to run 1, so they double as a repeat check.

## What would change the report
- E1 "reads but doesn't apply": strengthens "doesn't connect scale text to the marks".
- E1 "can't read": rewrite that finding as a reading failure for axis ticks and legends.
- E2: replaces "digit size is a candidate" with a measured answer for the resolution effect.
- E3: the same, within charts.

---
**Date correction, added 2026-10-07 14:15 (+03), after run 2.** Both dates "2026-10-08" above are a typo for 2026-10-07.
This file was created at 07:16 (+03) and last edited at 10:53 (+03), all on 2026-10-07. Run 2 was started in Colab at about
13:25 (+03) the same day; `answers_run2.csv` is stamped 10:56 in Colab's clock (UTC), i.e. 13:56 (+03). Nothing above this line was changed
after the run. Analyses added after seeing the answers are marked as such in `analyze2.py` and in the report.
