"""s06 — TV weather full-screen graphic with four glass thermometers (Canvas 2D).

The mercury columns encode the real noon temperature; the big readout under each tube is the cue text.
In `conflict` the readouts are permuted (31<->-3, 12<->24) while every pixel of the drawing stays the same.
In `nonumbers` the four readout strings are not drawn; the empty white readout boxes stay, so nothing moves.
Each tube carries one identical, unlabeled notch at 0 °C (no text, same in all four images).

Deviations from DESIGN.md §s06 (review fixes; DESIGN.md still lists the old names/q4):
- city names Ardena/Belmora/Castelo/Dunmere -> Avlen/Berim/Covra/Dimel: invented, no regional morphology
  (Dun-/-mere read cold-northern, Castel-/-o warm-southern, Ard- ~ "ardent"; an earlier "Davro" was one letter
  from the alpine resort Davos), so no name prior for warm/cold;
- q4 reads Dimel (visual -3, text 31), not Castelo: Castelo's 12<->24 swap is with the ADJACENT card, so a
  neighbour mis-read looked like 'visual', and its text answer 12 also matched the '12:00' clock. -3 and 31
  sit three cards apart and are printed nowhere else.

Set-level review: condensed broadcast typography (DIN Condensed for readouts/title/clock/band, Avenir Next Condensed
for names and running text; both checked for ş ğ ı İ ç ö ü) so the set does not reuse one sans everywhere;
answers use the shared lists in common/answers.py (YES/NO, num_accept).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
from lib import CONDS, LANGS, finish, fmt_num, name, render_html  # noqa: E402
from scoring import tokens  # noqa: E402
from answers import NO, YES, num_accept  # noqa: E402

SID = "s06_tv_thermometers"
CITIES = ["Avlen", "Berim", "Covra", "Dimel"]                 # invented, identical in en and tr
VISUAL = [31, 12, 24, -3]                                      # mercury level = readout in `consistent`
CONFLICT = [-3, 24, 12, 31]                                    # readouts in `conflict` (permutation)
READOUTS = {"consistent": VISUAL, "conflict": CONFLICT, "nonumbers": [None] * 4}   # nonumbers: empty readout boxes
T_MIN, T_MAX = -10, 40                                         # tube bottom/top in °C (no ticks are drawn)

T = {
    "en": dict(
        title="NOON TEMPERATURES",
        sub="Sunday, 4 October  ·  readings in °C",
        live="LIVE",
        band="WEATHER",
        ticker="Readings from city weather stations at 12:00",
        host="with Selin Ova",
        next="Next update 18:00"),
    "tr": dict(
        title="ÖĞLE SICAKLIKLARI",
        sub="4 Ekim Pazar  ·  değerler °C cinsinden",
        live="CANLI",
        band="HAVA DURUMU",
        ticker="Şehir istasyonlarının saat 12:00 ölçümleri",
        host="Sunucu: Selin Ova",
        next="Sonraki güncelleme 18:00"),
}

JS = r"""
const D = __DATA__;
const W = 896, H = 896;
const cv = document.getElementById('c');
const ctx = cv.getContext('2d');
// condensed broadcast faces (both cover ş ğ ı İ ç ö ü ° −): DIN Condensed (bold only) for the big numerals and
// caps, Avenir Next Condensed for names and running text
const SANS = '"Avenir Next Condensed", "Arial Narrow", sans-serif';
const DIN = '"DIN Condensed", "Avenir Next Condensed", "Arial Narrow", sans-serif';
const INK = '#1c1a26', PAPER = '#f2f1f6', SILVER = '#c9c6d6';

function rr(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }
function txt(s, x, y, font, color, align) {
  ctx.font = font; ctx.fillStyle = color; ctx.textAlign = align || 'left'; ctx.textBaseline = 'alphabetic';
  ctx.fillText(s, x, y);
}

// glass thermometer outline: rounded tube on top of a round bulb
function tubePath(cx, top, hw, by, R) {
  const a = Math.acos(hw / R), neck = by - Math.sqrt(R * R - hw * hw);
  ctx.beginPath();
  ctx.moveTo(cx + hw, neck);
  ctx.lineTo(cx + hw, top + hw);
  ctx.arc(cx, top + hw, hw, 0, Math.PI, true);
  ctx.lineTo(cx - hw, neck);
  ctx.arc(cx, by, R, a - Math.PI, -a, true);
  ctx.closePath();
}

