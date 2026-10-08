"""s08 — phone photo of a printed academic paper page with a grouped bar chart.

Pipeline: matplotlib draws Figure 2 (grouped bars, value labels, no y numbers) as SVG → the SVG is inlined in an
HTML two-column paper page (headless Chrome) → PIL turns the screenshot into a "photo of a printout"
(slight perspective, desk strip with shadow, lighting gradient, camera softness, sensor noise).
The photo transform and the noise seed are identical in all 6 versions, so consistent vs conflict differ only
where the printed value labels differ. In `conflict` the labels are permuted within each benchmark; in
`nonumbers` the value labels are drawn as empty strings at the same positions (bars, names, brackets, caption
and body text untouched), so only the drawing carries the values.

Neutral naming and order (no third cue): the methods have coined names that imply no ownership, size or rank
(no Base/Ours, no -S/-L), the body text calls none of them a baseline or the contribution, and the drawing order
is not sorted by height (tallest bar in the middle, shortest on the right), so neither a name prior nor a
"proposed method last / sorted ascending" position prior predicts the visual answers.
"""
import io
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from PIL import Image, ImageFilter  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
from lib import CONDS, IMAGES, LANGS, SIZE, finish, fmt_num, name, render_html, save_image  # noqa: E402
from answers import NO, YES, num_accept  # noqa: E402

SID = "s08_paper_grouped_bars"
METHODS = ["Roan", "Kerf", "Ossel"]                         # drawing order; identical in en and tr (they appear in answers)
BENCH = ["Quorlet", "Harnwick"]                             # coined benchmark names (no real dataset or model; web-checked 2026-10-04)
VISUAL = {"Quorlet": [64, 78, 52], "Harnwick": [47, 69, 41]}     # bar heights = printed labels in `consistent`
CONFLICT = {"Quorlet": [78, 52, 64], "Harnwick": [69, 41, 47]}   # printed labels in `conflict` (rotation by one)
LABELS = {"consistent": VISUAL, "conflict": CONFLICT, "nonumbers": None}   # None = value labels blanked
for b in BENCH:
    assert sorted(VISUAL[b]) == sorted(CONFLICT[b]), "conflict must be a permutation"

# categorical bar colours of similar lightness (L* 59-64): colour encodes method only, never value/direction
COLORS = {"Roan": "#6f8fc0", "Kerf": "#b8955a", "Ossel": "#ac8bb0"}

T = {
    "en": dict(
        header_l="Workshop on Grounded Visual Reasoning, 2026", header_r="6",
        ylabel="Accuracy (%)",
        caption="<b>Figure 2:</b> Accuracy (%) of three methods on two benchmarks. "
                "Each bar is the mean of three training runs on the held-out test split.",
        section="4.2&ensp;Benchmarks and protocol",
        body=["Quorlet contains ren&shy;dered indoor scenes paired with tem&shy;plated questions about the number, "
              "colour and po&shy;si&shy;tion of objects. Harnwick pairs crops of printed town maps with questions "
              "about routes, street names and distances.",
              "The three methods share the same image encoder and are trained for the same number of steps. "
              "They differ only in the output head, which is described in Section&nbsp;3.",
              "Accuracy is the share of test questions answered with an exact match. Test splits are kept "
              "apart from the training data, and every run uses a fixed random seed."]),
    "tr": dict(
        header_l="Görsel Akıl Yürütme Çalıştayı, 2026", header_r="6",
        ylabel="Doğruluk (%)",
        caption="<b>Şekil 2:</b> Üç yöntemin iki değerlendirme kümesindeki doğruluğu (%). "
                "Her çubuk, ayrılmış test bölümünde üç eğitim koşusunun ortalamasıdır.",
        section="4.2&ensp;Veri kümeleri ve protokol",
        body=["Quorlet, bilgisayarda üretilmiş iç mekân sahnelerini nesnelerin sayısı, rengi ve konumu üzerine "
              "şablon sorularla eşleştirir. Harnwick ise basılı kasaba haritası kesitleri kullanır ve rotalar, "
              "sokak adları ve mesafeler hakkında sorular sorar.",
              "Üç yöntem de aynı görüntü kodlayıcıyı paylaşır ve aynı sayıda adım boyunca eğitilir. Yalnızca "
              "üçüncü bölümde anlatılan çıktı katmanında ayrılırlar.",
              "Doğruluk, test sorularından tam eşleşmeyle yanıtlananların oranıdır. Test bölümleri eğitim "
              "verisinden ayrı tutulur ve her koşuda sabit bir rastgele tohum kullanılır."]),
}

