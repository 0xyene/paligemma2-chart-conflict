"""s13 — phone home screen with a 'Batteries' widget: four radial progress rings (inline SVG in HTML).

Ring arc length encodes the real charge; the percentage printed in each ring centre is the cue text.
In `conflict` the percentages are permuted (Phone 88<->9 Earbuds, Watch 54<->31 Tablet), the rings stay put.
In `nonumbers` the centre <text> is kept but rendered empty (rings, glyphs, device names unchanged).
Square canvas = inner screen of a foldable phone. The status bar deliberately has NO battery icon
(it would be a second, agreeing visual cue for the phone).
Answers use the shared lists in common/answers.py: YES/NO for the q3 pair, num_accept() for q4.
Turkish device lists hold Turkish words only (plus brand names that are identical in both languages).
q1/q2 TR prompts are worded in parallel ("şarjı en az / en çok kaldı") so the argmin/argmax pair differs in one word.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
from lib import CONDS, LANGS, finish, fmt_pct, name, render_html  # noqa: E402
from answers import NO, YES, num_accept  # noqa: E402

SID = "s13_widget_battery"
DEVICES = ["phone", "earbuds", "watch", "tablet"]               # drawing order, left to right
VISUAL = [88, 9, 54, 31]                                        # ring fill = printed % in `consistent`
CONFLICT = [9, 88, 31, 54]                                      # printed % in `conflict` (swap 1<->2, 3<->4)
PCT = {"consistent": VISUAL, "conflict": CONFLICT, "nonumbers": [None] * 4}   # None = empty centre text

T = {
    "en": dict(clock="14:27", title="Batteries",
               dev={"phone": "Phone", "earbuds": "Earbuds", "watch": "Watch", "tablet": "Tablet"},
               apps=["Photos", "Calendar", "Notes", "Maps", "Mail", "Files",
                     "Music", "Contacts", "Translate", "Recorder", "Books", "Settings"]),
    "tr": dict(clock="14:27", title="Piller",
               dev={"phone": "Telefon", "earbuds": "Kulaklık", "watch": "Saat", "tablet": "Tablet"},
               apps=["Fotoğraflar", "Takvim", "Notlar", "Haritalar", "Posta", "Dosyalar",
                     "Müzik", "Kişiler", "Çeviri", "Ses Kaydı", "Kitaplar", "Ayarlar"]),
}

RING = "#353a57"        # one neutral ink for every ring (no low-battery colour)
TRACK = "#dedce8"

# device glyphs in the ring centre, 24x24 viewBox, stroked/filled with the ring ink
DEV_GLYPH = {
    "phone": '<rect x="7" y="2.2" width="10" height="19.6" rx="2.6" fill="none" stroke="C" stroke-width="2"/>'
             '<path d="M10.6 18.4h2.8" stroke="C" stroke-width="1.8" stroke-linecap="round"/>',
    "earbuds": '<circle cx="7" cy="7.6" r="3.6" fill="C"/><path d="M8.4 9.6v9.4" stroke="C" stroke-width="2.6" stroke-linecap="round"/>'
               '<circle cx="17" cy="7.6" r="3.6" fill="C"/><path d="M15.6 9.6v9.4" stroke="C" stroke-width="2.6" stroke-linecap="round"/>',
    "watch": '<path d="M8.6 6V2.4h6.8V6M8.6 18v3.6h6.8V18" fill="none" stroke="C" stroke-width="2" stroke-linejoin="round"/>'
             '<rect x="5.6" y="6" width="12.8" height="12" rx="3.6" fill="none" stroke="C" stroke-width="2"/>',
    "tablet": '<rect x="3.6" y="2.6" width="16.8" height="18.8" rx="2.4" fill="none" stroke="C" stroke-width="2"/>'
              '<circle cx="12" cy="18.2" r="1" fill="C"/>',
}

# fictional app icons: background colour + white glyph (24x24 viewBox)
W_ = 'fill="none" stroke="#fff" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"'
APP_ICONS = [
    ("#5f6f94", f'<rect x="3" y="4.5" width="18" height="15" rx="2.5" {W_}/><path d="M3.5 17l5-5.5 4 4 2.5-2.5 5.5 5" {W_}/><circle cx="15.8" cy="8.8" r="1.6" fill="#fff"/>'),
    ("#f4f2f7", '<rect x="3.5" y="4.5" width="17" height="16" rx="2.5" fill="none" stroke="#4a4f6b" stroke-width="1.9"/>'
                '<path d="M3.5 9h17" stroke="#4a4f6b" stroke-width="1.9"/><path d="M8 2.8v3.4M16 2.8v3.4" stroke="#4a4f6b" stroke-width="1.9" stroke-linecap="round"/>'
                + "".join(f'<circle cx="{7.5 + 3 * (i % 4):.1f}" cy="{12.5 + 3.5 * (i // 4):.1f}" r="0.95" fill="#4a4f6b"/>' for i in range(8))),
    ("#8a7a5f", f'<rect x="5" y="3" width="14" height="18" rx="2" {W_}/><path d="M8.5 8h7M8.5 12h7M8.5 16h4.5" {W_}/>'),
    ("#56738a", f'<path d="M3 6.5l5.5-2.5 7 2.5 5.5-2.5v13.5l-5.5 2.5-7-2.5-5.5 2.5z" {W_}/><path d="M8.5 4v13.5M15.5 6.5V20" {W_}/>'),
    ("#4f5ba0", f'<rect x="3" y="5.5" width="18" height="13" rx="2" {W_}/><path d="M3.8 6.5l8.2 6.5 8.2-6.5" {W_}/>'),
    ("#7a8aa6", f'<path d="M3 7.5a2 2 0 0 1 2-2h4.2l2 2.2H19a2 2 0 0 1 2 2v7.8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" {W_}/>'),
    ("#6a4f86", '<path d="M9.5 17.5V5.5l10-2v12" fill="none" stroke="#fff" stroke-width="1.9" stroke-linejoin="round"/>'
                '<circle cx="7.2" cy="17.6" r="2.6" fill="#fff"/><circle cx="17.2" cy="15.6" r="2.6" fill="#fff"/>'),
    ("#8f8a99", f'<circle cx="12" cy="9" r="3.6" {W_}/><path d="M5 20c.8-3.8 3.6-5.8 7-5.8s6.2 2 7 5.8" {W_}/>'),
    ("#3f6f86", f'<rect x="2.8" y="3.5" width="11" height="10" rx="2" {W_}/><rect x="10.2" y="10.5" width="11" height="10" rx="2" fill="#3f6f86" stroke="#fff" stroke-width="1.9"/>'
                f'<path d="M5.8 11l2.5-5.5 2.5 5.5M6.8 9h3" {W_}/>'),
    ("#2f3446", f'<rect x="8.8" y="3" width="6.4" height="11" rx="3.2" {W_}/><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21" {W_}/>'),
    ("#9a7f6a", f'<path d="M12 6.5c-2.2-1.6-5-2-8-1.8v13.5c3-.2 5.8.2 8 1.8 2.2-1.6 5-2 8-1.8V4.7c-3-.2-5.8.2-8 1.8zM12 6.5v13.5" {W_}/>'),
    ("#6f7180", f'<circle cx="12" cy="12" r="3" {W_}/>'
                + "".join(f'<path d="M{12 + 6.2 * math.cos(a):.2f} {12 + 6.2 * math.sin(a):.2f}L{12 + 8.6 * math.cos(a):.2f} {12 + 8.6 * math.sin(a):.2f}" stroke="#fff" stroke-width="2.6" stroke-linecap="round"/>'
                          for a in [k * math.pi / 4 for k in range(8)])
                + f'<circle cx="12" cy="12" r="6.2" {W_}/>'),
]
DOCK_ICONS = [
    ("#4f6a8a", '<path d="M7.2 3.5l2.6 4.2-1.9 2.3a12 12 0 0 0 6.1 6.1l2.3-1.9 4.2 2.6-.9 3.2c-.3.9-1.2 1.5-2.1 1.4C10.3 20.8 3.2 13.7 2.6 6.5c-.1-.9.5-1.8 1.4-2.1z" fill="#fff"/>'),
    ("#5c5f9e", '<path d="M12 4c5 0 9 3.2 9 7.2s-4 7.2-9 7.2c-1 0-2-.1-2.9-.4L5 20l1-3.6C4.2 15.1 3 13.2 3 11.2 3 7.2 7 4 12 4z" fill="#fff"/>'),
    ("#f4f2f7", '<circle cx="12" cy="12" r="8.8" fill="none" stroke="#4a4f6b" stroke-width="1.9"/>'
                '<path d="M15.8 8.2l-2.4 5.2-5.2 2.4 2.4-5.2z" fill="#4a4f6b"/>'),
    ("#3b3e4f", f'<path d="M4 8.5a2 2 0 0 1 2-2h2.2l1.5-2h4.6l1.5 2H18a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z" {W_}/><circle cx="12" cy="13" r="3.4" {W_}/>'),
]


def status_bar(t):
    bars = "".join(f'<rect x="{i * 7}" y="{14 - 4 - i * 3.3:.1f}" width="5" height="{4 + i * 3.3:.1f}" rx="1.2" fill="#fff"/>'
                   for i in range(4))
    wifi = ('<path d="M1 6.5a14 14 0 0 1 20 0" stroke="#fff" stroke-width="2.2" fill="none" stroke-linecap="round"/>'
            '<path d="M4.6 10.2a9 9 0 0 1 12.8 0" stroke="#fff" stroke-width="2.2" fill="none" stroke-linecap="round"/>'
            '<path d="M8.2 13.8a4 4 0 0 1 5.6 0L11 16.6z" fill="#fff"/>')
    return (f'<div class="status"><span class="clock">{t["clock"]}</span><span class="sicons">'
            f'<svg width="27" height="14" viewBox="0 0 27 14">{bars}</svg>'
            f'<svg width="22" height="17" viewBox="0 0 22 17">{wifi}</svg></span></div>')


def ring_svg(dev, v, label):
    """One radial ring: 164 px, stroke 18; arc length from VISUAL only, centre text = cue."""
    s, sw = 164, 18
    r = (s - sw) / 2
    c = 2 * math.pi * r
    arc = c * v / 100
    g = DEV_GLYPH[dev].replace('"C"', f'"{RING}"')
    return f"""<svg width="{s}" height="{s}" viewBox="0 0 {s} {s}" xmlns="http://www.w3.org/2000/svg">
      <circle cx="{s / 2}" cy="{s / 2}" r="{r}" fill="none" stroke="{TRACK}" stroke-width="{sw}"/>
      <circle cx="{s / 2}" cy="{s / 2}" r="{r}" fill="none" stroke="{RING}" stroke-width="{sw}" stroke-linecap="round"
              stroke-dasharray="{arc:.2f} {c:.2f}" transform="rotate(-90 {s / 2} {s / 2})"/>
      <svg x="{s / 2 - 15}" y="{s / 2 - 46}" width="30" height="30" viewBox="0 0 24 24">{g}</svg>
      <text x="{s / 2}" y="{s / 2 + 33}" text-anchor="middle" class="pct">{label}</text>
    </svg>"""


def icon(bg, glyph, size, label=None):
    lab = f'<div class="alab">{label}</div>' if label is not None else ""
    return (f'<div class="app"><div class="ico" style="width:{size}px;height:{size}px;background:{bg}">'
            f'<svg width="{size * 0.56:.0f}" height="{size * 0.56:.0f}" viewBox="0 0 24 24">{glyph}</svg></div>{lab}</div>')


def page(cond, lang):
    t = T[lang]
    rings = "".join(f'<div class="cell">{ring_svg(d, v, "" if p is None else fmt_pct(p, lang))}<div class="dname">{t["dev"][d]}</div></div>'
                    for d, v, p in zip(DEVICES, VISUAL, PCT[cond]))
    grid = "".join(icon(bg, g, 94, lab) for (bg, g), lab in zip(APP_ICONS, t["apps"]))
    dock = "".join(icon(bg, g, 88) for bg, g in DOCK_ICONS)
    return f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{ width: 896px; height: 896px; overflow: hidden; }}
  body {{ position: relative; font-family: Seravek, "Gill Sans", "Helvetica Neue", sans-serif; color: #fff;
          -webkit-font-smoothing: antialiased;
          background:
            radial-gradient(circle at 18% 24%, rgba(186,176,214,.55) 0, rgba(186,176,214,0) 38%),
            radial-gradient(circle at 86% 58%, rgba(214,196,178,.55) 0, rgba(214,196,178,0) 42%),
            radial-gradient(circle at 30% 92%, rgba(120,128,160,.55) 0, rgba(120,128,160,0) 40%),
            linear-gradient(160deg, #6f6a8f 0%, #857d97 45%, #9c8f8f 100%); }}
  .status {{ position: absolute; left: 0; right: 0; top: 0; height: 58px; padding: 0 50px; display: flex;
             align-items: center; justify-content: space-between; }}
  .clock {{ font-size: 25px; font-weight: 600; letter-spacing: .3px; }}
  .sicons {{ display: flex; align-items: center; gap: 10px; }}
  .widget {{ position: absolute; left: 40px; top: 70px; width: 816px; height: 326px; border-radius: 44px;
             background: rgba(250,249,252,.86); box-shadow: 0 10px 34px rgba(40,36,60,.22); color: #23242f;
             padding: 24px 0 0; }}
  .wt {{ font-size: 27px; font-weight: 600; padding: 0 38px; letter-spacing: .2px; }}
  .rings {{ display: flex; margin-top: 14px; padding: 0 20px; }}
  .cell {{ width: 194px; display: flex; flex-direction: column; align-items: center; }}
  .pct {{ font-family: Seravek, "Gill Sans", sans-serif; font-size: 40px; font-weight: 700; fill: #1d1e29;
          font-variant-numeric: tabular-nums; }}
  .dname {{ font-size: 25px; font-weight: 500; color: #3a3b48; margin-top: 10px; }}
  .grid {{ position: absolute; left: 40px; top: 428px; width: 816px; display: grid;
           grid-template-columns: repeat(6, 136px); row-gap: 22px; }}
  .app {{ display: flex; flex-direction: column; align-items: center; }}
  .ico {{ border-radius: 24px; display: flex; align-items: center; justify-content: center;
          box-shadow: 0 3px 10px rgba(30,28,45,.18); }}
  .alab {{ margin-top: 8px; font-size: 20px; font-weight: 500; white-space: nowrap;
           text-shadow: 0 1px 3px rgba(20,18,30,.45); }}
  .dots {{ position: absolute; left: 0; right: 0; top: 734px; display: flex; justify-content: center; gap: 12px; }}
  .dots i {{ width: 10px; height: 10px; border-radius: 5px; background: rgba(255,255,255,.45); }}
  .dots i:first-child {{ background: #fff; }}
  .dock {{ position: absolute; left: 40px; top: 764px; width: 816px; height: 114px; border-radius: 40px;
           background: rgba(255,255,255,.26); display: flex; align-items: center; justify-content: space-evenly; }}
  .dock .ico {{ border-radius: 23px; }}
</style></head><body>
  {status_bar(t)}
  <div class="widget"><div class="wt">{t["title"]}</div><div class="rings">{rings}</div></div>
  <div class="grid">{grid}</div>
  <div class="dots"><i></i><i></i><i></i></div>
  <div class="dock">{dock}</div>
</body></html>"""