function background() {
  const g = ctx.createLinearGradient(0, 0, 0, H);
  g.addColorStop(0, '#2a2838'); g.addColorStop(1, '#14131b');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  const r = ctx.createRadialGradient(448, 300, 40, 448, 300, 620);
  r.addColorStop(0, 'rgba(255,255,255,0.07)'); r.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = r; ctx.fillRect(0, 0, W, H);
  // faint isobar-like contours
  ctx.strokeStyle = 'rgba(255,255,255,0.05)'; ctx.lineWidth = 2;
  for (let k = 0; k < 9; k++) {
    ctx.beginPath();
    for (let x = -10; x <= W + 10; x += 8) {
      const y = 150 + k * 78 + 26 * Math.sin(x / 140 + k * 0.9) + 14 * Math.sin(x / 61 + k * 2.1);
      x === -10 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.stroke();
  }
}

function header() {
  const g = ctx.createLinearGradient(0, 0, 0, 120);
  g.addColorStop(0, '#3a3748'); g.addColorStop(1, '#2b2938');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, 120);
  ctx.fillStyle = SILVER; ctx.fillRect(0, 120, W, 3);
  // channel bug
  rr(32, 23, 74, 74, 14); ctx.fillStyle = PAPER; ctx.fill();
  txt('4', 69, 83, '700 64px ' + DIN, INK, 'center');
  ctx.letterSpacing = '2px';
  txt(D.t.title, 126, 67, '700 50px ' + DIN, '#ffffff');
  ctx.letterSpacing = '0px';
  txt(D.t.sub, 127, 100, '500 26px ' + SANS, SILVER);
  // clock + live badge
  txt('12:00', 864, 62, '700 44px ' + DIN, '#ffffff', 'right');
  ctx.letterSpacing = '1px';
  ctx.font = '700 22px ' + DIN;
  const lw = ctx.measureText(D.t.live).width + 24;
  rr(864 - lw, 74, lw, 30, 6); ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 2; ctx.stroke();
  txt(D.t.live, 864 - lw / 2, 97, '700 22px ' + DIN, '#ffffff', 'center');
  ctx.letterSpacing = '0px';
}

function card(i, city, temp, label) {
  const cw = 192, gap = 16, x0 = 40, top = 142, h = 630;
  const x = x0 + i * (cw + gap), cx = x + cw / 2;
  rr(x, top, cw, h, 22);
  ctx.fillStyle = 'rgba(255,255,255,0.06)'; ctx.fill();
  ctx.strokeStyle = 'rgba(255,255,255,0.16)'; ctx.lineWidth = 2; ctx.stroke();

  txt(city, cx, 196, '600 34px ' + SANS, '#ffffff', 'center');
  ctx.fillStyle = 'rgba(201,198,214,0.6)'; ctx.fillRect(cx - 30, 212, 60, 2);

  // glass tube
  const tTop = 238, hw = 25, by = 630, R = 38;
  tubePath(cx, tTop, hw, by, R);
  ctx.fillStyle = 'rgba(255,255,255,0.10)'; ctx.fill();
  // empty inner channel
  const iTop = tTop + 12, ihw = 11, iR = 27;
  tubePath(cx, iTop, ihw, by, iR);
  ctx.fillStyle = '#121119'; ctx.fill();
  // mercury: bulb always full, column up to the level (no tick scale)
  const yFull = iTop + ihw, yEmpty = by - iR;
  const f = (temp - D.tmin) / (D.tmax - D.tmin);
  const level = yEmpty - f * (yEmpty - yFull);
  ctx.save();
  tubePath(cx, iTop, ihw, by, iR); ctx.clip();
  const mg = ctx.createLinearGradient(cx - iR, 0, cx + iR, 0);
  mg.addColorStop(0, '#8d90a2'); mg.addColorStop(0.38, '#ffffff'); mg.addColorStop(0.62, '#d8dae4'); mg.addColorStop(1, '#8a8d9e');
  ctx.fillStyle = mg; ctx.fillRect(cx - iR, level, 2 * iR, by + iR - level);
  const bg = ctx.createRadialGradient(cx - 9, by - 10, 2, cx, by, iR);
  bg.addColorStop(0, '#ffffff'); bg.addColorStop(0.55, '#d3d5df'); bg.addColorStop(1, '#8a8d9e');
  ctx.beginPath(); ctx.arc(cx, by, iR, 0, 2 * Math.PI); ctx.fillStyle = bg; ctx.fill();
  ctx.restore();
  // glass outline + highlights
  tubePath(cx, tTop, hw, by, R);
  ctx.strokeStyle = 'rgba(255,255,255,0.62)'; ctx.lineWidth = 3; ctx.stroke();
  ctx.strokeStyle = 'rgba(255,255,255,0.30)'; ctx.lineWidth = 4; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(cx - 18, tTop + 22); ctx.lineTo(cx - 18, by - 46); ctx.stroke();
  ctx.beginPath(); ctx.arc(cx, by, R - 8, Math.PI * 1.08, Math.PI * 1.32); ctx.stroke();
  // one unlabeled reference notch at 0 °C, identical on every tube (no scale, no text)
  const y0 = Math.round(yEmpty - (0 - D.tmin) / (D.tmax - D.tmin) * (yEmpty - yFull));
  ctx.strokeStyle = 'rgba(255,255,255,0.75)'; ctx.lineWidth = 3; ctx.lineCap = 'butt';
  ctx.beginPath();
  ctx.moveTo(cx - hw - 12, y0); ctx.lineTo(cx - hw + 1, y0);
  ctx.moveTo(cx + hw - 1, y0); ctx.lineTo(cx + hw + 12, y0);
  ctx.stroke();

  // readout
  rr(cx - 76, 688, 152, 68, 14); ctx.fillStyle = PAPER; ctx.fill();
  // `nonumbers`: label is '' -> the empty readout box stays, nothing is drawn inside it
  if (label) txt(label, cx, 745, '700 64px ' + DIN, INK, 'center');     // cap height 0.712 em -> centred in the 68 px box
}

