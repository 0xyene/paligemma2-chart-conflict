"""Judge verdicts for runs 3-4 (judge/adjudication.json, written by judge/merge.py).

lookup(kind, image, prompt, answer) -> verdict or None. kind: "yesno" / "which" / "read".
"""
import json
from pathlib import Path

_P = Path(__file__).resolve().parent / "adjudication.json"
_ADJ = {}
if _P.exists():
    for o in json.loads(_P.read_text(encoding="utf-8"))["items"]:
        _ADJ[(o["kind"], o["image"], o["question"], o["answer"])] = o["verdict"]


def lookup(kind, image, prompt, answer):
    return _ADJ.get((kind, image, prompt.split(" ", 2)[2], answer))


def available():
    return bool(_ADJ)
