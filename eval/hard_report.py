"""Per-ad outcomes on the harder set (split: hard), grouped by what makes the ad hard: long captions,
three-frame video screenshots, single images. Reads stored outputs; no model calls.

  python eval/hard_report.py      (writes eval/results/hard-2026-11-14.ads.md)

For each ad: the answer, then every arm's decision per run with the categories it named. Group rows
count violating (ad, run) pairs rejected and trap (ad, run) pairs approved, as eval/score.py does.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))
sys.path.insert(0, str(ROOT / "agent"))
from score import load_runs  # noqa: E402
from load import load_items  # noqa: E402

RES = ROOT / "eval" / "results"
FILES = ["hard-2026-11-14", "wordlist-hard", "clip-hard", "siglip2-hard", "safeguard-vl-hard", "qwen3guard-hard", "granite-guardian-hard"]
ARMS = ["oneshot", "agent", "wordlist", "clip", "siglip2", "safeguard-vl", "qwen3guard", "granite-guardian"]


def group(it: dict) -> str:
    if it["kind"] == "text":
        return "long caption"
    return "video frames" if it["image"]["layout"] == "frames" else "single image"


def main():
    items = {i["id"]: i for i in load_items() if i["split"] == "hard"}
    rows = load_runs([RES / f"{n}.jsonl" for n in FILES if (RES / f"{n}.jsonl").exists()])
    out: dict = {}
    for r in rows:
        if r["item"] in items:
            out.setdefault((r["arm"], r["item"]), {})[r["run"]] = r["output"]
    arms = [a for a in ARMS if any(k[0] == a for k in out)]

    def cell(arm, iid):
        runs = out.get((arm, iid))
        if not runs:
            return "—"
        bits = []
        for run in sorted(runs):
            o = runs[run]
            cats = sorted({v["category"] for v in o.get("violations", [])})
            bits.append(("R " + "+".join(cats)) if o.get("violations") else "A")
        return " / ".join(bits)

    L = ["# Harder set: every ad, every arm", "",
         "A = approve, R = reject with the categories named; runs separated by “/”. Answer: the labelled categories, or approve.", ""]
    L += ["| Group | Arm | Violating ad-runs rejected | Trap ad-runs approved |", "|---|---|---|---|"]
    for g in ["long caption", "video frames", "single image", "all"]:
        ids = [i for i, it in items.items() if g == "all" or group(it) == g]
        for arm in arms:
            v = t = vn = tn = 0
            for iid in ids:
                for o in (out.get((arm, iid)) or {}).values():
                    if items[iid]["labels"]:
                        vn += 1
                        v += bool(o.get("violations"))
                    elif items[iid].get("trap"):
                        tn += 1
                        t += not o.get("violations")
            if vn or tn:
                L.append(f"| {('**' + g + '**') if g == 'all' else g} | {arm} | {v}/{vn} | {t}/{tn} |")
    L += ["", "| Ad | Group | Answer | " + " | ".join(arms) + " |", "|---|---|---|" + "---|" * len(arms)]
    for iid, it in items.items():
        ans = "R " + "+".join(sorted({l["cat"] for l in it["labels"]})) if it["labels"] else "A (trap)"
        L.append(f"| {iid} | {group(it)} | {ans} | " + " | ".join(cell(a, iid) for a in arms) + " |")
    path = RES / "hard-2026-11-14.ads.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(L))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