# ---------- Figure 2 (matplotlib → SVG, drawn in a pixel coordinate system) ----------
FW, FH = 804, 432            # figure size in px (as placed on the page)
BASE = 98                    # baseline height from the figure bottom
K = 3.75                     # px per accuracy point (78 → 292 px)
BW, GAP = 84, 12             # bar width, gap between bars of a group
GROUP_CX = [244, 616]        # group centres
DPI = 100
plt.rcParams["svg.fonttype"] = "path"
plt.rcParams["svg.hashsalt"] = SID


def check_turkish_glyphs():
    """Every font face used (page: Times New Roman; figure: DejaVu Sans) must cover ş ğ ı İ ç ö ü."""
    from fontTools.ttLib import TTFont
    from matplotlib.font_manager import findfont
    sup = "/System/Library/Fonts/Supplemental/"
    faces = [sup + f"Times New Roman{s}.ttf" for s in ("", " Bold", " Italic")]
    faces += [findfont(FontProperties(family="DejaVu Sans", weight=w), fallback_to_default=False) for w in ("normal", "bold")]
    for f in faces:
        cmap = TTFont(f).getBestCmap()
        missing = [c for c in "şğıİçöüŞĞÇÖÜâ" if ord(c) not in cmap]
        assert not missing, f"{f} lacks {missing}"


check_turkish_glyphs()


def pt(px):
    return px * 72 / DPI


def fp(px, bold=False):
    return FontProperties(family="DejaVu Sans", weight="bold" if bold else "normal", size=pt(px))


def bar_x(g, i):
    return GROUP_CX[g] + (i - 1) * (BW + GAP)


def figure_svg(cond, lang):
    labels = LABELS[cond]
    fig = plt.figure(figsize=(FW / DPI, FH / DPI), dpi=DPI)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, FW)
    ax.set_ylim(0, FH)
    ax.axis("off")
    for g, b in enumerate(BENCH):
        for i, m in enumerate(METHODS):
            x, h = bar_x(g, i), VISUAL[b][i] * K
            ax.add_patch(plt.Rectangle((x - BW / 2, BASE), BW, h, fc=COLORS[m], ec="#1b1b1b", lw=pt(1.3), zorder=2))
            s = fmt_num(labels[b][i], lang) if labels else ""          # nonumbers: same text element, empty
            ax.text(x, BASE + h + 9, s, ha="center", va="baseline",
                    fontproperties=fp(28, bold=True), color="#111111", zorder=3)
            ax.text(x, BASE - 30, m, ha="center", va="baseline", fontproperties=fp(23), color="#1b1b1b")
        x0, x1 = bar_x(g, 0) - BW / 2, bar_x(g, 2) + BW / 2       # bracket under the group
        yb = BASE - 44
        ax.plot([x0, x0, x1, x1], [yb + 7, yb, yb, yb + 7], color="#555555", lw=pt(1.3), solid_joinstyle="miter")
        ax.text(GROUP_CX[g], BASE - 80, b, ha="center", va="baseline", fontproperties=fp(23, bold=True),
                color="#111111")
    ax.plot([40, FW - 4], [BASE, BASE], color="#111111", lw=pt(1.8), solid_capstyle="butt", zorder=4)
    ax.text(18, BASE + 150, T[lang]["ylabel"], rotation=90, ha="center", va="center",
            fontproperties=fp(21), color="#1b1b1b")
    buf = io.StringIO()
    fig.savefig(buf, format="svg", transparent=True)
    plt.close(fig)
    svg = buf.getvalue()
    svg = svg[svg.index("<svg"):]
    svg = re.sub(r'width="[\d.]+pt" height="[\d.]+pt"', f'width="{FW}" height="{FH}"', svg, count=1)
    return svg


# ---------- the paper page (HTML) ----------
NO_HYPHEN = METHODS + BENCH


def protect(s):
    """Justified columns use the browser's hyphenation, but names must never be split."""
    for w in NO_HYPHEN:
        s = s.replace(w, f'<span class="nh">{w}</span>')
    return s


