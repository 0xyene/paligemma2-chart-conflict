"""s14 — generic spreadsheet window, in-cell data bars (HTML table + CSS). Five regions, unsorted;
conflict permutes the printed revenues so the longest bar (East) reads 180 and the shortest (South) reads 330.
The total row is identical in both versions (the printed values are a permutation).
Data bars are orange (non-semantic, same in all six images). The yes/no pair asks about West vs North (the region
whose printed value goes UP in conflict is the subject): bars West 260 < North 420, conflict text West 420 > North 260.
`nonumbers`: same drawing with the five region revenue strings blanked (the .val span is kept, empty); data bars,
region names and the total row stay. Only q4 (read East) needs the removed text -> nonumbers false.
Answers use the shared lists in common/answers.py (YES/NO, num_accept)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
from answers import NO, YES, num_accept  # noqa: E402
from lib import CONDS, LANGS, finish, fmt_num, name, render_html  # noqa: E402

SID = "s14_spreadsheet_databars"
KEYS = ["north", "south", "east", "west", "central"]                 # drawing order, rows 4..8
VISUAL = [420, 180, 610, 260, 330]                                    # bar lengths = printed values in `consistent`
CONFLICT = [260, 330, 180, 420, 610]                                  # DESIGN.md permutation
LABELS = {"consistent": VISUAL, "conflict": CONFLICT, "nonumbers": [None] * len(VISUAL)}   # None = blank cue string
TOTAL = sum(VISUAL)
assert sorted(VISUAL) == sorted(CONFLICT) and sum(CONFLICT) == TOTAL  # total row identical in both versions

T = {
    "en": dict(
        regions=["North", "South", "East", "West", "Central"],
        win="Regional revenue 2026",
        menu=["File", "Edit", "View", "Insert", "Format", "Data", "Tools", "Help"],
        func="SUM",
        title="Q3 revenue by region (thousand €)",
        sub="July–September 2026 · source: regional sales ledgers",
        h_region="Region", h_rev="Revenue (k€)",
        total="Total",
        note="Figures rounded to the nearest thousand euros.",
        tabs=["Regions", "Stores", "Notes"],
        ready="Ready",
    ),
    "tr": dict(
        regions=["Kuzey", "Güney", "Doğu", "Batı", "Merkez"],
        win="Bölge gelirleri 2026",
        menu=["Dosya", "Düzen", "Görünüm", "Ekle", "Biçim", "Veri", "Araçlar", "Yardım"],
        func="TOPLA",
        title="Bölgelere göre 3. çeyrek geliri (bin €)",
        sub="Temmuz–Eylül 2026 · kaynak: bölge satış defterleri",
        h_region="Bölge", h_rev="Gelir (bin €)",
        total="Toplam",
        note="Rakamlar en yakın bin avroya yuvarlanmıştır.",
        tabs=["Bölgeler", "Mağazalar", "Notlar"],
        ready="Hazır",
    ),
}


def fmt_total(x, lang):
    """The total (1800) is the only number >= 1000; it carries no cue and is identical in both versions.
    Spreadsheet locale grouping: EN 1,800 · TR 1.800."""
    s = f"{x:,}"
    return s.replace(",", ".") if lang == "tr" else s


# ---------- geometry (shared by all versions) ----------
COLS = [("", 46), ("A", 196), ("B", 438), ("C", 128), ("D", 72)]       # row-number column + A..D (D cut by the scrollbar)
ROW_H = {1: 58, 2: 42, 3: 50, 4: 60, 5: 60, 6: 60, 7: 60, 8: 60, 9: 56, 10: 46, 11: 46}
BAR_LEFT, BAR_MAX, NUM_RIGHT = 12, 288, 18                             # px inside column B
SEL_ROW, SEL_COL = 9, "B"                                              # selected cell = the total (formula is constant)


def bar_px(v):
    return round(BAR_MAX * v / max(VISUAL))


ICONS = {   # 24x24 line icons for the toolbar, neutral grey
    "undo": '<path d="M9 7H4V2" fill="none" stroke="#555" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
            '<path d="M4.5 7.2A8 8 0 1 1 6 17.5" fill="none" stroke="#555" stroke-width="2" stroke-linecap="round"/>',
    "redo": '<path d="M15 7h5V2" fill="none" stroke="#555" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
            '<path d="M19.5 7.2A8 8 0 1 0 18 17.5" fill="none" stroke="#555" stroke-width="2" stroke-linecap="round"/>',
    "print": '<rect x="6" y="3" width="12" height="5" fill="none" stroke="#555" stroke-width="1.8"/>'
             '<rect x="3" y="8" width="18" height="9" rx="2" fill="none" stroke="#555" stroke-width="1.8"/>'
             '<rect x="7" y="14" width="10" height="7" fill="#f6f7f9" stroke="#555" stroke-width="1.8"/>',
    "left": '<path d="M3 5h18M3 10h12M3 15h18M3 20h12" stroke="#555" stroke-width="2" stroke-linecap="round"/>',
    "center": '<path d="M3 5h18M6 10h12M3 15h18M6 20h12" stroke="#555" stroke-width="2" stroke-linecap="round"/>',
    "right": '<path d="M3 5h18M9 10h12M3 15h18M9 20h12" stroke="#555" stroke-width="2" stroke-linecap="round"/>',
    "border": '<rect x="3" y="3" width="18" height="18" fill="none" stroke="#555" stroke-width="1.8"/>'
              '<path d="M12 3v18M3 12h18" stroke="#555" stroke-width="1.2" stroke-dasharray="2 2"/>',
    "fill": '<path d="M5 12l7-7 7 7-7 7z" fill="none" stroke="#555" stroke-width="1.8" stroke-linejoin="round"/>'
            '<rect x="3" y="20" width="18" height="2.5" fill="#888"/>',
    "databar": '<rect x="2" y="3" width="20" height="18" fill="none" stroke="#555" stroke-width="1.6"/>'
               '<rect x="4.5" y="6" width="13" height="3.2" fill="#e8a25a"/><rect x="4.5" y="10.5" width="8" height="3.2" fill="#e8a25a"/>'
               '<rect x="4.5" y="15" width="15" height="3.2" fill="#e8a25a"/>',
    "filter": '<path d="M3 4h18l-7 8v7l-4 2v-9z" fill="none" stroke="#555" stroke-width="1.8" stroke-linejoin="round"/>',
}


def icon(k, active=False):
    cls = "tb on" if active else "tb"
    return f'<span class="{cls}"><svg width="24" height="24" viewBox="0 0 24 24">{ICONS[k]}</svg></span>'


CARET = '<svg width="10" height="6" viewBox="0 0 10 6"><path d="M0 0h10L5 6z" fill="#777"/></svg>'   # dropdown arrow drawn as a shape (no sub-20px text)


def toolbar(lang):
    sep = '<span class="sep"></span>'
    return (f'<div class="toolbar">{icon("undo")}{icon("redo")}{icon("print")}{sep}'
            f'<span class="box font">Arial{CARET}</span><span class="box size">11{CARET}</span>{sep}'
            f'<span class="tb txt"><b>B</b></span><span class="tb txt"><i class="it">I</i></span>'
            f'<span class="tb txt"><u>U</u></span>{sep}'
            f'{icon("left")}{icon("center")}{icon("right")}{sep}'
            f'<span class="tb txt">€</span><span class="tb txt">%</span><span class="tb txt sm">{".00" if lang == "en" else ",00"}</span>{sep}'
            f'{icon("border")}{icon("fill")}{icon("databar", active=True)}{icon("filter")}'
            f'<span class="tb txt sig">Σ</span></div>')


def grid(cond, lang):
    t = T[lang]
    labels = LABELS[cond]
    head = "".join(f'<th class="ch{" csel" if c == SEL_COL else ""}" style="width:{w}px">{c}</th>' for c, w in COLS)
    rows = [f'<tr class="hdr" style="height:34px">{head}</tr>']

    def rn(r):
        return f'<td class="rn{" rsel" if r == SEL_ROW else ""}">{r}</td>'

    def tr(r, cells, cls=""):
        return f'<tr class="{cls}" style="height:{ROW_H[r]}px">{rn(r)}{cells}</tr>'

    rows.append(tr(1, f'<td colspan="4" class="title">{t["title"]}</td>'))
    rows.append(tr(2, f'<td colspan="4" class="sub">{t["sub"]}</td>'))
    rows.append(tr(3, f'<td class="th">{t["h_region"]}</td><td class="th num">{t["h_rev"]}</td><td></td><td></td>', "colhead"))
    for i, (reg, v, lab) in enumerate(zip(t["regions"], VISUAL, labels)):
        r = 4 + i
        bar = (f'<div class="cell" style="height:{ROW_H[r] - 1}px"><div class="bar" style="left:{BAR_LEFT}px;width:{bar_px(v)}px"></div>'
               f'<span class="val">{"" if lab is None else fmt_num(lab, lang)}</span></div>')
        rows.append(tr(r, f'<td class="reg">{reg}</td><td class="db">{bar}</td><td></td><td></td>'))
    rows.append(tr(9, f'<td class="reg tot">{t["total"]}</td>'
                      f'<td class="db totv"><div class="cell" style="height:{ROW_H[9] - 1}px"><span class="val">{fmt_total(TOTAL, lang)}</span>'
                      f'<div class="selbox"></div><div class="handle"></div></div></td><td></td><td></td>', "totrow"))
    rows.append(tr(10, "<td></td><td></td><td></td><td></td>"))
    rows.append(tr(11, f'<td colspan="4" class="note">{t["note"]}</td>'))
    return f'<table class="grid">{"".join(rows)}</table>'


def page(cond, lang):
    t = T[lang]
    menu = "".join(f"<span>{m}</span>" for m in t["menu"])
    tabs = "".join(f'<span class="tab{" act" if i == 0 else ""}">{n}</span>' for i, n in enumerate(t["tabs"]))
    zoom = "%100" if lang == "tr" else "100%"
    return f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{ width: 896px; height: 896px; overflow: hidden; }}
  body {{ background: #fff; color: #202124; font-family: "Helvetica Neue", Arial, sans-serif; display: flex; flex-direction: column; }}
  .titlebar {{ height: 44px; flex: none; background: #e4e6ea; border-bottom: 1px solid #c9ccd2; position: relative;
               display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: 500; color: #3c4043; }}
  .dots {{ position: absolute; left: 16px; top: 15px; display: flex; gap: 9px; }}
  .dots i {{ width: 14px; height: 14px; border-radius: 50%; background: #b3b7be; border: 1px solid #a2a6ad; }}
  .menubar {{ height: 40px; flex: none; background: #f6f7f9; display: flex; align-items: center; gap: 24px; padding: 0 18px;
              font-size: 20px; color: #3c4043; }}
  .toolbar {{ height: 54px; flex: none; background: #f6f7f9; border-top: 1px solid #e3e5e8; border-bottom: 1px solid #d5d8dc;
              display: flex; align-items: center; gap: 3px; padding: 0 10px; }}
  .tb {{ width: 34px; height: 36px; display: flex; align-items: center; justify-content: center; border-radius: 5px;
         font-family: Arial, sans-serif; font-size: 21px; color: #444; }}
  .tb.on {{ background: #dde3ec; box-shadow: inset 0 0 0 1px #b8c2d1; }}
  .tb.sm {{ font-size: 20px; width: 40px; }}
  .tb.sig {{ font-size: 24px; }}
  .tb .it {{ font-family: Georgia, serif; font-style: italic; font-weight: 700; }}
  .sep {{ width: 1px; height: 28px; background: #cfd2d7; margin: 0 6px; }}
  .box {{ height: 34px; border: 1px solid #c6c9ce; border-radius: 5px; background: #fff; display: flex; align-items: center;
          justify-content: space-between; padding: 0 8px; font-family: Arial, sans-serif; font-size: 20px; color: #333; }}
  .box svg {{ margin-left: 8px; flex: none; }}
  .box.font {{ width: 104px; }}
  .box.size {{ width: 58px; margin-left: 6px; }}
  .fbar {{ height: 48px; flex: none; display: flex; align-items: center; border-bottom: 1px solid #d5d8dc; background: #fff; }}
  .namebox {{ width: 92px; height: 100%; border-right: 1px solid #d5d8dc; display: flex; align-items: center; justify-content: center;
              font-family: Arial, sans-serif; font-size: 21px; color: #333; }}
  .fx {{ width: 52px; text-align: center; font-family: Georgia, serif; font-style: italic; font-size: 22px; color: #777;
         border-right: 1px solid #e3e5e8; }}
  .formula {{ padding-left: 14px; font-family: Arial, sans-serif; font-size: 21px; color: #222; }}
  .sheet {{ flex: 1; position: relative; overflow: hidden; background: #fff; }}
  .vscroll {{ position: absolute; right: 0; top: 0; bottom: 0; width: 16px; background: #f4f5f7; border-left: 1px solid #dfe1e5; }}
  .vscroll i {{ position: absolute; left: 3px; right: 3px; top: 40px; height: 120px; border-radius: 5px; background: #c8cbd0; }}
  table.grid {{ border-collapse: collapse; table-layout: fixed; font-family: Arial, sans-serif; }}
  .grid td, .grid th {{ border: 1px solid #dadce0; padding: 0; overflow: hidden; white-space: nowrap; }}
  .grid th.ch {{ background: #f1f3f5; color: #5f6368; font-weight: 400; font-size: 20px; text-align: center; }}
  .grid th.ch:first-child {{ background: #e8eaed; }}
  .grid th.csel {{ background: #dfe5ee; color: #1f2d3d; font-weight: 700; box-shadow: inset 0 -3px 0 #3d5a80; }}
  .grid td.rn {{ background: #f1f3f5; color: #5f6368; font-size: 20px; text-align: center; }}
  .grid td.rsel {{ background: #dfe5ee; color: #1f2d3d; font-weight: 700; box-shadow: inset -3px 0 0 #3d5a80; }}
  .title {{ font-size: 26px; font-weight: 700; padding-left: 10px !important; color: #202124; }}
  .sub {{ font-size: 20px; color: #5f6368; padding-left: 10px !important; font-style: italic; }}
  .note {{ font-size: 20px; color: #5f6368; padding-left: 10px !important; }}
  tr.colhead td.th {{ background: #eceff3; font-size: 22px; font-weight: 700; padding-left: 10px; color: #202124;
                      border-bottom: 2px solid #9aa0a6; }}
  tr.colhead td.th.num {{ text-align: right; padding-right: {NUM_RIGHT}px; }}
  td.reg {{ font-size: 24px; padding-left: 10px !important; color: #202124; }}
  td.db {{ position: relative; }}
  .cell {{ position: relative; }}
  .bar {{ position: absolute; top: 13px; bottom: 13px; background: linear-gradient(90deg, #e8a25a 0%, #f3c793 100%);
          border: 1px solid #c47f35; }}
  .val {{ position: absolute; right: {NUM_RIGHT}px; top: 50%; transform: translateY(-50%); font-size: 26px; font-weight: 700;
          color: #202124; font-variant-numeric: tabular-nums; }}
  tr.totrow td {{ border-top: 3px double #5f6368; }}
  tr.totrow td.rn {{ border-top: 1px solid #dadce0; }}
  td.tot {{ font-weight: 700; }}
  .selbox {{ position: absolute; left: -1px; top: -1px; right: -1px; bottom: -1px; border: 3px solid #3d5a80; }}
  .handle {{ position: absolute; right: -2px; bottom: -2px; width: 9px; height: 9px; background: #3d5a80; border: 1px solid #fff; }}
  .tabs {{ height: 44px; flex: none; background: #f1f3f5; border-top: 1px solid #d5d8dc; display: flex; align-items: stretch;
           padding-left: 10px; font-size: 20px; color: #5f6368; }}
  .tabs .plus {{ width: 40px; display: flex; align-items: center; justify-content: center; font-size: 26px; color: #777; }}
  .tab {{ display: flex; align-items: center; padding: 0 20px; border-right: 1px solid #d5d8dc; }}
  .tab.act {{ background: #fff; color: #1f2d3d; font-weight: 700; box-shadow: inset 0 -3px 0 #3d5a80; }}
  .status {{ height: 34px; flex: none; background: #e9ebee; border-top: 1px solid #d5d8dc; display: flex; align-items: center;
             justify-content: space-between; padding: 0 16px; font-size: 20px; color: #5f6368; }}
  .zoom {{ display: flex; align-items: center; gap: 10px; }}
  .zoom .track {{ width: 110px; height: 3px; background: #a6aab0; position: relative; }}
  .zoom .track i {{ position: absolute; left: 50px; top: -6px; width: 6px; height: 15px; background: #6b7078; border-radius: 2px; }}
</style></head><body>
  <div class="titlebar"><div class="dots"><i></i><i></i><i></i></div>{t["win"]}</div>
  <div class="menubar">{menu}</div>
  {toolbar(lang)}
  <div class="fbar"><div class="namebox">{SEL_COL}{SEL_ROW}</div><div class="fx">fx</div>
    <div class="formula">={t["func"]}(B4:B8)</div></div>
  <div class="sheet">{grid(cond, lang)}<div class="vscroll"><i></i></div></div>
  <div class="tabs"><span class="plus">+</span>{tabs}</div>
  <div class="status"><span>{t["ready"]}</span><span class="zoom"><span>−</span><span class="track"><i></i></span><span>+</span>
    <span>{zoom}</span></span></div>
</body></html>"""


