"""Screenshot one section of the report in the blog's words (true / lying / no-numbers chart).

usage: python3.12 blog_figures/post/shot_report.py <section_id> <model 224|448> <out.png> [width] [css selectors to hide]
Figure 6 inputs:
  python3.12 blog_figures/post/shot_report.py pull 224 blog_figures/post/pull224.png 760 "#pull > h2, #pull > p, #pull > ul, #pullPlot text.t-txt"
  python3.12 blog_figures/post/shot_report.py pull 448 blog_figures/post/pull448.png 760 "#pull > h2, #pull > p, #pull > ul, #pullPlot text.t-txt"
Headless Chrome gets its own throwaway profile and a 60 s timeout.
"""
import re, shutil, subprocess, sys, tempfile, time
from pathlib import Path
from PIL import Image, ImageChops

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
REPORT = Path(__file__).resolve().parents[2] / "report"
sec, model, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
W = int(sys.argv[4]) if len(sys.argv) > 4 else 760
hide = sys.argv[5] if len(sys.argv) > 5 else ""   # extra CSS selectors to hide inside the section

html = (REPORT / "index.html").read_text()
assert 'let MODEL = "448";' in html
html = html.replace('let MODEL = "448";', f'let MODEL = "{model}";', 1)
css = f"""<style>
nav, header, footer, .toc, #toc {{ display:none !important; }}
main > section:not(#{sec}) {{ display:none !important; }}
main {{ margin:0 !important; padding:0 12px !important; max-width:none !important; }}
body {{ background:#fff !important; }}
#{sec} {{ padding-top:8px !important; margin:0 !important; border:0 !important; }}
#{sec} .controls, #{sec} .eyebrow {{ display:none !important; }}
{hide} {{ display:none !important; }}
</style>"""
js = f"""<script>
window.addEventListener('load', () => {{ 
  setTimeout(() => {{
    const R = [["no-numbers version","no-numbers chart"],["normal version","true chart"],["conflict version","lying chart"],
               ["(normal, conflict only)","(true and lying only)"],["NORMAL VERSION","TRUE CHART"],["CONFLICT VERSION","LYING CHART"]];
    const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let n;
    while ((n = w.nextNode())) {{ let t = n.nodeValue; R.forEach(([a,b]) => t = t.split(a).join(b)); if (t !== n.nodeValue) n.nodeValue = t; }}
  }}, 3000); }});
</script>"""
html = ("<!doctype html><html data-theme=\"light\"><head><meta charset=\"utf-8\">" + css + "</head><body>" + html + js + "</body></html>")
tmpdir = Path(tempfile.mkdtemp(prefix="fbshot-"))
# keep relative img paths working
(tmpdir / "img").symlink_to(REPORT / "img") if (REPORT / "img").exists() else None
src = tmpdir / "page.html"; src.write_text(html)
out.unlink(missing_ok=True)
profile = tempfile.mkdtemp(prefix="fbshot-chrome-")
proc = subprocess.Popen([CHROME, "--headless=new", f"--user-data-dir={profile}", "--no-first-run", "--no-default-browser-check",
    "--disable-component-update", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
    "--virtual-time-budget=8000", f"--window-size={W},3000", f"--screenshot={out}", src.as_uri()],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    deadline, last = time.time() + 60, -1
    while time.time() < deadline:
        if out.exists() and out.stat().st_size > 0 and out.stat().st_size == last: break
        last = out.stat().st_size if out.exists() else -1
        time.sleep(0.4)
    else: raise TimeoutError("no screenshot")
finally:
    proc.kill(); proc.wait(timeout=10); shutil.rmtree(profile, ignore_errors=True); shutil.rmtree(tmpdir, ignore_errors=True)
im = Image.open(out).convert("RGB")
bg = Image.new("RGB", im.size, im.getpixel((2, im.height - 3)))
bbox = ImageChops.difference(im, bg).getbbox()
if bbox:
    l, t, r, b = bbox; im = im.crop((max(l-16,0), max(t-16,0), min(r+16,im.width), min(b+16,im.height)))
im.save(out); print(out, im.size)
