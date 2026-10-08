"""s02 — dark-theme news-site article with a line chart (pure matplotlib).

The line rises 2018→2025 on a normal 0–600 axis. In `conflict` only the y tick labels are inverted
(0 at the top, 600 at the bottom), so the very same line now encodes falling values (v → 600 − v).
In `nonumbers` the y tick labels (the only cue strings) are hidden; gridlines, years and all other text stay.

Yearly (not monthly) totals on purpose: bicycle theft is strongly seasonal (low in winter, high in summer),
so a Jan→Aug x-axis would add a world-knowledge cue agreeing with the rising line. Years carry no such prior,
and the year labels are identical in en/tr.
"""
import io
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from fontTools.ttLib import TTCollection, TTFont  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.patches import Circle, Ellipse, FancyBboxPatch, Rectangle  # noqa: E402
from matplotlib.transforms import blended_transform_factory  # noqa: E402
from PIL import Image  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
from answers import DOWN, NO, UP, YES  # noqa: E402
from lib import BUILD, CONDS, LANGS, SIZE, finish, fmt_num, name, save_image  # noqa: E402

SID = "s02_magazine_line_inverted"
YEARS = list(range(2018, 2026))                             # x labels, identical in en/tr
VISUAL = [180, 260, 240, 330, 380, 360, 450, 520]          # line geometry on a normal axis = values in `consistent`
# first point 180 (not 210): keeps a >= 60-unit (~25 px at 896) gap to the runner-up 240, so the min (visual) /
# max (conflict text) point is unambiguous even at 224 px, while the 260 > 240 dip stays.
YMAX, YSTEP = 600, 100
TICKS = list(range(0, YMAX + 1, YSTEP))                     # tick positions (geometry, never change)
TICK_LABELS = {"consistent": TICKS, "conflict": [YMAX - t for t in TICKS],   # text printed at each tick position
               "nonumbers": TICKS}      # nonumbers: laid out as in consistent but drawn invisible (visible=False)
TRUTH = {"consistent": VISUAL, "conflict": [YMAX - v for v in VISUAL]}       # what the printed axis says

# ---------- fonts (macOS system fonts; faces pulled out of .ttc collections so matplotlib can use them) ----------
SYS, SUP = "/System/Library/Fonts/", "/System/Library/Fonts/Supplemental/"
FONT_SRC = {
    "serif": (SUP + "Charter.ttc", 0), "serif_b": (SUP + "Charter.ttc", 3), "serif_i": (SUP + "Charter.ttc", 1),
    "sans": (SYS + "Avenir Next.ttc", 7), "sans_m": (SYS + "Avenir Next.ttc", 5),
    "sans_d": (SYS + "Avenir Next.ttc", 2), "sans_i": (SYS + "Avenir Next.ttc", 4),
}
TURKISH = "şğıİçöüŞĞÇÖÜ"


def load_fonts():
    d = BUILD / "fonts"
    d.mkdir(parents=True, exist_ok=True)
    fonts = {}
    for key, (path, idx) in FONT_SRC.items():
        if idx is None:
            out, face = Path(path), TTFont(path)
        else:
            out = d / f"{Path(path).stem.replace(' ', '')}-{idx}.ttf"
            face = TTCollection(path).fonts[idx]
            if not out.exists():
                face.save(out)
        missing = [c for c in TURKISH if ord(c) not in face.getBestCmap()]
        assert not missing, f"{key}: font lacks Turkish glyphs {missing}"
        fonts[key] = out
    return fonts


FONTS = load_fonts()
DPI = 100


def pt(px):
    """CSS-style pixel size -> matplotlib points at DPI 100."""
    return px * 72 / DPI