# ---------- questions (answers computed from the data arrays) ----------
REG = {   # accept lists per region: canonical first
    "north": {"en": ["north", "north region", "northern"], "tr": ["kuzey"]},
    "south": {"en": ["south", "south region", "southern"], "tr": ["güney"]},
    "east": {"en": ["east", "east region", "eastern"], "tr": ["doğu"]},
    "west": {"en": ["west", "west region", "western"], "tr": ["batı"]},
    "central": {"en": ["central", "central region", "centre", "center"], "tr": ["merkez"]},
}
# Yes/no = the shared YES/NO, plus the Turkish echo answer to "...elde etti mi?": "(Elde) etti." = yes, "(Elde) etmedi." = no.
Y = {"en": YES["en"], "tr": YES["tr"] + ["^etti", "^elde etti"]}
N = {"en": NO["en"], "tr": NO["tr"] + ["^etmedi", "^elde etmedi"]}


def region_of(values, pick):
    return KEYS[values.index(pick(values))]


def num(v):
    """Digits (by value, anywhere) + whole-answer number words (num_accept). '610,000' / TR '610.000' / '610 bin' already
    match '610' (the scorer reads 610,000 and 610.000 as 610.0), so the only extra is the ungrouped '610000'."""
    return {lang: num_accept(v, lang, extra=(f"{v}000",)) for lang in LANGS}