def page(cond, lang):
    t = T[lang]
    body = "".join(f"<p>{protect(p)}</p>" for p in t["body"])
    return f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{ width: 896px; height: 896px; overflow: hidden; }}
  body {{ background: #ffffff; color: #111; font-family: "Times New Roman", Times, serif; padding: 26px 46px 0 46px; }}
  .hdr {{ display: flex; justify-content: space-between; font-size: 21px; font-style: italic; color: #333;
          border-bottom: 1px solid #333; padding-bottom: 6px; }}
  .hdr span:last-child {{ font-style: normal; }}
  figure {{ margin-top: 16px; }}
  svg {{ display: block; }}
  figcaption {{ margin-top: 6px; font-size: 22px; line-height: 1.3; text-align: justify; }}
  h2 {{ font-size: 23px; font-weight: 700; margin-bottom: 6px; }}
  .cols {{ margin-top: 20px; column-count: 2; column-gap: 34px; font-size: 22px; line-height: 1.33;
           text-align: justify; hyphens: auto; orphans: 1; widows: 1; }}
  .nh {{ hyphens: none; white-space: nowrap; }}
  .cols p {{ text-indent: 1.1em; }}
  .cols h2 + p {{ text-indent: 0; }}
</style></head><body>
  <div class="hdr"><span>{t["header_l"]}</span><span>{t["header_r"]}</span></div>
  <figure>
    {figure_svg(cond, lang)}
    <figcaption>{t["caption"]}</figcaption>
  </figure>
  <div class="cols"><h2>{t["section"]}</h2>{body}</div>
</body></html>"""


# ---------- photo-of-a-printout transform (identical for all 6 versions) ----------
# where the four page corners land in the photo (TL, TR, BR, BL): ≤ 1° rotation, mild keystone, desk strip on the left
QUAD = [(30, -12), (912, -2), (902, 910), (44, 902)]
SEED = 8


def perspective_coeffs(dst, src):
    """PIL PERSPECTIVE data mapping output points `dst` back to input points `src`."""
    a, bvec = [], []
    for (x, y), (u, v) in zip(dst, src):
        a.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); bvec.append(u)
        a.append([0, 0, 0, x, y, 1, -v * x, -v * y]); bvec.append(v)
    return np.linalg.solve(np.array(a, float), np.array(bvec, float)).tolist()


def _fields():
    rng = np.random.default_rng(SEED)
    yy, xx = np.mgrid[0:SIZE, 0:SIZE] / (SIZE - 1)
    # light from the upper right: brighter there, falling off towards the lower left, soft vignette
    light = (1.0 + 0.03 * xx - 0.08 * yy
             + 0.045 * np.exp(-((xx - 0.72) ** 2 + (yy - 0.15) ** 2) / 0.14)
             - 0.10 * ((xx - 0.5) ** 2 + (yy - 0.5) ** 2))
    # desk: dark neutral wood-ish surface, fine grain running along the strip, slightly out of focus
    streaks = Image.fromarray((rng.random((10, 260)) * 255).astype(np.uint8)).resize((SIZE, SIZE), Image.BICUBIC)
    blotch = Image.fromarray((rng.random((5, 5)) * 255).astype(np.uint8)).resize((SIZE, SIZE), Image.BICUBIC)
    grain = (0.6 * np.asarray(streaks.filter(ImageFilter.GaussianBlur(1.2)), float)
             + 0.4 * np.asarray(blotch, float)) / 255
    desk = np.array([66, 61, 56], float)[None, None, :] * (0.88 + 0.22 * grain[..., None])
    noise = rng.normal(0, 3.0, (SIZE, SIZE, 1)) + rng.normal(0, 1.2, (SIZE, SIZE, 3))
    return light, desk, noise


LIGHT, DESK, NOISE = _fields()
WARM = np.array([1.0, 0.975, 0.935])


def photo(img):
    src = [(0, 0), (SIZE, 0), (SIZE, SIZE), (0, SIZE)]
    coeffs = perspective_coeffs(QUAD, src)
    warped = np.asarray(img.convert("RGB").transform((SIZE, SIZE), Image.PERSPECTIVE, coeffs, Image.BICUBIC,
                                                     fillcolor=(0, 0, 0)), float)
    mask_img = Image.new("L", (SIZE, SIZE), 255).transform((SIZE, SIZE), Image.PERSPECTIVE, coeffs, Image.BILINEAR,
                                                           fillcolor=0)
    mask = np.asarray(mask_img, float)[..., None] / 255
    shadow = np.asarray(mask_img.transform((SIZE, SIZE), Image.AFFINE, (1, 0, 7, 0, 1, -4))   # cast to the left
                        .filter(ImageFilter.GaussianBlur(7)), float)[..., None] / 255
    desk = DESK * (1 - 0.5 * shadow)
    comp = warped * mask + desk * (1 - mask)
    comp = np.asarray(Image.fromarray(np.clip(comp, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.5)),
                      float)
    comp = comp * LIGHT[..., None] * WARM[None, None, :] + NOISE
    return Image.fromarray(np.clip(comp, 0, 255).astype(np.uint8))


# ---------- questions ----------
def method(m):
    toks = m.lower()
    return list(dict.fromkeys([toks, toks.replace("-", " "), toks.replace("-", "")]))


def argmax(v):
    return max(range(len(v)), key=v.__getitem__)


def argmin(v):
    return min(range(len(v)), key=v.__getitem__)


def ans_method(i):
    return {lg: method(METHODS[i]) for lg in LANGS}


def yn(flag):
    """Shared yes/no accept lists (common/answers.py), chosen from the data."""
    return {lg: list((YES if flag else NO)[lg]) for lg in LANGS}


def num(n):
    return {lg: num_accept(n, lg) for lg in LANGS}


iR, iK, iO = (METHODS.index(m) for m in ("Roan", "Kerf", "Ossel"))
VQ, CQ = VISUAL["Quorlet"], CONFLICT["Quorlet"]
VH, CH = VISUAL["Harnwick"], CONFLICT["Harnwick"]
assert argmax(VQ) != argmax(CQ) and argmin(VH) != argmin(CH)
assert (VH[iK] > VH[iO]) != (CH[iK] > CH[iO])
# no position prior lines up with the drawing: tallest bar never rightmost, shortest never leftmost
for b in BENCH:
    assert argmax(VISUAL[b]) != len(METHODS) - 1 and argmin(VISUAL[b]) != 0, b
# q4 target (Roan on Quorlet, an end bar): its visual value is printed two bars away, never on its neighbour,
# so misreading the neighbouring label scores as "neither", not as "visual"
assert CQ[iO] == VQ[iR] and abs(iO - iR) == 2 and CQ[iK] != VQ[iR] and CQ[iR] != VQ[iR]

SPEC = {
    "id": SID,
    "title": {"en": "Accuracy of three methods on two benchmarks (photographed paper page)",
              "tr": "Üç yöntemin iki veri kümesindeki doğruluğu (fotoğraflanmış makale sayfası)"},
    "chart": "grouped bars", "style": "photographed page of an academic paper",
    "tech": "matplotlib SVG figure inlined in an HTML page (headless Chrome) + PIL photo effect",
    "mechanism": "label",
    "conflict_summary": "Bars drawn Roan/Kerf/Ossel: Kerf (middle) is tallest and Ossel (right) shortest on both "
                        "benchmarks; in conflict the printed labels are rotated by one within each benchmark "
                        "(Quorlet 78/52/64, Harnwick 69/41/47), so the labels make Roan best and Kerf worst, "
                        "and put Kerf below Ossel on Harnwick.",
    "data": {"methods": METHODS, "benchmarks": BENCH, "visual": VISUAL, "conflict_labels": CONFLICT,
             "photo_quad_tl_tr_br_bl": QUAD, "noise_seed": SEED},
    "questions": [
        {"qid": "s08_q1", "kind": "argmax", "pair": None,
         "prompt": {"en": "answer en which method has the highest accuracy on quorlet?",
                    "tr": "answer tr quorlet'te en yüksek doğruluğu hangi yöntem elde ediyor?"},
         "visual": ans_method(argmax(VQ)), "text": ans_method(argmax(CQ)),
         "nonumbers": True},          # tallest bar in the Quorlet group is visible without labels
        {"qid": "s08_q2", "kind": "argmin", "pair": None,
         "prompt": {"en": "answer en which method has the lowest accuracy on harnwick?",
                    "tr": "answer tr harnwick'te en düşük doğruluğu hangi yöntem elde ediyor?"},
         "visual": ans_method(argmin(VH)), "text": ans_method(argmin(CH)),
         "nonumbers": True},          # shortest bar in the Harnwick group is visible without labels
        {"qid": "s08_q3a", "kind": "compare", "pair": "s08_p1",
         # minimal-pair wording: q3a/q3b differ only in higher/lower (yüksek/düşük)
         "prompt": {"en": "answer en does kerf score higher than ossel on harnwick?",
                    "tr": "answer tr harnwick'te kerf, ossel'den daha yüksek puan alıyor mu?"},
         "visual": yn(VH[iK] > VH[iO]), "text": yn(CH[iK] > CH[iO]),
         "nonumbers": True},          # bar heights compare directly (69 vs 41 → 105 px apart)
        {"qid": "s08_q3b", "kind": "compare", "pair": "s08_p1",
         "prompt": {"en": "answer en does kerf score lower than ossel on harnwick?",
                    "tr": "answer tr harnwick'te kerf, ossel'den daha düşük puan alıyor mu?"},
         "visual": yn(VH[iK] < VH[iO]), "text": yn(CH[iK] < CH[iO]),
         "nonumbers": True},          # same pair, same flag
        {"qid": "s08_q4", "kind": "read_value", "pair": None,
         "prompt": {"en": "answer en what is the accuracy of roan on quorlet?",
                    "tr": "answer tr quorlet'te roan yönteminin doğruluğu kaç?"},
         "visual": num(VQ[iR]), "text": num(CQ[iR]),
         "nonumbers": False},         # no y ticks/gridlines: the exact value was only in the removed label
    ],
}

if __name__ == "__main__":
    for cond in CONDS:
        for lang in LANGS:
            n = name(SID, cond, lang)
            render_html(page(cond, lang), n)                 # flat page → images/<n>.png
            save_image(photo(Image.open(IMAGES / f"{n}.png")), n)   # overwritten with the photographed version
    finish(SPEC)
