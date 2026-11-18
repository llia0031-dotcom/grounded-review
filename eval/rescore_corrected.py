"""Score the held-out run again with the answer-key corrections of 2026-11-18 (testset/key_corrections_2026-11-18.yaml).

  python eval/rescore_corrected.py     (writes eval/results/test-2026-11-13.corrected-key.md)

Post hoc: the corrections were found after every run, so the preregistered numbers stay the reported ones and these
are a second scoring. Same rules as eval/score.py; quotes are not checked again (labels do not change them). A label
counts as found when the arm lists any violation of its category (score.py), so the table adds a stricter count from
eval/key_audit.py: in how many runs the arm named the missing statement itself.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))
sys.path.insert(0, str(ROOT / "agent"))
import key_audit  # noqa: E402
import score  # noqa: E402
from load import load_items  # noqa: E402

ROWS = ["items", "tp", "tn", "fp", "traps_approved", "exact_categories", "labels_span", "labels_visual", "labels_absence",
        "found_absence", "clause_checked", "clause_right"]
NAMES = {"items": "Runs scored", "tp": "Violating ads rejected", "tn": "Compliant ads approved", "fp": "Compliant ads rejected",
         "traps_approved": "Traps approved", "exact_categories": "Exactly the labelled categories",
         "labels_span": "Word labels (over runs)", "labels_visual": "Picture labels (over runs)",
         "labels_absence": "Missing-element labels (over runs)", "found_absence": "Missing-element labels found (same category)",
         "clause_checked": "Found labels with a clause checked", "clause_right": "Right clause cited"}


def main():
    frozen = {i["id"]: i for i in load_items() if i["split"] == "test"}
    corr = yaml.safe_load((ROOT / "testset" / "key_corrections_2026-11-18.yaml").read_text(encoding="utf-8"))
    fixed = copy.deepcopy(frozen)
    for c in corr:
        fixed[c["id"]]["labels"].append(c["add"])
    rows = score.load_runs([ROOT / "eval" / "results" / "test-2026-11-13.jsonl"])
    rows = [r for r in rows if r["item"] in frozen]
    L = ["# Held-out run scored with the corrected answer key (2026-11-18)", "",
         f"{len(corr)} ads gain a label for a statement their clause requires: {', '.join('`' + c['id'] + '`' for c in corr)}. "
         "The frozen item files are unchanged; the preregistered numbers remain the reported ones. Quotes are not re-checked.", "",
         "| | " + " | ".join(f"{a}, frozen key | {a}, corrected key" for a in ("oneshot", "agent")) + " |",
         "|---|" + "---|" * 4]
    res = {}
    for arm in ("oneshot", "agent"):
        ar = [r for r in rows if r["arm"] == arm]
        res[arm] = (score.score_arm(ar, frozen, False)["counts"], score.score_arm(ar, fixed, False)["counts"])
    L.append("| Decisions right | " + " | ".join(f"{res[a][0]['tp'] + res[a][0]['tn']} | {res[a][1]['tp'] + res[a][1]['tn']}" for a in ("oneshot", "agent")) + " |")
    for k in ROWS:
        L.append(f"| {NAMES[k]} | " + " | ".join(f"{res[a][0].get(k, 0)} | {res[a][1].get(k, 0)}" for a in ("oneshot", "agent")) + " |")
    # stricter: the arm named the missing statement itself
    strict = {"oneshot": [0, 0], "agent": [0, 0]}
    for c in corr:
        it = frozen[c["id"]]
        req = c["add"]["clauses"][0]
        for r in rows:
            if r["item"] == it["id"] and r["arm"] in strict:
                strict[r["arm"]][1] += 1
                strict[r["arm"]][0] += key_audit.listed(r["output"], req)
    L.append("| Runs that named the missing statement itself (the 6 corrected ads) | " +
             " | ".join(f"– | {strict[a][0]}/{strict[a][1]}" for a in ("oneshot", "agent")) + " |")
    out = ROOT / "eval" / "results" / "test-2026-11-13.corrected-key.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(L))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
