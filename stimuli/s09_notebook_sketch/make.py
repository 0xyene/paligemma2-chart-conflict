"""s09 — hand-drawn line chart on squared notebook paper. The ink line FALLS Mon→Sun;
in conflict the handwritten numbers rise (reversal with Sat/Sun swapped, see CONFLICT)."""
import random
import sys
from math import cos, hypot, sin, tau
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
from answers import DOWN, NO, UP, YES, num_accept  # noqa: E402
from lib import CONDS, LANGS, finish, fmt_num, name, render_html  # noqa: E402

SID = "s09_notebook_sketch"
VISUAL = [140, 125, 105, 110, 85, 70, 50]                # point heights = written numbers in `consistent`
# DESIGN.md says "reversed" (50,70,85,110,105,125,140). Plain reversal puts the text maximum on Sunday ("Pazar"),
# which is a prefix of Monday ("Pazartesi") -> the Turkish argmax answers cannot be told apart by the matcher.
# So Sat/Sun are swapped: the text still rises Mon→Sun, but its maximum is Saturday ("Cumartesi").
CONFLICT = [50, 70, 85, 110, 105, 140, 125]
LABELS = {"consistent": VISUAL, "conflict": CONFLICT, "nonumbers": VISUAL}   # nonumbers: same <text>s, visibility hidden
assert sorted(CONFLICT) == sorted(VISUAL)
MON, FRI, SUN = 0, 4, 6

T = {
    "en": dict(
        date_lbl="DATE", date="4 Oct 2026",
        title="Daily users of our app", title2="(week 41)",
        ylab="users", xlab="day",
        days=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        notes=["* user = an account that opened the app that day",
               "counted from the sign-in log · next: week 42"]),
    "tr": dict(
        date_lbl="TARİH", date="4 Ekim 2026",
        title="Uygulamamızın günlük kullanıcıları", title2="(41. hafta)",
        ylab="kullanıcı", xlab="gün",
        days=["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"],
        notes=["* kullanıcı = o gün uygulamayı açan hesap",
               "giriş kayıtlarından sayıldı · sıradaki: 42. hafta"]),
}

# ---------- geometry (shared by all six images) ----------
W = 896
GRID = 30                       # squared paper: 1 square = 10 users
K = GRID / 10                   # px per user
X0, BASE = 180, 720             # y-axis x, x-axis y (both on grid lines)
PX = [X0 + 2 * GRID + 3 * GRID * i for i in range(7)]           # 240, 330, ..., 780 (every 3rd grid line)
PY = [BASE - v * K for v in VISUAL]
INK = "#22408f"                 # blue ballpoint
PENCIL = "#4f545b"
HAND = "'Bradley Hand', 'Noteworthy', cursive"
PRINT = "'Avenir Next', 'Helvetica Neue', sans-serif"

rng = random.Random(9)


def _seg_points(p, q, step=22, amp=1.3):
    """Densify segment p→q with a little perpendicular hand tremor; endpoints stay exact."""
    (x1, y1), (x2, y2) = p, q
    length = hypot(x2 - x1, y2 - y1)
    n = max(2, int(length / step))
    nx, ny = -(y2 - y1) / length, (x2 - x1) / length
    pts = []
    for k in range(n + 1):
        t = k / n
        j = 0 if k in (0, n) else rng.uniform(-amp, amp)
        pts.append((x1 + (x2 - x1) * t + nx * j, y1 + (y2 - y1) * t + ny * j))
    return pts


def _smooth(pts):
    """Catmull-Rom through pts as cubic Béziers (path data, no leading M)."""
    ext = [pts[0]] + pts + [pts[-1]]
    d = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append(f"C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}")
    return " ".join(d)


