"""s11 — finance app watchlist with 1-month sparklines. KDNL/MXRA/VESK end above their start line, TLWY below;
conflict flips the sign of every printed 1-month change (last prices stay the same).

Rows are A–Z (stated on the page), and the values are assigned so that neither the visual winner (MXRA, row 2) nor the
text winner in conflict (TLWY, row 3) sits in the first/last row, and the consistent change column is not sorted
(a 'first row' or 'list sorted by performance' prior must not point at either answer).
Tickers KDNL / MXRA / TLWY replace the DESIGN.md placeholders KORA (a real EGX ticker) / MIRX (close to TSXV 'MIR.X') /
TALN (Talon International, OTC); a web search (2026-10-04) found no listing for KDNL, MXRA, TLWY or VESK.

No third cue for q1 ('gained the most'): a sign flip keeps every magnitude, so the largest printed number is the same in
both versions and must belong to the TEXT winner (TLWY 18.4, not MXRA 12.7). A sign-blind 'biggest number' reader then
answers TLWY on the consistent image too, fails the consistent control and is filtered out instead of being counted as a
geometry win. Last prices are assigned so neither winner holds the highest or lowest price.

Deviations from DESIGN.md: values (KORA +18.4 / MIRX +7.5 / TALN +3.1 / VESK −12.7 → the rule above; the smallest riser is
+4.8, not +3.1, so its line ends ≥ 20 px above the start line at 896 px and a geometry reader still counts it as 'up');
q2 asks about TLWY, the one line that falls (visual 'down', conflict text 'up'), not MIRX: it balances the q4 pair, whose
row (MXRA) rises, so the stimulus has one visual-down and one visual-up direction item; the count question is asked both
ways (q3a 'went up', q3b 'went down', see COUNT); there is no read_value question (see data.no_read_value).
Answers use the shared lists in common/answers.py (UP/DOWN, YES/NO, num_accept) plus the finance-specific extras below."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
from answers import DOWN, NO, UP, YES, num_accept  # noqa: E402
from lib import CONDS, LANGS, finish, fmt_num, fmt_pct, name, render_html  # noqa: E402

SID = "s11_finance_watchlist"
TICKERS = ["KDNL", "MXRA", "TLWY", "VESK"]                       # drawing order (A–Z, stated on the page)
COMPANIES = ["Korandel Metals", "Mirexa Labs", "Talnway Freight", "Vesker Energy"]   # listed names: same in en and tr
VISUAL = [4.8, 12.7, -18.4, 7.5]                                 # 1-month change the sparklines encode (%)
CHANGE = {"consistent": VISUAL, "conflict": [-v for v in VISUAL]}  # conflict = sign flip
CHANGE["nonumbers"] = VISUAL                                     # nonumbers: change text blanked (pills stay empty)
LAST = [132.40, 64.85, 88.05, 27.16]                             # last price, identical in both versions

# 21 daily closes, 4 Sep – 2 Oct 2026, as % change from the 4 Sep close (Brownian bridges, numpy seeds 114/101/102/107,
# picked so the last third of each line stays clearly on one side of the start line; MXRA and TLWY are the negated
# seed-102 and seed-101 paths, which end exactly at +12.7 / −18.4 without rescaling; KDNL is the seed-114 path scaled
# ×4.8/3.1 so it ends at +4.8 instead of +3.1, see the docstring). Hard-coded so the drawing never drifts.
SERIES = {
    "KDNL": [0.0, -0.57, 0.08, -0.54, 0.88, 2.69, 3.33, 3.3, 3.89, 3.99, 3.64, 3.56, 4.12, 5.51, 6.41, 5.9, 4.2,
             3.45, 3.21, 4.68, 4.8],
    "MXRA": [0.0, 0.12, -1.91, -2.25, 0.27, 2.1, 1.89, 2.95, 2.28, 6.0, 4.04, 2.4, 5.43, 6.84, 8.68, 10.2, 9.81,
             11.49, 13.73, 13.67, 12.7],
    "TLWY": [0.0, 0.17, 2.2, 0.28, -1.86, -2.41, -3.98, -7.57, -10.18, -12.26, -14.31, -14.03, -16.49, -15.04, -15.56,
             -15.92, -14.35, -15.2, -18.68, -19.19, -18.4],
    "VESK": [0.0, 0.85, -1.02, -0.68, 1.84, 0.43, 1.54, 1.22, 3.52, 3.38, 3.05, 5.49, 7.46, 7.45, 5.45, 3.85, 4.82,
             5.81, 4.48, 6.43, 7.5],
}
for _tk, _v in zip(TICKERS, VISUAL):
    assert SERIES[_tk][0] == 0 and SERIES[_tk][-1] == _v, _tk
    assert all((p > 0) == (_v > 0) and abs(p) > 1.5 for p in SERIES[_tk][14:]), _tk   # last third: clearly one side

T = {
    "en": dict(
        nav=["Home", "Watchlist", "Markets", "News"], search="Search", avatar="EK",
        h1="Watchlist", h1_dim="· 1 month", ranges=["1D", "1W", "1M", "3M", "1Y"],
        sub="4 symbols &nbsp;·&nbsp; sorted A–Z &nbsp;·&nbsp; prices in USD",
        cols=["Symbol", "Past month · Sep 4 – Oct 2", "Last", "1M change"],
        foot="Prices delayed 15 min &nbsp;·&nbsp; close of Oct 2, 2026", add="Add symbol"),
    "tr": dict(
        nav=["Ana sayfa", "İzleme listesi", "Piyasalar", "Haberler"], search="Ara", avatar="EK",
        h1="İzleme listesi", h1_dim="· 1 ay", ranges=["1G", "1H", "1A", "3A", "1Y"],
        sub="4 sembol &nbsp;·&nbsp; A'dan Z'ye sıralı &nbsp;·&nbsp; fiyatlar USD cinsinden",
        cols=["Sembol", "Son 1 ay · 4 Eyl – 2 Eki", "Son fiyat", "Aylık değişim"],
        foot="Fiyatlar 15 dk gecikmeli &nbsp;·&nbsp; 2 Eki 2026 kapanışı", add="Sembol ekle"),
}

INK, LINE, MUTED = "#1d2330", "#2f3b5c", "#6c7180"
SW, SH, PAD = 270, 128, 9                                        # sparkline box
# One shared px-per-% scale for every row (so line heights compare across rows, unlike a per-row auto-scale);
# each row's own range (incl. its 0% start line) is centred in its box.
SPAN = max(max(max(s), 0) - min(min(s), 0) for s in SERIES.values()) + 1.0
PX_PER_PCT = (SH - 2 * PAD) / SPAN
# every line ends clearly off its start line (≥ 20 px at 896, ≥ 10 px at 448), so 'up'/'down' is readable for every row
assert all(abs(v) * PX_PER_PCT >= 20 for v in VISUAL), [round(abs(v) * PX_PER_PCT, 1) for v in VISUAL]


def chg_text(x, lang):
    """Printed 1-month change. TR puts the sign after '%' ('%−18,4', read 'yüzde eksi 18,4', a common Turkish form)
    instead of fmt_pct's '−%18,4', so a copied answer keeps its minus in scoring.tokens() (which drops a minus that does
    not touch the digits). No current question reads the number, but the format stays scoring-safe."""
    return "%" + fmt_num(x, lang, 1, sign=True) if lang == "tr" else fmt_pct(x, lang, 1, sign=True)


def spark_svg(series):
    n = len(series)
    xs = [PAD + i * (SW - 2 * PAD - 6) / (n - 1) for i in range(n)]
    mid = (max(max(series), 0) + min(min(series), 0)) / 2
    y = lambda p: SH / 2 - (p - mid) * PX_PER_PCT                 # noqa: E731
    y0 = y(0)
    pts = " ".join(f"{x:.1f},{y(p):.1f}" for x, p in zip(xs, series))
    area = f"M{xs[0]:.1f},{y0:.1f} L" + " L".join(f"{x:.1f},{y(p):.1f}" for x, p in zip(xs, series)) + \
           f" L{xs[-1]:.1f},{y0:.1f} Z"
    return (f'<svg width="{SW}" height="{SH}" viewBox="0 0 {SW} {SH}" xmlns="http://www.w3.org/2000/svg">'
            f'<path d="{area}" fill="{LINE}" fill-opacity="0.11"/>'
            f'<line x1="0" y1="{y0:.1f}" x2="{SW}" y2="{y0:.1f}" stroke="#a9a397" stroke-width="2" stroke-dasharray="3 5"/>'
            f'<polyline points="{pts}" fill="none" stroke="{LINE}" stroke-width="3.2" stroke-linejoin="round" '
            f'stroke-linecap="round"/>'
            f'<circle cx="{xs[-1]:.1f}" cy="{y(series[-1]):.1f}" r="6" fill="{LINE}" stroke="#fff" stroke-width="2.5"/>'
            f'</svg>')


LOGO = ('<svg width="38" height="38" viewBox="0 0 38 38"><rect width="38" height="38" rx="10" fill="#2f3b5c"/>'
        '<circle cx="19" cy="19" r="10" fill="none" stroke="#fff" stroke-width="3"/>'
        '<circle cx="19" cy="19" r="3.5" fill="#fff"/></svg>')
LENS = ('<svg width="22" height="22" viewBox="0 0 22 22"><circle cx="9.5" cy="9.5" r="6.5" fill="none" stroke="#6c7180" '
        'stroke-width="2.4"/><line x1="14.5" y1="14.5" x2="20" y2="20" stroke="#6c7180" stroke-width="2.6" '
        'stroke-linecap="round"/></svg>')
PLUS = ('<svg width="20" height="20" viewBox="0 0 20 20"><line x1="10" y1="3" x2="10" y2="17" stroke="#2f3b5c" '
        'stroke-width="2.6" stroke-linecap="round"/><line x1="3" y1="10" x2="17" y2="10" stroke="#2f3b5c" '
        'stroke-width="2.6" stroke-linecap="round"/></svg>')


def page(cond, lang):
    t = T[lang]
    nav = "".join(f'<span class="{"on" if i == 1 else ""}">{s}</span>' for i, s in enumerate(t["nav"]))
    ranges = "".join(f'<span class="{"on" if i == 2 else ""}">{s}</span>' for i, s in enumerate(t["ranges"]))
    rows = []
    for tk, co, last, chg in zip(TICKERS, COMPANIES, LAST, CHANGE[cond]):
        rows.append(f"""
      <div class="row">
        <div class="sym"><div class="mono">{tk[0]}</div><div><div class="tk">{tk}</div><div class="co">{co}</div></div></div>
        <div class="spark">{spark_svg(SERIES[tk])}</div>
        <div class="last">{fmt_num(last, lang, 2)}</div>
        <div class="chg"><span>{"" if cond == "nonumbers" else chg_text(chg, lang)}</span></div>
      </div>""")
    c = t["cols"]
    return f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{ width: 896px; height: 896px; overflow: hidden; }}
  body {{ position: relative; background: #f3f1ec; color: {INK}; font-family: Seravek, "Gill Sans", sans-serif;
          -webkit-font-smoothing: antialiased; }}
  .top {{ height: 72px; background: #fff; border-bottom: 1px solid #e0dcd3; display: flex; align-items: center;
          padding: 0 32px; gap: 30px; }}
  .nav {{ display: flex; gap: 28px; font-size: 21px; color: {MUTED}; height: 72px; }}
  .nav span {{ display: flex; align-items: center; border-bottom: 3px solid transparent; padding-top: 3px; }}
  .nav span.on {{ color: {INK}; font-weight: 600; border-bottom-color: {LINE}; }}
  .search {{ margin-left: auto; display: flex; align-items: center; gap: 10px; width: 150px; height: 42px;
             border-radius: 21px; background: #f1efea; padding: 0 16px; font-size: 20px; color: {MUTED}; }}
  .avatar {{ width: 42px; height: 42px; border-radius: 50%; background: #d9d5cc; color: {INK}; font-size: 20px;
             font-weight: 600; display: flex; align-items: center; justify-content: center; }}
  main {{ padding: 24px 32px 0; }}
  .head {{ display: flex; align-items: center; justify-content: space-between; }}
  h1 {{ font-size: 40px; font-weight: 700; letter-spacing: -.3px; line-height: 1.1; }}
  h1 .dim {{ color: {MUTED}; font-weight: 500; }}
  .seg {{ display: flex; background: #e6e3dc; border-radius: 12px; padding: 4px; }}
  .seg span {{ font-family: "DIN Alternate", sans-serif; font-size: 21px; color: {MUTED}; width: 54px; height: 36px;
               display: flex; align-items: center; justify-content: center; border-radius: 9px; padding-top: 2px; }}
  .seg span.on {{ background: #fff; color: {INK}; box-shadow: 0 1px 3px rgba(0,0,0,.12); }}
  .sub {{ font-size: 20px; color: {MUTED}; margin-top: 6px; }}
  .card {{ margin-top: 18px; background: #fff; border: 1px solid #e0dcd3; border-radius: 16px; padding: 0 24px;
           box-shadow: 0 2px 6px rgba(30,30,40,.05); }}
  .row {{ display: flex; align-items: center; gap: 18px; height: 146px; border-top: 1px solid #ebe8e1; }}
  .row.hd {{ height: 52px; border-top: none; font-size: 20px; color: {MUTED}; font-weight: 500; }}
  .sym {{ width: 214px; display: flex; align-items: center; gap: 14px; }}
  .mono {{ width: 48px; height: 48px; border-radius: 50%; background: #ebe8e1; color: {LINE}; flex: none;
           font-family: "DIN Alternate", sans-serif; font-size: 24px; display: flex; align-items: center;
           justify-content: center; padding-top: 2px; }}
  .tk {{ font-family: "DIN Alternate", sans-serif; font-size: 29px; letter-spacing: .5px; line-height: 1.05; }}
  .co {{ font-size: 20px; color: {MUTED}; margin-top: 4px; white-space: nowrap; }}
  .spark {{ width: {SW}px; flex: none; }}
  .spark svg {{ display: block; }}
  .last {{ width: 90px; text-align: right; font-family: "DIN Alternate", sans-serif; font-size: 27px;
           font-variant-numeric: tabular-nums; }}
  /* the sign is the whole cue: big condensed-bold face so the '+' stroke survives the 448 / 224 downsizes */
  .chg {{ width: 156px; display: flex; justify-content: flex-end; }}
  .chg span {{ display: block; width: 156px; height: 56px; line-height: 59px; border-radius: 12px; background: #eceae4;
               text-align: right; padding-right: 16px; font-family: "Avenir Next Condensed", sans-serif; font-weight: 700;
               font-size: 38px; color: {INK}; font-variant-numeric: tabular-nums; white-space: nowrap; }}
  .hd .sym, .hd .spark {{ white-space: nowrap; }}
  .hd .last, .hd .chg {{ font-family: Seravek, sans-serif; font-size: 20px; white-space: nowrap; }}
  .foot {{ display: flex; justify-content: space-between; align-items: center; margin-top: 16px; font-size: 20px;
           color: {MUTED}; }}
  .foot .add {{ display: flex; align-items: center; gap: 8px; color: {LINE}; font-weight: 600; }}
</style></head><body>
  <div class="top">{LOGO}<div class="nav">{nav}</div>
    <div class="search">{LENS}<span>{t["search"]}</span></div><div class="avatar">{t["avatar"]}</div></div>
  <main>
    <div class="head"><h1>{t["h1"]} <span class="dim">{t["h1_dim"]}</span></h1><div class="seg">{ranges}</div></div>
    <div class="sub">{t["sub"]}</div>
    <div class="card">
      <div class="row hd"><div class="sym">{c[0]}</div><div class="spark">{c[1]}</div>
        <div class="last">{c[2]}</div><div class="chg">{c[3]}</div></div>{"".join(rows)}
    </div>
    <div class="foot"><span>{t["foot"]}</span><span class="add">{PLUS}{t["add"]}</span></div>
  </main>
</body></html>"""


