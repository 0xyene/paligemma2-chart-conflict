"""s04 — phone 'screen time' screen, dark UI, horizontal bars (HTML/CSS flex). Rows are A–Z, and the page says so
with a 'Sort: A–Z' chip; conflict mirrors the printed times by rank (longest bar <-> shortest time, and so on).

App icons are neutral monograms (first letter on a coloured squircle): a speech bubble / play button / map pin /
notepad / card glyph would tell the model each app's category, and world knowledge about typical usage
(chat & video high, bank low) would then act as a third cue.

Deviations from DESIGN.md §s04 (review fixes; DESIGN.md still lists the old names and the sorted order):
- names Chirp/Tubeo/Mapster/Notely/Bankly -> Dorvi/Gisano/Kuvelo/Libezu/Tovra. The old names carried a category
  (chirp = chat, tube = video, map, note, bank), which makes the conflict text (bank app 9h 40m, chat app 1h 5m)
  implausible by world knowledge and so favours the visual answer. Chirp/Notely/Bankly are also real product names
  (rule 5). The new names are coined: no English or Turkish meaning, no category root, same in en and tr.
  Row 4 was 'Rimso' in an earlier version: RIMSO is a registered mark (Research Industries Corp., RIMSO-50, a DMSO
  bladder drug), so the earlier 'no mark found' claim was wrong. Replacement 'Libezu' (sorts between Kuvelo and
  Tovra, so every position check is unchanged; no shared prefix with the other four; no v/o/r letters, so it does
  not look like Dorvi/Tovra/Kuvelo). Search 2026-10-05 for the bare word: Google Play search 'libezu' -> "No results";
  App Store (web search restricted to apps.apple.com) -> no Libezu app, closest is 'Libanezu', a different word;
  USPTO via Trademarkia -> "0 Trademark Results found for 'libezu'" (Justia blocks automated fetches: HTTP 403);
  general web search -> no exact match (only the Czech village Libež). Rejected on the way: Sefumi (Italian
  'se fumi' = 'if you smoke'; Play returns quit-smoking apps), Nivura (~ Nivra, an EdTech app), Ramzeli (~ Turkish
  given name Remzi), Lesvani (~ Lesvos), Ruvzi (shares 'uv' with Kuvelo).
- rows A–Z instead of 'longest first'. Sorted rows made list position a third cue: in conflict, the top row was the
  visual answer to q1, the bottom row to q2, and 'row above = more' matched the visual answer to q3. Values are
  assigned to the A–Z rows so that (all asserted below, see POSITION_CHECKS):
    * both extreme apps (q1/q2 answers, for both cues) sit in rows 2 and 4, so top and bottom rows are mid-usage apps
      (a first/last-item bias hits neither cue) and each extreme is two rows from the other cue's row of the same
      question (misbinding a time to the next row hits neither cue);
    * in the q3 pair (Dorvi vs Kuvelo) the visually larger app is the LOWER row. A residual 'higher row = more' habit
      now points to the text answer on q3a/q3b and to the visual answer on q1/q2 (row 2 vs row 4), i.e. 2 questions
      each way instead of 5 pointing at 'visual';
    * the conflict times read top to bottom are not the visual times read bottom to top, so reverse-order binding
      cannot produce the visual mapping.
- q3 asks Dorvi vs Kuvelo. q4 reads Dorvi (visual 2h 30m, text 7h 10m; the plan's q4 had the same two values the other
  way round). Until round 3 q4 read Kuvelo, whose visual time 7h 10m was then printed on Dorvi = the TOP row of the
  conflict list, so a 'read the first value' habit scored as 'visual'. Now the q4 visual time 2h 30m is printed on
  Kuvelo's row 3: two rows from Dorvi and neither first nor last (asserted in POSITION_CHECKS).
- no 'Show categories' link; the screen is less iOS-like (generic back label, underline tabs, non-iOS status icons).
- minutes are not zero-padded ('1h 5m', '1 sa 5 dk'), as in real screen-time screens.
- bars and the UI accent (back label, active-tab underline) are teal #4fb3a6 (was lavender #a9b8ff), so the set is
  not all blue/indigo. Non-semantic and identical in all 4 images; the bars stay one colour for every app.
Turkish accept lists are Turkish-only (like the evet/hayır lists in every stimulus): an English reply to a tr prompt
scores 'neither' for both cues. The q3 pair uses the shared YES/NO lists (common/answers.py; TR 'no' also takes a bare
'değil'). Turkish verb-echo yes/no answers ('kullanıldı' / 'kullanılmadı') are deliberately NOT added: 'kullanıldı'
also appears in natural negative answers ('hayır, daha az kullanıldı'), and the s01 reference uses plain YES/NO too.
q4 is a duration, not an integer, so it keeps its own dur_variants() lists instead of num_accept().
nonumbers: the five per-app time labels (the only strings that differ between consistent and conflict) are blanked.
The .time span stays in the row with its fixed 190 px width and holds a single no-break space, so it keeps its line
box and baseline: app name, chevron, bar and every other element stay pixel-identical. The weekly total and daily
average stay (same in all versions; a sum/mean of five values does not give any one of them). q1-q3 are answerable
from bar lengths alone; q4 (exact time) is not: the bars have no scale and its only source was the removed label.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
from answers import NO, YES  # noqa: E402
from lib import CONDS, LANGS, finish, name, render_html  # noqa: E402
from scoring import tokens  # noqa: E402

SID = "s04_app_screentime"
# minutes = bar lengths = printed times in `consistent`, keyed by app
VISUAL_MIN = {"Dorvi": 150, "Gisano": 580, "Kuvelo": 430, "Libezu": 65, "Tovra": 260}
APPS = sorted(VISUAL_MIN)                                       # drawing order top to bottom = A–Z (the chip says so)
_RANKED = sorted(VISUAL_MIN, key=VISUAL_MIN.get, reverse=True)
# conflict = rank mirror: longest bar gets the shortest time and so on (Gisano<->Libezu, Kuvelo<->Dorvi, Tovra stays)
CONFLICT_MIN = {a: VISUAL_MIN[b] for a, b in zip(_RANKED, _RANKED[::-1])}
VISUAL = [VISUAL_MIN[a] for a in APPS]
LABELS = {"consistent": VISUAL, "conflict": [CONFLICT_MIN[a] for a in APPS],
          "nonumbers": [None] * len(APPS)}                       # None = time label blanked (span kept, see docstring)
TOTAL = sum(VISUAL)                                             # identical in both versions (labels are a permutation)
AVG = round(TOTAL / 7)
CMP_A, CMP_B = "Dorvi", "Kuvelo"                                # q3: "was Dorvi used more/less than Kuvelo?"
READ = "Dorvi"                                                  # q4: "how long was Dorvi used?"


def dur(mins, lang):
    h, m = divmod(mins, 60)
    return f"{h}h {m}m" if lang == "en" else f"{h} sa {m} dk"     # no zero padding, like real screen-time UIs


T = {
    "en": dict(back="Device", title="Screen time", seg=("Day", "Week"), week="This week", rng="28 Sep – 4 Oct",
               total="Total", avg="Daily average", apps="Apps", sort="Sort: A–Z",
               foot="Updated today at 21:40"),
    "tr": dict(back="Cihaz", title="Ekran süresi", seg=("Gün", "Hafta"), week="Bu hafta", rng="28 Eyl – 4 Eki",
               total="Toplam", avg="Günlük ortalama", apps="Uygulamalar", sort="Sırala: A–Z",
               foot="Bugün 21.40'ta güncellendi"),
}

ACCENT = "#4fb3a6"   # bars + back label + active-tab underline; one teal for every app, same in all 4 images
# neutral app icons: white first letter on a coloured squircle (no category glyphs, see docstring)
ICON_BG = {"Dorvi": "#4b63d8", "Gisano": "#7a52c7", "Kuvelo": "#56627a", "Libezu": "#3b3f8f", "Tovra": "#8a5aa8"}


def status_bar():
    # generic glyphs (filled signal wedge, filled wifi sector, upright battery), not the iOS bar/fan/pill shapes
    signal = ('<path d="M1 17 L17 1 V17 Z" fill="#5a5a60"/><path d="M1 17 L12 6 V17 Z" fill="#fff"/>')
    wifi = '<path d="M10 17 L0.5 6.2 A14.5 14.5 0 0 1 19.5 6.2 Z" fill="#fff"/>'
    batt = ('<rect x="3.5" y="0.5" width="5" height="2.5" rx="1" fill="#c7c7cc"/>'
            '<rect x="1" y="2.5" width="10" height="16" rx="2" fill="none" stroke="#c7c7cc" stroke-width="1.5"/>'
            '<rect x="3" y="6.5" width="6" height="10" rx="1" fill="#fff"/>')
    return (f'<div class="status"><span class="clock">21:41</span><span class="sicons">'
            f'<svg width="18" height="18" viewBox="0 0 18 18">{signal}</svg>'
            f'<svg width="20" height="18" viewBox="0 0 20 18">{wifi}</svg>'
            f'<svg width="12" height="19" viewBox="0 0 12 19">{batt}</svg></span></div>')


def rows(cond, lang):
    out = []
    mx = max(VISUAL_MIN.values())
    for app, v, lab in zip(APPS, VISUAL, LABELS[cond]):
        out.append(f"""
      <div class="row">
        <div class="icon" style="background:{ICON_BG[app]}">{app[0]}</div>
        <div class="main">
          <div class="line"><span class="app">{app}</span><span class="time">{"&nbsp;" if lab is None else dur(lab, lang)}</span><span class="chev">›</span></div>
          <div class="track"><div class="bar" style="width:{100 * v / mx:.2f}%"></div></div>
        </div>
      </div>""")
    return "".join(out)


def page(cond, lang):
    t = T[lang]
    return f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{ width: 896px; height: 896px; overflow: hidden; }}
  body {{ background: #000; color: #f2f2f7; font-family: "Avenir Next", "Helvetica Neue", sans-serif;
          padding: 0 40px; position: relative; -webkit-font-smoothing: antialiased; }}
  .status {{ height: 52px; display: flex; align-items: center; justify-content: space-between; padding: 0 14px; }}
  .clock {{ font-size: 23px; font-weight: 600; letter-spacing: .3px; }}
  .sicons {{ display: flex; align-items: center; gap: 10px; }}
  .nav {{ height: 44px; display: flex; align-items: center; justify-content: space-between; }}
  .back {{ font-size: 24px; font-weight: 500; color: {ACCENT}; }}
  .back b {{ font-size: 34px; font-weight: 400; margin-right: 6px; position: relative; top: 2px; }}
  .tabs {{ display: flex; gap: 30px; padding-right: 8px; }}
  .tabs span {{ font-size: 22px; font-weight: 600; color: #8e8e95; padding: 2px 2px 5px; border-bottom: 3px solid transparent; }}
  .tabs span.on {{ color: #fff; border-bottom-color: {ACCENT}; }}
  h1 {{ font-size: 44px; font-weight: 700; letter-spacing: -.3px; margin-top: 10px; line-height: 1.1; }}
  .card {{ background: #1c1c1e; border-radius: 22px; }}
  .sum {{ margin-top: 16px; padding: 18px 26px; display: flex; justify-content: space-between; align-items: flex-end; }}
  .lab {{ font-size: 20px; font-weight: 600; color: #9a9aa0; text-transform: uppercase; letter-spacing: .8px; }}
  .big {{ font-size: 40px; font-weight: 700; margin-top: 2px; line-height: 1.15; }}
  .sub {{ font-size: 20px; font-weight: 500; color: #9a9aa0; }}
  .avg {{ text-align: right; }}
  .avg .val {{ font-size: 28px; font-weight: 600; margin-top: 2px; }}
  .sect {{ display: flex; justify-content: space-between; align-items: center; margin: 16px 8px 10px; }}
  .sect .lab {{ font-size: 21px; }}
  .chip {{ font-size: 21px; font-weight: 600; color: #d6d9ec; border: 1.5px solid #4a4a50; border-radius: 18px;
           padding: 3px 14px 4px 16px; background: #141416; }}
  .chip i {{ font-style: normal; color: #8e8e95; margin-left: 8px; font-size: 18px; }}
  .list {{ padding: 4px 0 4px 22px; }}
  .row {{ display: flex; align-items: center; gap: 20px; height: 88px; }}
  .row + .row .main {{ border-top: 1px solid #38383a; }}
  .icon {{ width: 60px; height: 60px; border-radius: 15px; flex: none; display: flex; align-items: center; justify-content: center;
           font-size: 31px; font-weight: 700; color: #fff; line-height: 1; padding-top: 3px; }}
  .main {{ flex: 1; height: 100%; display: flex; flex-direction: column; justify-content: center; padding-right: 20px; }}
  .line {{ display: flex; align-items: baseline; }}
  .app {{ font-size: 27px; font-weight: 600; flex: 1; }}
  .time {{ width: 190px; flex: none; text-align: right; font-size: 28px; font-weight: 700; color: #fff;
           font-variant-numeric: tabular-nums; white-space: nowrap; }}
  .chev {{ width: 30px; flex: none; text-align: right; font-size: 32px; color: #636366; font-weight: 500; }}
  .track {{ margin-top: 9px; margin-right: 30px; height: 16px; }}
  .bar {{ height: 100%; border-radius: 8px; background: {ACCENT}; }}
  .foot {{ text-align: center; font-size: 20px; color: #9a9aa0; margin-top: 12px; }}
</style></head><body>
  {status_bar()}
  <div class="nav"><span class="back"><b>‹</b>{t["back"]}</span>
    <div class="tabs"><span>{t["seg"][0]}</span><span class="on">{t["seg"][1]}</span></div></div>
  <h1>{t["title"]}</h1>
  <div class="card sum">
    <div><div class="lab">{t["week"]} · {t["total"]}</div><div class="big">{dur(TOTAL, lang)}</div>
         <div class="sub">{t["rng"]}</div></div>
    <div class="avg"><div class="sub">{t["avg"]}</div><div class="val">{dur(AVG, lang)}</div></div>
  </div>
  <div class="sect"><span class="lab">{t["apps"]}</span><span class="chip">{t["sort"]}<i>▾</i></span></div>
  <div class="card list">{rows(cond, lang)}
  </div>
  <div class="foot">{t["foot"]}</div>
</body></html>"""


