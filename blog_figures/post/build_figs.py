"""Blog post figures 4-8 -> blog_figures/post/fig*.png (2x, trimmed).

usage: python3.12 blog_figures/post/build_figs.py
fig6 needs pull224.png / pull448.png first: screenshots of the report's "By question type" chart (blog terms, no pts labels).
Headless Chrome gets its own throwaway profile and a 60 s timeout (see common/lib.py).
"""
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from PIL import Image, ImageChops

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
IMG = ROOT / "images"
BIC = Image.Resampling.BICUBIC

CSS = """<style>
body { margin:0; background:#fff; font-family:'Public Sans',Helvetica,Arial,sans-serif; color:#1d2327; }
.wrap { width:740px; padding:10px; }
.row { display:flex; gap:12px; }
.col { flex:1; min-width:0; }
.col img { width:100%; display:block; border:1px solid #d9dde1; border-radius:4px; }
.tag { display:inline-block; font-size:14px; font-weight:600; padding:3px 10px; border-radius:99px; margin-bottom:6px; color:#fff; }
.true { background:#3d4a55; } .lie { background:#e0612d; } .none { background:#8a959e; } .mdl { background:#1d2327; }
.sub { font-size:12.5px; color:#5b666f; margin-top:5px; line-height:1.35; }
.grid { display:grid; grid-template-columns:repeat(5,1fr); gap:10px 8px; }
.grid img { width:100%; display:block; border:1px solid #d9dde1; border-radius:3px; }
.grid .nm { font-size:11.5px; color:#3d4a55; margin-top:3px; line-height:1.25; }
.panel { margin-bottom:10px; } .panel img { width:100%; display:block; }
table { border-collapse:collapse; width:100%; margin-top:12px; font-size:13.5px; }
th { text-align:left; font-weight:600; color:#5b666f; font-size:12.5px; padding:6px 8px; border-bottom:2px solid #c9cfd4; }
td { padding:7px 8px; border-bottom:1px solid #e3e6e9; vertical-align:top; }
td.a { white-space:nowrap; font-family:'IBM Plex Mono',Menlo,monospace; font-size:13px; }
.ok { color:#1f7a4d; font-weight:600; } .bad { color:#c2410c; font-weight:600; }
.kind { display:block; font-size:11.5px; color:#7a858e; margin-top:2px; }
.c-true { background:#f3f5f7; } .c-lie { background:#fdf1ec; }
.flip { display:inline-block; font-size:10px; font-weight:600; color:#fff; background:#8a959e; border-radius:99px; padding:0 6px; margin-left:3px; vertical-align:1px; }
.xlab { text-align:center; font-size:12.5px; color:#5b666f; margin:4px 0 0 18%; }
</style>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;600&family=IBM+Plex+Mono:wght@400&display=swap">"""


def page(body):
    return f"<!doctype html><html><head><meta charset='utf-8'>{CSS}</head><body><div class='wrap'>{body}</div></body></html>"