# ---------- palette (neutral: periwinkle site accent, amber data line; no red/green, nothing tied to direction) ----------
BG, NAV, CARD, CARD_EDGE = "#0e1015", "#07080b", "#161921", "#272c37"
INK, INK2, INK3, GRID, ACC = "#eeece7", "#aab0bb", "#7d8490", "#3b4354", "#a9b6fb"
LINE = "#f0a840"            # data line + markers: amber for set variety only (same in all 4 images, not semantic)
GRID_LW = 2.0               # px; visible enough at 448 to tie each point to its tick label
# y tick labels ARE the cue: Avenir Next Demi Bold 29 px -> cap height 20.5 px, digit height 21.6 px (~11 px at 448)
TICK_FONT, TICK_PX, TICK_GAP = "sans_d", 29, 16
YEAR_FONT, YEAR_PX = "sans_m", 22

T = {
    "en": dict(
        site="The Evening Lantern", logo="EL",
        nav=["News", "City", "Data", "Culture", "Sport"],
        kicker="CITY  /  DATA",
        headline="What the city's theft reports show",
        dek="Quellbury police publish every bicycle theft report filed in the city. "
            "We charted the yearly totals from 2018 to 2025.",
        byline="By Mara Quinn", meta="4 October 2026  ·  3 min read", share="Share",
        chart_title="Bicycle thefts reported per year",
        chart_sub="Quellbury, 2018–2025  ·  number of reports",
        source="Source: Quellbury Police open-data portal",
        body="A report is counted in the year it was filed, not the year the bicycle went missing. "
             "Reports made online and at the city's three stations are both included."),
    "tr": dict(
        site="Kent Feneri", logo="KF",              # not "Akşam …": Akşam is a real national daily (rule 5)
        nav=["Haberler", "Şehir", "Veri", "Kültür", "Spor"],
        kicker="ŞEHİR  /  VERİ",
        headline="Şehrin hırsızlık kayıtları ne anlatıyor?",
        dek="Quellbury polisi şehirde yapılan her bisiklet hırsızlığı ihbarını yayımlıyor. "
            "2018–2025 arasındaki yıllık toplamları grafiğe döktük.",
        byline="Mara Quinn", meta="4 Ekim 2026  ·  3 dk okuma", share="Paylaş",
        chart_title="Yıllara göre bildirilen bisiklet hırsızlıkları",
        chart_sub="Quellbury, 2018–2025  ·  ihbar sayısı",
        source="Kaynak: Quellbury Polisi açık veri portalı",
        body="Bir ihbar, bisikletin kaybolduğu yılda değil, yapıldığı yılda sayılıyor. "
             "Hem internetten hem de şehirdeki üç karakoldan yapılan ihbarlar verilere dahil."),
}

# ---------- fixed layout (px, y from top) — identical for every condition and language ----------
M = 40                      # page side margin
NAV_H = 68
KICKER_Y = 104              # baselines
HEAD_Y = 158
DEK_Y, DEK_LH = 200, 31
BYLINE_Y = 290
CARD_BOX = (M, 322, SIZE - M, 790)            # x0, y0, x1, y1
PLOT_BOX = (136, 444, 826, 696)               # plot box inside the card: x0, y0(top), x1, y1(bottom); x0 puts the
#                                               widest tick label flush with the card title (x = 66)
BODY_Y, BODY_LH = 830, 30
CONTENT_W = SIZE - 2 * M


