"""Advice turns whose fields were filled in wrongly (common.advice_problems), per stored multi-turn
run, and what common.clean_advice (agent v1.3) makes of them. No model calls.

  python eval/advice_faults.py      (writes eval/results/advice-faults-2026-11-13.md)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "agent"))
import common  # noqa: E402

RUNS = ["multiturn-2026-11-13", "multiturn-mt2-v1", "multiturn-mt2-v1.1", "multiturn-mt3-v1.1", "multiturn-mt3-v1.2",
        "multiturn-mt4-v1.1", "multiturn-mt4-v1.3"]


def main():
    res = ROOT / "eval" / "results"
    L = ["# Advice fields filled in wrongly", "",
         "Fault = tool markup inside an advice field, or a corrected caption that is empty or one word (`common.advice_problems`).",
         "For v1.2 the stored advice is the one finally accepted. \"After cleanup\" applies `common.clean_advice` (agent v1.3) offline.", "",
         "| Run | Conversations stored | With markup | Caption empty or one word | Fault after cleanup |", "|---|---|---|---|---|"]
    detail = []
    tot = [0, 0, 0, 0]
    for name in RUNS:
        path = res / f"{name}.jsonl"
        if not path.exists():
            L.append(f"| {name} | 0 | | | |")
            continue
        rows = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if not r.get("errors"):
                rows[(r["item"], r["run"])] = r
        n = markup = cap = after = 0
        for (item, run), r in sorted(rows.items()):
            n += 1
            p = common.advice_problems(r["turn2"])
            fixed, notes = common.clean_advice(r["turn2"])
            p2 = common.advice_problems(fixed)
            markup += any("markup" in x for x in p)
            cap += any(x.startswith("revised_caption is") for x in p)
            after += bool(p2)
            if p:
                detail.append(f"| {name} | {item} | {run} | {'; '.join(p)} | {'; '.join(notes) or '—'} | {'; '.join(p2) or 'none'} |")
        tot = [tot[0] + n, tot[1] + markup, tot[2] + cap, tot[3] + after]
        L.append(f"| {name} | {n} | {markup} | {cap} | {after} |")
        if name == "multiturn-mt3-v1.2":  # the runs read before the check and the cleanup were written
            L.append(f"| *first five runs (read before writing the check and the cleanup)* | {tot[0]} | {tot[1]} | {tot[2]} | {tot[3]} |")
    L.append(f"| **all** | **{tot[0]}** | **{tot[1]}** | **{tot[2]}** | **{tot[3]}** |")
    L += ["", "| Run | Item | Run no. | Fault | Cleanup | Fault after cleanup |", "|---|---|---|---|---|---|"] + detail + [""]
    out = res / "advice-faults-2026-11-13.md"
    out.write_text("\n".join(L), encoding="utf-8", newline="\n")
    print("\n".join(L[:16]))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
