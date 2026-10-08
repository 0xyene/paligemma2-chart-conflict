"""s12 — textbook exercise page with a scatter plot (Canvas 2D).

Variables: distance from home to school (km, x) vs final exam score (y). Deliberately NOT "hours studied": everyone
expects more study -> higher score, a common-sense prior that would side with the conflict text on every question.
Distance to school has no agreed folk direction.

20 dots fall from top-left to bottom-right (negative-looking). In `consistent` the x tick labels run 0, 2, …, 14
left to right. In `conflict` only those tick labels change: they run 14, 12, …, 0 (reversed axis), so the same dots
now encode a positive relationship. The conflict image therefore has a correct answer: the text one.

Residual prior: some people may expect a long commute to lower scores. If that prior exists it agrees with the
visual (negative) reading, never with the conflict text, so text wins on s12 are a conservative estimate.

Review fixes: the top scorer sits on a labelled tick (2 km; conflict label 12) so q5 needs no interpolation; q2 lists
the text answer first ("positive or negative") and q3 lists it second ("low or high") so a first-option bias cannot
look like a text win on both.

Set-level review: prompts shortened to <= 10 words (q3 keeps "low or high", not the suggested "high or low", for the
counterbalance above); yes/no and number answers come from common/answers.py; q1/q4 are a "compare" pair (farther vs
nearer students), q3 is "relation". The x tick labels (the cue) are Avenir Next Demi Bold 28 px (Seravek has no
semibold: its 600 fell back to Bold 25 px, digits 17 px tall); y tick labels moved to Avenir Next Medium to match.
Dots are near-black (#222), as in a printed textbook, instead of the page accent.

nonumbers: the same page with the x tick labels (the only cue strings) drawn as empty text; tick marks, the x-axis
title, y ticks and dots are unchanged. The axis is then read by convention (left to right = more km), so q1-q4 stay
answerable from the dots; q5 needs the km value that only the removed labels gave.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
from answers import NO, YES, num_accept  # noqa: E402
from lib import CONDS, LANGS, finish, name, render_html  # noqa: E402

SID = "s12_textbook_scatter"
X_MAX = 14                                                    # x axis spans 0..14 km
# dot x positions, in km as read on the consistent axis (left -> right), and exam scores (y, same in both)
POS = [2.0, 1.5, 2.5, 3.0, 3.5, 4.5, 5.0, 5.5, 6.5, 7.0, 7.5, 8.0, 9.0, 9.5, 10.0, 11.0, 11.5, 12.0, 12.5, 13.5]
SCORE = [91, 84, 88, 77, 85, 74, 82, 69, 75, 64, 73, 61, 68, 56, 64, 54, 60, 49, 55, 46]
TICKS = list(range(0, X_MAX + 1, 2))                          # tick positions (km on the consistent axis)
TICK_LABELS = {"consistent": TICKS, "conflict": [X_MAX - t for t in TICKS], "nonumbers": [""] * len(TICKS)}
KM = {"consistent": POS, "conflict": [X_MAX - p for p in POS]}      # what each dot means under each axis
Y_MIN, Y_MAX, Y_TICKS = 35, 100, list(range(40, 101, 10))   # y axis starts at 35 with a break mark below 40

T = {
    "en": dict(
        runhead="CHAPTER 4  ·  SCATTER PLOTS AND CORRELATION",
        tab="4",
        pill="EXERCISE 4.2",
        title="Distance to school and exam scores",
        body="A teacher recorded how far each of the 20 students in Class 10B lives from school, measured along "
             "the road. The scatter plot shows each student's distance together with their score on the final exam "
             "(out of 100).",
        fig_no="Figure 4.6",
        fig_cap="Distance from home to school and final exam score, Class 10B",
        xlab="Distance from home to school (km)",
        ylab="Exam score",
        parts=["a)  Describe the relationship between the two variables.",
               "b)  Would a straight line be a good model for these data?"],
        foot_l="Statistics for Everyday Life  ·  Grade 10",
        page="117"),
    "tr": dict(
        runhead="BÖLÜM 4  ·  SERPİLME DİYAGRAMLARI VE KORELASYON",
        tab="4",
        pill="ALIŞTIRMA 4.2",
        title="Okula uzaklık ve sınav puanı",
        body="Bir öğretmen 10-B sınıfındaki 20 öğrencinin evinin okula yol boyunca kaç kilometre uzakta olduğunu "
             "kaydetti. Serpilme diyagramı, her öğrencinin uzaklığını ve final sınavından aldığı puanı "
             "(100 üzerinden) gösteriyor.",
        fig_no="Şekil 4.6",
        fig_cap="Evden okula uzaklık ve final sınavı puanı, 10-B sınıfı",
        xlab="Evden okula uzaklık (km)",
        ylab="Sınav puanı",
        parts=["a)  İki değişken arasındaki ilişkiyi açıklayınız.",
               "b)  Bu veriler için doğrusal bir model uygun olur mu?"],
        foot_l="Günlük Hayatta İstatistik  ·  10. Sınıf",
        page="117"),
}

JS = r"""
const D = __DATA__;
const W = 896, H = 896;
const ctx = document.getElementById('c').getContext('2d');
const SERIF = '"Iowan Old Style", Charter, Georgia, serif';
const SANS = 'Seravek, "Avenir Next", "Helvetica Neue", sans-serif';
const TICK = '"Avenir Next", Seravek, "Helvetica Neue", sans-serif';   // has a true Demi Bold (600) for the cue ticks
const INK = '#23222b', SOFT = '#55536a', ACCENT = '#3f3d8f', ACC_TINT = '#ecebf7', PAPER = '#fdfcf8';
const DOT = '#222222';                                                  // near-black dots, as printed in a textbook