# ---------- number words for spelled-out durations (0-59) ----------
_EN_1 = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
         "seventeen eighteen nineteen").split()
_EN_10 = {2: "twenty", 3: "thirty", 4: "forty", 5: "fifty"}
_TR_1 = "sıfır bir iki üç dört beş altı yedi sekiz dokuz".split()
_TR_10 = {1: "on", 2: "yirmi", 3: "otuz", 4: "kırk", 5: "elli"}


def num_word(n, lang):
    assert 0 <= n < 60
    if lang == "en":
        return _EN_1[n] if n < 20 else _EN_10[n // 10] + ("" if n % 10 == 0 else "-" + _EN_1[n % 10])
    return _TR_1[n] if n < 10 else _TR_10[n // 10] + ("" if n % 10 == 0 else " " + _TR_1[n % 10])


def dur_variants(mins, lang):
    """Short answers a model could give for a duration, canonical (as printed) first.

    Both sides get the same templates: digits with every unit spelling, h:mm (and the Turkish h.mm), total minutes,
    and spelled-out hours + minutes ('seven hours ten minutes', 'yedi saat on dakika'). Half-hour forms
    ('2.5 hours', 'two and a half', 'iki buçuk') are added whenever m == 30 because they are the natural way to say
    such a value. Hour-only answers that copy the printed hour ('7 hours', '2 saat', 'about two hours') are accepted
    on both sides by the same template; every app has a different hour digit, so the hour alone names one row.
    No rounding forms ('3 hours' for 2h 30m): a model copying the printed hour truncates, and rounding would add a
    form to one side only. Turkish lists are Turkish-only (see docstring). Duplicates by token sequence are dropped.
    """
    h, m = divmod(mins, 60)
    if lang == "en":
        hu, mu = ("hour" if h == 1 else "hours"), ("minute" if m == 1 else "minutes")
        hw, mw = num_word(h, "en"), num_word(m, "en")
        out = [dur(mins, "en")]
        out += [f"{h} {a}{j} {m} {b}" for a in ("h", "hr", "hrs", hu) for j in ("", " and") for b in ("m", "min", "mins", mu)]
        out += [f"{hw} {hu}{j} {mw} {mu}" for j in ("", " and")]
        out += [f"{h}:{m:02d}", f"{mins} minutes", f"{mins} mins", f"{mins} min"]
        if m == 30:
            out += [f"{h}.5 hours", f"{h}.5 hrs", f"{h}.5 h", f"{h} and a half hours", f"{h} and a half",
                    f"{hw} and a half hours", f"{hw} and a half"]
        out += [f"{h} {a}" for a in ("h", "hr", "hrs", hu)] + [f"{hw} {hu}"]          # hour only
    else:
        hw, mw = num_word(h, "tr"), num_word(m, "tr")
        out = [dur(mins, "tr")]
        out += [f"{h} {a}{j} {m} {b}" for a in ("sa", "saat") for j in ("", " ve") for b in ("dk", "dakika")]
        out += [f"{hw} saat{j} {mw} dakika" for j in ("", " ve")]
        out += [f"{h}:{m:02d}", f"{h}.{m:02d}", f"{mins} dakika", f"{mins} dk"]
        out += [f"{h} sa", f"{h} saat", f"{hw} saat"]                                 # hour only
        if m == 30:
            out += [f"{h},5 saat", f"{h},5 sa", f"{h} buçuk saat", f"{hw} buçuk saat", f"{h} buçuk", f"{hw} buçuk"]
    uniq, seen = [], set()
    for v in out:
        key = tuple(tokens(v))
        if key not in seen:
            seen.add(key)
            uniq.append(v)
    return uniq


def ablative(word):
    """Turkish ablative suffix with vowel harmony and consonant assimilation: kuvelo -> kuvelo'dan."""
    last_vowel = [c for c in word.lower() if c in "aıoueiöü"][-1]
    v = "a" if last_vowel in "aıou" else "e"
    c = "t" if word[-1].lower() in "pçtkfhsş" else "d"
    return f"{word}'{c}{v}n"


# ---------- position checks: list position must not act as a third cue ----------
CV, CT = VISUAL, LABELS["conflict"]
row = APPS.index
top_v, top_t = APPS[CV.index(max(CV))], APPS[CT.index(max(CV))]
low_v, low_t = APPS[CV.index(min(CV))], APPS[CT.index(min(CV))]
more_v = VISUAL_MIN[CMP_A] > VISUAL_MIN[CMP_B]
more_t = CONFLICT_MIN[CMP_A] > CONFLICT_MIN[CMP_B]
_src = APPS[CT.index(VISUAL_MIN[READ])]                         # row whose printed conflict time = READ's visual time
POSITION_CHECKS = {
    "rows_alphabetical": APPS == sorted(APPS),
    "every_question_differs": top_v != top_t and low_v != low_t and more_v != more_t and VISUAL_MIN[READ] != CONFLICT_MIN[READ],
    "extremes_not_first_or_last_row": all(0 < row(a) < len(APPS) - 1 for a in (top_v, top_t, low_v, low_t)),
    "q1_q2_cues_two_rows_apart": abs(row(top_v) - row(top_t)) >= 2 and abs(row(low_v) - row(low_t)) >= 2,
    "q3_visually_larger_is_lower_row": row(CMP_A if more_v else CMP_B) > row(CMP_B if more_v else CMP_A),
    "q4_visual_time_printed_two_rows_away": abs(row(_src) - row(READ)) >= 2,
    "q4_visual_time_row_not_first_or_last": 0 < row(_src) < len(APPS) - 1,
    "hour_digits_distinct": len({v // 60 for v in VISUAL}) == len(VISUAL),        # hour-only q4 answers name one row
    "columns_not_monotone": all(s != sorted(s) and s != sorted(s, reverse=True) for s in (CV, CT)),
    "conflict_is_not_row_reversal": CT != CV[::-1],
    "names_no_prefix_clash": not any(a != b and b.lower().startswith(a.lower()) for a in APPS for b in APPS),
}
assert all(POSITION_CHECKS.values()), {k: v for k, v in POSITION_CHECKS.items() if not v}
assert sorted(CT) == sorted(CV)


def _listing(mins):
    return ", ".join(f"{a} {dur(v, 'en')}" for a, v in zip(APPS, mins))


SUMMARY = (f"Rows in A–Z order, stated by a 'Sort: A–Z' chip ({_listing(VISUAL)}); in conflict the printed times are "
           f"mirrored by rank ({_listing(CT)}). Weekly total {dur(TOTAL, 'en')} is identical in both.")
_gap = row(_src) - row(READ)
READ_NOTE = (f"q4 conflict: the visual answer {dur(VISUAL_MIN[READ], 'en')} is printed in the image, on {_src}'s row, "
             f"{abs(_gap)} row{'s' if abs(_gap) > 1 else ''} {'below' if _gap > 0 else 'above'} {READ}. Bars have "
             "no scale, so geometry alone cannot give that exact value: a 'visual' hit means a value reached by rank "
             "re-mapping or a misread row, not a bar measurement.")

CA, CB, RN = CMP_A.lower(), CMP_B.lower(), READ.lower()

SPEC = {
    "id": SID,
    "title": {"en": "Screen time this week (phone app)", "tr": "Bu haftaki ekran süresi (telefon uygulaması)"},
    "chart": "horizontal bars", "style": "phone app screenshot, dark UI", "tech": "HTML/CSS flex (headless Chrome)",
    "mechanism": "label",
    "conflict_summary": SUMMARY,
    "data": {"apps": APPS, "visual_minutes": VISUAL, "conflict_label_minutes": CT,
             "visual_labels": {lg: [dur(v, lg) for v in VISUAL] for lg in LANGS},
             "conflict_labels": {lg: [dur(v, lg) for v in CT] for lg in LANGS},
             "total_minutes": TOTAL, "daily_average_minutes": AVG,
             "icons": "neutral monograms (white first letter on a coloured squircle); no category glyphs",
             "row_order": "A–Z, stated on the page by a 'Sort: A–Z' / 'Sırala: A–Z' chip",
             "position_checks": POSITION_CHECKS,
             "position_note": (f"Extremes ({top_v}/{low_v}) sit in rows {row(top_v) + 1} and {row(low_v) + 1}; top and "
                               f"bottom rows are mid-usage apps. In the q3 pair the visually larger app ({CMP_B}) is "
                               "the lower row, so a residual 'higher row = more' habit points to the text answer on "
                               "q3a/q3b and to the visual answer on q1/q2 (row 2 vs row 4): 2 questions each way."),
             "names_note": "coined names, identical in en/tr, no English/Turkish meaning or category root. Row 4 was "
                           "'Rimso' in an earlier version; RIMSO is a registered mark (RIMSO-50, a DMSO drug), so it "
                           "was replaced by 'Libezu'. Search 2026-10-05 for the bare word 'libezu': Google Play "
                           "search -> 'No results'; App Store (web search on apps.apple.com) -> no Libezu app "
                           "(closest 'Libanezu', a different word); USPTO via Trademarkia -> 0 results (Justia "
                           "returned HTTP 403 to automated fetches); general web -> no exact match.",
             "design_deviation": "DESIGN.md plan: Chirp/Tubeo/Mapster/Notely/Bankly sorted longest first, q3 Chirp vs "
                                 "Tubeo, q4 Tubeo (visual 7h 10m, text 2h 30m). Built: coined names in A–Z rows with "
                                 "a sort chip, q3 Dorvi vs Kuvelo, q4 Dorvi (visual 2h 30m, text 7h 10m), so names "
                                 "and row position carry no cue (see make.py docstring).",
             "read_value_note": READ_NOTE,
             "nonumbers_note": "per-app time labels blanked (span kept at its fixed width, holding one no-break "
                               "space); weekly total and daily average kept (identical in all versions). q1-q3 "
                               "answerable from bar lengths; q4 not (bars have no scale)."},
    "questions": [
        {"qid": "s04_q1", "kind": "argmax", "pair": None,
         "prompt": {"en": "answer en which app was used the most this week?",
                    "tr": "answer tr bu hafta en çok hangi uygulama kullanıldı?"},
         "visual": {"en": [top_v.lower()], "tr": [top_v.lower()]},
         "text": {"en": [top_t.lower()], "tr": [top_t.lower()]},
         "nonumbers": True},                                    # longest bar is visible without labels
        {"qid": "s04_q2", "kind": "argmin", "pair": None,
         "prompt": {"en": "answer en which app was used the least this week?",
                    "tr": "answer tr bu hafta en az hangi uygulama kullanıldı?"},
         "visual": {"en": [low_v.lower()], "tr": [low_v.lower()]},
         "text": {"en": [low_t.lower()], "tr": [low_t.lower()]},
         "nonumbers": True},                                    # shortest bar is visible without labels
        {"qid": "s04_q3a", "kind": "compare", "pair": "s04_p1",
         "prompt": {"en": f"answer en was {CA} used more than {CB} this week?",
                    "tr": f"answer tr {CA} bu hafta {ablative(CB)} daha fazla kullanıldı mı?"},
         "visual": YES if more_v else NO, "text": YES if more_t else NO,
         "nonumbers": True},                                    # two bar lengths compared
        {"qid": "s04_q3b", "kind": "compare", "pair": "s04_p1",
         "prompt": {"en": f"answer en was {CA} used less than {CB} this week?",
                    "tr": f"answer tr {CA} bu hafta {ablative(CB)} daha az kullanıldı mı?"},
         "visual": NO if more_v else YES, "text": NO if more_t else YES,
         "nonumbers": True},                                    # same pair, same flag
        {"qid": "s04_q4", "kind": "read_value", "pair": None,
         "prompt": {"en": f"answer en how long was {RN} used this week?",
                    "tr": f"answer tr {RN} bu hafta ne kadar süre kullanıldı?"},
         "visual": {lg: dur_variants(VISUAL_MIN[READ], lg) for lg in LANGS},
         "text": {lg: dur_variants(CONFLICT_MIN[READ], lg) for lg in LANGS},
         "nonumbers": False},                                   # exact time: only source was the blanked label
    ],
}

if __name__ == "__main__":
    for cond in CONDS:
        for lang in LANGS:
            render_html(page(cond, lang), name(SID, cond, lang))
    finish(SPEC)