# ---------- questions ----------
ANS = {   # accepted short answers per device; tr = Turkish words + brand names (identical in en and tr)
    "phone": {"en": ["phone", "smartphone", "mobile", "cellphone", "iphone"],
              "tr": ["telefon", "akıllı telefon", "cep telefonu", "iphone"]},
    "earbuds": {"en": ["earbuds", "earbud", "earphones", "earphone", "headphones", "headphone", "buds", "airpods", "headset"],
                "tr": ["kulaklık", "kulak", "airpods"]},
    "watch": {"en": ["watch", "smartwatch"], "tr": ["saat", "akıllı saat"]},
    "tablet": {"en": ["tablet", "ipad"], "tr": ["tablet", "ipad"]},
}
PCT_WORDS = {"en": "^{w} percent", "tr": "^yüzde {w}"}     # q4 asks "what percentage" / "yüzde kaç?"
PCT_DIGITS = {"en": ["{v}%", "{v} percent"], "tr": ["%{v}", "yüzde {v}"]}


def pct_num(v):
    """Digits (by value, anywhere) + whole-answer number words from num_accept, plus the percent forms."""
    out = {}
    for lang in LANGS:
        words = [a[1:] for a in num_accept(v, lang) if a.startswith("^")]
        extra = [f.format(v=v) for f in PCT_DIGITS[lang]] + [PCT_WORDS[lang].format(w=w) for w in words]
        out[lang] = num_accept(v, lang, extra=extra)
    return out