def hand_polyline(pts, **kw):
    """Corners stay at the given points (like a pen stopping at each dot); each segment wobbles a little."""
    d = [f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"]
    for p, q in zip(pts, pts[1:]):
        d.append(_smooth(_seg_points(p, q, **kw)))
    return " ".join(d)


def hand_dot(cx, cy, r=7.2):
    """Slightly irregular filled blob for a data point."""
    pts = []
    for k in range(10):
        a = tau * k / 10
        rr = r * rng.uniform(0.85, 1.12)
        pts.append((cx + rr * cos(a), cy + rr * sin(a)))
    pts.append(pts[0])
    return f"M{pts[0][0]:.1f},{pts[0][1]:.1f} " + _smooth(pts) + " Z"


LINE_PTS = list(zip(PX, PY))
LINE_A = hand_polyline(LINE_PTS)                          # main stroke
LINE_B = hand_polyline([(x + 0.8, y - 0.6) for x, y in LINE_PTS], amp=1.8)   # pen retrace, offset a hair
DOTS = [hand_dot(x, y) for x, y in LINE_PTS]
Y_AXIS = hand_polyline([(X0 + 1, BASE + 14), (X0 - 1, 300), (X0, 238)], amp=1.0, step=40)
X_AXIS = hand_polyline([(X0 - 14, BASE + 1), (500, BASE - 1), (854, BASE + 1)], amp=1.0, step=40)
Y_HEAD = f"M{X0 - 9},{254} L{X0},{236} L{X0 + 10},{253}"
X_HEAD = f"M{838},{711} L{856},{BASE + 1} L{839},{730}"
HOLES_Y = list(range(36, 880, 47))


def spiral():
    out = ['<rect x="0" y="0" width="13" height="896" fill="#2f3135"/>',
           '<rect x="13" y="0" width="22" height="896" fill="url(#edge)"/>',
           '<line x1="74" y1="0" x2="74" y2="896" stroke="#c9cdd3" stroke-width="1.4" stroke-dasharray="2 5"/>']
    for y in HOLES_Y:
        out.append(f'<ellipse cx="44" cy="{y}" rx="8.5" ry="7.5" fill="#2b2d31"/>')
        out.append(f'<path d="M45,{y + 1} C33,{y - 15} 10,{y - 13} 3,{y + 3}" fill="none" stroke="#454950" '
                   f'stroke-width="8" stroke-linecap="round"/>')
        out.append(f'<path d="M44,{y - 1} C33,{y - 14} 12,{y - 12} 5,{y + 1}" fill="none" stroke="#c3c8cf" '
                   f'stroke-width="3" stroke-linecap="round"/>')
    return "\n".join(out)


def coffee_ring():
    cx, cy, r = 842, 846, 62
    pts = []
    for k in range(24):
        a = tau * k / 24
        rr = r * rng.uniform(0.97, 1.03)
        pts.append((cx + rr * cos(a), cy + rr * sin(a)))
    pts.append(pts[0])
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f} " + _smooth(pts) + " Z"
    return (f'<path d="{d}" fill="none" stroke="#9c7447" stroke-opacity=".20" stroke-width="7" filter="url(#rough)"/>'
            f'<path d="{d}" fill="#9c7447" fill-opacity=".04" stroke="#8a6034" stroke-opacity=".16" stroke-width="2"/>')


SPIRAL_SVG = spiral()
RING_SVG = coffee_ring()


