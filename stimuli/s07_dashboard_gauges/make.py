"""s07 — dark server-monitoring dashboard with three semicircle CPU gauges.

Needle + filled arc show alpha-01 38, beta-02 15, gamma-03 92. In `conflict` only the digital readout under each
gauge changes (rotated: alpha-01 15, beta-02 92, gamma-03 38). Whole page is one inline 896x896 SVG.

Card order is alphabetical (and the hosts table repeats it), so the values are assigned such that card POSITION is not a
third cue: for both cues the argmax is not the first card and the argmin is not the last card (asserted below).
(DESIGN.md originally had visual 92/38/15 left-to-right — strictly falling, so "first card = highest, last = lowest"
would have been scored as `visual` on q1/q2 without looking at a needle.)

The hosts table puts each server name in a bold row next to numbers (address, rack, uptime). A model that binds
"server name -> that row's biggest/smallest number" must not land on either cue, so every numeric column is ordered
alpha > beta > gamma: argmax alpha-01 / argmin gamma-03, while the needles give gamma/beta and the readouts beta/alpha
(asserted below). Round 2 fix: the uptimes used to be 41 d / 27 d / 63 d, which ranked gamma > alpha > beta, the
exact needle order.
Round 3: whole page set in Menlo (monospace) for set-level typography variety; chip widths, table columns and the
status-bar strings were refitted to monospace widths (same in all 4 images). Accept lists use common/answers.py.
`nonumbers`: same page with the three big digital readouts hidden (visibility="hidden", element kept so nothing moves);
gauges, needles, fills, ticks and the constant "0"/"100" end labels stay. q1/q2/q3 answerable from the needles; q4 not.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
from answers import NO, YES, num_accept  # noqa: E402
from lib import CONDS, LANGS, finish, fmt_pct, name, render_html  # noqa: E402

SID = "s07_dashboard_gauges"
SERVERS = ["alpha-01", "beta-02", "gamma-03"]
VISUAL = [38, 15, 92]                                     # needle / fill = readout in `consistent`
CONFLICT = [VISUAL[1], VISUAL[2], VISUAL[0]]              # rotation -> alpha 15, beta 92, gamma 38
READOUT = {"consistent": VISUAL, "conflict": CONFLICT, "nonumbers": VISUAL}   # nonumbers: readout drawn hidden
THRESH = 80                                               # q3 pair: "above/below 80 percent"
THRESH_IDX = SERVERS.index("gamma-03")                    # q3 pair asks about gamma-03 (needle 92 / readout 38)
READ_IDX = SERVERS.index("alpha-01")                      # q4 reads alpha-01 (needle 38 / readout 15); the visual
                                                          # number 38 is printed two cards away (gamma-03), not next door

# host table: neutral, identical in every version (no CPU-related numbers; avoids 15/38/80/92). Every number in it
# falls alpha > beta > gamma, so its argmax/argmin (alpha/gamma) differs from both cues (asserted below).
HOSTS = [("10.0.4.21", "B4", (63, 19)), ("10.0.4.17", "B2", (41, 6)), ("10.0.4.12", "A1", (27, 2))]

T = {
    "en": dict(
        crumbs=["Monitoring", "lab-cluster", "Overview"],
        clock="04 Oct 2026 · 14:20 UTC",
        title="CPU load",
        sub="3 servers · average of the last 5 minutes",
        range="Last 1 hour", refresh="30 s",
        caption="avg. last 5 min",
        hosts="Hosts",
        cols=["Host", "Address", "Rack", "Uptime", "Status"],
        uptime="{d} d {h} h", online="online",
        status_l="Connected · data source: lab-metrics · UTC",
        status_r="Auto-refresh on"),
    "tr": dict(
        crumbs=["İzleme", "lab-cluster", "Genel bakış"],
        clock="04 Eki 2026 · 14:20 UTC",
        title="CPU yükü",
        sub="3 sunucu · son 5 dakikanın ortalaması",
        range="Son 1 saat", refresh="30 sn",
        caption="son 5 dk ortalaması",
        hosts="Sunucular",
        cols=["Sunucu", "Adres", "Kabin", "Çalışma süresi", "Durum"],
        uptime="{d} gün {h} sa", online="çevrimiçi",
        status_l="Bağlı · veri kaynağı: lab-metrics · UTC",
        status_r="Otomatik yenileme açık"),
}

# palette: dark UI, one neutral accent for every gauge (no traffic-light zones)
BG, BAR, PANEL, EDGE = "#0e1218", "#151a23", "#171d27", "#262e3b"
TXT, TXT2, TXT3 = "#e7ebf2", "#a3adbd", "#8a94a6"
ACCENT, TRACK = "#86a0f2", "#2a3241"
# Round 3: one monospace face for the whole dashboard (set-level typography variety: no other stimulus is monospace;
# Avenir Next / DIN were already used by s02-s06/s11). Menlo has real Regular + Bold and covers ş ğ ı İ ç ö ü.
# Its slashed zero only appears in constant text (end label "0", addresses); no readout contains a 0.
MONO = "Menlo, 'PT Mono', monospace"
UI = NUM = MONO


def pol(cx, cy, r, v):
    """Point on the gauge for value v in 0..100 (0 = left end, 100 = right end, arc over the top)."""
    a = math.radians(180 - 1.8 * v)
    return cx + r * math.cos(a), cy - r * math.sin(a)


def arc(cx, cy, r, v0, v1):
    x0, y0 = pol(cx, cy, r, v0)
    x1, y1 = pol(cx, cy, r, v1)
    return f"M{x0:.2f},{y0:.2f} A{r},{r} 0 0 1 {x1:.2f},{y1:.2f}"


def gauge_card(x, y, w, h, server, value, readout, t, lang, cond):
    cx, cy, r, sw = x + w / 2, y + 226, 102, 22
    o = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{PANEL}" stroke="{EDGE}" stroke-width="1.5"/>',
         f'<text x="{x + 20}" y="{y + 42}" font-family="{MONO}" font-size="24" font-weight="700" fill="{TXT}">{server}</text>']
    for k in range(3):                                    # kebab menu
        o.append(f'<circle cx="{x + w - 22}" cy="{y + 24 + 9 * k}" r="2.6" fill="{TXT3}"/>')
    o.append(f'<line x1="{x + 1}" y1="{y + 62}" x2="{x + w - 1}" y2="{y + 62}" stroke="{EDGE}" stroke-width="1.5"/>')
    for v in range(10, 100, 10):                          # unlabeled ticks outside the arc (none at the ends: they read as "−")
        x0, y0 = pol(cx, cy, r + sw / 2 + 5, v)
        x1, y1 = pol(cx, cy, r + sw / 2 + (13 if v % 50 == 0 else 9), v)
        o.append(f'<line x1="{x0:.2f}" y1="{y0:.2f}" x2="{x1:.2f}" y2="{y1:.2f}" stroke="{TXT3}" stroke-width="2" stroke-linecap="round"/>')
    o.append(f'<path d="{arc(cx, cy, r, 0, 100)}" fill="none" stroke="{TRACK}" stroke-width="{sw}"/>')
    o.append(f'<path d="{arc(cx, cy, r, 0, value)}" fill="none" stroke="{ACCENT}" stroke-width="{sw}"/>')
    # needle: slim triangle from the hub to just inside the arc
    a = math.radians(180 - 1.8 * value)
    tip = (cx + (r - 14) * math.cos(a), cy - (r - 14) * math.sin(a))
    nx, ny = math.sin(a), math.cos(a)                     # unit normal to the needle direction
    b1 = (cx + 7 * nx, cy + 7 * ny)
    b2 = (cx - 7 * nx, cy - 7 * ny)
    o.append(f'<path d="M{b1[0]:.2f},{b1[1]:.2f} L{tip[0]:.2f},{tip[1]:.2f} L{b2[0]:.2f},{b2[1]:.2f} Z" fill="{ACCENT}"/>')
    o.append(f'<circle cx="{cx}" cy="{cy}" r="12" fill="{ACCENT}"/><circle cx="{cx}" cy="{cy}" r="5" fill="{PANEL}"/>')
    for v, lab in ((0, "0"), (100, "100")):               # constant end labels
        lx, _ = pol(cx, cy, r, v)
        o.append(f'<text x="{lx:.2f}" y="{cy + 34}" text-anchor="middle" font-family="{UI}" font-size="22" '
                 f'font-weight="500" fill="{TXT2}">{lab}</text>')
    # `nonumbers`: the readout stays in the SVG (same position/font) but is visibility:hidden -> nothing else moves
    hide = ' visibility="hidden"' if cond == "nonumbers" else ""
    o.append(f'<text x="{cx}" y="{y + 326}" text-anchor="middle" font-family="{NUM}" font-size="60" font-weight="700" '
             f'fill="{TXT}"{hide}>{fmt_pct(readout, lang)}</text>')
    o.append(f'<text x="{cx}" y="{y + 362}" text-anchor="middle" font-family="{UI}" font-size="20" fill="{TXT2}">{t["caption"]}</text>')
    return "\n".join(o)


def clock_icon(x, y):
    return (f'<circle cx="{x}" cy="{y}" r="9" fill="none" stroke="{TXT2}" stroke-width="2"/>'
            f'<path d="M{x},{y - 5} V{y} H{x + 4}" fill="none" stroke="{TXT2}" stroke-width="2" stroke-linecap="round"/>')


def refresh_icon(x, y):
    r = 8
    x0, y0 = x + r * math.cos(math.radians(-40)), y + r * math.sin(math.radians(-40))
    x1, y1 = x + r * math.cos(math.radians(250)), y + r * math.sin(math.radians(250))
    return (f'<path d="M{x0:.2f},{y0:.2f} A{r},{r} 0 1 1 {x1:.2f},{y1:.2f}" fill="none" stroke="{TXT2}" stroke-width="2" stroke-linecap="round"/>'
            f'<path d="M{x0 - 5:.2f},{y0 - 1:.2f} L{x0 + 1:.2f},{y0 + 1:.2f} L{x0 + 2:.2f},{y0 - 6:.2f}" fill="none" stroke="{TXT2}" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')


def page(cond, lang):
    t = T[lang]
    W = 896
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{W}" viewBox="0 0 {W} {W}">',
         f'<rect width="{W}" height="{W}" fill="{BG}"/>']
    # --- top bar
    o.append(f'<rect width="{W}" height="60" fill="{BAR}"/><line x1="0" y1="60" x2="{W}" y2="60" stroke="{EDGE}" stroke-width="1.5"/>')
    hx, hy = 38, 30
    hexa = " ".join(f"{hx + 13 * math.cos(math.radians(60 * k + 30)):.2f},{hy + 13 * math.sin(math.radians(60 * k + 30)):.2f}" for k in range(6))
    o.append(f'<polygon points="{hexa}" fill="none" stroke="{ACCENT}" stroke-width="3"/><circle cx="{hx}" cy="{hy}" r="4" fill="{ACCENT}"/>')
    c = t["crumbs"]
    o.append(f'<text x="66" y="38" font-family="{UI}" font-size="21" fill="{TXT2}">{c[0]}<tspan fill="{TXT3}"> / </tspan>'
             f'{c[1]}<tspan fill="{TXT3}"> / </tspan><tspan fill="{TXT}" font-weight="600">{c[2]}</tspan></text>')
    o.append(f'<text x="872" y="38" text-anchor="end" font-family="{UI}" font-size="20" fill="{TXT2}">{t["clock"]}</text>')
    # --- title row + chips
    o.append(f'<text x="24" y="110" font-family="{UI}" font-size="32" font-weight="700" fill="{TXT}">{t["title"]}</text>')
    o.append(f'<text x="24" y="140" font-family="{UI}" font-size="20" fill="{TXT2}">{t["sub"]}</text>')
    chip_r_w, chip_l_w = 118, 190                         # monospace: "Last 1 hour" = 11 cells x 12 px
    rx0 = 872 - chip_r_w
    lx0 = rx0 - 12 - chip_l_w
    for cx0, cw in ((lx0, chip_l_w), (rx0, chip_r_w)):
        o.append(f'<rect x="{cx0}" y="80" width="{cw}" height="42" rx="8" fill="{PANEL}" stroke="{EDGE}" stroke-width="1.5"/>')
    o.append(clock_icon(lx0 + 24, 101))
    o.append(f'<text x="{lx0 + 42}" y="108" font-family="{UI}" font-size="20" font-weight="500" fill="{TXT}">{t["range"]}</text>')
    o.append(refresh_icon(rx0 + 24, 101))
    o.append(f'<text x="{rx0 + 42}" y="108" font-family="{UI}" font-size="20" font-weight="500" fill="{TXT}">{t["refresh"]}</text>')
    # --- gauge cards
    cw, ch, gap, y0 = 272, 384, 16, 158
    for i, (srv, v, rd) in enumerate(zip(SERVERS, VISUAL, READOUT[cond])):
        o.append(gauge_card(24 + i * (cw + gap), y0, cw, ch, srv, v, rd, t, lang, cond))
    # --- hosts table
    ty, th = 558, 274
    o.append(f'<rect x="24" y="{ty}" width="848" height="{th}" rx="10" fill="{PANEL}" stroke="{EDGE}" stroke-width="1.5"/>')
    o.append(f'<text x="44" y="{ty + 40}" font-family="{UI}" font-size="24" font-weight="700" fill="{TXT}">{t["hosts"]}</text>')
    colx = [44, 200, 360, 470, 690]                       # fits "Çalışma süresi" / "çevrimiçi" in monospace
    for x, lab in zip(colx, t["cols"]):
        o.append(f'<text x="{x}" y="{ty + 82}" font-family="{UI}" font-size="20" font-weight="500" fill="{TXT3}">{lab}</text>')
    o.append(f'<line x1="25" y1="{ty + 98}" x2="871" y2="{ty + 98}" stroke="{EDGE}" stroke-width="1.5"/>')
    for k, (srv, (addr, rack, (d, h))) in enumerate(zip(SERVERS, HOSTS)):
        by = ty + 136 + 50 * k
        if k:
            o.append(f'<line x1="44" y1="{by - 32}" x2="852" y2="{by - 32}" stroke="{EDGE}" stroke-width="1"/>')
        o.append(f'<text x="{colx[0]}" y="{by}" font-family="{MONO}" font-size="21" font-weight="700" fill="{TXT}">{srv}</text>')
        o.append(f'<text x="{colx[1]}" y="{by}" font-family="{MONO}" font-size="21" fill="{TXT2}">{addr}</text>')
        o.append(f'<text x="{colx[2]}" y="{by}" font-family="{MONO}" font-size="21" fill="{TXT2}">{rack}</text>')
        o.append(f'<text x="{colx[3]}" y="{by}" font-family="{UI}" font-size="21" fill="{TXT2}">{t["uptime"].format(d=d, h=h)}</text>')
        o.append(f'<circle cx="{colx[4] + 6}" cy="{by - 7}" r="6" fill="{TXT3}"/>')
        o.append(f'<text x="{colx[4] + 20}" y="{by}" font-family="{UI}" font-size="21" fill="{TXT2}">{t["online"]}</text>')
    # --- status bar
    o.append(f'<rect x="0" y="848" width="{W}" height="48" fill="{BAR}"/><line x1="0" y1="848" x2="{W}" y2="848" stroke="{EDGE}" stroke-width="1.5"/>')
    o.append(f'<circle cx="32" cy="872" r="5" fill="{ACCENT}"/>')
    o.append(f'<text x="46" y="879" font-family="{UI}" font-size="20" fill="{TXT2}">{t["status_l"]}</text>')
    o.append(f'<text x="872" y="879" text-anchor="end" font-family="{UI}" font-size="20" fill="{TXT2}">{t["status_r"]}</text>')
    o.append("</svg>")
    svg = "\n".join(o)
    return f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><style>
  * {{ margin: 0; padding: 0; }}
  html, body {{ width: 896px; height: 896px; overflow: hidden; background: {BG}; }}
  svg {{ display: block; }}
</style></head><body>
{svg}
</body></html>"""


