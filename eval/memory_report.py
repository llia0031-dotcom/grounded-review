"""Memory test: the agent with and without earlier decisions (split: memory).

  python eval/memory_report.py eval/results/memory-2026-11-16.jsonl

Writes eval/results/<name>.report.md: decisions right per arm, by relation (follow / distinguish) and by type; how
often all runs of an ad agree; on follow-reject ads, how often the clause and category of the earlier decision are
cited; on distinguish ads, how often the arm repeats the earlier decision when it should not; cost per review; and
a per-ad table. The ads are fictional, so the table can be public.
"""
from __future__ import annotations

import argparse
import collections
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "testset"))
sys.path.insert(0, str(ROOT / "agent"))
import memory  # noqa: E402
from load import load_items  # noqa: E402

ARMS = ["agent", "agent_memory"]
NAMES = {"agent": "Agent, no memory", "agent_memory": "Agent with memory"}
TYPES = ["follow-reject", "follow-approve", "fixed", "qualified", "history", "dropped", "new-violation"]


def right(item: dict, decision: str) -> bool:
    return decision == ("reject" if item["labels"] else "approve")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("file", type=Path)
    a = ap.parse_args(argv)
    items = {i["id"]: i for i in load_items() if i["split"] == "memory"}
    prec = {r["id"]: r for r in memory.load()}
    rows = [json.loads(l) for l in a.file.read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = [r for r in rows if r["item"] in items and r["arm"] in ARMS]
    errors = [r for r in rows if r.get("error")]
    by = collections.defaultdict(list)  # (arm, item) -> rows
    for r in rows:
        if not r.get("error"):
            by[(r["arm"], r["item"])].append(r)
    runs = max((r["run"] for r in rows), default=0)

    def dec(r):
        return (r.get("output") or {}).get("decision", "error")

    out = [f"# Memory test: results ({a.file.name})", "",
           f"{len(items)} fictional text ads (12 Chinese, 12 English), {runs} runs per arm, model claude-haiku-5-5. "
           f"Stored results: {len(rows) - len(errors)}; failed requests: {len(errors)}.", ""]

    # ------------------------------------------------------------ headline table
    head = ["| | " + " | ".join(NAMES[x] for x in ARMS) + " |", "|---|" + "---|" * len(ARMS)]

    def line(label, fn):
        return f"| {label} | " + " | ".join(fn(arm) for arm in ARMS) + " |"

    def count(arm, ids):
        rs = [r for i in ids for r in by[(arm, i)]]
        return sum(right(items[r["item"]], dec(r)) for r in rs), len(rs)

    def frac(arm, ids):
        k, n = count(arm, ids)
        return f"{k}/{n}"

    follow = [i for i in items if items[i]["relation"] == "follow"]
    dist = [i for i in items if items[i]["relation"] == "distinguish"]
    rows_t = head + [line("Decisions right, all ads", lambda arm: frac(arm, list(items))),
                     line("Follow: the earlier decision applies", lambda arm: frac(arm, follow)),
                     line("Distinguish: it does not apply (traps)", lambda arm: frac(arm, dist))]
    for t in TYPES:
        ids = [i for i in items if items[i]["type"] == t]
        rows_t.append(line(f"&nbsp;&nbsp;{t} ({len(ids)} ads)", lambda arm, ids=ids: frac(arm, ids)))

    def agree(arm):
        n = sum(1 for i in items if len({dec(r) for r in by[(arm, i)]}) == 1 and len(by[(arm, i)]) == runs)
        return f"{n}/{len(items)}"

    def clause_match(arm):
        ids = [i for i in items if items[i]["type"] == "follow-reject"]
        rs = [r for i in ids for r in by[(arm, i)]]
        c = sum(any(v.get("clause_id") == prec[items[r["item"]]["precedent"]]["violations"][0]["clause"]
                    for v in r["output"]["violations"]) for r in rs)
        k = sum(any(v.get("category") == prec[items[r["item"]]["precedent"]]["violations"][0]["cat"]
                    for v in r["output"]["violations"]) for r in rs)
        return f"clause {c}/{len(rs)}, category {k}/{len(rs)}"

    def carried(arm):
        rs = [r for i in dist for r in by[(arm, i)]]
        n = sum(dec(r) == prec[items[r["item"]]["precedent"]]["decision"] for r in rs)
        return f"{n}/{len(rs)}"

    def cost(arm):
        rs = [r for i in items for r in by[(arm, i)]]
        c = [r["usage"]["cost_usd"] for r in rs]
        calls = [r["usage"]["calls"] for r in rs]
        return f"US${statistics.mean(c):.5f} ({statistics.mean(calls):.1f} calls)" if c else "-"

    def recalled(arm):
        rs = [r for i in items for r in by[(arm, i)] if "recalled" in r]
        if not rs:
            return "-"
        hit = sum(items[r["item"]]["precedent"] in r["recalled"] for r in rs)
        return f"{hit}/{len(rs)}"

    rows_t += [line("All runs of an ad agree", agree),
               line("Follow-reject: the earlier clause and category cited", clause_match),
               line("Distinguish: repeats the earlier decision", carried),
               line("The matching earlier decision was shown", recalled),
               line("Cost per review, batch price", cost)]
    out += rows_t
    total = sum(r["usage"]["cost_usd"] for r in rows)
    out += ["", f"Total cost of this file: US${total:.4f} (batch price).", ""]

    # ------------------------------------------------------------ per ad
    out += ["## Per ad", "", "Decisions of each run, in run order (A approve, R reject). Answer: the decision fixed when the ad was written.", "",
            "| Ad | Type | Earlier decision | Answer | " + " | ".join(NAMES[x] for x in ARMS) + " |",
            "|---|---|---|---|" + "---|" * len(ARMS)]
    for i, it in items.items():
        p = prec[it["precedent"]]
        cells = []
        for arm in ARMS:
            rs = sorted(by[(arm, i)], key=lambda r: r["run"])
            cells.append(" ".join(("A" if dec(r) == "approve" else "R" if dec(r) == "reject" else "?") for r in rs) or "-")
        ans = "reject" if it["labels"] else "approve"
        out.append(f"| `{i}` | {it['type']} | {p['decision']} (`{p['id']}`) | {ans} | " + " | ".join(cells) + " |")
    out += ["", "## Ads", ""]
    for i, it in items.items():
        p = prec[it["precedent"]]
        out.append(f"- `{i}` ({it['advertiser']}, {it['type']}): {it['copy']}  \n  Earlier (`{p['id']}`, {p['decision']}): {p['copy']}")
    text = "\n".join(out) + "\n"
    dest = a.file.with_suffix(".report.md")
    dest.write_text(text, encoding="utf-8", newline="\n")
    print(text)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
