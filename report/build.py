"""Inline report/data.json into report/template.html → report/index.html (the page published as an artifact)."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "data.json").read_text(encoding="utf-8"))
html = (HERE / "template.html").read_text(encoding="utf-8")
blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")      # keep "</script>" out of the JSON
(HERE / "index.html").write_text(html.replace("__DATA__", blob), encoding="utf-8")
print("index.html:", round((HERE / "index.html").stat().st_size / 1024), "KB")