# ---------- questions (answers computed from the data arrays) ----------
Y, N = YES, NO                                            # shared lists (TR "no" includes a whole-answer "^değil")
SRV_ACCEPT = {   # canonical first; TR also accepts the Turkish spellings "alfa"/"gama"
    "alpha-01": {"en": ["alpha-01", "alpha"], "tr": ["alpha-01", "alpha", "alfa-01", "alfa"]},
    "beta-02": {"en": ["beta-02", "beta"], "tr": ["beta-02", "beta"]},
    "gamma-03": {"en": ["gamma-03", "gamma"], "tr": ["gamma-03", "gamma", "gama-03", "gama"]},
}
TR_GEN = {"alpha-01": "'in", "beta-02": "'nin", "gamma-03": "'ün"}   # genitive after 01 bir / 02 iki / 03 üç
PCT = {"en": "^{w} percent", "tr": "^yüzde {w}"}          # q4 asks "yüzde kaç?": spelled "yüzde otuz sekiz" too


def srv(values, pick):
    return SRV_ACCEPT[SERVERS[pick(range(len(values)), key=values.__getitem__)]]


def num(v):
    """Digits (any position, by value: covers "38%", "%38", "yüzde 38") + whole-answer number words from num_accept,
    plus the spelled-out form with the unit."""
    out = {}
    for lang in LANGS:
        words = [a[1:] for a in num_accept(v, lang) if a.startswith("^")]
        out[lang] = num_accept(v, lang, extra=[PCT[lang].format(w=w) for w in words])
    return out


