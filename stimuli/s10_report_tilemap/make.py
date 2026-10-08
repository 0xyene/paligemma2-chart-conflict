"""s10 — scanned page of a municipal air-quality report (PDF) with a 3x3 tile map and a gradient colour legend.

Nine fictional districts, one sequential purple ramp (light -> dark, interpolated in CIELAB).
Tile darkness encodes the `consistent` values (10 = lightest end, 80 = darkest end of the legend).
Conflict = the legend's labels are reversed (light = 80 "Polluted", dark = 10 "Clean"); the drawing
is untouched, so in conflict the true value of every tile is LO + HI - v (darkest tile = cleanest air).
Nonumbers = the same page with the legend labels (tick numbers and the Clean/Polluted words) rendered as empty
<text> elements; the gradient bar, its tick marks and the unit title stay, so only the usual darker = more
convention is left to read the map by.
Page = HTML/CSS with inline SVG for the map and the legend (headless Chrome).

Look (set-level review, 2026-10): s10 used to share s03's template (white page, dark header band with logo, caps
kicker, grey boxes). It is now a scanned council PDF page: cream paper, Baskerville throughout (no other stimulus uses
it), letterhead with a line-art crest and thin double rule instead of a band, thin rules, a faint paper grain and a
scanner shadow on the left edge. The grain is a fixed-seed feTurbulence overlay (deterministic, identical in all 6
images) and the edge shadow stops 24 px from the edge, well clear of the map, so it can't change the tiles' darkness
order. Legend labels (the cue) are 32 px Baskerville SemiBold: ~21 px cap height, up from ~18 px glyphs.

Questions: q3a/q3b ask about Dunmore (lightest tile) vs Glenrock (darkest), so the visual answer to "more polluted?"
is "no" and a model that leans on "yes" can't score on q3a from the visual side. Yes/no use the shared YES/NO lists
(common/answers.py); no verb-echo extras ("daha kirli") because they also occur inside negative answers.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
from answers import NO, YES  # noqa: E402
from lib import CONDS, LANGS, finish, fmt_num, name, render_html  # noqa: E402

SID = "s10_report_tilemap"
DISTRICTS = ["Asterly", "Brookfield", "Cedarline",
             "Dunmore", "Elmwood", "Fairhaven",
             "Glenrock", "Harborview", "Ivydale"]           # reading order on the 3x3 grid; identical in en and tr
VISUAL = [72, 38, 48, 15, 63, 33, 80, 55, 30]                # tile darkness on the consistent legend scale;
# Ivydale/Brookfield raised from 20/25 so the lightest tile (Dunmore, the q2 answer) stands out at 448 (ΔL* ≈ 16, was ≈ 5)
LO, HI = 10, 80                                              # legend ends: light end, dark end (consistent)
TICKS = list(range(LO, HI + 1, 10))                          # tick positions (consistent value space), light -> dark
FLIP = {"consistent": lambda v: v, "conflict": lambda v: LO + HI - v}
TRUTH = {c: [FLIP[c](v) for v in VISUAL] for c in FLIP}      # what the legend says each tile is worth
# (nonumbers has no labels, so no legend-implied values; its labels are drawn like consistent's, with empty text)

# ---------- colour ramp: one purple hue, light -> dark, linear in CIELAB ----------
LAB_LIGHT, LAB_DARK = (96.0, 2.5, -4.5), (21.0, 30.0, -44.0)


def _lab_to_hex(L, a, b):
    fy = (L + 16) / 116
    fx, fz = fy + a / 500, fy - b / 200
    d = 6 / 29
    finv = lambda f: f ** 3 if f > d else 3 * d * d * (f - 4 / 29)  # noqa: E731
    xyz = np.array([0.95047 * finv(fx), finv(fy), 1.08883 * finv(fz)])
    m = np.array([[3.2406, -1.5372, -0.4986], [-0.9689, 1.8758, 0.0415], [0.0557, -0.2040, 1.0570]])
    lin = np.clip(m @ xyz, 0, 1)
    srgb = np.where(lin <= 0.0031308, 12.92 * lin, 1.055 * lin ** (1 / 2.4) - 0.055)
    r, g, bl = (np.clip(srgb, 0, 1) * 255).round().astype(int)
    return f"#{r:02x}{g:02x}{bl:02x}"


def ramp(t):
    t = min(max(t, 0.0), 1.0)
    return _lab_to_hex(*[lo + (hi - lo) * t for lo, hi in zip(LAB_LIGHT, LAB_DARK)])


def tile_color(v):
    return ramp((v - LO) / (HI - LO))


COLORS = [tile_color(v) for v in VISUAL]

# ---------- text ----------
T = {
    "en": dict(
        council="Calderford City Council", dept="Environment Department",
        report="Air Quality Report 2025", section="Section 3",
        title="3.2&ensp;Air quality by district",
        body="The map shows Calderford's nine districts as tiles of equal size, each placed roughly where the "
             "district lies. A tile's shade gives the 2025 annual mean of fine particles (PM2.5) measured "
             "at the three roadside stations in that district.",
        north="N",
        fig="Figure 3.2&ensp;Fine particles (PM2.5) by district, annual mean 2025",
        key_title="PM2.5 (µg/m³)",
        light_word="Clean", dark_word="Polluted",
        notes_h="About the data",
        notes=["27 stations, 3 per district", "January–December 2025", "Daily filter samples"],
        source="Source: Calderford Environment Department",
        foot_l="Calderford Air Quality Report 2025", foot_r="14",
    ),
    "tr": dict(
        council="Calderford Belediyesi", dept="Çevre Müdürlüğü",
        report="Hava Kalitesi Raporu 2025", section="Bölüm 3",
        title="3.2&ensp;İlçelere göre hava kalitesi",
        body="Harita, Calderford'un dokuz ilçesini eşit büyüklükte karolar hâlinde, her ilçeyi kabaca "
             "bulunduğu yere koyarak gösteriyor. Her karonun tonu, o ilçedeki üç yol kenarı istasyonunda "
             "ölçülen ince partiküllerin (PM2,5) 2025 yıllık ortalamasını veriyor.",
        north="K",
        fig="Şekil 3.2&ensp;İlçelere göre ince partikül (PM2,5), 2025 yıllık ortalaması",
        key_title="PM2,5 (µg/m³)",
        light_word="Temiz", dark_word="Kirli",
        notes_h="Veri hakkında",
        notes=["27 istasyon, ilçe başına 3", "Ocak–Aralık 2025", "Günlük filtre örnekleri"],
        source="Kaynak: Calderford Belediyesi Çevre Müdürlüğü",
        foot_l="Calderford Hava Kalitesi Raporu 2025", foot_r="14",
    ),
}

# ---------- geometry ----------
TILE, GAP, STRIP = 152, 10, 40                               # tile edge, gap, name-strip height
MAP_W = 3 * TILE + 2 * GAP                                   # 476
SERIF = 'Baskerville, "Baskerville Old Face", "Libre Baskerville", Georgia, serif'
INK, INK2, RULE, PAPER = "#26231f", "#45403a", "#5c564d", "#f3eddd"
LEFT, MAP_TOP = 40, 300                                      # page margin, top of the map


def map_svg():
    out = [f'<svg width="{MAP_W}" height="{MAP_W}" viewBox="0 0 {MAP_W} {MAP_W}" xmlns="http://www.w3.org/2000/svg">']
    for i, (d, col) in enumerate(zip(DISTRICTS, COLORS)):
        x, y = (i % 3) * (TILE + GAP), (i // 3) * (TILE + GAP)
        out.append(f'<g transform="translate({x},{y})">'
                   f'<rect x="0" y="0" width="{TILE}" height="{TILE - STRIP}" fill="{col}"/>'
                   f'<rect x="0.75" y="0.75" width="{TILE - 1.5}" height="{TILE - 1.5}" fill="none" '
                   f'stroke="{RULE}" stroke-width="1.5"/>'
                   f'<line x1="0" y1="{TILE - STRIP}" x2="{TILE}" y2="{TILE - STRIP}" stroke="{RULE}" stroke-width="1"/>'
                   f'<text x="{TILE / 2}" y="{TILE - 12}" text-anchor="middle" class="dn">{d}</text></g>')
    out.append("</svg>")
    return "\n".join(out)


KEY_W, KEY_H = 316, 312
BAR_X, BAR_W, BAR_TOP, BAR_BOT = 6, 40, 18, 298              # legend bar box inside the key svg (40 px per tick)


def key_svg(cond, lang):
    t = T[lang]
    stops = "".join(f'<stop offset="{k / 16:.4f}" stop-color="{ramp(k / 16)}"/>' for k in range(17))
    out = [f'<svg width="{KEY_W}" height="{KEY_H}" viewBox="0 0 {KEY_W} {KEY_H}" xmlns="http://www.w3.org/2000/svg">',
           f'<defs><linearGradient id="g" x1="0" y1="1" x2="0" y2="0">{stops}</linearGradient></defs>',
           f'<rect x="{BAR_X}" y="{BAR_TOP}" width="{BAR_W}" height="{BAR_BOT - BAR_TOP}" fill="url(#g)" '
           f'stroke="{RULE}" stroke-width="1.5"/>']
    words = {LO: t["light_word"], HI: t["dark_word"]}          # consistent wording at the light / dark end
    for v in TICKS:
        y = BAR_BOT - (v - LO) / (HI - LO) * (BAR_BOT - BAR_TOP)
        blank = cond == "nonumbers"                            # cue removed: same <text> elements, empty content
        lab = FLIP["consistent" if blank else cond](v)         # printed number at this position
        out.append(f'<line x1="{BAR_X + BAR_W}" y1="{y:.1f}" x2="{BAR_X + BAR_W + 10}" y2="{y:.1f}" '
                   f'stroke="{INK2}" stroke-width="2"/>')
        out.append(f'<text x="{BAR_X + BAR_W + 18}" y="{y + 11:.1f}" class="tk">{"" if blank else fmt_num(lab, lang)}</text>')
        if lab in words:
            out.append(f'<text x="{BAR_X + BAR_W + 70}" y="{y + 11:.1f}" class="kw">{"" if blank else words[lab]}</text>')
    out.append("</svg>")
    return "\n".join(out)


# line-art council crest: shield outline with a three-tower skyline, printed in ink
CREST = (f'<svg width="46" height="54" viewBox="0 0 46 54" xmlns="http://www.w3.org/2000/svg">'
         f'<path d="M3,3 H43 V27 C43,40 33,47 23,51 C13,47 3,40 3,27 Z" fill="none" stroke="{INK}" stroke-width="2"/>'
         f'<path d="M5.5,5.5 H40.5 V27 C40.5,38.5 31.5,44.5 23,48.3 C14.5,44.5 5.5,38.5 5.5,27 Z" fill="none" '
         f'stroke="{INK}" stroke-width="0.8"/>'
         f'<path d="M11,34 V22 L14.5,18.5 L18,22 V34 M18,34 V15 L23,10 L28,15 V34 M28,34 V24 L32,20 L35,24 V34 M9,35 H37" '
         f'fill="none" stroke="{INK}" stroke-width="1.8" stroke-linejoin="round"/></svg>')


def north_arrow(letter):
    return (f'<svg width="56" height="34" viewBox="0 0 56 34" xmlns="http://www.w3.org/2000/svg">'
            f'<path d="M42,3 L50,30 L42,24 Z" fill="{INK}"/>'
            f'<path d="M42,3 L34,30 L42,24 Z" fill="none" stroke="{INK}" stroke-width="1.2" stroke-linejoin="round"/>'
            f'<text x="20" y="26" text-anchor="middle" class="nl">{letter}</text></svg>')


# fixed-seed paper grain (deterministic -> identical in all 4 images), drawn over the whole page at low alpha
GRAIN = ('<svg class="grain" width="896" height="896" xmlns="http://www.w3.org/2000/svg">'
         '<filter id="paper" x="0" y="0" width="100%" height="100%">'
         '<feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="2" seed="11" stitchTiles="stitch"/>'
         '<feColorMatrix type="matrix" values="0 0 0 0 0.30  0 0 0 0 0.25  0 0 0 0 0.16  0.13 0 0 0 0"/>'
         '</filter><rect width="896" height="896" filter="url(#paper)"/></svg>')


def page(cond, lang):
    t = T[lang]
    notes = "".join(f"<li>{n}</li>" for n in t["notes"])
    side_l = LEFT + MAP_W + 30
    return f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{ width: 896px; height: 896px; overflow: hidden; }}
  body {{ position: relative; background: {PAPER}; color: {INK}; font-family: {SERIF}; }}
  .head {{ position: absolute; left: {LEFT}px; right: {LEFT}px; top: 20px; height: 56px; display: flex; align-items: center; }}
  .org {{ margin-left: 14px; line-height: 1.12; }}
  .o1 {{ font-size: 25px; font-weight: 600; letter-spacing: .2px; }}
  .o2 {{ font-size: 20px; font-style: italic; color: {INK2}; }}
  .ref {{ margin-left: auto; text-align: right; font-size: 20px; line-height: 1.2; color: {INK2}; }}
  .rule2 {{ position: absolute; left: {LEFT}px; right: {LEFT}px; top: 86px; height: 6px;
            border-top: 2px solid {INK}; border-bottom: 1px solid {INK}; }}
  h1 {{ position: absolute; left: {LEFT}px; top: 104px; font-size: 36px; font-weight: 600; letter-spacing: -.1px; }}
  .body {{ position: absolute; left: {LEFT}px; right: {LEFT}px; top: 154px; font-size: 21.5px; line-height: 1.36;
           text-align: justify; hyphens: none; }}
  .fig {{ position: absolute; left: {LEFT}px; right: {LEFT}px; top: {MAP_TOP - 50}px; border-top: 1px solid {RULE};
          padding-top: 9px; font-size: 21px; font-weight: 600; }}
  .na {{ position: absolute; right: 0; top: 6px; }}
  .map {{ position: absolute; left: {LEFT}px; top: {MAP_TOP}px; }}
  .side {{ position: absolute; left: {side_l}px; right: {LEFT - 10}px; top: {MAP_TOP}px; height: {MAP_W}px; }}
  .kt {{ font-size: 22px; font-weight: 600; line-height: 1.1; }}
  .key svg {{ display: block; margin-top: 4px; }}
  .tk {{ font-family: {SERIF}; font-size: 32px; font-weight: 600; fill: {INK}; }}
  .kw {{ font-family: {SERIF}; font-size: 32px; font-weight: 600; fill: {INK}; }}
  .nl {{ font-family: {SERIF}; font-size: 24px; font-weight: 600; fill: {INK}; }}
  .dn {{ font-family: {SERIF}; font-size: 24px; font-weight: 600; fill: {INK}; }}
  .notes {{ position: absolute; left: 0; right: 0; bottom: 0; border-top: 1px solid {RULE}; padding-top: 7px; }}
  .notes h2 {{ font-size: 20px; font-weight: 600; font-style: italic; }}
  .notes ul {{ list-style: none; font-size: 20px; line-height: 1.28; color: {INK2}; }}
  .src {{ position: absolute; left: {LEFT}px; right: {LEFT}px; top: {MAP_TOP + MAP_W + 10}px;
          font-size: 20px; font-style: italic; color: {INK2}; }}
  .foot {{ position: absolute; left: {LEFT}px; right: {LEFT}px; bottom: 20px; border-top: 1px solid {RULE};
           padding-top: 6px; font-size: 20px; color: {INK2}; display: flex; justify-content: space-between; }}
  .foot .l {{ font-style: italic; }}
  .grain {{ position: absolute; left: 0; top: 0; pointer-events: none; }}
  .edge {{ position: absolute; inset: 0; pointer-events: none;
           background: linear-gradient(to right, rgba(70,58,38,.20) 0, rgba(70,58,38,.07) 9px, rgba(70,58,38,0) 24px),
                       linear-gradient(to bottom, rgba(70,58,38,.07) 0, rgba(70,58,38,0) 14px); }}
</style></head><body>
  <div class="head">{CREST}<div class="org"><div class="o1">{t["council"]}</div><div class="o2">{t["dept"]}</div></div>
    <div class="ref"><div>{t["report"]}</div><div>{t["section"]}</div></div></div>
  <div class="rule2"></div>
  <h1>{t["title"]}</h1>
  <div class="body">{t["body"]}</div>
  <div class="fig">{t["fig"]}<span class="na">{north_arrow(t["north"])}</span></div>
  <div class="map">{map_svg()}</div>
  <div class="side">
    <div class="key"><div class="kt">{t["key_title"]}</div>{key_svg(cond, lang)}</div>
    <div class="notes"><h2>{t["notes_h"]}</h2><ul>{notes}</ul></div>
  </div>
  <div class="src">{t["source"]}</div>
  <div class="foot"><span class="l">{t["foot_l"]}</span><span>{t["foot_r"]}</span></div>
  {GRAIN}
  <div class="edge"></div>
</body></html>"""