def dev_at(values, pick):
    return DEVICES[values.index(pick(values))]


VIS_MIN, TXT_MIN = dev_at(VISUAL, min), dev_at(CONFLICT, min)        # earbuds / phone
VIS_MAX, TXT_MAX = dev_at(VISUAL, max), dev_at(CONFLICT, max)        # phone / earbuds
PHONE_VIS, PHONE_TXT = VISUAL[0], CONFLICT[0]
assert PHONE_VIS >= 80 and PHONE_TXT <= 15                            # "almost full" visually, "almost empty" in text
W_VIS, W_TXT = VISUAL[2], CONFLICT[2]
assert len({VIS_MIN, TXT_MIN}) == 2 and len({VIS_MAX, TXT_MAX}) == 2 and W_VIS != W_TXT

SPEC = {
    "id": SID,
    "title": {"en": "Batteries widget on a phone home screen", "tr": "Telefon ana ekranında Piller widget'ı"},
    "chart": "radial progress rings", "style": "phone home-screen widget (light, frosted card on soft wallpaper)",
    "tech": "HTML/CSS + inline SVG rings (stroke-dasharray), headless Chrome",
    "mechanism": "label",
    "conflict_summary": "Ring fills Phone 88 / Earbuds 9 / Watch 54 / Tablet 31; in conflict the centre "
                        "percentages read Phone 9 / Earbuds 88 / Watch 31 / Tablet 54.",
    "data": {"devices": [T["en"]["dev"][d] for d in DEVICES], "visual": VISUAL, "conflict_labels": CONFLICT,
             "ring": "starts at 12 o'clock, clockwise, 0-100 % of the circle; no ticks or scale"},
    "questions": [
        {"qid": "s13_q1", "kind": "argmin", "pair": None, "nonumbers": True,
         "prompt": {"en": "answer en which device has the least battery left?",
                    "tr": "answer tr hangi cihazın şarjı en az kaldı?"},
         "visual": ANS[VIS_MIN], "text": ANS[TXT_MIN]},
        {"qid": "s13_q2", "kind": "argmax", "pair": None, "nonumbers": True,
         "prompt": {"en": "answer en which device has the most battery left?",
                    "tr": "answer tr hangi cihazın şarjı en çok kaldı?"},
         "visual": ANS[VIS_MAX], "text": ANS[TXT_MAX]},
        {"qid": "s13_q3a", "kind": "threshold", "pair": "s13_p1", "nonumbers": True,
         "prompt": {"en": "answer en is the phone battery almost empty?",
                    "tr": "answer tr telefonun şarjı bitmek üzere mi?"},
         "visual": NO, "text": YES},
        {"qid": "s13_q3b", "kind": "threshold", "pair": "s13_p1", "nonumbers": True,
         "prompt": {"en": "answer en is the phone battery almost full?",
                    "tr": "answer tr telefonun şarjı neredeyse dolu mu?"},
         "visual": YES, "text": NO},
        {"qid": "s13_q4", "kind": "read_value", "pair": None, "nonumbers": False,
         "prompt": {"en": "answer en what percentage of battery does the watch have?",
                    "tr": "answer tr saatin şarjı yüzde kaç?"},
         "visual": pct_num(W_VIS), "text": pct_num(W_TXT)},
    ],
}

if __name__ == "__main__":
    for cond in CONDS:
        for lang in LANGS:
            render_html(page(cond, lang), name(SID, cond, lang))
    finish(SPEC)
