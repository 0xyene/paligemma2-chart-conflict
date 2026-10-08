"""s05 — school poster with an isotype pictogram (1 tree icon = 10 trees). Rows NOT sorted.
Icon counts encode Aster 50, Lumen 80, Mira 30, Nova 20; in conflict the printed row totals are permuted
(Aster 20, Lumen 30, Mira 80, Nova 50). Rows are drawn top→bottom Aster, Mira, Nova, Lumen (see SCHOOLS).
nonumbers: the printed row totals are blanked (the badge circles stay, empty); the key "1 icon = 10 trees" is kept,
it is the same in every version, so every question (q2 included: icons x key) stays answerable from the drawing.
Deviations from DESIGN.md: the q3 pair asks about Mira vs Lumen (DESIGN.md: Lumen vs Mira), so the subject is the school
with FEWER icons and the visual answer to "more?" is no; the header band reads "Willowmere District Schools" (not
"Riverside", which s01's newspaper already uses)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
from answers import NO, YES, num_accept  # noqa: E402
from lib import CONDS, LANGS, finish, fmt_num, name, render_html  # noqa: E402

SID = "s05_poster_pictogram"
PER_ICON = 10                                            # key: 1 icon = 10 trees
ICONS_BY = {"Aster": 5, "Lumen": 8, "Mira": 3, "Nova": 2}         # DESIGN.md: tree icons per school
CONFLICT_BY = {"Aster": 20, "Lumen": 30, "Mira": 80, "Nova": 50}  # DESIGN.md: printed totals in `conflict`
# chosen so the text argmax/argmin (Mira/Aster) are NOT the visual argmin/argmax (Nova/Lumen):
# a model that mixes up "most" and "fewest" can't pass for a text-follower.
# Drawing order (top→bottom). The row order must not act as a third cue (asserts below):
#  - row-binding slip: a printed total read off the neighbouring row must not land on the visual answer. Mira ('80' =
#    text max) sits two rows from Lumen (most icons), Aster ('20' = text min) two rows from Nova (fewest icons).
#  - positional fallback: a model that doesn't compare and reads the answer off the layout must not land on the VISUAL
#    answer. That answer is also right on the consistent twin, so it survives the notebook's ctrl_ok filter and would
#    pass for visual-following (a fallback that lands on the TEXT answer is wrong on the twin and gets filtered out).
#    Only 4 orders pass the other rules; this is the one where the two likeliest fallbacks miss the visual answer:
#    ranked list (top row = most, bottom row = fewest, higher row = more) and "name the first school listed".
#    Residual, unavoidable: "always name the LAST school" gives Lumen = q1 visual.
#  The old order Mira, Aster, Lumen, Nova put the text max on top and the visual min at the bottom (ranked list → q1 text,
#  q4 visual); the order Nova, Lumen, Aster, Mira would put the visual min on top and Lumen above Mira (q4 / q3 visual).
SCHOOLS = ["Aster", "Mira", "Nova", "Lumen"]
ICONS = [ICONS_BY[s] for s in SCHOOLS]                   # 5, 3, 2, 8  (not sorted)
VISUAL = [n * PER_ICON for n in ICONS]                   # 50, 30, 20, 80 = printed totals in `consistent`
CONFLICT = [CONFLICT_BY[s] for s in SCHOOLS]             # 20, 80, 50, 30 = printed totals in `conflict` (not sorted)
TOTALS = {"consistent": VISUAL, "conflict": CONFLICT, "nonumbers": [None] * len(SCHOOLS)}   # None = empty badge
MAX_ICONS = 8
assert sorted(CONFLICT) == sorted(VISUAL) and all(a != b for a, b in zip(VISUAL, CONFLICT))
for seq in (ICONS, CONFLICT):
    assert seq != sorted(seq) and seq != sorted(seq, reverse=True), f"rows must not be sorted: {seq}"

T = {
    "en": dict(
        band_l="Willowmere District Schools", band_r="Spring Planting Week",
        title="Trees planted by each school this spring",
        key_h="KEY", key_txt=f"= {PER_ICON} trees",
        col_school="School", col_trees="Trees planted", col_total="Total",
        kind="Primary School",
        foot="Every sapling came from the town nursery and was counted by the pupils on planting day.",
        credit=("Made by", "Science Club")),
    "tr": dict(
        band_l="Willowmere İlçesi Okulları", band_r="Bahar Dikim Haftası",
        title="Bu bahar her okulun diktiği ağaçlar",
        key_h="AÇIKLAMA", key_txt=f"= {PER_ICON} ağaç",
        col_school="Okul", col_trees="Dikilen ağaçlar", col_total="Toplam",
        kind="İlkokulu",
        foot="Bütün fidanlar ilçe fidanlığından geldi; dikim günü öğrenciler onları tek tek saydı.",
        credit=("Hazırlayan", "Fen Kulübü")),
}

# one flat isotype tree, reused by <use>; same colour in every row (no per-row semantics)
TREE_SYMBOL = """
<svg width="0" height="0" style="position:absolute">
  <defs>
    <symbol id="tree" viewBox="0 0 60 74">
      <rect x="26" y="44" width="8" height="28" rx="2" fill="#6e5236"/>
      <path d="M30 4 C44 4 52 14 51 25 C57 29 58 41 50 47 C45 52 37 52 33 49 L27 49 C23 52 15 52 10 47
               C2 41 3 29 9 25 C8 14 16 4 30 4 Z" fill="#3b7550"/>
      <path d="M30 22 L30 46 M30 32 L37 26 M30 38 L23 32" stroke="#2c5a3d" stroke-width="2.4"
            stroke-linecap="round" fill="none"/>
    </symbol>
    <symbol id="leaf" viewBox="0 0 40 24">
      <path d="M2 12 C10 1 28 0 38 12 C28 24 10 23 2 12 Z" fill="#9bbf8a"/>
      <path d="M4 12 L34 12" stroke="#7aa36a" stroke-width="1.6"/>
    </symbol>
  </defs>
