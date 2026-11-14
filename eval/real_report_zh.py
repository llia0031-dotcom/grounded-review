"""Per-ad outcomes on the Chinese real ads (split: real, lang zh): SAMR typical cases (violating) and
published cases where a regulator or court found no breach (compliant). Reads stored outputs; no model calls.

  python eval/real_report_zh.py   (writes eval/results/real-zh-2026-11-14.ads.md; private)

For each ad: the ASA decision, then every arm's decision per run with the categories it named. Group rows
count Upheld (ad, run) pairs rejected and Not upheld (ad, run) pairs approved, as eval/score.py does, for
all ads and again without the ads whose ruling turned on evidence the ad does not show.
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
FILES = ["real-zh-2026-11-14", "wordlist-real", "qwen3guard-real", "granite-guardian-real"]
ARMS = ["oneshot", "agent", "wordlist", "qwen3guard", "granite-guardian"]
BUCKET = {"MEDICAL": "disease and health claims", "ABSOLUTE": "sales ranking", "DATA": "sales ranking"}
TRAP_BUCKET = {"CN-AL-9-3": "superlatives found lawful"}


def bucket(it: dict) -> str:
    if it["labels"]:
        return BUCKET[it["labels"][0]["cat"]]
    return TRAP_BUCKET[it["basis"][0]]


def main():
    items = {i["id"]: i for i in load_items() if i["split"] == "real" and i["lang"] == "zh"}
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

    def counts(arm, ids):
        v = t = vn = tn = 0
        for iid in ids:
            for o in (out.get((arm, iid)) or {}).values():
                if items[iid]["labels"]:
                    vn += 1
                    v += bool(o.get("violations"))
                else:
                    tn += 1
                    t += not o.get("violations")
        return v, vn, t, tn

    L = ["# Real Chinese ads (SAMR cases and lawful-superlative cases): every ad, every arm", "",
         "A = approve, R = reject with the categories named; runs separated by “/”. "
         "Answer: the published decision (penalised = reject, with the categories its quoted words map to; found lawful = approve). "
         "* = the ruling turned on evidence the ad does not show.", ""]
    L += ["| Group | Arm | Upheld ad-runs rejected | Not upheld ad-runs approved |", "|---|---|---|---|"]
    groups = ["disease and health claims", "sales ranking", "superlatives found lawful"]
    for g in groups + ["all", "all without *"]:
        if g == "all":
            ids = list(items)
        elif g == "all without *":
            ids = [i for i, it in items.items() if not it["source"]["evidence_dependent"]]
        else:
            ids = [i for i, it in items.items() if bucket(it) == g]
        for arm in arms:
            v, vn, t, tn = counts(arm, ids)
            if vn or tn:
                name = ("**" + g + "**") if g.startswith("all") else g
                L.append(f"| {name} | {arm} | {v}/{vn} | {t}/{tn} |")
    L += ["", "| Ad | Group | Answer | " + " | ".join(arms) + " | Source |", "|---|---|---|" + "---|" * len(arms) + "---|"]
    for iid, it in items.items():
        ans = "R " + "+".join(sorted({l["cat"] for l in it["labels"]})) if it["labels"] else "A (found lawful)"
        star = "*" if it["source"]["evidence_dependent"] else ""
        L.append(f"| {iid}{star} | {bucket(it)} | {ans} | " + " | ".join(cell(a, iid) for a in arms)
                 + f" | [{it['source']['date']}]({it['source']['report']}) |")
    path = RES / "real-zh-2026-11-14.ads.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(L))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