TS, RS = SERVERS[THRESH_IDX], SERVERS[READ_IDX]
a_vis, a_txt = VISUAL[THRESH_IDX] > THRESH, CONFLICT[THRESH_IDX] > THRESH
assert sorted(CONFLICT) == sorted(VISUAL)                              # rule 3: conflict = permutation of visual
assert a_vis != a_txt and srv(VISUAL, max) != srv(CONFLICT, max) and srv(VISUAL, min) != srv(CONFLICT, min)
assert VISUAL[READ_IDX] != CONFLICT[READ_IDX]
for vals in (VISUAL, CONFLICT):                                        # no positional cue (cards + hosts table order)
    assert vals.index(max(vals)) != 0 and vals.index(min(vals)) != len(vals) - 1, vals


def _arg(vals, pick):
    assert vals.count(pick(vals)) == 1, vals                           # unique extreme, no ties
    return vals.index(pick(vals))


CUE_MAX = {_arg(VISUAL, max), _arg(CONFLICT, max)}                     # {gamma, beta}
CUE_MIN = {_arg(VISUAL, min), _arg(CONFLICT, min)}                     # {beta, alpha}
HOST_COLS = {"address": [int(a.rsplit(".", 1)[1]) for a, _, _ in HOSTS],
             "rack": [int(r[1:]) for _, r, _ in HOSTS],
             "uptime_days": [d for _, _, (d, _) in HOSTS],
             "uptime_hours": [h for _, _, (_, h) in HOSTS]}