def yn(cond):
    return Y if cond else N


I_N, I_W, I_E = KEYS.index("north"), KEYS.index("west"), KEYS.index("east")
assert VISUAL[I_W] < VISUAL[I_N] and CONFLICT[I_W] > CONFLICT[I_N]      # q3a: bars say no, conflict text says yes
assert VISUAL[I_E] != CONFLICT[I_E]                                      # q4 differs
assert region_of(VISUAL, max) != region_of(CONFLICT, max) and region_of(VISUAL, min) != region_of(CONFLICT, min)

SPEC = {
    "id": SID,
    "title": {"en": "Q3 revenue by region (spreadsheet)", "tr": "Bölgelere göre 3. çeyrek geliri (tablo)"},
    "chart": "in-cell data bars", "style": "generic spreadsheet screenshot", "tech": "HTML table + CSS (headless Chrome)",
    "mechanism": "label",
    "conflict_summary": "Data bars: East longest, South shortest, North > West; in conflict the printed revenues are permuted "
                        "(East 180, Central 610, West 420 > North 260). Total 1,800 identical. Bars orange in all versions.",
    "data": {"regions": T["en"]["regions"], "regions_tr": T["tr"]["regions"], "visual": VISUAL,
             "conflict_labels": CONFLICT, "total": TOTAL, "unit": "thousand €"},
    "questions": [
        {"qid": "s14_q1", "kind": "argmax", "pair": None,
         "prompt": {"en": "answer en which region had the highest revenue in q3?",
                    "tr": "answer tr 3. çeyrekte geliri en yüksek olan bölge hangisi?"},
         "visual": REG[region_of(VISUAL, max)], "text": REG[region_of(CONFLICT, max)],
         "nonumbers": True},      # longest bar (East) is plain on the drawing
        {"qid": "s14_q2", "kind": "argmin", "pair": None,
         "prompt": {"en": "answer en which region had the lowest revenue in q3?",
                    "tr": "answer tr 3. çeyrekte geliri en düşük olan bölge hangisi?"},
         "visual": REG[region_of(VISUAL, min)], "text": REG[region_of(CONFLICT, min)],
         "nonumbers": True},      # shortest bar (South) is plain on the drawing
        {"qid": "s14_q3a", "kind": "compare", "pair": "s14_p1",
         "prompt": {"en": "answer en did the west region earn more than the north region?",
                    "tr": "answer tr batı bölgesi, kuzey bölgesinden daha fazla gelir elde etti mi?"},
         "visual": yn(VISUAL[I_W] > VISUAL[I_N]), "text": yn(CONFLICT[I_W] > CONFLICT[I_N]),
         "nonumbers": True},      # West bar (123 px) vs North bar (198 px): clearly different lengths
        {"qid": "s14_q3b", "kind": "compare", "pair": "s14_p1",
         "prompt": {"en": "answer en did the west region earn less than the north region?",
                    "tr": "answer tr batı bölgesi, kuzey bölgesinden daha az gelir elde etti mi?"},
         "visual": yn(VISUAL[I_W] < VISUAL[I_N]), "text": yn(CONFLICT[I_W] < CONFLICT[I_N]),
         "nonumbers": True},      # same pair as q3a
        {"qid": "s14_q4", "kind": "read_value", "pair": None,
         "prompt": {"en": "answer en what was the revenue of the east region?",
                    "tr": "answer tr doğu bölgesinin geliri ne kadardı?"},
         "visual": num(VISUAL[I_E]), "text": num(CONFLICT[I_E]),
         "nonumbers": False},     # exact value only came from the removed cell text (no axis/scale on data bars)
    ],
}

if __name__ == "__main__":
    for cond in CONDS:
        for lang in LANGS:
            render_html(page(cond, lang), name(SID, cond, lang))
    finish(SPEC)