</svg>"""

ICON_W, ICON_H, ICON_GAP = 52, 64, 9


def icon_row(n):
    w = MAX_ICONS * ICON_W + (MAX_ICONS - 1) * ICON_GAP
    out = [f'<svg width="{w}" height="{ICON_H + 10}" viewBox="0 0 {w} {ICON_H + 10}">']
    out.append(f'<rect x="0" y="{ICON_H + 2}" width="{w}" height="6" rx="3" fill="#d9ccb0"/>')   # ground strip (constant)
    for i in range(n):
        out.append(f'<use href="#tree" x="{i * (ICON_W + ICON_GAP)}" y="0" width="{ICON_W}" height="{ICON_H + 4}"/>')
    out.append("</svg>")
    return "".join(out)


def page(cond, lang):
    t = T[lang]
    rows = []
    for s, n, tot in zip(SCHOOLS, ICONS, TOTALS[cond]):
        rows.append(f"""
      <div class="row">
        <div class="nm"><div class="sn">{s}</div><div class="sk">{t["kind"]}</div></div>
        <div class="ic">{icon_row(n)}</div>
        <div class="tt"><div class="badge">{"" if tot is None else fmt_num(tot, lang)}</div></div>
      </div>""")
    return f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{ width: 896px; height: 896px; overflow: hidden; }}
  body {{ position: relative; background: #b3864f; font-family: "Avenir Next", "Helvetica Neue", sans-serif; color: #26313d; }}
  .cork {{ position: absolute; inset: 0; }}
  .poster {{ position: absolute; left: 30px; top: 28px; width: 836px; height: 842px; background: #fcf8ee;
             box-shadow: 0 6px 14px rgba(40, 22, 5, .45), 0 1px 2px rgba(40, 22, 5, .4); overflow: hidden; }}
  .paper {{ position: absolute; inset: 0; opacity: .55; mix-blend-mode: multiply; pointer-events: none; }}
  .tape {{ position: absolute; width: 132px; height: 38px; background: rgba(236, 226, 196, .82);
           box-shadow: 0 1px 2px rgba(0,0,0,.15); z-index: 5;
           clip-path: polygon(0 8%, 4% 0, 9% 10%, 14% 0, 100% 0, 97% 50%, 100% 100%, 6% 100%, 0 92%, 3% 50%); }}
  .band {{ height: 58px; background: #2f566f; color: #f6f1e4; display: flex; align-items: center;
           justify-content: space-between; padding: 0 76px; font-size: 22px; font-weight: 600; letter-spacing: .4px; }}
  .band .r {{ font-weight: 500; opacity: .92; }}
  .inner {{ padding: 0 30px; position: relative; }}
  .head {{ display: flex; justify-content: space-between; align-items: center; margin-top: 22px; height: 118px; }}
  h1 {{ font-family: "Chalkboard SE", "Marker Felt", sans-serif; font-weight: 700; font-size: 44px; line-height: 1.16;
        width: 520px; color: #24303c; }}
  .key {{ width: 236px; height: 104px; border: 3px dashed #7d8b96; border-radius: 16px; padding: 8px 14px 6px;
          background: #ffffff; }}
  .key .kh {{ font-size: 20px; font-weight: 700; letter-spacing: 2px; color: #5c6a75; }}
  .key .kb {{ display: flex; align-items: center; gap: 10px; margin-top: 2px; }}
  .key .kt {{ font-size: 28px; font-weight: 700; white-space: nowrap; }}
  .cols {{ display: flex; margin-top: 18px; padding-bottom: 6px; border-bottom: 3px solid #2f566f;
           font-size: 20px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; color: #5c6a75; }}
  .cols .a {{ width: 178px; }} .cols .b {{ flex: 1; padding-left: 4px; }} .cols .c {{ width: 104px; text-align: center; }}
  .row {{ display: flex; align-items: center; height: 116px; border-bottom: 2px dotted #b9b2a2; }}
  .nm {{ width: 178px; }}
  .sn {{ font-family: "Chalkboard SE", sans-serif; font-weight: 700; font-size: 34px; line-height: 1.05; }}
  .sk {{ font-size: 20px; font-weight: 500; color: #4a5763; margin-top: 2px; }}
  .ic {{ flex: 1; padding-left: 4px; padding-top: 4px; }}
  .ic svg {{ display: block; }}
  .tt {{ width: 104px; display: flex; justify-content: center; }}
  .badge {{ width: 84px; height: 84px; border-radius: 50%; border: 4px solid #2f566f; background: #fff;
            display: flex; align-items: center; justify-content: center; font-size: 36px; font-weight: 700;
            color: #1f2a35; }}
  .foot {{ display: flex; justify-content: space-between; align-items: flex-end; margin-top: 18px; gap: 24px; }}
  .foot p {{ font-size: 21px; line-height: 1.36; width: 520px; color: #3a4652; }}
  .sticker {{ display: flex; align-items: center; gap: 10px; padding: 8px 16px 8px 12px; margin: 0 6px 4px 0;
              background: #edf2e3; border: 2px dashed #8fb07f; border-radius: 14px; transform: rotate(-3deg);
              font-family: "Chalkboard SE", sans-serif; color: #33414d; }}
  .sticker .s1 {{ font-size: 20px; line-height: 1.1; }}
  .sticker .s2 {{ font-size: 23px; font-weight: 700; line-height: 1.15; white-space: nowrap; }}
</style></head><body>
{TREE_SYMBOL}
<svg class="cork" width="896" height="896" viewBox="0 0 896 896">
  <filter id="corkf" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.75" numOctaves="3" seed="7" result="n"/>
    <feColorMatrix in="n" type="matrix"
      values="0 0 0 0 0.30  0 0 0 0 0.18  0 0 0 0 0.07  1.6 0 0 0 -0.62"/>
  </filter>
  <filter id="corkl" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.5" numOctaves="2" seed="21" result="n"/>
    <feColorMatrix in="n" type="matrix"
      values="0 0 0 0 0.86  0 0 0 0 0.68  0 0 0 0 0.45  0 1.5 0 0 -0.78"/>
  </filter>
  <rect width="896" height="896" fill="#b3864f"/>
  <rect width="896" height="896" filter="url(#corkl)"/>
  <rect width="896" height="896" filter="url(#corkf)"/>
</svg>
<div class="tape" style="left: -6px; top: 18px; transform: rotate(-32deg);"></div>
<div class="tape" style="right: -6px; top: 18px; transform: rotate(32deg);"></div>
<div class="tape" style="left: -8px; bottom: 22px; transform: rotate(28deg);"></div>
<div class="tape" style="right: -8px; bottom: 22px; transform: rotate(-28deg);"></div>
<div class="poster">
  <svg class="paper" width="836" height="842"><filter id="pf"><feTurbulence type="fractalNoise" baseFrequency="1.6"
    numOctaves="2" seed="4"/><feColorMatrix type="matrix" values="0 0 0 0 0.55  0 0 0 0 0.5  0 0 0 0 0.4  0 0 0 0.9 -0.32"/>
    </filter><rect width="836" height="842" filter="url(#pf)"/></svg>
  <div class="band"><span>{t["band_l"]}</span><span class="r">{t["band_r"]}</span></div>
  <div class="inner">
    <div class="head">
      <h1>{t["title"]}</h1>
      <div class="key">
        <div class="kh">{t["key_h"]}</div>
        <div class="kb"><svg width="48" height="60"><use href="#tree" width="48" height="60"/></svg>
          <span class="kt">{t["key_txt"]}</span></div>
      </div>
    </div>
    <div class="cols"><span class="a">{t["col_school"]}</span><span class="b">{t["col_trees"]}</span>
      <span class="c">{t["col_total"]}</span></div>
    {"".join(rows)}
    <div class="foot">
      <p>{t["foot"]}</p>
      <div class="sticker"><svg width="44" height="27"><use href="#leaf" width="44" height="27"/></svg>
        <div><div class="s1">{t["credit"][0]}</div><div class="s2">{t["credit"][1]}</div></div></div>
    </div>
  </div>
</div>
</body></html>"""


