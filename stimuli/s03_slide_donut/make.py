"""s03 — corporate presentation slide with a donut chart and callout labels.

Slices clockwise from 12 o'clock: Nimbus 46, Orca 27, Pixa 17, Zento 10 (slice sizes).
Conflict callouts print the shares reversed (Nimbus 10 … Zento 46); both sets sum to 100.
Nonumbers: identical slide with the percentage callouts left empty (brand names, leader lines, dots kept).
The whole slide is one hand-built SVG document (rendered by headless Chrome).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
from answers import NO, YES, num_accept  # noqa: E402
from lib import CONDS, LANGS, finish, fmt_pct, name, render_html  # noqa: E402

SID = "s03_slide_donut"
BRANDS = ["Nimbus", "Orca", "Pixa", "Zento"]             # names are identical in en and tr
VISUAL = [46, 27, 17, 10]                                 # slice sizes = printed shares in `consistent`
LABELS = {"consistent": VISUAL, "conflict": VISUAL[::-1], "nonumbers": [None] * len(VISUAL)}   # None = blank callout
assert sum(VISUAL) == 100 and sum(LABELS["conflict"]) == 100
# categorical, non-semantic colours; lightness deliberately NOT monotonic with slice size
COLORS = ["#4a86ad", "#2c3a86", "#c2bba9", "#8f88c6"]

W = H = 896
CX, CY, R_OUT, R_IN = 456, 452, 176, 106                  # donut geometry
LABEL_GAP = 64                                            # label column distance from the outer radius

T = {
    "en": dict(
        org="HALCYRA RESEARCH",
        deck="Quarterly market review · 2026",
        kicker="MARKET OVERVIEW",
        title="Smartphone market share, Q2 2026",
        sub="Share of smartphone units shipped, by brand",
        center=("Q2", "2026"),
        tiles=[("PERIOD", "April–June 2026"), ("MEASURE", "Units shipped"), ("COVERAGE", "All sales channels")],
        source="Source: Halcyra retail panel",
        tag="Internal",
    ),
    "tr": dict(
        org="HALCYRA RESEARCH",
        deck="Çeyreklik pazar raporu · 2026",
        kicker="PAZAR GÖRÜNÜMÜ",
        title="Akıllı telefon pazar payı, 2026 yılı 2. çeyrek",   # not "2026 2. çeyrek": two numbers back to back
        sub="Markalara göre akıllı telefon sevkiyat payı",
        center=("2. çeyrek", "2026"),
        tiles=[("DÖNEM", "Nisan–Haziran 2026"), ("ÖLÇÜT", "Sevkiyat adedi"), ("KAPSAM", "Tüm satış kanalları")],
        source="Kaynak: Halcyra perakende paneli",
        tag="Şirket içi",
    ),
}


def polar(deg, r):
    """Angle measured clockwise from 12 o'clock."""
    a = math.radians(deg)
    return CX + r * math.sin(a), CY - r * math.cos(a)


def slice_path(a0, a1):
    large = 1 if a1 - a0 > 180 else 0
    (x0, y0), (x1, y1) = polar(a0, R_OUT), polar(a1, R_OUT)
    (x2, y2), (x3, y3) = polar(a1, R_IN), polar(a0, R_IN)
    return (f"M{x0:.2f},{y0:.2f} A{R_OUT},{R_OUT} 0 {large} 1 {x1:.2f},{y1:.2f} "
            f"L{x2:.2f},{y2:.2f} A{R_IN},{R_IN} 0 {large} 0 {x3:.2f},{y3:.2f} Z")


# leader-line radial reach beyond the outer edge, per slice (tuned so labels clear each other and the title)
REACH = [20, 22, 18, 30]


