"""s01 — newspaper page with a column chart. Bars rise Jan→Jun (wifi); conflict labels fall."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
from answers import DOWN, NO, UP, YES, num_accept  # noqa: E402
from lib import CONDS, LANGS, finish, fmt_num, name, render_html  # noqa: E402

SID = "s01_newspaper_bars"
VISUAL = [120, 210, 330, 420, 540, 640]                  # bar heights = printed values in `consistent`
LABELS = {"consistent": VISUAL, "conflict": VISUAL[::-1]}   # "nonumbers": same <text> elements, left empty

T = {
    "en": dict(
        masthead="The Riverside Courier",
        dateline="Sunday, 4 October 2026 &nbsp;·&nbsp; Business &nbsp;·&nbsp; Page 7",
        kicker="LOCAL BUSINESS",
        headline="A corner bakery on Mill Street, counted loaf by loaf",
        byline="By Lena Hart",
        body=["Mill Street Bakery has stood next to the river bridge since 1987, in what used to be a print shop. "
              "Owner Defne Ak bakes three kinds of bread every morning, starting at four.",
              "The figures in the chart come from the shop's till, which records every loaf sold. "
              "Ak says she keeps them to plan how much flour to order each week."],
        chart_title="Loaves sold per month",
        chart_sub="Mill Street Bakery, 2026",
        months=["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        source="Source: bakery till records",
        foot_l="Inside: weekend markets &nbsp;·&nbsp; weather &nbsp;·&nbsp; crossword", foot_r="7"),
    "tr": dict(
        masthead="Kıyı Postası",
        dateline="4 Ekim 2026 Pazar &nbsp;·&nbsp; Ekonomi &nbsp;·&nbsp; Sayfa 7",
        kicker="YEREL EKONOMİ",
        headline="Değirmen Sokak'ın köşe fırını ekmeklerini tek tek sayıyor",
        byline="Lena Hart",
        body=["Değirmen Sokak Fırını 1987'den beri nehir köprüsünün yanında, eskiden matbaa olan binada. "
              "Fırının sahibi Defne Ak her sabah saat dörtte üç çeşit ekmek pişiriyor.",
              "Grafikteki rakamlar, satılan her ekmeği kaydeden kasadan alındı. "
              "Ak, haftalık un siparişini planlamak için bu rakamları tuttuğunu söylüyor."],
        chart_title="Aylık satılan ekmek",
        chart_sub="Değirmen Sokak Fırını, 2026",
        months=["Oca", "Şub", "Mar", "Nis", "May", "Haz"],
        source="Kaynak: fırının kasa kayıtları",
        foot_l="İçeride: hafta sonu pazarları &nbsp;·&nbsp; hava durumu &nbsp;·&nbsp; bulmaca", foot_r="7"),
}


def bars_svg(labels, months):
    w, h, base, top = 470, 410, 366, 52                  # plot box; bars grow up from `base`
    slot = w / len(VISUAL)
    bw = 46
    scale = (base - top) / max(VISUAL)
    out = [f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">']
    for i, (v, lab, m) in enumerate(zip(VISUAL, labels, months)):
        x = slot * i + (slot - bw) / 2
        bh = v * scale
        out.append(f'<path d="M{x:.1f},{base} V{base - bh + 4:.1f} Q{x:.1f},{base - bh:.1f} {x + 4:.1f},{base - bh:.1f} '
                   f'H{x + bw - 4:.1f} Q{x + bw:.1f},{base - bh:.1f} {x + bw:.1f},{base - bh + 4:.1f} V{base} Z" fill="#1f3a5f"/>')
        out.append(f'<text x="{x + bw / 2:.1f}" y="{base - bh - 12:.1f}" text-anchor="middle" class="val">{lab}</text>')
        out.append(f'<text x="{x + bw / 2:.1f}" y="{base + 34}" text-anchor="middle" class="mon">{m}</text>')
    out.append(f'<line x1="0" y1="{base}" x2="{w}" y2="{base}" stroke="#222" stroke-width="2"/>')
    out.append("</svg>")
    return "\n".join(out)


def page(cond, lang):
    t = T[lang]
    if cond == "nonumbers":
        labels = [""] * len(VISUAL)                      # value labels blanked; <text> nodes stay in place
    else:
        labels = [fmt_num(v, lang) for v in LABELS[cond]]
    body = "".join(f"<p>{p}</p>" for p in t["body"])
    return f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{ width: 896px; height: 896px; overflow: hidden; }}
  body {{ position: relative; background: #f6f1e7; color: #1a1a1a; font-family: Georgia, serif; padding: 30px 36px; }}
  .mast {{ text-align: center; font-family: Didot, "Bodoni 72", Georgia, serif; font-size: 58px; font-weight: 700;
           letter-spacing: 1px; line-height: 1.05; }}
  .rule {{ border-top: 3px double #1a1a1a; border-bottom: 1px solid #1a1a1a; margin-top: 10px; padding: 6px 0;
           text-align: center; font-size: 20px; font-variant: small-caps; letter-spacing: .5px; }}
  .kicker {{ margin-top: 18px; font-family: "Helvetica Neue", Arial, sans-serif; font-size: 20px; font-weight: 700;
             letter-spacing: 2px; color: #8a2c1d; }}
  h1 {{ font-size: 40px; line-height: 1.12; margin-top: 6px; font-weight: 700; }}
  .by {{ margin-top: 8px; font-size: 20px; font-style: italic; color: #444; }}
  .cols {{ display: flex; gap: 26px; margin-top: 16px; border-top: 1px solid #999; padding-top: 16px; }}
  .text {{ width: 300px; font-size: 21px; line-height: 1.42; text-align: left; hyphens: manual; }}
  .text p + p {{ margin-top: 12px; text-indent: 1.2em; }}
  .chart {{ flex: 1; border-left: 1px solid #999; padding-left: 24px; }}
  .ct {{ font-family: "Helvetica Neue", Arial, sans-serif; font-size: 24px; font-weight: 700; }}
  .cs {{ font-family: "Helvetica Neue", Arial, sans-serif; font-size: 20px; color: #555; margin-top: 2px; }}
  svg {{ display: block; margin-top: 4px; }}
  .val {{ font-family: "Helvetica Neue", Arial, sans-serif; font-size: 25px; font-weight: 700; fill: #1a1a1a; }}
  .mon {{ font-family: "Helvetica Neue", Arial, sans-serif; font-size: 23px; fill: #333; }}
  .src {{ font-size: 20px; font-style: italic; color: #555; margin-top: 2px; }}
  .foot {{ position: absolute; left: 36px; right: 36px; bottom: 26px; border-top: 3px double #1a1a1a; padding-top: 8px;
           font-size: 20px; font-variant: small-caps; letter-spacing: .5px; display: flex; justify-content: space-between; }}
</style></head><body>
  <div class="mast">{t["masthead"]}</div>
  <div class="rule">{t["dateline"]}</div>
  <div class="kicker">{t["kicker"]}</div>
  <h1>{t["headline"]}</h1>
  <div class="by">{t["byline"]}</div>
  <div class="cols">
    <div class="text">{body}</div>
    <div class="chart">
      <div class="ct">{t["chart_title"]}</div>
      <div class="cs">{t["chart_sub"]}</div>
      {bars_svg(labels, t["months"])}
      <div class="src">{t["source"]}</div>
    </div>
  </div>
  <div class="foot"><span>{t["foot_l"]}</span><span>{t["foot_r"]}</span></div>
</body></html>"""