# ---------- questions ----------
# Shared UP/DOWN (common/answers.py) + the finance words a stock answer uses ('gained', 'lost', 'değer kazandı').
# TR extras are full word forms, never bare stems: a TR accept word prefix-matches an inflected answer ('yükseliş' already
# covers 'yükselişte'). 'düşmedi'/'yükselmedi' (didn't fall / didn't rise) answer the up-or-down question by negation;
# scoring.py never lets them match the positive verb, so they sit safely on the opposite side.
UP_X = {"en": ["gained", "gain", "climbed", "positive"],
        "tr": ["kazandı", "kazanmış", "pozitif", "düşmedi", "düşmemiş"]}
DOWN_X = {"en": ["lost", "loss", "negative"],
          "tr": ["gerilemiş", "kaybetti", "kaybetmiş", "kayıp", "negatif", "yükselmedi", "yükselmemiş"]}
RISE = {lang: UP[lang] + UP_X[lang] for lang in LANGS}
FALL = {lang: DOWN[lang] + DOWN_X[lang] for lang in LANGS}
# yes/no pair about one ticker: shared YES/NO (TR NO includes a bare '^değil'), plus the verb echo a reply often gives
# instead of yes/no (EN 'up' — whole-word match already covers 'went up' — and 'rose'; TR 'yükseldi', 'düşmedi',
# reported-past 'düşmemiş').
ROSE_ECHO = {"en": ["up", "rose"], "tr": ["yükseldi", "yükselmiş", "düşmedi", "düşmemiş"]}
FELL_ECHO = {"en": ["down", "fell"], "tr": ["düştü", "düşmüş", "yükselmedi", "yükselmemiş"]}