def school_list(school):
    return {"en": [school.lower()], "tr": [school.lower()]}


def argmax(vals):
    return SCHOOLS[max(range(len(vals)), key=vals.__getitem__)]


def argmin(vals):
    return SCHOOLS[min(range(len(vals)), key=vals.__getitem__)]


# Yes/no = the shared YES/NO, plus the Turkish echo answer to "...dikti mi?": "Dikti." = yes, "Dikmedi." = no.
# The verbs are whole-answer only ("^"): inside a longer answer they flip meaning ("hayır, daha az dikti" is a no).
Y = {"en": YES["en"], "tr": YES["tr"] + ["^dikti"]}
N = {"en": NO["en"], "tr": NO["tr"] + ["^dikmedi"]}


def number_list(v):
    return {lang: num_accept(v, lang) for lang in LANGS}


A, L, M = SCHOOLS.index("Aster"), SCHOOLS.index("Lumen"), SCHOOLS.index("Mira")
# q3 pair subject = Mira (fewest icons of the two): visual "did Mira plant more than Lumen?" = no, text = yes
mira_more_vis, mira_more_txt = VISUAL[M] > VISUAL[L], CONFLICT[M] > CONFLICT[L]
assert (mira_more_vis, mira_more_txt) == (False, True), (VISUAL[M], VISUAL[L], CONFLICT[M], CONFLICT[L])
assert argmax(VISUAL) != argmax(CONFLICT) and argmin(VISUAL) != argmin(CONFLICT) and VISUAL[A] != CONFLICT[A]
# no row-binding slip onto the visual answer: the row that prints the text answer is never next to the visual answer's row
row = SCHOOLS.index
assert abs(row(argmax(CONFLICT)) - row(argmax(VISUAL))) > 1, "text max printed next to the most-icons row"
assert abs(row(argmin(CONFLICT)) - row(argmin(VISUAL))) > 1, "text min printed next to the fewest-icons row"
assert abs(CONFLICT.index(VISUAL[A]) - A) > 1, "Aster's visual value printed on a neighbouring row in conflict"
# positional fallbacks (see the SCHOOLS comment)
assert SCHOOLS[0] not in {argmax(VISUAL), argmax(CONFLICT)} and SCHOOLS[-1] not in {argmin(VISUAL), argmin(CONFLICT)}, \
    "ranked-list fallback (top row = most, bottom row = fewest) lands on a scored q1/q4 answer"
