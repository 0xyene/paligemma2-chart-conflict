# Chart cue-conflict stimuli for PaliGemma 2

> This is the original plan. Some stimuli changed during build and review on purpose (e.g. s02 uses years instead of
> months to remove the seasonal prior; s05 rows were reordered). **[QUESTIONS.md](QUESTIONS.md), generated from the specs,
> is the source of truth** for what was built and asked; each `make.py` documents why it deviates.

Does PaliGemma 2 answer chart questions from **what the marks look like** (bar height, slice size,
needle angle, line slope, colour darkness) or from **what the text says** (value labels, axis ticks,
legend)? Each stimulus comes in two versions that share the exact same drawing:

- `consistent`: the text agrees with the drawing.
- `conflict`: the drawing is pixel-identical; only the text changes so that it contradicts the drawing.

Each version exists in English (`en`) and Turkish (`tr`) → **4 PNGs per stimulus**.

## Global rules (every stimulus)

1. **Canvas 896 × 896 px PNG.** PaliGemma 2 `mix-448` downsizes it to 448, so text must stay legible at half size:
   - text that carries a cue (value labels, ticks, legend labels, readouts): **≥ 22 px**, bold or medium weight preferred
   - any other text (body copy, captions, axis titles): **≥ 20 px**
   - check `check/448/<image>.png` by eye; if you can't read a number there, the model can't either.
2. **Identical geometry.** Marks, positions, layout and colours are the same in `consistent` and `conflict`
   (and in `en`/`tr`). Only the strings that carry the cue change. `common/lib.py: diffcheck()` shows the changed pixels;
   they must sit only on those strings.
3. **Conflict numbers are derived from consistent numbers** (a permutation, a sign flip, or an inverted axis/legend),
   chosen so that **every question gets a different answer** in the conflict version.
   Consequence used everywhere: *the "visual" answer to a conflict image = the answer to its consistent image.*
4. **No third cue.** Headlines, body text, captions, colours and icons must not reveal direction or values:
   no "sales soar", no "best method", no red/green for down/up, no blue for cold, no warning colour for high load.
   Body text is neutral context (who, where, how the data was collected).
5. **Fictional everything.** No real brands, newspapers, apps, companies, people, logos or trademarked UI.
   Names that appear in answers (cities, brands, servers, schools, districts, tickers, methods) are **identical in en and tr**;
   common nouns (months, days, regions, devices) are translated.
6. **Locale formatting.** EN `45%`, `18.4` · TR `%45`, `18,4`. Keep numbers < 1000 so no thousands separator is needed.
7. **Turkish must render.** Check ş ğ ı İ ç ö ü in every font you use (some decorative fonts lack them → fallback glyphs look wrong).
8. Questions use the PaliGemma mix prompt format: `answer en <question>` / `answer tr <soru>`, lowercase, one short answer
   (a name, a number, yes/no, up/down). Yes/no questions come in **pairs** that ask the same fact with opposite polarity
   (`pair` field), so a model that leans on "yes" fails one side.

## Mechanisms

| mechanism | what changes in `conflict` | does the conflict image have a correct answer? |
|---|---|---|
| `label`   | value labels next to marks contradict mark size | **no** — the chart contradicts itself; we only measure which cue wins |
| `readout` | the digital readout contradicts a needle / fill level | **no** |
| `axis`    | axis tick labels are inverted/reversed | **yes, the text** — misleading but internally consistent (Reuters 2014 Florida chart) |
| `legend`  | colour legend is reversed (dark = low) | **yes, the text** — breaks the convention, internally consistent |

## Spec format (`stimuli/<id>/spec.json`, written by `make.py`)

```json
{
  "id": "s01_newspaper_bars",
  "title": {"en": "...", "tr": "..."},
  "chart": "column bar", "style": "newspaper page", "tech": "HTML/CSS + inline SVG",
  "mechanism": "label", "conflict_has_truth": false,
  "conflict_summary": "Bars rise Jan→Jun; printed values fall 640→120.",
  "data": { "...": "free-form: the numbers you drew and printed" },
  "questions": [
    {"qid": "s01_q1", "kind": "trend", "pair": null,
     "prompt": {"en": "answer en ...", "tr": "answer tr ..."},
     "visual": {"en": ["up", "increased", "rose"], "tr": ["arttı", "artış", "yükseldi"]},
     "text":   {"en": ["down", "decreased", "fell"], "tr": ["azaldı", "düştü", "azalış"]}}
  ]
}
```

- `visual` = accepted answers when reading the drawing (= the answer to the consistent image).
- `text` = accepted answers when reading the printed text of the conflict image.
- First item of each list is the canonical answer; the rest are synonyms a short answer could use.
  Matching is case-insensitive, whole-word. **No word sequence may appear in both lists.**