for col, vals in HOST_COLS.items():                                    # table numbers are not a third cue
    assert _arg(vals, max) not in CUE_MAX and _arg(vals, min) not in CUE_MIN, (col, vals)
    assert not {15, 38, 80, 92} & set(vals), (col, vals)

SPEC = {
    "id": SID,
    "title": {"en": "CPU load per server (monitoring dashboard)", "tr": "Sunucu başına CPU yükü (izleme panosu)"},
    "chart": "semicircle gauges", "style": "server monitoring dashboard, dark UI, monospace type (Menlo)",
    "tech": "inline SVG (single 896x896 SVG page, headless Chrome)",
    "mechanism": "readout",
    "conflict_summary": "Needles/fills show " + ", ".join(f"{s} {v}" for s, v in zip(SERVERS, VISUAL))
                        + "; in conflict the readouts under the gauges say "
                        + ", ".join(f"{s} {v}%" for s, v in zip(SERVERS, CONFLICT)) + ".",
    "data": {"servers": SERVERS, "visual": VISUAL, "conflict_readouts": CONFLICT, "threshold": THRESH,
             "threshold_server": TS, "read_server": RS,
             "scale": "arc 0-100, end labels '0' and '100' only, unlabeled ticks every 10",
             "position_check": "argmax is never the first card and argmin never the last card, for either cue",
             "hosts_table": [{"server": s, "address": a, "rack": r, "uptime": f"{d} d {h} h"}
                             for s, (a, r, (d, h)) in zip(SERVERS, HOSTS)],
             "hosts_table_check": "every number in the hosts table has argmax alpha-01 / argmin gamma-03; needles give "
                                  "gamma-03/beta-02, readouts beta-02/alpha-01, so name->row-number binding hits neither cue",
             "design_deviation": "DESIGN.md plan: visual alpha 92 / beta 38 / gamma 15, q3 on alpha-01, q4 on gamma-03. "
                                 "Built: 38/15/92, q3 on gamma-03, q4 on alpha-01, so card position is not a cue "
                                 "(see make.py docstring).",
             "read_value_note": f"q4 conflict: the visual answer {VISUAL[READ_IDX]} is printed as the readout of "
                                f"{SERVERS[CONFLICT.index(VISUAL[READ_IDX])]}; a 'visual' hit can be a misbind to that card. "
                                f"A needle-only estimate (~{round(VISUAL[READ_IDX], -1)}) scores 'neither'. "
                                f"Analysis: report conflict-q4 'visual' hits separately as 'possible misbind' and keep "
                                f"them out of the visual-vs-text headline (unavoidable with a 3-value permutation)."},
    "questions": [
        {"qid": "s07_q1", "nonumbers": True, "kind": "argmax", "pair": None,
         "prompt": {"en": "answer en which server has the highest cpu load?",
                    "tr": "answer tr cpu yükü en yüksek olan sunucu hangisi?"},
         "visual": srv(VISUAL, max), "text": srv(CONFLICT, max)},
        {"qid": "s07_q2", "nonumbers": True, "kind": "argmin", "pair": None,
         "prompt": {"en": "answer en which server has the lowest cpu load?",
                    "tr": "answer tr cpu yükü en düşük olan sunucu hangisi?"},
         "visual": srv(VISUAL, min), "text": srv(CONFLICT, min)},
        {"qid": "s07_q3a", "nonumbers": True, "kind": "threshold", "pair": "s07_p1",
         "prompt": {"en": f"answer en is the cpu load of {TS} above {THRESH} percent?",
                    "tr": f"answer tr {TS}{TR_GEN[TS]} cpu yükü yüzde {THRESH}'in üzerinde mi?"},
         "visual": Y if a_vis else N, "text": Y if a_txt else N},
        {"qid": "s07_q3b", "nonumbers": True, "kind": "threshold", "pair": "s07_p1",
         "prompt": {"en": f"answer en is the cpu load of {TS} below {THRESH} percent?",
                    "tr": f"answer tr {TS}{TR_GEN[TS]} cpu yükü yüzde {THRESH}'in altında mı?"},
         "visual": N if a_vis else Y, "text": N if a_txt else Y},
        {"qid": "s07_q4", "nonumbers": False, "kind": "read_value", "pair": None,
         "prompt": {"en": f"answer en what is the cpu load of {RS}?",
                    "tr": f"answer tr {RS}{TR_GEN[RS]} cpu yükü yüzde kaç?"},
         "visual": num(VISUAL[READ_IDX]), "text": num(CONFLICT[READ_IDX])},
    ],
}

if __name__ == "__main__":
    for cond in CONDS:
        for lang in LANGS:
            render_html(page(cond, lang), name(SID, cond, lang))
    finish(SPEC)