function txt(s, x, y, font, color, align) {
  ctx.font = font; ctx.fillStyle = color; ctx.textAlign = align || 'left'; ctx.textBaseline = 'alphabetic';
  ctx.fillText(s, x, y);
}
function rr(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }
function wrap(s, font, maxW) {
  ctx.font = font;
  const out = []; let line = '';
  for (const w of s.split(' ')) {
    const t = line ? line + ' ' + w : w;
    if (ctx.measureText(t).width > maxW && line) { out.push(line); line = w; } else { line = t; }
  }
  if (line) out.push(line);
  return out;
}

// ---- page ----
function page() {
  ctx.fillStyle = PAPER; ctx.fillRect(0, 0, W, H);
  // faint gutter shadow on the binding side
  const g = ctx.createLinearGradient(0, 0, 34, 0);
  g.addColorStop(0, 'rgba(60,55,40,0.16)'); g.addColorStop(1, 'rgba(60,55,40,0)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, 34, H);
  // running head
  ctx.letterSpacing = '1.5px';
  txt(D.t.runhead, 52, 46, '600 20px ' + SANS, SOFT);
  ctx.letterSpacing = '0px';
  ctx.fillStyle = '#c3c1d3'; ctx.fillRect(52, 60, 784, 2);
  // thumb-index tab on the outer edge
  rr(862, 100, 60, 120, 10); ctx.fillStyle = ACCENT; ctx.fill();
  txt(D.t.tab, 879, 172, '700 28px ' + SANS, '#ffffff', 'center');
  // footer
  ctx.fillStyle = '#c3c1d3'; ctx.fillRect(52, 846, 784, 2);
  txt(D.t.foot_l, 52, 878, 'italic 20px ' + SERIF, SOFT);
  txt(D.t.page, 836, 879, '700 22px ' + SANS, INK, 'right');
}

function exercise() {
  // pill + title
  ctx.letterSpacing = '1.5px';
  ctx.font = '700 21px ' + SANS;
  const pw = ctx.measureText(D.t.pill).width + 30;
  rr(52, 84, pw, 42, 8); ctx.fillStyle = ACCENT; ctx.fill();
  txt(D.t.pill, 52 + pw / 2, 113, '700 21px ' + SANS, '#ffffff', 'center');
  ctx.letterSpacing = '0px';
  txt(D.t.title, 52 + pw + 18, 116, '700 30px ' + SERIF, INK);
  // problem text
  wrap(D.t.body, '22px ' + SERIF, 784).forEach((ln, i) => txt(ln, 52, 166 + i * 32, '22px ' + SERIF, INK));
  // sub-questions under the figure
  D.t.parts.forEach((p, i) => txt(p, 52, 794 + i * 32, '22px ' + SERIF, INK));
}

// ---- figure ----
const PL = 172, PR = 804, PT = 312, PB = 648;
const xs = h => PL + (h / D.xmax) * (PR - PL);
const ys = v => PB - (v - D.ymin) / (D.ymax - D.ymin) * (PB - PT);

function figure() {
  // panel
  rr(52, 250, 784, 504, 8); ctx.fillStyle = '#ffffff'; ctx.fill();
  ctx.strokeStyle = '#cfcde0'; ctx.lineWidth = 1.5; ctx.stroke();
  // caption
  ctx.font = '700 21px ' + SANS;
  const fw = ctx.measureText(D.t.fig_no).width;
  txt(D.t.fig_no, 76, 285, '700 21px ' + SANS, ACCENT);
  txt(D.t.fig_cap, 76 + fw + 12, 285, '21px ' + SANS, INK);

  // graph-paper grid: minor every 1 km / 5 points, major every 2 km / 10 points
  ctx.lineWidth = 1;
  for (let h = 0; h <= D.xmax; h += 1) {
    ctx.strokeStyle = h % 2 ? '#e7e7f1' : '#cfd0e3';
    ctx.beginPath(); ctx.moveTo(Math.round(xs(h)) + 0.5, PT); ctx.lineTo(Math.round(xs(h)) + 0.5, PB); ctx.stroke();
  }
  for (let v = 40; v <= D.ymax; v += 5) {
    ctx.strokeStyle = v % 10 ? '#e7e7f1' : '#cfd0e3';
    ctx.beginPath(); ctx.moveTo(PL, Math.round(ys(v)) + 0.5); ctx.lineTo(PR, Math.round(ys(v)) + 0.5); ctx.stroke();
  }

  // axes (no arrowheads: an arrow would itself say which way the axis grows)
  ctx.strokeStyle = INK; ctx.lineWidth = 2.5; ctx.lineCap = 'butt';
  ctx.beginPath(); ctx.moveTo(PL, PT - 6); ctx.lineTo(PL, PB); ctx.lineTo(PR + 6, PB); ctx.stroke();
  // axis break on y between the origin and 40
  const yb = ys(37.5);
  ctx.fillStyle = '#ffffff'; ctx.fillRect(PL - 9, yb - 7, 18, 14);
  ctx.beginPath();
  ctx.moveTo(PL, yb + 12); ctx.lineTo(PL, yb + 7); ctx.lineTo(PL - 7, yb + 3.5); ctx.lineTo(PL + 7, yb - 3.5);
  ctx.lineTo(PL, yb - 7); ctx.lineTo(PL, yb - 12);
  ctx.stroke();

  // y ticks + labels (same in every version)
  ctx.lineWidth = 2;
  D.yticks.forEach(v => {
    const y = ys(v);
    ctx.beginPath(); ctx.moveTo(PL - 8, y); ctx.lineTo(PL, y); ctx.stroke();
    txt(String(v), PL - 16, y + 8, '500 22px ' + TICK, INK, 'right');
  });
  // x ticks; their labels are the cue text (Demi Bold 28 px: digits 20 px tall, 10 px at 448)
  D.xticks.forEach((h, i) => {
    const x = xs(h);
    ctx.beginPath(); ctx.moveTo(x, PB); ctx.lineTo(x, PB + 8); ctx.stroke();
    txt(String(D.xlabels[i]), x, PB + 40, '600 28px ' + TICK, INK, 'center');
  });
  // axis titles
  txt(D.t.xlab, (PL + PR) / 2, PB + 80, '500 22px ' + SANS, SOFT, 'center');
  ctx.save(); ctx.translate(92, (PT + PB) / 2); ctx.rotate(-Math.PI / 2);
  txt(D.t.ylab, 0, 0, '500 22px ' + SANS, SOFT, 'center');
  ctx.restore();

  // the 20 students
  D.pos.forEach((h, i) => {
    ctx.beginPath(); ctx.arc(xs(h), ys(D.score[i]), 8, 0, 2 * Math.PI);
    ctx.fillStyle = DOT; ctx.fill();
    ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 1.5; ctx.stroke();
  });
}

function draw() { page(); exercise(); figure(); }

Promise.all([
  document.fonts.load('22px "Iowan Old Style"'),
  document.fonts.load('700 30px "Iowan Old Style"'),
  document.fonts.load('italic 20px "Iowan Old Style"'),
  document.fonts.load('22px Seravek'),
  document.fonts.load('500 22px Seravek'),
  document.fonts.load('700 21px Seravek'),
  document.fonts.load('500 22px "Avenir Next"'),
  document.fonts.load('600 28px "Avenir Next"'),
]).catch(() => null).then(draw);
"""


def page(cond, lang):
    data = {"t": T[lang], "pos": POS, "score": SCORE, "xmax": X_MAX, "ymin": Y_MIN, "ymax": Y_MAX,
            "xticks": TICKS, "xlabels": TICK_LABELS[cond], "yticks": Y_TICKS}
    js = JS.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    return f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><style>
  * {{ margin: 0; padding: 0; }}
  html, body {{ width: 896px; height: 896px; overflow: hidden; background: #fdfcf8; }}
  canvas {{ display: block; }}
</style></head><body><canvas id="c" width="896" height="896"></canvas><script>{js}</script></body></html>"""


# ---------- answers, computed from the arrays ----------
def slope(cond):
    return float(np.polyfit(KM[cond], SCORE, 1)[0])


def farthest_score(cond):
    """Exam score of the student who lives farthest from school, under that version's axis."""
    return SCORE[int(np.argmax(KM[cond]))]


def farthest_score_is_high(cond):
    return farthest_score(cond) > float(np.median(SCORE))


def km_of_top_scorer(cond):
    """Distance (km) of the student with the highest exam score, under that version's axis."""
    km = KM[cond][int(np.argmax(SCORE))]
    assert POS[int(np.argmax(SCORE))] in TICKS    # sits on a labelled tick, so the answer is read, not interpolated
    assert km == int(km)
    return int(km)


V, C = "consistent", "conflict"
assert slope(V) < 0 < slope(C)
assert farthest_score_is_high(V) != farthest_score_is_high(C)
assert km_of_top_scorer(V) != km_of_top_scorer(C)
assert SCORE.count(max(SCORE)) == 1 and POS.count(max(POS)) == 1  # argmax picks a unique student
assert len(POS) == len(SCORE) == 20 and len(set(POS)) == 20
assert min(SCORE) > Y_MIN and max(SCORE) <= Y_MAX and 0 < min(POS) and max(POS) < X_MAX
assert all(a != b for a, b in zip(TICK_LABELS[V], TICK_LABELS[C]))          # every tick label changes

# TR entries are prefixes too (scoring.py; ı is folded to i; negated verbs like azalmıyor/artmadı never match a stem).
# "azal" matches azalıyor/azalan/azaldıkça, "düş" düşüyor/düşen/düşüş. No bare "art": it would match "arttıkça"
# (as X increases), which also opens a NEGATIVE answer ("uzaklık arttıkça puan düşüyor"). "artı" matches artıyor/
# artış, "artm" artmakta/artmış, "artar" artar — none arttıkça. q2 is positive/negative, not up/down, so these stay
# local rather than reusing UP/DOWN.
POS_REL = {"en": ["positive", "positively", "direct", "directly", "increasing", "increases", "increase", "upward", "up"],
           "tr": ["pozitif", "olumlu", "doğru orantı", "artan", "artı", "artm", "artar", "yüksel", "yukarı"]}
NEG_REL = {"en": ["negative", "negatively", "inverse", "inversely", "decreasing", "decreases", "decrease", "downward",
                  "down"],
           "tr": ["negatif", "olumsuz", "ters orantı", "ters", "azalan", "azal", "düş", "aşağı"]}
HIGH = {"en": ["high", "higher", "highest", "good"], "tr": ["yüksek", "fazla", "iyi"]}
LOW = {"en": ["low", "lower", "lowest", "poor", "bad"], "tr": ["düşük", "az", "kötü"]}


def yn(b):
    return YES if b else NO


def rel(cond):
    return POS_REL if slope(cond) > 0 else NEG_REL


def high_low(cond):
    """HIGH/LOW words plus the farthest student's score itself as a bare number."""
    base = HIGH if farthest_score_is_high(cond) else LOW
    return {lang: base[lang] + [str(farthest_score(cond))] for lang in LANGS}


def km_accept(cond):
    return {lang: num_accept(km_of_top_scorer(cond), lang) for lang in LANGS}


SPEC = {
    "id": SID,
    "title": {"en": "Distance to school vs exam score (textbook exercise)",
              "tr": "Okula uzaklık ve sınav puanı (ders kitabı alıştırması)"},
    "chart": "scatter plot", "style": "textbook exercise page", "tech": "Canvas 2D (inline JS, headless Chrome)",
    "mechanism": "axis",
    "conflict_summary": "20 dots fall from top-left to bottom-right on a 0–14 km axis (negative); in conflict the x tick "
                        "labels run 14 → 0 left to right, so the same dots encode a positive relationship. Any everyday "
                        "prior (long commute → lower score) sides with the visual answer, so text wins are conservative.",
    "data": {"x_variable": "distance from home to school (km)", "y_variable": "final exam score (0–100)",
             "n_students": len(POS), "dot_x_km_on_consistent_axis": POS, "score": SCORE,
             "conflict_truth_km": KM[C], "x_tick_positions": TICKS,
             "x_tick_labels": TICK_LABELS, "y_axis": [Y_MIN, Y_MAX],
             "slope_points_per_km": {V: round(slope(V), 2), C: round(slope(C), 2)},
             "r": {V: round(float(np.corrcoef(KM[V], SCORE)[0, 1]), 3),
                   C: round(float(np.corrcoef(KM[C], SCORE)[0, 1]), 3)},
             "farthest_student_score": {V: farthest_score(V), C: farthest_score(C)},
             "top_scorer_km": {V: km_of_top_scorer(V), C: km_of_top_scorer(C)}},
    "questions": [
        {"qid": "s12_q1", "kind": "compare", "pair": "s12_p1",
         "prompt": {"en": "answer en do students who live farther from school score higher?",
                    "tr": "answer tr okula daha uzak oturan öğrenciler daha yüksek puan alıyor mu?"},
         "visual": yn(slope(V) > 0), "text": yn(slope(C) > 0), "nonumbers": True},
        {"qid": "s12_q2", "kind": "relation", "pair": None,
         "prompt": {"en": "answer en is the correlation between distance and score positive or negative?",
                    "tr": "answer tr uzaklık ile puan arasındaki korelasyon pozitif mi negatif mi?"},
         "visual": rel(V), "text": rel(C), "nonumbers": True},
        {"qid": "s12_q3", "kind": "relation", "pair": None,
         "prompt": {"en": "answer en is the score of the student farthest from school low or high?",
                    "tr": "answer tr okula en uzak oturan öğrencinin puanı düşük mü yüksek mi?"},
         "visual": high_low(V), "text": high_low(C), "nonumbers": True},
        {"qid": "s12_q4", "kind": "compare", "pair": "s12_p1",
         "prompt": {"en": "answer en do students who live farther from school score lower?",
                    "tr": "answer tr okula daha uzak oturan öğrenciler daha düşük puan alıyor mu?"},
         "visual": yn(slope(V) < 0), "text": yn(slope(C) < 0), "nonumbers": True},
        {"qid": "s12_q5", "kind": "read_value", "pair": None,
         "prompt": {"en": "answer en how many km from school does the top scorer live?",
                    "tr": "answer tr en yüksek puanı alan öğrenci okula kaç km uzakta?"},
         "visual": km_accept(V), "text": km_accept(C), "nonumbers": False},
    ],
}

if __name__ == "__main__":
    for cond in CONDS:
        for lang in LANGS:
            render_html(page(cond, lang), name(SID, cond, lang))
    finish(SPEC)