- `kind` ∈ `trend`, `argmax`, `argmin`, `compare` (yes/no), `threshold` (yes/no), `read_value`, `count`, `relation`.
- Number answers: canonical is the bare number (`"640"`); add `"640%"`-style variants only where natural.

## The 14 stimuli

Values are listed in drawing order. "visual" = what the geometry encodes = printed numbers in `consistent`.

### s01_newspaper_bars — newspaper page · column bars · `label` · HTML/CSS + inline SVG
Fictional broadsheet ("The Riverside Courier" / "Kıyı Postası"), neutral headline about a long-established corner bakery (no "first months" framing — a new shop implies growth, a prior that agrees with the rising bars),
two columns of neutral body text, chart inset "Loaves sold per month". 6 bars Jan–Jun rising like a wifi icon; no y-axis.
- visual: Jan 120, Feb 210, Mar 330, Apr 420, May 540, Jun 640 · conflict labels: reversed (640 … 120)
- q1 trend (up/down Jan→Jun) · q2 argmax month · q3a/q3b pair "more/fewer in June than January" · q4 read June

### s02_magazine_line_inverted — news-site article page, dark theme · line chart · `axis` · matplotlib
Article "What the city's theft reports show" (neutral) about bicycle thefts in fictional city Northbridge, Jan–Aug line with
markers, no fill (fill direction would differ). y ticks 0–600 step 100. In `conflict` the y-axis is **inverted (0 at top)** so the
same rising line now encodes falling values (visual v → 600 − v).
- visual: 210, 260, 240, 330, 380, 360, 450, 520 · conflict truth: 390, 340, 360, 270, 220, 240, 150, 80
- q1 trend · q2 argmax month · q3 argmin month · q4a/q4b pair "more/fewer thefts in August than January"

### s03_slide_donut — corporate presentation slide · donut · `label` · SVG
Slide "Smartphone market share, Q2 2026" with fictional brands, callout labels "Nimbus 46%" with leader lines (no colour legend
lookup needed). Slices clockwise from 12 o'clock, single-hue or neutral categorical colours.
- visual: Nimbus 46, Orca 27, Pixa 17, Zento 10 · conflict: Nimbus 10, Orca 17, Pixa 27, Zento 46 (sums stay 100)
- q1 argmax brand · q2 argmin brand · q3a/q3b pair "does Nimbus have more/less than a third of the market?" · q4 read Orca

### s04_app_screentime — phone app screenshot, dark UI · horizontal bars · `label` · HTML/CSS flex
Generic "Screen time · this week" screen (no OS branding), 5 fictional apps, bars sorted longest first, times "9h 40m" / "9 sa 40 dk".
- visual: Chirp 9h 40m, Tubeo 7h 10m, Mapster 4h 20m, Notely 2h 30m, Bankly 1h 05m · conflict: reversed (Chirp 1h 05m … Bankly 9h 40m)
- q1 argmax app · q2 argmin app · q3a/q3b pair "was Chirp used more/less than Tubeo?" · q4 read Tubeo (not Mapster: middle is unchanged)

### s05_poster_pictogram — school poster · pictogram (isotype) · `label` · SVG icons
"Trees planted by each school this spring", key "1 tree icon = 10 trees", rows of tree icons + a printed total per row,
rows NOT sorted. Schools: Aster, Lumen, Mira, Nova.
- visual icons: Aster 5 (50), Lumen 8 (80), Mira 3 (30), Nova 2 (20) · conflict totals: Aster 20, Lumen 30, Mira 80, Nova 50 (text argmax/argmin ≠ visual argmin/argmax)
- q1 argmax school · q2 read Aster · q3a/q3b pair "did Lumen plant more/fewer trees than Mira?" · q4 argmin school

### s06_tv_thermometers — TV weather broadcast graphic · thermometer fills · `readout` · Canvas 2D
"Noon temperatures", 4 fictional cities, tubes WITHOUT tick scale, same mercury colour for all, big readout under each.
- visual: Ardena 31°, Belmora 12°, Castelo 24°, Dunmere −3° · conflict readouts: Ardena −3°, Belmora 24°, Castelo 12°, Dunmere 31°
- q1 argmax (warmest) · q2 argmin (coldest) · q3a/q3b pair "is it below/above freezing in Ardena?" · q4 read Castelo

### s07_dashboard_gauges — server monitoring dashboard, dark · semicircle gauges · `readout` · SVG
"CPU load", servers alpha-01, beta-02, gamma-03. Arc 0–100 with constant end labels "0" and "100", filled portion + needle in one
neutral accent colour (no green/amber/red zones), digital readout under each gauge.
- visual: alpha-01 92, beta-02 38, gamma-03 15 · conflict readouts: alpha-01 15, beta-02 92, gamma-03 38
- q1 argmax server · q2 argmin server · q3a/q3b pair "is alpha-01 above/below 80 percent load?" · q4 read gamma-03

