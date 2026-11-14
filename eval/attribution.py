"""Failure attribution for the model arms: list every miss and every wrong flag with a cause.

Causes (fixed in eval/PREREGISTRATION.md):
  ocr            the labelled words are in the image but not in the OCR text
  picture        a picture-only violation was not found
  absence        a missing required statement was not found
  wrong_category the labelled words were flagged, but under another category
  missed         the violation was not flagged at all
  trap           a trap (compliant on purpose) was flagged
  extra          a category was flagged that the item is not labelled with (not a trap); each one is
                 read and marked in attribution_reading.yaml as defensible (a reading a reviewer could
                 also take under a library clause) or wrong
  clause         category found but none of its violations cites an accepted clause

  python eval/attribution.py eval/results/test-2026-11-13.jsonl --out eval/results/attribution-2026-11-13.md
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "agent"))
import common  # noqa: E402,F401
from load import load_items  # noqa: E402
from score import load_runs, norm, overlaps  # noqa: E402

OCR = json.loads((ROOT / "testset" / "ocr.json").read_text(encoding="utf-8"))
READING = ROOT / "eval" / "attribution_reading.yaml"


def attribute(rows, items):
    reading = yaml.safe_load(READING.read_text(encoding="utf-8")) if READING.exists() else {}
    reading = reading or {}
    out = []
    for r in rows:
        it = items[r["item"]]
        viols = r["output"].get("violations", [])
        cats = {v["category"] for v in viols}
        for lab in it["labels"]:
            match = [v for v in viols if v["category"] == lab["cat"]]
            if match:
                if not any(v.get("clause_id") in lab["clauses"] for v in match):
                    out.append((r, lab["cat"], "clause", ", ".join(v.get("clause_id", "") for v in match)))
                continue
            if "visual" in lab:
                cause = "picture"
            elif "absence" in lab:
                cause = "absence"
            elif it["kind"] == "image" and norm(lab["span"]) not in norm(it["copy"]) and norm(lab["span"]) not in norm(OCR[it["id"]]["text"]):
                cause = "ocr"
            elif any(overlaps(v.get("ad_quote", ""), lab["span"], it["lang"]) for v in viols):
                other = [v["category"] for v in viols if overlaps(v.get("ad_quote", ""), lab["span"], it["lang"])]
                cause = "wrong_category"
                out.append((r, lab["cat"], cause, "flagged as " + "/".join(sorted(set(other)))))
                continue
            else:
                cause = "missed"
            out.append((r, lab["cat"], cause, ""))
        for c in sorted(cats - {l["cat"] for l in it["labels"]}):
            if c == "OTHER" and it["labels"]:
                continue  # an extra OTHER on a violating ad changes nothing that is scored
            v = next(v for v in viols if v["category"] == c)
            if "trap" in it:
                cause = "trap"
            else:
                key = f"{r['arm']}|{it['id']}|{r['run']}|{c}"
                cause = "extra:" + reading.get(key, "unread")
            out.append((r, c, cause, f"{v.get('clause_id', '')}: \"{v.get('ad_quote', '')}\" — {v.get('explanation', '')[:160]}"))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--split", default="test")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    items = {i["id"]: i for i in load_items() if i["split"] == a.split}
    rows = [r for r in load_runs(a.files) if r["item"] in items and r["arm"] in {"oneshot", "agent"}]
    found = attribute(rows, items)
    L = ["# Failure attribution", "", "Every miss and wrong flag of the two model arms, two runs each. Causes are defined in `eval/attribution.py`.", ""]
    count = collections.Counter((r["arm"], cause.split(":")[0] if not cause.startswith("extra") else cause) for r, _, cause, _ in found)
    arms = ["oneshot", "agent"]
    causes = sorted({c for _, c in count})
    L += ["| Cause | " + " | ".join(arms) + " |", "|---|" + "---|" * len(arms)]
    for c in causes:
        L.append(f"| {c} | " + " | ".join(str(count[(a_, c)]) for a_ in arms) + " |")
    L += ["", "| Arm | Item | Run | Category | Cause | Detail |", "|---|---|---|---|---|---|"]
    for r, cat, cause, detail in sorted(found, key=lambda x: (x[0]["item"], x[0]["arm"], x[0]["run"])):
        L.append(f"| {r['arm']} | {r['item']} | {r['run']} | {cat} | {cause} | {detail.replace('|', '/')} |")
    text = "\n".join(L) + "\n"
    print(text)
    if a.out:
        a.out.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
