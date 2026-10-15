"""Build the run-4 bundle: run4/chart_conflict_run4_bundle.zip = images/ + questions4.json.

python3.12 run4/build4.py

Run 4 follows up run 3 ("asked directly, neither 3B model answers differently on agreeing and lying charts"):
  E4  concrete comparisons (English). Run 3 asked an abstract question ("do the numbers match the bars?"); if the model
      simply doesn't understand that kind of question, run 3's flat result says little. E4 asks the same comparison in
      concrete form, and splits it into its two parts on the same image:
        cmp_big_max   "is the number above the tallest bar the largest of the six numbers?"
        cmp_big_min   "...the smallest of the six numbers?"
        cmp_small_min "is the number above the shortest bar the smallest of the six numbers?"
        cmp_small_max "...the largest of the six numbers?"
        any_more_big  "among the six numbers above the bars, is any larger than the number above the tallest bar?"
        any_less_small "…is any smaller than the number above the shortest bar?"   (exact opposites of cmp_big_max /
                      cmp_small_min: the right answer is always the reverse, so a yes-habit can't pass as a comparison)
        which_big / which_small   "which month has the tallest / shortest bar?"   (drawing only)
        read_big / read_small     "what number is written above the June bar?"    (text only; June = the tallest bar)
      The right yes/no answer is computed from the chart's spec (stimuli/<id>/spec.json), never typed by hand.
  E5  the "no" ladder (English, same 22 images): easy questions whose right answer is mostly NO, at rising difficulty, with
      a few YES ones so a model that always says no can't pass:
        L0 object  "is there a dog / cat / car in this image?" (no) · "are there any numbers in this image?" (yes)
        L1 text    "is this chart about car sales?" (no) · "...about bread sales?" (yes) ·
                   "is december one of the months on the chart?" (no) · "is march ...?" (yes)
        L2 drawing "does january have the tallest bar?" (no) · "does june have the shortest bar?" (no) · "does june have
                   the tallest bar?" (yes). On lying charts L2 is also a cue conflict (the printed numbers point the other
                   way), so the clean ladder uses the agreeing charts.
        L3 = E4's comparison questions.
      Where does "no" break down? If only at L3, run 3's flat result is about comparing, not a yes-habit.
  F   model size: run 3's 132 questions (run3/bundle/questions3.json, en + tr) on more checkpoints.
Every row is answered by every model in the notebook (3B in float32 and bfloat16, 10B and 28B in bfloat16).
"""
import json
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R4 = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "run3"))
from build3 import MARKS, prompts as prompts3  # noqa: E402