### s08_paper_grouped_bars — photographed page of an academic paper · grouped bars · `label` · matplotlib figure in HTML page + PIL photo effect
Two-column paper excerpt, "Figure 2: Accuracy (%) of three methods on two benchmarks." Methods Base, Ours-S, Ours-L on fictional
benchmarks SynthQA and MapBench; value labels on bars, no y-axis numbers. Body text neutral (no "our method wins").
The whole page then gets the same mild "photo of a printout" transform in all 4 versions (≤ 3° perspective, lighting gradient, light noise) — still legible at 448.
- visual: SynthQA Base 52, Ours-S 64, Ours-L 78 · MapBench Base 41, Ours-S 47, Ours-L 69
- conflict: SynthQA Base 78, Ours-S 52, Ours-L 64 · MapBench Base 69, Ours-S 41, Ours-L 47
- q1 argmax method on SynthQA · q2 argmin method on MapBench · q3a/q3b pair "does Ours-L beat / is Ours-L worse than Base on MapBench?" · q4 read Ours-S on SynthQA

### s09_notebook_sketch — hand-drawn chart on squared notebook paper · line · `label` · SVG + displacement filter + handwriting font
"Daily users of our app (first week)", Mon–Sun, wobbly hand-drawn line, handwritten number at each point, axes without ticks.
Visual direction is **falling** (counterbalances s01/s02, whose visual direction is rising).
- visual: Mon 140, Tue 125, Wed 105, Thu 110, Fri 85, Sat 70, Sun 50 · conflict: reversed (Mon 50 … Sun 140)
- q1 trend · q2 argmax day · q3a/q3b pair "more/fewer users on Sunday than Monday?" · q4 read Friday (not Thursday: middle unchanged)

### s10_report_tilemap — municipal report page · tile map with colour legend · `legend` · SVG
"Air quality by district", 3×3 tile map of fictional districts, one sequential hue light→dark, gradient legend.
consistent legend: light = "Clean" (10), dark = "Polluted" (80) · conflict legend: light = "Polluted" (80), dark = "Clean" (10).
- darkness (visual pollution): Asterly 72, Brookfield 25, Cedarline 48, Dunmore 15 (lightest), Elmwood 63, Fairhaven 33, Glenrock 80 (darkest), Harborview 55, Ivydale 20
- q1 "worst air" district · q2 "cleanest air" district · q3a/q3b pair "is Glenrock more polluted / cleaner than Dunmore?"

### s11_finance_watchlist — finance app watchlist · sparklines · `label` (sign flip) · HTML + SVG
"Watchlist · 1 month", tickers KORA, MIRX, TALN, VESK (fictional companies), sparkline + last price + 1-month change.
Sparkline and change text in neutral colours (no green/red). Last price identical in both versions. Conflict = sign flip.
- visual: KORA +18.4%, MIRX +7.5%, TALN +3.1%, VESK −12.7% · conflict: KORA −18.4%, MIRX −7.5%, TALN −3.1%, VESK +12.7%
- q1 argmax "gained the most" · q2 "did MIRX go up or down?" · q3 count "how many went up?" (3 vs 1) · q4a/q4b pair "did KORA go up / down?"

### s12_textbook_scatter — textbook exercise page · scatter · `axis` · Canvas 2D
"Exercise 4.2: hours studied per week vs exam score for 20 students." Points fall left→right (negative-looking).
In `conflict` the **x-axis tick labels run right-to-left** (14, 12, …, 0), so the true relationship is positive.
Visual direction is negative here to counterbalance.
- q1 "do students who study more get higher scores?" (no vs yes) · q2 relation positive/negative · q3 "does the student who studied the most have a high or low score?" · q4 pair of q1 "…get lower scores?"

### s13_widget_battery — phone home-screen widget · radial progress rings · `label` · SVG
"Batteries" widget: Phone, Earbuds, Watch, Tablet; single neutral ring colour (no red for low), % in the ring centre.
- visual: Phone 88, Earbuds 9, Watch 54, Tablet 31 · conflict: Phone 9, Earbuds 88, Watch 31, Tablet 54
- q1 "needs charging most urgently" · q2 "most battery left" · q3a/q3b pair "is the phone battery almost empty / almost full?" · q4 read Watch

### s14_spreadsheet_databars — generic spreadsheet screenshot · in-cell data bars · `label` · HTML table
"Q3 revenue by region (thousand €)", regions North, South, East, West, Central (translated), number + conditional-format data bar,
total row (identical in both versions). No real spreadsheet branding.
- visual: North 420, South 180, East 610, West 260, Central 330 · conflict: North 260, South 330, East 180, West 420, Central 610
- q1 argmax region · q2 argmin region · q3a/q3b pair "did North earn more/less than West?" · q4 read East