assert (row("Mira") < row("Lumen")) != mira_more_vis, "'higher row = more' fallback on q3 lands on the visual answer"
assert SCHOOLS[0] != argmin(VISUAL), "'first school listed' fallback on q4 lands on the visual answer"

_src = CONFLICT.index(VISUAL[A])
READ_NOTE = (f"q2 is not geometry-only: the visual answer {VISUAL[A]} = {ICONS[A]} icons x the printed key "
             f"'= {PER_ICON} trees', and the key is text too. Report q2 apart from the geometry-only questions, as "
             f"'icon count x key vs printed total', with the bare '{ICONS[A]}' answers (data.q2_icon_count) listed "
             f"separately. In conflict, {VISUAL[A]} is also printed on {SCHOOLS[_src]}'s row, {abs(_src - A)} rows "
             f"{'below' if _src > A else 'above'} {SCHOOLS[A]}, so a 'visual' hit may also be a misread row.")
SUMMARY = ("Icon rows (top to bottom) show " + ", ".join(f"{s} {n}" for s, n in zip(SCHOOLS, ICONS))
           + f" trees (x{PER_ICON}); in conflict the printed row totals read "
           + ", ".join(f"{s} {v}" for s, v in zip(SCHOOLS, CONFLICT)) + ".")

SPEC = {
    "id": SID,
    "title": {"en": "Trees planted by each school (school poster)", "tr": "Okulların diktiği ağaçlar (okul afişi)"},
    "chart": "pictogram (isotype)", "style": "school poster pinned to a cork board",
    "tech": "HTML/CSS + inline SVG icons (<symbol>/<use>) + SVG feTurbulence textures (headless Chrome)",
    "mechanism": "label",
    "conflict_summary": SUMMARY,
    "data": {"schools": SCHOOLS, "icons": ICONS, "per_icon": PER_ICON,
             "visual": VISUAL, "conflict_labels": CONFLICT,
             # for the analysis only (not scored): q2 answered with the raw icon count = followed the drawing, ignored the key
             "q2_icon_count": number_list(ICONS[A]),
             "read_value_note": READ_NOTE},
    "questions": [
        {"qid": "s05_q1", "kind": "argmax", "pair": None,
         "nonumbers": True,   # longest icon row
         "prompt": {"en": "answer en which school planted the most trees?",
                    "tr": "answer tr en çok ağacı hangi okul dikti?"},
         "visual": school_list(argmax(VISUAL)), "text": school_list(argmax(CONFLICT))},
        {"qid": "s05_q2", "kind": "read_value", "pair": None,
         "nonumbers": True,   # 5 icons x the key "= 10 trees" (the key is kept in every version, only totals are blanked)
         "prompt": {"en": "answer en how many trees did aster school plant?",
                    "tr": "answer tr aster okulu kaç ağaç dikti?"},
         # bare "5" (icons counted, key ignored) is deliberately NOT accepted: it would score as correct on consistent
         # images. It stays 'neither' here; data.q2_icon_count lets the analysis tag it separately.
         "visual": number_list(VISUAL[A]), "text": number_list(CONFLICT[A])},
        {"qid": "s05_q3a", "kind": "compare", "pair": "s05_p1",
         "nonumbers": True,   # Mira 3 icons vs Lumen 8
         "prompt": {"en": "answer en did mira school plant more trees than lumen school?",
                    "tr": "answer tr mira okulu, lumen okulundan daha fazla ağaç dikti mi?"},
         "visual": Y if mira_more_vis else N, "text": Y if mira_more_txt else N},
        {"qid": "s05_q3b", "kind": "compare", "pair": "s05_p1",
         "nonumbers": True,   # same pair, same flag
         "prompt": {"en": "answer en did mira school plant fewer trees than lumen school?",
                    "tr": "answer tr mira okulu, lumen okulundan daha az ağaç dikti mi?"},
         "visual": N if mira_more_vis else Y, "text": N if mira_more_txt else Y},
        {"qid": "s05_q4", "kind": "argmin", "pair": None,
         "nonumbers": True,   # shortest icon row
         "prompt": {"en": "answer en which school planted the fewest trees?",
                    "tr": "answer tr en az ağacı hangi okul dikti?"},
         "visual": school_list(argmin(VISUAL)), "text": school_list(argmin(CONFLICT))},
    ],
}

if __name__ == "__main__":
    for cond in CONDS:
        for lang in LANGS:
            render_html(page(cond, lang), name(SID, cond, lang))
    finish(SPEC)