def render(name, html):
    src, out = HERE / f"{name}.html", HERE / f"{name}.png"
    src.write_text(html)
    out.unlink(missing_ok=True)
    profile = tempfile.mkdtemp(prefix="pg2-blogfig-chrome-")
    proc = subprocess.Popen([CHROME, "--headless=new", f"--user-data-dir={profile}", "--no-first-run",
                             "--no-default-browser-check", "--disable-component-update", "--disable-gpu", "--hide-scrollbars",
                             "--force-device-scale-factor=2", "--virtual-time-budget=6000", "--allow-file-access-from-files",
                             "--window-size=760,1800", f"--screenshot={out}", src.as_uri()],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        deadline, last = time.time() + 60, -1
        while time.time() < deadline:
            if out.exists() and out.stat().st_size > 0 and out.stat().st_size == last:
                break
            last = out.stat().st_size if out.exists() else -1
            time.sleep(0.4)
        else:
            raise TimeoutError(f"Chrome did not write {out.name}")
    finally:
        proc.kill()
        proc.wait(timeout=10)
        shutil.rmtree(profile, ignore_errors=True)
    im = Image.open(out).convert("RGB")
    l, t, r, b = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    im.crop((max(l - 12, 0), max(t - 12, 0), min(r + 12, im.width), min(b + 12, im.height))).save(out)
    print(out.name, Image.open(out).size)


def uri(p):
    return Path(p).as_uri()


# fig4: one chart, three versions (s01 newspaper, English), cropped to the chart
CROP = (360, 330, 892, 836)  # chart area of s01 in the 896 px image
for v in ("consistent", "conflict", "nonumbers"):
    Image.open(IMG / f"s01_newspaper_bars_{v}_en.png").convert("RGB").crop(CROP).save(HERE / f"s01_{v}_crop.png")
render("fig4_three_versions", page(f"""<div class="row">
<div class="col"><span class="tag true">True chart</span><img src="{uri(HERE / 's01_consistent_crop.png')}"><div class="sub">The numbers match the bars.</div></div>
<div class="col"><span class="tag lie">Lying chart</span><img src="{uri(HERE / 's01_conflict_crop.png')}"><div class="sub">Same bars, pixel for pixel. The numbers are in reverse order.</div></div>
<div class="col"><span class="tag none">No-numbers chart</span><img src="{uri(HERE / 's01_nonumbers_crop.png')}"><div class="sub">Same bars, no numbers.</div></div>
</div>"""))

# fig5: the 14 charts (true versions, English)
NAMES = {"s01": "Newspaper page", "s02": "News site, dark", "s03": "Presentation slide", "s04": "Phone app, screen time",
         "s05": "School poster", "s06": "TV weather", "s07": "Server dashboard", "s08": "Photo of a paper page",
         "s09": "Notebook sketch", "s10": "Scanned report, map", "s11": "Finance app", "s12": "Textbook exercise",
         "s13": "Phone battery widget", "s14": "Spreadsheet"}
FLIPPED = {"s02", "s10", "s12"}  # axis / legend charts: the lying version flips the scale, so its text stays correct (DESIGN.md)
cells = []
for f in sorted(IMG.glob("s*_consistent_en.png")):
    th = HERE / f"thumb_{f.name[:3]}.jpg"
    Image.open(f).convert("RGB").resize((300, 300), Image.Resampling.LANCZOS).save(th, quality=90)
    flip = ' <span class="flip">flipped scale</span>' if f.name[:3] in FLIPPED else ""
    cells.append(f'<div><img src="{uri(th)}"><div class="nm">{NAMES[f.name[:3]]}{flip}</div></div>')
assert len(cells) == 14
render("fig5_fourteen_charts", page(f'<div class="grid">{"".join(cells)}</div>'))

# fig6: the report's "by question type" chart, both models
render("fig6_results", page(f"""
<div class="panel"><span class="tag mdl">3B-224</span><img src="{uri(HERE / 'pull224.png')}"><div class="xlab">share of answers that give the answer of the lying numbers</div></div>
<div class="panel"><span class="tag mdl">3B-448</span><img src="{uri(HERE / 'pull448.png')}"><div class="xlab">share of answers that give the answer of the lying numbers</div></div>"""))

# fig7: run 2 inputs, zoomed on the chart (s01 lying version, as in run 2's demo)
src = Image.open(IMG / "s01_newspaper_bars_conflict_en.png").convert("RGB")
in448 = src.resize((448, 448), BIC)                                   # 3B-448, run 1
in448r = src.resize((224, 224), BIC).resize((448, 448), BIC)          # 3B-448, run 2 (run2/build2.py)
in224 = src.resize((224, 224), BIC)                                   # 3B-224, run 1
c = tuple(v // 2 for v in CROP)
in448.crop(c).save(HERE / "r2_448.png")
in448r.crop(c).save(HERE / "r2_448_reduced.png")
in224.crop(tuple(v // 4 for v in CROP)).save(HERE / "r2_224.png")
render("fig7_less_detail", page(f"""<div class="row">
<div class="col"><span class="tag mdl">3B-448, normal</span><img src="{uri(HERE / 'r2_448.png')}"><div class="sub">448 px input (run 1)</div></div>
<div class="col"><span class="tag lie">3B-448, less detail</span><img src="{uri(HERE / 'r2_448_reduced.png')}"><div class="sub">Reduced to 224 px, then enlarged back to 448 px (run 2)</div></div>
<div class="col"><span class="tag none">3B-224</span><img src="{uri(HERE / 'r2_224.png')}"><div class="sub">224 px input (run 1), shown enlarged</div></div>
</div>"""))

# fig8: one chart, six questions, 10B-448 (answers from report/data.json, which reads answers_run4.csv)
ex = json.loads((ROOT / "report" / "data.json").read_text())["run4"]["example"]
assert [e["agree"] for e in ex] == ["avlen", "no", "31°", "yes", "yes", "yes"], ex
assert [e["lie"] for e in ex] == ["dimel", "yes", "-3°", "yes", "yes", "yes"], ex
# the full prompts (data.json keeps a shortened label for q4); the last two are one exact-opposite pair, shown as one row,
# because yes to both is a contradiction even where one of the two answers is right
Q = ["Which city has the fullest thermometer?", "Does Dimel have the fullest thermometer?",
     "What temperature is shown for Avlen?",
     "Is the temperature under the fullest thermometer the highest of the four temperatures?"]
KIND = ["drawing question", "wrong claim about the drawing", "reads the text", "concrete comparison (run 4)"]
RIGHT = [("avlen", "avlen"), ("no", "no"), ("31°", "-3°"), ("yes", "no")]  # (true, lying)
cell = lambda a, r: f'{a} <span class="{"ok" if a == r else "bad"}">{"✓" if a == r else "✗"}</span>'
rows = [f'<tr><td>{q}<span class="kind">{k}</span></td><td class="a c-true">{cell(e["agree"], rt)}</td>'
        f'<td class="a c-lie">{cell(e["lie"], rl)}</td></tr>' for e, q, k, (rt, rl) in zip(ex, Q, KIND, RIGHT)]
pair = lambda m, c: f'{m} / {c} <span class="{"ok" if m != c else "bad"}">{"✓" if m != c else "✗"}</span>'
rows.append(f'<tr><td>Do the numbers match the thermometer fills? / Do they contradict them?'
            f'<span class="kind">direct question pair (run 3): yes to both is a contradiction</span></td>'
            f'<td class="a c-true">{pair(ex[4]["agree"], ex[5]["agree"])}</td><td class="a c-lie">{pair(ex[4]["lie"], ex[5]["lie"])}</td></tr>')
render("fig8_one_chart", page(f"""<div class="row">
<div class="col"><span class="tag true">True chart</span><img src="{uri(IMG / 's06_tv_thermometers_consistent_en.png')}"></div>
<div class="col"><span class="tag lie">Lying chart</span><img src="{uri(IMG / 's06_tv_thermometers_conflict_en.png')}"></div>
</div>
<table><tr><th>Question to 10B-448</th><th>True chart</th><th>Lying chart</th></tr>{"".join(rows)}</table>"""))