def yn(asked_rise, rose):
    """Accept lists for 'did X go up?' (asked_rise) / 'did X go down?', given whether X rose in that reading."""
    yes = asked_rise == rose
    echo = ROSE_ECHO if rose else FELL_ECHO
    return {lang: (YES if yes else NO)[lang] + echo[lang] for lang in LANGS}


# counts: num_accept gives the digits (anywhere, by value) + whole-answer number words ('^one', '^üç'); the extras are
# short phrases around the number. Bare TR 'bir'/'tek' are accepted as EXACT matches ("=" prefix, see scoring.py),
# because the Turkish suffix rule would otherwise let 'bir' match 'birkaç'/'birçoğu'. The count prompts say 'son ayda',
# not 'son bir ayda', so an answer that echoes the prompt can't score '1'. The count is asked both ways (q3a went up:
# visual 3 / text 1; q3b went down: visual 1 / text 3), which also catches a constant '3' or '1' answer the way yes/no
# pairs catch a yes-bias. Every TR entry that contains the word 'bir' is exact ('=bir tanesi', not 'bir tanesi', which
# would score 'birkaç tanesi' = 'a few of them' as 1); 'biri' stays suffix-tolerant ('birisi'), it can't prefix-match
# 'birkaç'/'birçoğu'/'hiçbiri'. 'üç' is too short for the suffix rule, so 'üçü' is listed on its own.
COUNT_X = {1: {"en": ["only one", "just one", "one stock", "one of them"],
               "tr": ["=bir", "=tek", "biri", "=bir tane", "=bir tanesi", "=yalnızca bir", "=sadece bir", "yalnızca biri",
                      "sadece biri", "=bir hisse"]},
           3: {"en": ["three stocks", "three of them"],
               "tr": ["üçü", "üç tane", "üç hisse"]}}