class Page:
    """A full-figure axes in pixel coordinates (origin top-left)."""

    def __init__(self, fig):
        self.fig = fig
        self.ax = fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, SIZE)
        self.ax.set_ylim(SIZE, 0)
        self.ax.axis("off")
        self.r = fig.canvas.get_renderer()

    def fp(self, key, px):
        return FontProperties(fname=FONTS[key], size=pt(px))

    def width(self, s, key, px):
        w, _, _ = self.r.get_text_width_height_descent(s, self.fp(key, px), ismath=False)
        return w

    def text(self, x, y, s, key, px, color=INK, ha="left", va="baseline", **kw):
        return self.ax.text(x, y, s, fontproperties=self.fp(key, px), color=color, ha=ha, va=va, **kw)

    def wrap(self, s, key, px, maxw):
        lines, cur = [], ""
        for word in s.split():
            trial = f"{cur} {word}".strip()
            if cur and self.width(trial, key, px) > maxw:
                lines.append(cur)
                cur = word
            else:
                cur = trial
        return lines + [cur]

    def rect(self, x0, y0, x1, y1, color, r=0, lw=0, edge=None, z=1):
        if r:
            p = FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle=f"round,pad=0,rounding_size={r}",
                               fc=color, ec=edge or color, lw=pt(lw), zorder=z)
        else:
            p = Rectangle((x0, y0), x1 - x0, y1 - y0, fc=color, ec=edge or color, lw=pt(lw), zorder=z)
        self.ax.add_patch(p)

    def hline(self, x0, x1, y, color, lw=1, z=2):
        self.ax.plot([x0, x1], [y, y], color=color, lw=pt(lw), solid_capstyle="butt", zorder=z)