# Per chart: item names (as printed), the drawn values, the printed values on the lying version, and the wording.
#   big / small   phrase for the mark with the largest / smallest drawn value
#   ref           how the number belongs to the mark ("the number above")
#   group         what "the largest of ..." ranges over
#   hi / lo       "largest" / "smallest" (or "highest" / "lowest")
#   which         question asking for the item whose mark is big / small ({} = big or small phrase)
#   read          question asking for one item's printed value ({} = item name)
#   alias         extra accepted spellings for item names
C = {
    "s01_newspaper_bars": dict(
        names=["jan", "feb", "mar", "apr", "may", "jun"], read_names=["january", "february", "march", "april", "may", "june"],
        big="the tallest bar", small="the shortest bar", ref="the number above", group="the six numbers above the bars",
        which="which month has {}?", read="what number is written above the {} bar?",
        alias={"jan": ["january"], "jun": ["june"]}),
    "s03_slide_donut": dict(
        names=["nimbus", "orca", "pixa", "zento"],
        big="the biggest slice", small="the smallest slice", ref="the percentage for", group="the four percentages",
        which="which brand has {}?", read="what percentage is written for {}?"),
    "s04_app_screentime": dict(
        names=["dorvi", "gisano", "kuvelo", "libezu", "tovra"],
        big="the longest bar", small="the shortest bar", ref="the time next to", group="the five times",
        which="which app has {}?", read="what time is written for {}?"),
    "s05_poster_pictogram": dict(
        names=["aster", "mira", "nova", "lumen"],
        big="the longest row of tree icons", small="the shortest row of tree icons", ref="the total next to",
        group="the four totals", which="which school has {}?", read="what total is written for {}?"),
    "s06_tv_thermometers": dict(
        names=["avlen", "berim", "covra", "dimel"],
        big="the fullest thermometer", small="the emptiest thermometer", ref="the temperature under",
        group="the four temperatures", hi="highest", lo="lowest",
        which="which city has {}?", read="what temperature is shown for {}?"),
    "s07_dashboard_gauges": dict(
        names=["alpha-01", "beta-02", "gamma-03"],
        big="the fullest gauge", small="the emptiest gauge", ref="the number under", group="the three numbers under the gauges",
        which="which server has {}?", read="what number is shown under the {} gauge?",
        alias={"alpha-01": ["alpha"], "beta-02": ["beta"], "gamma-03": ["gamma"]}),
    "s08_paper_grouped_bars": dict(
        names=["roan", "kerf", "ossel"],
        big="the tallest bar", small="the shortest bar", ref="the number on", group="the three numbers for quorlet",
        prefix="on quorlet, ", which="which method has {}?", read="what number is written on the {} bar?"),
    "s09_notebook_sketch": dict(
        names=["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
        read_names=["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
        big="the highest point of the line", small="the lowest point of the line", ref="the number at",
        group="the seven numbers on the line", which="which day is {}?", read="what number is written at {}'s point?",
        alias={"mon": ["monday"], "sun": ["sunday"]}),
    "s11_finance_watchlist": dict(
        names=["kdnl", "mxra", "tlwy", "vesk"],
        big="the line that rises the most", small="the line that falls the most", ref="the percentage change next to",
        group="the four percentage changes", which="which stock has {}?", read="what percentage change is shown for {}?",
        alias={"kdnl": ["korandel"], "mxra": ["mirexa"], "tlwy": ["talnway"], "vesk": ["vesker"]}),
    "s13_widget_battery": dict(
        names=["phone", "earbuds", "watch", "tablet"],
        big="the fullest ring", small="the emptiest ring", ref="the percentage in", group="the four percentages",
        which="which device has {}?", read="what percentage is shown for the {}?"),
    "s14_spreadsheet_databars": dict(
        names=["north", "south", "east", "west", "central"],
        big="the longest data bar", small="the shortest data bar", ref="the number next to",
        group="the five region numbers", which="which region has {}?", read="what number is shown for {}?"),
}


def values(sid):
    d = json.loads((ROOT / "stimuli" / sid / "spec.json").read_text(encoding="utf-8"))["data"]
    if sid == "s04_app_screentime":
        return d["visual_minutes"], d["conflict_label_minutes"], d["visual_labels"]["en"], d["conflict_labels"]["en"]
    if sid == "s06_tv_thermometers":
        return d["visual"], d["conflict_readouts"], None, None
    if sid == "s07_dashboard_gauges":
        return d["visual"], d["conflict_readouts"], None, None
    if sid == "s08_paper_grouped_bars":
        return d["visual"]["Quorlet"], d["conflict_labels"]["Quorlet"], None, None
    if sid == "s11_finance_watchlist":
        return d["visual_change_pct"], d["conflict_change_pct"], None, None
    return d["visual"], d["conflict_labels"], None, None


def e4_rows():
    rows = []
    for sid, c in C.items():
        vis, lie, vis_txt, lie_txt = values(sid)
        assert len(vis) == len(lie) == len(c["names"]), sid
        big, small = vis.index(max(vis)), vis.index(min(vis))
        hi, lo, pre = c.get("hi", "largest"), c.get("lo", "smallest"), c.get("prefix", "")
        read_names = c.get("read_names", c["names"])
        for cond in ("consistent", "conflict"):
            lab = vis if cond == "consistent" else lie
            txt = (vis_txt if cond == "consistent" else lie_txt) if vis_txt else None
            img = f"{sid}_{cond}_en.png"
            base = {"exp": "E4", "image": img, "stimulus": sid, "cond": cond, "lang": "en"}
            for qt, mark, word, test in (("cmp_big_max", c["big"], hi, lab.index(max(lab)) == big),
                                         ("cmp_big_min", c["big"], lo, lab.index(min(lab)) == big),
                                         ("cmp_small_min", c["small"], lo, lab.index(min(lab)) == small),
                                         ("cmp_small_max", c["small"], hi, lab.index(max(lab)) == small)):
                rows.append({**base, "qtype": qt, "prompt": f"answer en {pre}is {c['ref']} {mark} the {word} of {c['group']}?",
                             "right": "yes" if test else "no"})
            # exact opposites of cmp_big_max / cmp_small_min, for the yes-habit: the right answer is always the reverse
            more, less = {"largest": "larger", "highest": "higher"}[hi], {"smallest": "smaller", "lowest": "lower"}[lo]
            for qt, mark, word, test in (("any_more_big", c["big"], more, lab.index(max(lab)) != big),
                                         ("any_less_small", c["small"], less, lab.index(min(lab)) != small)):
                rows.append({**base, "qtype": qt, "prompt": f"answer en {pre}among {c['group']}, is any {word} than {c['ref']} {mark}?",
                             "right": "yes" if test else "no"})
            for qt, idx, mark in (("which_big", big, c["big"]), ("which_small", small, c["small"])):
                names = [c["names"][idx]] + c.get("alias", {}).get(c["names"][idx], [])
                rows.append({**base, "qtype": qt, "prompt": f"answer en {pre}{c['which'].format(mark)}", "right": names, "item": c["names"][idx]})
            for qt, idx in (("read_big", big), ("read_small", small)):
                label = txt[idx] if txt else lab[idx]
                drawn = (vis_txt[idx] if vis_txt else vis[idx])
                rows.append({**base, "qtype": qt, "prompt": f"answer en {pre}{c['read'].format(read_names[idx])}",
                             "right": str(label), "drawn": str(drawn), "item": c["names"][idx]})
    return rows


# E5 wording per chart: topic (yes, no), what the items are called, an item that is not on the chart, one that is,
# and how to say "<item> has <mark>" when the default "does <item> have <mark>?" reads badly
E5 = {
    "s01_newspaper_bars": dict(topic=("bread sales", "car sales"), kind="months", absent="december", present="march"),
    "s03_slide_donut": dict(topic=("smartphone market share", "rainfall"), kind="brands", absent="veltra", present="orca"),
    "s04_app_screentime": dict(topic=("screen time", "electricity prices"), kind="apps", absent="zumo", present="kuvelo"),
    "s05_poster_pictogram": dict(topic=("trees planted by schools", "football scores"), kind="schools", absent="orion", present="mira"),
    "s06_tv_thermometers": dict(topic=("temperatures", "stock prices"), kind="cities", absent="marlo", present="covra"),
    "s07_dashboard_gauges": dict(topic=("cpu load", "hospital visits"), kind="servers", absent="delta-04", present="alpha-01"),
    "s08_paper_grouped_bars": dict(topic=("the accuracy of methods", "house prices"), kind="methods", absent="quill", present="roan"),
    "s09_notebook_sketch": dict(topic=("daily app users", "rainfall"), kind="days", absent="january", present="wednesday",
                                has="is {} at {}?"),
    "s11_finance_watchlist": dict(topic=("stock prices", "temperatures"), kind="stocks", absent="brix", present="vesk"),
    "s13_widget_battery": dict(topic=("battery levels", "train delays"), kind="devices", absent="laptop", present="watch",
                               has="is {} the device with {}?"),
    "s14_spreadsheet_databars": dict(topic=("revenue by region", "air pollution"), kind="regions", absent="coast", present="west"),
}


def e5_rows():
    rows = []
    for sid, c in C.items():
        e = E5[sid]
        vis = values(sid)[0]
        big, small = vis.index(max(vis)), vis.index(min(vis))
        nm = c.get("read_names", c["names"])
        pre, has = c.get("prefix", ""), e.get("has", "does {} have {}?")
        qs = [("L0", "obj_dog", "is there a dog in this image?", "no"),
              ("L0", "obj_cat", "is there a cat in this image?", "no"),
              ("L0", "obj_car", "is there a car in this image?", "no"),
              ("L0", "obj_numbers", "are there any numbers in this image?", "yes"),
              ("L1", "topic_no", f"is this chart about {e['topic'][1]}?", "no"),
              ("L1", "topic_yes", f"is this chart about {e['topic'][0]}?", "yes"),
              ("L1", "name_absent", f"is {e['absent']} one of the {e['kind']} on the chart?", "no"),
              ("L1", "name_present", f"is {e['present']} one of the {e['kind']} on the chart?", "yes"),
              ("L2", "draw_small_big", pre + has.format(nm[small], c["big"]), "no"),
              ("L2", "draw_big_small", pre + has.format(nm[big], c["small"]), "no"),
              ("L2", "draw_big_big", pre + has.format(nm[big], c["big"]), "yes")]
        for cond in ("consistent", "conflict"):
            for level, qt, q, right in qs:
                rows.append({"exp": "E5", "image": f"{sid}_{cond}_en.png", "stimulus": sid, "cond": cond, "lang": "en",
                             "level": level, "qtype": qt, "prompt": f"answer en {q}", "right": right})
    return rows


def f_rows():
    rows = []
    for sid in MARKS:
        meta = json.loads((ROOT / "stimuli" / sid / "spec.json").read_text(encoding="utf-8"))
        for cond in ("consistent", "conflict"):
            for lang in ("en", "tr"):
                for qtype, prompt in prompts3(sid, lang).items():
                    right = ("yes" if cond == "consistent" else "no") if qtype == "match" else ("no" if cond == "consistent" else "yes")
                    rows.append({"exp": "F", "image": f"{sid}_{cond}_{lang}.png", "stimulus": sid, "mechanism": meta["mechanism"],
                                 "cond": cond, "lang": lang, "qtype": qtype, "prompt": prompt, "right": right})
    return rows


def main():
    rows = e4_rows() + e5_rows() + f_rows()
    bundle = R4 / "bundle"
    if bundle.exists():
        shutil.rmtree(bundle)
    (bundle / "images").mkdir(parents=True)
    for img in sorted({r["image"] for r in rows}):
        shutil.copyfile(ROOT / "images" / img, bundle / "images" / img)
    shutil.copyfile(ROOT / "run3" / "results" / "answers_run3.csv", bundle / "run3_answers.csv")
    (bundle / "questions4.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    zp = R4 / "chart_conflict_run4_bundle.zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(bundle.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(bundle))
    n = {x: sum(r["exp"] == x for r in rows) for x in ("E4", "E5", "F")}
    print(f"wrote {zp.name} ({zp.stat().st_size / 1e6:.1f} MB): {len({r['image'] for r in rows})} images, "
          + ", ".join(f"{k} {v}" for k, v in n.items()) + " questions")


if __name__ == "__main__":
    main()