def page(cond, lang):
    t = T[lang]
    labels = [fmt_num(v, lang) for v in LABELS[cond]]
    s = []
    s.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{W}" viewBox="0 0 {W} {W}">')
    s.append(f"""<defs>
  <pattern id="grid" width="{GRID}" height="{GRID}" patternUnits="userSpaceOnUse">
    <path d="M{GRID} 0 H0 V{GRID}" fill="none" stroke="#b9cbe0" stroke-width="1.1"/>
  </pattern>
  <linearGradient id="edge" x1="0" x2="1"><stop offset="0" stop-color="#d9d7cf"/><stop offset="1" stop-color="#fbfaf4" stop-opacity="0"/></linearGradient>
  <radialGradient id="light" cx="0.35" cy="0.3" r="0.95">
    <stop offset="0" stop-color="#ffffff" stop-opacity="0"/><stop offset="1" stop-color="#6b5a3a" stop-opacity="0.13"/>
  </radialGradient>
  <filter id="paper" filterUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{W}">
    <feTurbulence type="fractalNoise" baseFrequency="0.75" numOctaves="2" seed="11" result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.45  0 0 0 0 0.42  0 0 0 0 0.35  0 0 0 0.10 0"/>
  </filter>
  <filter id="rough" filterUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{W}">
    <feTurbulence type="fractalNoise" baseFrequency="0.032" numOctaves="2" seed="7" result="w"/>
    <feDisplacementMap in="SourceGraphic" in2="w" scale="6" xChannelSelector="R" yChannelSelector="G"/>
  </filter>
  <filter id="pencil" filterUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{W}">
    <feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="2" seed="3" result="w"/>
    <feDisplacementMap in="SourceGraphic" in2="w" scale="4" xChannelSelector="R" yChannelSelector="G" result="d"/>
    <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="1" seed="5" result="g"/>
    <feColorMatrix in="g" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -1.6 1.75" result="ga"/>
    <feComposite in="d" in2="ga" operator="in"/>
  </filter>
  <filter id="inktext" filterUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{W}">
    <feTurbulence type="fractalNoise" baseFrequency="0.06" numOctaves="1" seed="21" result="w"/>
    <feDisplacementMap in="SourceGraphic" in2="w" scale="1.6" xChannelSelector="R" yChannelSelector="G"/>
  </filter>
</defs>""")
    # paper
    s.append(f'<rect width="{W}" height="{W}" fill="#fbfaf4"/>')
    s.append(f'<rect width="{W}" height="{W}" fill="url(#grid)"/>')
    s.append(f'<rect width="{W}" height="{W}" filter="url(#paper)"/>')
    s.append(SPIRAL_SVG)
    s.append(RING_SVG)
    # printed header field
    s.append(f'<text x="600" y="66" font-family="{PRINT}" font-size="20" font-weight="600" letter-spacing="2" '
             f'fill="#8496ad">{t["date_lbl"]}</text>')
    s.append('<line x1="690" y1="72" x2="866" y2="72" stroke="#8496ad" stroke-width="1.5"/>')
    # handwriting (blue ballpoint), mild ink wobble
    s.append(f'<g filter="url(#inktext)" fill="{INK}" font-family="{HAND}" font-weight="700">')
    s.append(f'<text x="700" y="64" font-size="28">{t["date"]}</text>')
    s.append(f'<text x="98" y="128" font-size="{T_SIZE[lang]}">{t["title"]}</text>')
    s.append(f'<text x="102" y="170" font-size="30">{t["title2"]}</text>')
    s.append(f'<text x="{X0}" y="222" font-size="28" text-anchor="middle">{t["ylab"]}</text>')
    s.append(f'<text x="868" y="704" font-size="28" text-anchor="end">{t["xlab"]}</text>')
    for x, d in zip(PX, t["days"]):
        s.append(f'<text x="{x}" y="764" font-size="30" text-anchor="middle">{d}</text>')
    for i, line in enumerate(t["notes"]):
        s.append(f'<text x="{98 + (22 if i else 0)}" y="{822 + 40 * i}" font-size="28">{line}</text>')
    s.append("</g>")
    # cue: handwritten value at every point (nonumbers: same elements, hidden -> nothing else moves)
    vis = ' visibility="hidden"' if cond == "nonumbers" else ""
    s.append(f'<g filter="url(#inktext)" fill="{INK}" font-family="{HAND}" font-weight="700" font-size="40"{vis}>')
    for x, y, lab in zip(PX, PY, labels):
        s.append(f'<text x="{x + 8}" y="{y - 34:.0f}" text-anchor="middle">{lab}</text>')
    s.append("</g>")
    # pencil axes (ruler-less, no ticks)
    s.append(f'<g filter="url(#pencil)" fill="none" stroke="{PENCIL}" stroke-width="3.2" stroke-linecap="round" '
             f'stroke-linejoin="round">')
    s.append(f'<path d="{Y_AXIS}"/><path d="{X_AXIS}"/><path d="{Y_HEAD}"/><path d="{X_HEAD}"/>')
    s.append("</g>")
    # ink line + dots
    s.append(f'<g filter="url(#rough)">')
    s.append(f'<path d="{LINE_A}" fill="none" stroke="{INK}" stroke-width="3.8" stroke-linecap="round" '
             f'stroke-linejoin="round" opacity=".92"/>')
    s.append(f'<path d="{LINE_B}" fill="none" stroke="{INK}" stroke-width="1.6" stroke-linecap="round" opacity=".55"/>')
    for d in DOTS:
        s.append(f'<path d="{d}" fill="{INK}"/>')
    s.append("</g>")
    # photo lighting
    s.append(f'<rect width="{W}" height="{W}" fill="url(#light)" pointer-events="none"/>')
    s.append("</svg>")
    svg = "\n".join(s)
    return f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><style>
  * {{ margin: 0; padding: 0; }}
  html, body {{ width: {W}px; height: {W}px; overflow: hidden; background: #fbfaf4; }}
  svg {{ display: block; }}
</style></head><body>
{svg}
</body></html>"""


T_SIZE = {"en": 44, "tr": 40}

# ---------- questions (answers computed from the arrays) ----------
# Trend = shared UP/DOWN; yes/no = shared YES/NO (common/answers.py), plus the Turkish echo answer to "...var mıydı?":
# "Vardı." = yes, "Yoktu." = no. Whole-answer only ("^"): inside a longer answer they flip meaning
# ("hayır, daha az vardı" is a no to "were there more...?").
Y = {"en": YES["en"], "tr": YES["tr"] + ["^vardı"]}
N = {"en": NO["en"], "tr": NO["tr"] + ["^yoktu"]}
DAY = {  # canonical, abbreviation(s)
    "en": [["monday", "mon"], ["tuesday", "tue", "tues"], ["wednesday", "wed"], ["thursday", "thu", "thurs"],
           ["friday", "fri"], ["saturday", "sat"], ["sunday", "sun"]],
    "tr": [["pazartesi", "pzt", "pts"], ["salı", "sal"], ["çarşamba", "çar", "çrş"], ["perşembe", "per", "prş"],
           ["cuma", "cum"], ["cumartesi", "cmt", "cts"], ["pazar", "paz"]],
}


def trend(vals):
    return UP if vals[SUN] > vals[MON] else DOWN


def argmax_day(vals):
    i = vals.index(max(vals))
    return {lang: DAY[lang][i] for lang in LANGS}


def yn(flag):
    return Y if flag else N


assert max(VISUAL) != max(CONFLICT) or VISUAL.index(max(VISUAL)) != CONFLICT.index(max(CONFLICT))
assert VISUAL[FRI] != CONFLICT[FRI]

SPEC = {
    "id": SID,
    "title": {"en": "Daily users of our app (notebook sketch)", "tr": "Uygulamanın günlük kullanıcıları (defter çizimi)"},
    "chart": "line (hand-drawn)", "style": "squared notebook page with spiral binding",
    "tech": "inline SVG + feTurbulence/feDisplacementMap + handwriting font (Bradley Hand), headless Chrome",
    "mechanism": "label",
    "conflict_summary": "Hand-drawn ink line falls Mon 140 → Sun 50; in conflict the handwritten numbers rise "
                        "50, 70, 85, 110, 105, 140, 125 (text maximum on Saturday).",
    "data": {"days": T["en"]["days"], "visual": VISUAL, "conflict_labels": CONFLICT,
             "note": "conflict = reversal with Sat/Sun swapped so the TR argmax answers are not Pazartesi vs Pazar"},
    "questions": [
        {"qid": "s09_q1", "kind": "trend", "pair": None,
         "prompt": {"en": "answer en did the number of daily users go up or down from monday to sunday?",
                    "tr": "answer tr pazartesiden pazara günlük kullanıcı sayısı arttı mı azaldı mı?"},
         "visual": trend(VISUAL), "text": trend(CONFLICT), "nonumbers": True},
        {"qid": "s09_q2", "kind": "argmax", "pair": None,
         "prompt": {"en": "answer en on which day did the app have the most users?",
                    "tr": "answer tr hangi gün en çok kullanıcı vardı?"},
         "visual": argmax_day(VISUAL), "text": argmax_day(CONFLICT), "nonumbers": True},
        {"qid": "s09_q3a", "kind": "compare", "pair": "s09_p1",
         "prompt": {"en": "answer en were there more users on sunday than on monday?",
                    "tr": "answer tr pazar günü pazartesiden daha fazla kullanıcı var mıydı?"},
         "visual": yn(VISUAL[SUN] > VISUAL[MON]), "text": yn(CONFLICT[SUN] > CONFLICT[MON]), "nonumbers": True},
        {"qid": "s09_q3b", "kind": "compare", "pair": "s09_p1",
         "prompt": {"en": "answer en were there fewer users on sunday than on monday?",
                    "tr": "answer tr pazar günü pazartesiden daha az kullanıcı var mıydı?"},
         "visual": yn(VISUAL[SUN] < VISUAL[MON]), "text": yn(CONFLICT[SUN] < CONFLICT[MON]), "nonumbers": True},
        {"qid": "s09_q4", "kind": "read_value", "pair": None,
         "prompt": {"en": "answer en how many users did the app have on friday?",
                    "tr": "answer tr cuma günü kaç kullanıcı vardı?"},
         "visual": {lang: num_accept(VISUAL[FRI], lang) for lang in LANGS},
         "text": {lang: num_accept(CONFLICT[FRI], lang) for lang in LANGS},
         # no y ticks/numbers anywhere; only path to 85 is counting grid squares (1 sq = 10 users), which is stated nowhere
         "nonumbers": False},
    ],
}

if __name__ == "__main__":
    for cond in CONDS:
        for lang in LANGS:
            render_html(page(cond, lang), name(SID, cond, lang))
    finish(SPEC)