COUNT = {n: {lang: num_accept(n, lang, extra=COUNT_X[n][lang]) for lang in LANGS} for n in COUNT_X}
COMPANY = {tk: co.split()[0].lower() for tk, co in zip(TICKERS, COMPANIES)}   # first word = the same in en and tr


def best(changes):
    return TICKERS[max(range(len(changes)), key=lambda i: changes[i])]


def ups(changes):
    return sum(c > 0 for c in changes)


def chg(changes, tk):
    return changes[TICKERS.index(tk)]


def direction(changes, tk):
    return RISE if chg(changes, tk) > 0 else FALL


VIS, TXT = CHANGE["consistent"], CHANGE["conflict"]
WIN_V, WIN_T = best(VIS), best(TXT)
up_vis, up_txt = ups(VIS), ups(TXT)
down_vis, down_txt = len(TICKERS) - up_vis, len(TICKERS) - up_txt
FALLERS = [tk for tk in TICKERS if chg(VIS, tk) < 0]
Q2_TK = FALLERS[0]                   # trend question on the one line that falls (TLWY): visual 'down', conflict text 'up'
PAIR_TK = "MXRA"                     # yes/no pair on the visual winner's row (rises), so q2 and q4 cover both directions
assert WIN_V != WIN_T and up_vis != up_txt and down_vis != down_txt
assert len(FALLERS) == 1 and chg(VIS, Q2_TK) < 0 < chg(TXT, Q2_TK) and Q2_TK != PAIR_TK
assert TICKERS.index(WIN_V) not in (0, len(TICKERS) - 1) and TICKERS.index(WIN_T) not in (0, len(TICKERS) - 1)
assert sorted(VIS, reverse=True) != VIS and sorted(TXT, reverse=True) != TXT
assert chg(VIS, PAIR_TK) > 0 and chg(TXT, PAIR_TK) < 0    # the conflict minus sits on the row the pair asks about
# no third cue for q1: the largest printed magnitude (identical in both versions) belongs to the TEXT winner, so a
# sign-blind 'biggest number' reader fails the consistent control; and no winner holds the highest or lowest last price.
assert TICKERS[max(range(len(VIS)), key=lambda i: abs(VIS[i]))] == WIN_T
assert sorted(abs(v) for v in VIS)[-1] > sorted(abs(v) for v in VIS)[-2]
assert {TICKERS[LAST.index(max(LAST))], TICKERS[LAST.index(min(LAST))]}.isdisjoint({WIN_V, WIN_T})
pk = PAIR_TK.lower()