function lowerThird() {
  ctx.fillStyle = 'rgba(8,8,12,0.55)'; ctx.fillRect(0, 792, W, 56);
  ctx.fillStyle = PAPER; ctx.fillRect(0, 792, 210, 56);
  ctx.letterSpacing = '1.5px';
  txt(D.t.band, 105, 830, '700 28px ' + DIN, INK, 'center');
  ctx.letterSpacing = '0px';
  txt(D.t.ticker, 230, 829, '500 26px ' + SANS, '#ffffff');
  ctx.fillStyle = SILVER; ctx.fillRect(0, 848, W, 2);
  txt(D.t.host, 32, 881, 'italic 500 24px ' + SANS, SILVER);
  txt(D.t.next, 864, 881, '500 24px ' + SANS, SILVER, 'right');
}

function draw() {
  background();
  header();
  D.cities.forEach((c, i) => card(i, c, D.temps[i], D.labels[i]));
  lowerThird();
}

Promise.all([
  document.fonts.load('700 64px "DIN Condensed"'),
  document.fonts.load('600 34px "Avenir Next Condensed"'),
  document.fonts.load('500 26px "Avenir Next Condensed"'),
  document.fonts.load('italic 500 24px "Avenir Next Condensed"'),
]).catch(() => null).then(draw);
"""


def page(cond, lang):
    data = {"t": T[lang], "cities": CITIES, "temps": VISUAL, "tmin": T_MIN, "tmax": T_MAX,
            "labels": ["" if v is None else fmt_num(v, lang) + "°" for v in READOUTS[cond]]}
    js = JS.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    return f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><style>
  * {{ margin: 0; padding: 0; }}
  html, body {{ width: 896px; height: 896px; overflow: hidden; background: #14131b; }}
  canvas {{ display: block; }}
</style></head><body><canvas id="c" width="896" height="896"></canvas><script>{js}</script></body></html>"""


# ---------- questions (answers computed from the arrays) ----------
# shared lists (common/answers.py): NO["tr"] already holds "^değil" (bare "değil" as the whole answer).
# No extra "altında"/"üstünde" forms for the pair: "altında değil" (= no) would hit "altında" (= yes).
# q4 numbers via num_accept (digits by value + whole-answer words, incl. "minus three"/"eksi üç");
# local extras keep the digit + word spellings of the negative reading ("minus 3", "3 below zero", "eksi 3").
NUM_EXTRA = {-3: {"en": ("minus 3", "3 below zero", "three below zero"), "tr": ("eksi 3", "sıfırın altında 3")},
             31: {"en": (), "tr": ()}}


def city_of(vals, fn):
    return CITIES[vals.index(fn(vals))]


def names(c):
    return {"en": [c.lower()], "tr": [c.lower()]}


def yn(b):
    src = YES if b else NO
    return {lang: list(src[lang]) for lang in LANGS}


def num(v):
    return {lang: num_accept(v, lang, extra=NUM_EXTRA[v][lang]) for lang in LANGS}