def donut(labels, lang):
    out, acc = [], 0.0
    geo = []
    for v, col in zip(VISUAL, COLORS):
        a0, a1 = acc * 3.6, (acc + v) * 3.6
        acc += v
        out.append(f'<path d="{slice_path(a0, a1)}" fill="{col}" stroke="#ffffff" stroke-width="4" stroke-linejoin="round"/>')
        geo.append((a0 + a1) / 2)
    for brand, lab, mid, reach in zip(BRANDS, labels, geo, REACH):
        dx, dy = polar(mid, (R_OUT + R_IN) / 2)               # anchor dot in the middle of the ring
        ex, ey = polar(mid, R_OUT + reach)                    # elbow
        right = math.sin(math.radians(mid)) > 0
        lx = CX + (R_OUT + LABEL_GAP) * (1 if right else -1)  # end of the horizontal leader
        tx = lx + (10 if right else -10)
        anchor = "start" if right else "end"
        out.append(f'<polyline points="{dx:.1f},{dy:.1f} {ex:.1f},{ey:.1f} {lx:.1f},{ey:.1f}" fill="none" '
                   f'stroke="#3a4152" stroke-width="2"/>')
        out.append(f'<circle cx="{dx:.1f}" cy="{dy:.1f}" r="5.5" fill="#ffffff" stroke="#3a4152" stroke-width="2"/>')
        out.append(f'<text x="{tx:.1f}" y="{ey - 9:.1f}" text-anchor="{anchor}" class="brand">{brand}</text>')
        pct = "" if lab is None else fmt_pct(lab, lang)      # nonumbers: same <text> element, empty content
        out.append(f'<text x="{tx:.1f}" y="{ey + 38:.1f}" text-anchor="{anchor}" class="pct">{pct}</text>')
    c1, c2 = T[lang]["center"]
    out.append(f'<text x="{CX}" y="{CY + 4}" text-anchor="middle" class="c1">{c1}</text>')
    out.append(f'<text x="{CX}" y="{CY + 34}" text-anchor="middle" class="c2">{c2}</text>')
    return "\n".join(out)