def pct_list(changes):
    return ", ".join(f"{tk} {fmt_pct(v, 'en', 1, sign=True)}" for tk, v in zip(TICKERS, changes))


SPEC = {
    "id": SID,
    "title": {"en": "Watchlist · 1 month (finance app)", "tr": "İzleme listesi · 1 ay (finans uygulaması)"},
    "chart": "sparklines", "style": "finance app watchlist (light web app)", "tech": "HTML/CSS + inline SVG (headless Chrome)",
    "mechanism": "label",
    "conflict_summary": f"Rows A–Z: sparklines of KDNL, MXRA and VESK end above their dashed start line, TLWY below "
                        f"(shared % scale; MXRA rises most, TLWY moves most). Consistent changes: {pct_list(VIS)}. "
                        f"In conflict every printed sign is flipped ({pct_list(TXT)}), so the printed winner is {WIN_T}; "
                        f"magnitudes and last prices are identical, and the largest magnitude is the text winner's. "
                        f"Nonumbers: same page with the 1-month change pills left empty (tickers, names, last prices "
                        f"and sparklines unchanged), so every question is answered from the sparklines.",
    "data": {"tickers": TICKERS, "companies": COMPANIES, "visual_change_pct": VISUAL,
             "conflict_change_pct": CHANGE["conflict"], "last_price": LAST, "series_pct_from_start": SERIES,
             "dates": "21 daily closes, 4 Sep – 2 Oct 2026", "px_per_pct_shared": round(PX_PER_PCT, 3),
             "tr_change_format": "%+18,4 / %−18,4 (sign after %)",
             "third_cue_guard": f"largest |change| = {WIN_T} (text winner), so 'pick the biggest number' fails the "
                                f"consistent control; highest/lowest last price = {TICKERS[LAST.index(max(LAST))]} / "
                                f"{TICKERS[LAST.index(min(LAST))]} (neither winner)",
             "no_read_value": "No 'what was X's 1-month change' question: there is no y-axis, so in conflict the "
                              "magnitude can only come from the printed text, and a sign-dropped or sign-in-words reading "
                              "of that text ('12.7%', 'minus 12.7', 'eksi 12,7') would score as a geometry win. A sign-read "
                              "check would need a separate, unpooled control row type in common/collect.py + the notebook.",
             "analysis_note": f"q1 has a magnitude confound: in conflict the text winner {WIN_T} is also the line with the "
                              f"biggest move and shaded area, so a direction-blind 'most dramatic line' pick scores as text "
                              f"(the consistent control removes only readers who do this every time). Weight q2, q3a/q3b "
                              f"and q4a/q4b, which have no magnitude confound, above q1 when concluding 'text wins'."},
    "questions": [
        {"qid": "s11_q1", "kind": "argmax", "pair": None, "nonumbers": True,
         "prompt": {"en": "answer en which stock gained the most over the past month?",
                    "tr": "answer tr son bir ayda en çok hangi hisse değer kazandı?"},
         "visual": {lang: [WIN_V.lower(), COMPANY[WIN_V]] for lang in LANGS},
         "text": {lang: [WIN_T.lower(), COMPANY[WIN_T]] for lang in LANGS}},
        {"qid": "s11_q2", "kind": "trend", "pair": None, "nonumbers": True,
         "prompt": {"en": f"answer en did {Q2_TK.lower()} go up or down over the past month?",
                    "tr": f"answer tr {Q2_TK.lower()} son bir ayda yükseldi mi düştü mü?"},
         "visual": direction(VIS, Q2_TK), "text": direction(TXT, Q2_TK)},
        {"qid": "s11_q3a", "kind": "count", "pair": None, "nonumbers": True,
         "prompt": {"en": "answer en how many of the four stocks went up over the past month?",
                    "tr": "answer tr son ayda dört hisseden kaçı yükseldi?"},
         "visual": COUNT[up_vis], "text": COUNT[up_txt]},
        {"qid": "s11_q3b", "kind": "count", "pair": None, "nonumbers": True,
         "prompt": {"en": "answer en how many of the four stocks went down over the past month?",
                    "tr": "answer tr son ayda dört hisseden kaçı düştü?"},
         "visual": COUNT[down_vis], "text": COUNT[down_txt]},
        {"qid": "s11_q4a", "kind": "compare", "pair": "s11_p1", "nonumbers": True,
         "prompt": {"en": f"answer en did {pk} go up over the past month?",
                    "tr": f"answer tr {pk} son bir ayda yükseldi mi?"},
         "visual": yn(True, chg(VIS, PAIR_TK) > 0), "text": yn(True, chg(TXT, PAIR_TK) > 0)},
        {"qid": "s11_q4b", "kind": "compare", "pair": "s11_p1", "nonumbers": True,
         "prompt": {"en": f"answer en did {pk} go down over the past month?",
                    "tr": f"answer tr {pk} son bir ayda düştü mü?"},
         "visual": yn(False, chg(VIS, PAIR_TK) > 0), "text": yn(False, chg(TXT, PAIR_TK) > 0)},
    ],
}

if __name__ == "__main__":
    for cond in CONDS:
        for lang in LANGS:
            render_html(page(cond, lang), name(SID, cond, lang))
    finish(SPEC)