A = CITIES.index("Avlen")      # q3 pair: 31° drawn, −3° printed in conflict -> sign flips
D = CITIES.index("Dimel")      # q4: −3° drawn, 31° printed in conflict
assert city_of(VISUAL, max) != city_of(CONFLICT, max)
assert city_of(VISUAL, min) != city_of(CONFLICT, min)
assert (VISUAL[A] < 0) != (CONFLICT[A] < 0)
assert VISUAL[D] != CONFLICT[D]
assert sorted(VISUAL) == sorted(CONFLICT)
# q4 must not be confusable with a neighbouring readout: its visual answer is printed (in conflict) and its
# text answer is printed (in consistent) at least two cards away from the asked city.
assert abs(CONFLICT.index(VISUAL[D]) - D) >= 2 and abs(VISUAL.index(CONFLICT[D]) - D) >= 2
# no q4 answer may appear as a number anywhere else in the image (clock, date, ticker, channel bug)
_fixed = set(tok for lang in LANGS for s in T[lang].values() for tok in tokens(s)) | {"4"}
for _v in (VISUAL[D], CONFLICT[D]):
    assert tokens(fmt_num(_v, "en"))[0] not in _fixed, _v

SPEC = {
    "id": SID,
    "title": {"en": "Noon temperatures (TV weather)", "tr": "Öğle sıcaklıkları (TV hava durumu)"},
    "chart": "thermometer fills", "style": "TV weather broadcast graphic", "tech": "Canvas 2D (inline JS, headless Chrome)",
    "mechanism": "readout",
    "conflict_summary": "Mercury columns: Avlen highest, Dimel lowest (just under the 0 °C notch); in conflict the "
                        "readouts are swapped 31°<->−3° (Avlen<->Dimel, three cards apart) and 12°<->24° (Berim<->Covra).",
    "data": {"cities": CITIES, "visual": VISUAL, "conflict_readouts": CONFLICT,
             "tube_scale_c": [T_MIN, T_MAX], "zero_notch_c": 0,
             "note": "column height = (t - tmin)/(tmax - tmin) of the tube; no ticks or numbers on the tubes, "
                     "only one unlabeled notch at 0 °C on every tube (identical in all images)",
             "nonumbers": "readout strings not drawn, empty readout boxes kept; tubes/notches unchanged",
             "deviation_from_design_md": "names Ardena/Belmora/Castelo/Dunmere -> Avlen/Berim/Covra/Dimel "
                                         "(no regional cold/warm morphology); q4 reads Dimel instead of Castelo "
                                         "(Castelo's 12<->24 swap was with the adjacent card, and 12 collided "
                                         "with the 12:00 clock)"},
    "questions": [
        {"qid": "s06_q1", "kind": "argmax", "pair": None,
         "prompt": {"en": "answer en which city is the warmest?",
                    "tr": "answer tr en sıcak şehir hangisi?"},
         "visual": names(city_of(VISUAL, max)), "text": names(city_of(CONFLICT, max)),
         "nonumbers": True},             # tallest mercury column
        {"qid": "s06_q2", "kind": "argmin", "pair": None,
         "prompt": {"en": "answer en which city is the coldest?",
                    "tr": "answer tr en soğuk şehir hangisi?"},
         "visual": names(city_of(VISUAL, min)), "text": names(city_of(CONFLICT, min)),
         "nonumbers": True},             # shortest mercury column
        {"qid": "s06_q3a", "kind": "threshold", "pair": "s06_p1",
         "prompt": {"en": "answer en is it below freezing in avlen?",
                    "tr": "answer tr avlen'de sıcaklık sıfırın altında mı?"},
         "visual": yn(VISUAL[A] < 0), "text": yn(CONFLICT[A] < 0),
         "nonumbers": False},            # the 0 °C notch is unlabeled: without readouts nothing says where 0° is
        {"qid": "s06_q3b", "kind": "threshold", "pair": "s06_p1",
         "prompt": {"en": "answer en is it above freezing in avlen?",
                    "tr": "answer tr avlen'de sıcaklık sıfırın üstünde mi?"},
         "visual": yn(VISUAL[A] > 0), "text": yn(CONFLICT[A] > 0),
         "nonumbers": False},            # same pair, same flag
        {"qid": "s06_q4", "kind": "read_value", "pair": None,
         "prompt": {"en": "answer en what is the temperature in dimel?",
                    "tr": "answer tr dimel'de sıcaklık kaç derece?"},
         "visual": num(VISUAL[D]), "text": num(CONFLICT[D]),
         "nonumbers": False},            # exact value only came from the readout (tubes have no scale)
    ],
}

if __name__ == "__main__":
    for cond in CONDS:
        for lang in LANGS:
            render_html(page(cond, lang), name(SID, cond, lang))
    finish(SPEC)