def draw(cond, lang):
    t = T[lang]
    fig = plt.figure(figsize=(SIZE / DPI, SIZE / DPI), dpi=DPI, facecolor=BG)
    pg = Page(fig)

    # --- top navigation bar ---
    pg.rect(0, 0, SIZE, NAV_H, NAV)
    pg.hline(0, SIZE, NAV_H, CARD_EDGE, 1)
    pg.rect(M, 16, M + 36, 52, ACC, r=7, z=3)
    pg.text(M + 18, 34, t["logo"], "sans_d", 20, color=NAV, ha="center", va="center_baseline", zorder=4)
    pg.text(M + 50, 43, t["site"], "serif_b", 27)
    x = SIZE - M
    for item in reversed(t["nav"]):                       # right-aligned menu
        pg.text(x, 42, item, "sans_m", 20, color=INK2, ha="right")
        x -= pg.width(item, "sans_m", 20) + 24
    assert x > M + 50 + pg.width(t["site"], "serif_b", 27) + 20, "nav overlaps site name"

    # --- article header ---
    pg.text(M, KICKER_Y, t["kicker"], "sans_d", 20, color=ACC)
    assert pg.width(t["headline"], "serif_b", 42) <= CONTENT_W, f"headline too wide ({lang})"
    pg.text(M, HEAD_Y, t["headline"], "serif_b", 42)
    dek = pg.wrap(t["dek"], "serif", 22, CONTENT_W)
    assert len(dek) <= 2, f"dek wraps to {len(dek)} lines ({lang})"
    for i, line in enumerate(dek):
        pg.text(M, DEK_Y + i * DEK_LH, line, "serif", 22, color=INK2)

    # byline row: avatar, name, meta, share pill
    acx, acy = M + 17, BYLINE_Y - 7                        # generic avatar silhouette (no initials: no tiny text)
    disc = Circle((acx, acy), 17, fc="#2a3040", ec=CARD_EDGE, lw=pt(1), zorder=3)
    pg.ax.add_patch(disc)
    pg.ax.add_patch(Circle((acx, acy - 4), 6.5, fc=INK3, lw=0, zorder=4))
    body_shape = Ellipse((acx, acy + 15), 24, 20, fc=INK3, lw=0, zorder=4)
    pg.ax.add_patch(body_shape)
    body_shape.set_clip_path(disc)
    bx = M + 46
    pg.text(bx, BYLINE_Y, t["byline"], "sans_d", 20)
    bx += pg.width(t["byline"], "sans_d", 20) + 16
    pg.text(bx, BYLINE_Y, t["meta"], "sans", 20, color=INK2)
    sw = pg.width(t["share"], "sans_m", 20) + 36
    pg.rect(SIZE - M - sw, BYLINE_Y - 24, SIZE - M, BYLINE_Y + 9, NAV, r=16, lw=1.2, edge=CARD_EDGE, z=3)
    pg.text(SIZE - M - sw / 2, BYLINE_Y - 1, t["share"], "sans_m", 20, color=INK2, ha="center", zorder=4)

    # --- chart card ---
    x0, y0, x1, y1 = CARD_BOX
    pg.rect(x0, y0, x1, y1, CARD, r=14, lw=1.2, edge=CARD_EDGE)
    pg.text(x0 + 26, y0 + 46, t["chart_title"], "sans_d", 25)
    pg.text(x0 + 26, y0 + 78, t["chart_sub"], "sans", 20, color=INK2)
    pg.text(x0 + 26, y1 - 22, t["source"], "sans_i", 20, color=INK3)

    px0, py0, px1, py1 = PLOT_BOX
    widest = max(pg.width(fmt_num(v, lang), TICK_FONT, TICK_PX) for v in TICKS)
    assert px0 - TICK_GAP - widest >= x0 + 26 - 1, "tick labels stick out past the card padding"
    ax = fig.add_axes([px0 / SIZE, 1 - py1 / SIZE, (px1 - px0) / SIZE, (py1 - py0) / SIZE])
    ax.patch.set_alpha(0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlim(-0.4, len(VISUAL) - 0.6)
    ax.set_ylim(0, YMAX)
    yax = blended_transform_factory(ax.transAxes, ax.transData)
    xax = blended_transform_factory(ax.transData, ax.transAxes)
    for tick, lab in zip(TICKS, TICK_LABELS[cond]):        # every gridline drawn the same: no special zero baseline
        ax.plot([0, 1], [tick, tick], transform=yax, color=GRID, lw=pt(GRID_LW), clip_on=False, zorder=1)
        ax.text(-TICK_GAP / (px1 - px0), tick, fmt_num(lab, lang), transform=yax, ha="right", va="center_baseline",
                fontproperties=pg.fp(TICK_FONT, TICK_PX), color=INK, visible=cond != "nonumbers")
    for i, yr in enumerate(YEARS):
        ax.text(i, -16 / (py1 - py0), str(yr), transform=xax, ha="center", va="top",
                fontproperties=pg.fp(YEAR_FONT, YEAR_PX), color=INK2)
    xs = list(range(len(VISUAL)))
    ax.plot(xs, VISUAL, color=LINE, lw=pt(4), solid_joinstyle="round", solid_capstyle="round", zorder=3, clip_on=False)
    ax.plot(xs, VISUAL, ls="none", marker="o", ms=pt(15), mfc=LINE, mec=CARD, mew=pt(3), zorder=4, clip_on=False)

    # --- body text under the card ---
    body = pg.wrap(t["body"], "serif", 21, CONTENT_W)
    assert len(body) <= 2, f"body wraps to {len(body)} lines ({lang})"
    for i, line in enumerate(body):
        pg.text(M, BODY_Y + i * BODY_LH, line, "serif", 21)

    buf = io.BytesIO()
    fig.savefig(buf, dpi=DPI, facecolor=BG, format="png")
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf)


# ---------- questions ----------
# nonumbers: all True. Without tick labels the line is read by the default convention (up = more), so trend,
# argmax, argmin and the 2018-vs-2025 comparison all follow from the drawing alone (expected = visual list).
def year(i):
    return [str(YEARS[i])]                  # bare year; numbers match exactly, so "2025" never matches "2018"


def argmax(v):
    return max(range(len(v)), key=v.__getitem__)


def argmin(v):
    return min(range(len(v)), key=v.__getitem__)


# q1 asks "increase or decrease" (quantity words), never "go up or down": in the inverted-axis conflict image the
# line goes up on the page, so spatial wording would prime the visual answer. up/down stay as synonyms (shared
# UP/DOWN lists in common/answers.py, which no longer carry the "artma"/"azalma" stems that matched negations).


def yn(flag):
    return YES if flag else NO