SPEC = {
    "id": SID,
    "title": {"en": "Loaves sold per month (newspaper)", "tr": "Aylık satılan ekmek (gazete)"},
    "chart": "column bars", "style": "newspaper page", "tech": "HTML/CSS + inline SVG (headless Chrome)",
    "mechanism": "label",
    "conflict_summary": "Bars rise Jan→Jun like a wifi icon; in conflict the printed values fall 640→120.",
    "data": {"months": T["en"]["months"], "visual": VISUAL, "conflict_labels": LABELS["conflict"]},
    "questions": [
        {"qid": "s01_q1", "kind": "trend", "pair": None,
         "prompt": {"en": "answer en did monthly sales go up or down from january to june?",
                    "tr": "answer tr ocaktan hazirana aylık satışlar arttı mı azaldı mı?"},
         "visual": UP, "text": DOWN, "nonumbers": True},
        {"qid": "s01_q2", "kind": "argmax", "pair": None,
         "prompt": {"en": "answer en in which month were the most loaves sold?",
                    "tr": "answer tr en çok ekmek hangi ayda satıldı?"},
         "visual": {"en": ["june", "jun"], "tr": ["haziran", "=haz"]},     # "=": "haz" must not match "hazır"
         "text": {"en": ["january", "jan"], "tr": ["ocak", "=oca"]}, "nonumbers": True},
        {"qid": "s01_q3a", "kind": "compare", "pair": "s01_p1",
         "prompt": {"en": "answer en were more loaves sold in june than in january?",
                    "tr": "answer tr haziranda ocaktan daha fazla ekmek satıldı mı?"},
         "visual": YES, "text": NO, "nonumbers": True},
        {"qid": "s01_q3b", "kind": "compare", "pair": "s01_p1",
         "prompt": {"en": "answer en were fewer loaves sold in june than in january?",
                    "tr": "answer tr haziranda ocaktan daha az ekmek satıldı mı?"},
         "visual": NO, "text": YES, "nonumbers": True},
        {"qid": "s01_q4", "kind": "read_value", "pair": None,
         "prompt": {"en": "answer en how many loaves were sold in june?",
                    "tr": "answer tr haziranda kaç ekmek satıldı?"},
         "visual": {lg: num_accept(VISUAL[-1], lg) for lg in LANGS},
         "text": {lg: num_accept(LABELS["conflict"][-1], lg) for lg in LANGS},
         "nonumbers": False},            # exact count only came from the printed label
    ],
}

if __name__ == "__main__":
    for cond in CONDS:
        for lang in LANGS:
            render_html(page(cond, lang), name(SID, cond, lang))
    finish(SPEC)