# ---------- questions (answers computed from the arrays above) ----------
def worst(vals):
    return DISTRICTS[int(np.argmax(vals))]


def cleanest(vals):
    return DISTRICTS[int(np.argmin(vals))]


V, C = TRUTH["consistent"], TRUTH["conflict"]
D, G = DISTRICTS.index("Dunmore"), DISTRICTS.index("Glenrock")
assert worst(V) != worst(C) and cleanest(V) != cleanest(C)
assert worst(V) == "Glenrock" and cleanest(V) == "Dunmore"     # darkest / lightest tile, as DESIGN.md states
# q3 pair subject = Dunmore: visual (lightest tile) says "not more polluted than Glenrock"; reversed legend says it is
assert not V[D] > V[G] and C[D] > C[G]                         # q3a: visual no, text yes
assert V[D] < V[G] and not C[D] < C[G]                         # q3b: visual yes, text no

VARIANTS = {"Glenrock": ["glen rock"], "Dunmore": ["dun more"]}


def yn(flag):
    return YES if flag else NO


def district(dname):
    acc = [dname.lower()] + VARIANTS.get(dname, [])            # proper names: identical in en and tr
    return {"en": acc, "tr": acc}


SPEC = {
    "id": SID,
    "title": {"en": "Air quality by district (scanned municipal report, tile map)",
              "tr": "İlçelere göre hava kalitesi (taranmış belediye raporu, karo harita)"},
    "chart": "3x3 tile map with gradient colour legend", "style": "scanned municipal report page (PDF)",
    "tech": "HTML/CSS page + inline SVG tile map, gradient legend and fixed-seed paper grain (headless Chrome)",
    "mechanism": "legend",
    "conflict_summary": "Tiles are shaded in one purple ramp, Glenrock darkest and Dunmore lightest. Consistent legend: "
                        "light end = 10 Clean, dark end = 80 Polluted. In conflict only the legend labels are reversed "
                        "(light = 80 Polluted, dark = 10 Clean), so every tile's true value becomes 90 - v and the "
                        "darkest tile (Glenrock) has the cleanest air.",
    "data": {"districts": DISTRICTS, "grid": "3x3, reading order", "visual": VISUAL,
             "conflict_truth": TRUTH["conflict"], "legend_ends": {"light": LO, "dark": HI},
             "legend_ticks_light_to_dark": {**{c: [FLIP[c](v) for v in TICKS] for c in FLIP}, "nonumbers": []},
             "legend_words_light_to_dark": {"consistent": {"en": ["Clean", "Polluted"], "tr": ["Temiz", "Kirli"]},
                                            "conflict": {"en": ["Polluted", "Clean"], "tr": ["Kirli", "Temiz"]},
                                            "nonumbers": {"en": [], "tr": []}},
             "nonumbers": "legend tick numbers and end words blank; gradient bar, tick marks and unit title kept",
             "tile_colors": dict(zip(DISTRICTS, COLORS)), "unit": "µg/m³ PM2.5, annual mean (fictional)"},
    "questions": [
        {"qid": "s10_q1", "kind": "argmax", "pair": None,
         "prompt": {"en": "answer en which district has the most polluted air?",
                    "tr": "answer tr havası en kirli olan ilçe hangisi?"},
         "visual": district(worst(V)), "text": district(worst(C)),
         "nonumbers": True},           # darkest tile, darker = more
        {"qid": "s10_q2", "kind": "argmin", "pair": None,
         "prompt": {"en": "answer en which district has the cleanest air?",
                    "tr": "answer tr havası en temiz olan ilçe hangisi?"},
         "visual": district(cleanest(V)), "text": district(cleanest(C)),
         "nonumbers": True},           # lightest tile
        {"qid": "s10_q3a", "kind": "compare", "pair": "s10_p1",
         "prompt": {"en": "answer en is the air in dunmore more polluted than in glenrock?",
                    "tr": "answer tr dunmore'da hava glenrock'takinden daha mı kirli?"},
         "visual": yn(V[D] > V[G]), "text": yn(C[D] > C[G]),
         "nonumbers": True},           # lightest vs darkest tile
        {"qid": "s10_q3b", "kind": "compare", "pair": "s10_p1",
         "prompt": {"en": "answer en is the air in dunmore cleaner than in glenrock?",
                    "tr": "answer tr dunmore'da hava glenrock'takinden daha mı temiz?"},
         "visual": yn(V[D] < V[G]), "text": yn(C[D] < C[G]),
         "nonumbers": True},           # same pair, same flag
    ],
}

if __name__ == "__main__":
    for cond in CONDS:
        for lang in LANGS:
            render_html(page(cond, lang), name(SID, cond, lang))
    finish(SPEC)