def slide_svg(cond, lang):
    t = T[lang]
    labels = LABELS[cond]
    tiles = []
    tw, tg, tx0, ty = 252, 22, 48, 694
    for i, (k, v) in enumerate(t["tiles"]):
        x = tx0 + i * (tw + tg)
        tiles.append(f'<rect x="{x}" y="{ty}" width="{tw}" height="96" rx="10" fill="#f1f2f6"/>'
                     f'<rect x="{x}" y="{ty}" width="6" height="96" rx="3" fill="#2c3a86"/>'
                     f'<text x="{x + 24}" y="{ty + 38}" class="tk">{k}</text>'
                     f'<text x="{x + 24}" y="{ty + 72}" class="tv">{v}</text>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<style>
  text {{ font-family: "Avenir Next", "Helvetica Neue", sans-serif; fill: #1c2230; }}
  .org {{ font-size: 20px; font-weight: 700; letter-spacing: 3px; fill: #ffffff; }}
  .deck {{ font-size: 20px; font-weight: 500; fill: #dfe3f3; }}
  .kick {{ font-size: 20px; font-weight: 700; letter-spacing: 2.5px; fill: #2c3a86; }}
  .title {{ font-size: 38px; font-weight: 700; }}
  .sub {{ font-size: 22px; font-weight: 500; fill: #5b6372; }}
  .brand {{ font-size: 26px; font-weight: 600; fill: #3a4152; }}
  .pct {{ font-size: 44px; font-weight: 700; fill: #1c2230; }}
  .c1 {{ font-size: 28px; font-weight: 700; fill: #1c2230; }}
  .c2 {{ font-size: 22px; font-weight: 500; fill: #5b6372; }}
  .tk {{ font-size: 20px; font-weight: 700; letter-spacing: 2px; fill: #5b6372; }}
  .tv {{ font-size: 22px; font-weight: 600; fill: #1c2230; }}
  .foot {{ font-size: 20px; font-weight: 500; fill: #5b6372; }}
  .pg {{ font-size: 20px; font-weight: 700; fill: #ffffff; }}
</style>
<rect width="{W}" height="{H}" fill="#ffffff"/>
<rect width="{W}" height="58" fill="#1f2a63"/>
<rect x="48" y="15" width="28" height="28" rx="7" fill="#ffffff"/>
<path d="M62,20 L71,29 L62,38 L53,29 Z" fill="#1f2a63"/>
<text x="90" y="37" class="org">{t["org"]}</text>
<text x="{W - 48}" y="37" text-anchor="end" class="deck">{t["deck"]}</text>
<text x="48" y="100" class="kick">{t["kicker"]}</text>
<text x="48" y="145" class="title">{t["title"]}</text>
<text x="48" y="180" class="sub">{t["sub"]}</text>
<line x1="48" y1="203" x2="{W - 48}" y2="203" stroke="#d9dce4" stroke-width="2"/>
{donut(labels, lang)}
{"".join(tiles)}
<line x1="48" y1="827" x2="{W - 48}" y2="827" stroke="#d9dce4" stroke-width="2"/>
<text x="48" y="862" class="foot">{t["source"]}</text>
<text x="{W - 98}" y="862" text-anchor="end" class="foot">{t["tag"]}</text>
<rect x="{W - 84}" y="838" width="36" height="34" rx="6" fill="#1f2a63"/>
<text x="{W - 66}" y="862" text-anchor="middle" class="pg">7</text>
</svg>"""


def page(cond, lang):
    return f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><style>
  * {{ margin: 0; padding: 0; }}
  html, body {{ width: {W}px; height: {H}px; overflow: hidden; background: #ffffff; }}
  svg {{ display: block; }}
</style></head><body>
{slide_svg(cond, lang)}
</body></html>"""


# ---------- questions (answers computed from the arrays above) ----------
def shares(cond):
    return dict(zip(BRANDS, LABELS[cond]))


VIS, TXT = shares("consistent"), shares("conflict")
MAX_V, MAX_T = max(VIS, key=VIS.get), max(TXT, key=TXT.get)
MIN_V, MIN_T = min(VIS, key=VIS.get), min(TXT, key=TXT.get)
# threshold pair asks about Zento (the thin slice): visually 10% -> "no, not more than a third";
# its conflict callout prints 46% -> "yes". Both values sit far from the 33.3% boundary.
THIRD = "Zento"
THIRD_V, THIRD_T = VIS[THIRD] > 100 / 3, TXT[THIRD] > 100 / 3
assert MAX_V != MAX_T and MIN_V != MIN_T and VIS["Orca"] != TXT["Orca"]
assert (THIRD_V, THIRD_T) == (False, True), (VIS[THIRD], TXT[THIRD])
assert min(abs(VIS[THIRD] - 100 / 3), abs(TXT[THIRD] - 100 / 3)) > 10


def yn(flag):
    src = YES if flag else NO
    return {lang: list(src[lang]) for lang in LANGS}


def brand(b):
    return {"en": [b.lower()], "tr": [b.lower()]}             # proper names: identical in en and tr


def pct_answers(v):
    """Digits + whole-answer number words (num_accept), plus the percent forms ("27%", "yüzde yirmi yedi")."""
    out = {}
    for lang in LANGS:
        base = num_accept(v, lang)
        words = [w[1:] for w in base if w.startswith("^")]
        if lang == "en":
            extra = [f"{v}%", f"{v} percent"] + [f"^{w} percent" for w in words]
        else:
            extra = [f"%{v}", f"yüzde {v}"] + [f"^yüzde {w}" for w in words]
        out[lang] = base + extra
    return out


SPEC = {
    "id": SID,
    "title": {"en": "Smartphone market share (presentation slide)", "tr": "Akıllı telefon pazar payı (sunum slaytı)"},
    "chart": "donut", "style": "corporate presentation slide", "tech": "hand-built inline SVG document (headless Chrome)",
    "mechanism": "label",
    "conflict_summary": "Slices clockwise from 12 o'clock are Nimbus 46, Orca 27, Pixa 17, Zento 10; "
                        "in conflict the callouts print the shares reversed (Nimbus 10%, Orca 17%, Pixa 27%, Zento 46%).",
    "data": {"brands": BRANDS, "visual": VISUAL, "conflict_labels": LABELS["conflict"],
             "slice_order": "clockwise from 12 o'clock", "colors": dict(zip(BRANDS, COLORS))},
    "questions": [
        {"qid": "s03_q1", "kind": "argmax", "pair": None, "nonumbers": True,
         "prompt": {"en": "answer en which brand has the largest market share?",
                    "tr": "answer tr en büyük pazar payına hangi marka sahip?"},
         "visual": brand(MAX_V), "text": brand(MAX_T)},
        {"qid": "s03_q2", "kind": "argmin", "pair": None, "nonumbers": True,
         "prompt": {"en": "answer en which brand has the smallest market share?",
                    "tr": "answer tr en küçük pazar payına hangi marka sahip?"},
         "visual": brand(MIN_V), "text": brand(MIN_T)},
        {"qid": "s03_q3a", "kind": "threshold", "pair": "s03_p1", "nonumbers": True,
         "prompt": {"en": "answer en does zento have more than a third of the market?",
                    "tr": "answer tr zento'nun pazar payı üçte birden fazla mı?"},
         "visual": yn(THIRD_V), "text": yn(THIRD_T)},
        {"qid": "s03_q3b", "kind": "threshold", "pair": "s03_p1", "nonumbers": True,
         "prompt": {"en": "answer en does zento have less than a third of the market?",
                    "tr": "answer tr zento'nun pazar payı üçte birden az mı?"},
         "visual": yn(not THIRD_V), "text": yn(not THIRD_T)},
        {"qid": "s03_q4", "kind": "read_value", "pair": None, "nonumbers": False,
         "prompt": {"en": "answer en what is orca's market share?",
                    "tr": "answer tr orca'nın pazar payı yüzde kaç?"},
         "visual": pct_answers(VIS["Orca"]), "text": pct_answers(TXT["Orca"])},
    ],
}

if __name__ == "__main__":
    for cond in CONDS:
        for lang in LANGS:
            render_html(page(cond, lang), name(SID, cond, lang))
    finish(SPEC)