V, C = TRUTH["consistent"], TRUTH["conflict"]
assert (V[-1] > V[0]) != (C[-1] > C[0]) and argmax(V) != argmax(C) and argmin(V) != argmin(C)
A, B = YEARS[0], YEARS[-1]

SPEC = {
    "id": SID,
    "title": {"en": "Bicycle thefts reported per year (news site, dark)",
              "tr": "Yıllara göre bildirilen bisiklet hırsızlıkları (haber sitesi, koyu tema)"},
    "chart": "line with markers", "style": "news-site article page, dark theme", "tech": "matplotlib (whole page, Agg)",
    "mechanism": "axis",
    "conflict_summary": f"Line rises {A}→{B} ({V[0]}→{V[-1]} on a normal 0–600 axis); in conflict the y tick labels are "
                        f"inverted (0 at top, 600 at bottom), so the same line encodes falling values {C[0]}→{C[-1]}. "
                        "Years, not months: bicycle theft is seasonal, and a Jan→Aug axis would add a prior "
                        "agreeing with the rising line.",
    "data": {"years": YEARS, "visual": VISUAL, "conflict_truth": TRUTH["conflict"],
             "y_tick_positions": TICKS, "conflict_tick_labels_bottom_to_top": TICK_LABELS["conflict"],
             "nonumbers": "y tick labels hidden; gridlines, year labels and all other text unchanged"},
    "questions": [
        {"qid": "s02_q1", "kind": "trend", "pair": None, "nonumbers": True,
         "prompt": {"en": f"answer en did the number of bicycle thefts increase or decrease from {A} to {B}?",
                    "tr": f"answer tr {A}'den {B}'e bisiklet hırsızlığı sayısı arttı mı azaldı mı?"},
         "visual": UP if V[-1] > V[0] else DOWN, "text": UP if C[-1] > C[0] else DOWN},
        {"qid": "s02_q2", "kind": "argmax", "pair": None, "nonumbers": True,
         "prompt": {"en": "answer en in which year were the most bicycle thefts reported?",
                    "tr": "answer tr en çok bisiklet hırsızlığı hangi yıl bildirildi?"},
         "visual": {lg: year(argmax(V)) for lg in LANGS}, "text": {lg: year(argmax(C)) for lg in LANGS}},
        {"qid": "s02_q3", "kind": "argmin", "pair": None, "nonumbers": True,
         "prompt": {"en": "answer en in which year were the fewest bicycle thefts reported?",
                    "tr": "answer tr en az bisiklet hırsızlığı hangi yıl bildirildi?"},
         "visual": {lg: year(argmin(V)) for lg in LANGS}, "text": {lg: year(argmin(C)) for lg in LANGS}},
        {"qid": "s02_q4a", "kind": "compare", "pair": "s02_p1", "nonumbers": True,
         "prompt": {"en": f"answer en were more bicycle thefts reported in {B} than in {A}?",
                    "tr": f"answer tr {B}'te {A}'den daha fazla bisiklet hırsızlığı bildirildi mi?"},
         "visual": yn(V[-1] > V[0]), "text": yn(C[-1] > C[0])},
        {"qid": "s02_q4b", "kind": "compare", "pair": "s02_p1", "nonumbers": True,
         "prompt": {"en": f"answer en were fewer bicycle thefts reported in {B} than in {A}?",
                    "tr": f"answer tr {B}'te {A}'den daha az bisiklet hırsızlığı bildirildi mi?"},
         "visual": yn(V[-1] < V[0]), "text": yn(C[-1] < C[0])},
    ],
}
assert (A, B) == (2018, 2025), "Turkish suffixes ('den / 'e / 'te) are written for 2018 and 2025"


if __name__ == "__main__":
    for cond in CONDS:
        for lang in LANGS:
            save_image(draw(cond, lang), name(SID, cond, lang))
    finish(SPEC)
