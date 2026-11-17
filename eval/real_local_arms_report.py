"""Counts for the arms that run locally on the real ads (split: real): the word list and the two text guardrails.

  python eval/real_local_arms_report.py     (writes eval/results/real-local-arms-2026-11-15.md)

Reads the stored outputs (wordlist-real.jsonl, qwen3guard-real.jsonl, granite-guardian-real.jsonl), one run per ad.
Those files hold the ads' words and are not published; this table has counts only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "testset"))
from load import load_items  # noqa: E402

ARMS = [("wordlist", "wordlist-real", "Word list"), ("qwen3guard", "qwen3guard-real", "Qwen3Guard-Gen-4B"),
        ("granite-guardian", "granite-guardian-real", "Granite Guardian 3.3 8B")]
LANGS = [("en", "English, 30 ASA rulings"), ("zh", "Chinese, 16 published cases")]


def main():
    items = {i["id"]: i for i in load_items() if i["split"] == "real"}
    res = ROOT / "eval" / "results"
    L = ["# Real ads: the arms that run locally", "",
         "One run per ad. An ad whose published decision found a breach counts as right when it is rejected; an ad that was "
         "cleared counts as right when it is approved. The stored outputs hold the ads' words and are not published.", "",
         "| Arm | Language | Ads | Decision right | Breaching ads rejected | Cleared ads approved |", "|---|---|---|---|---|---|"]
    for arm, name, label in ARMS:
        rows = [json.loads(l) for l in (res / f"{name}.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
        assert all(r["arm"] == arm and not r.get("error") for r in rows) and len({r["item"] for r in rows}) == len(rows)
        for lang, what in LANGS:
            sub = [r for r in rows if items[r["item"]]["lang"] == lang]
            bad = [r for r in sub if items[r["item"]]["labels"]]
            ok = [r for r in sub if not items[r["item"]]["labels"]]
            rej = sum(r["output"]["decision"] == "reject" for r in bad)
            app = sum(r["output"]["decision"] == "approve" for r in ok)
            L.append(f"| {label} | {what} | {len(sub)} | {rej + app}/{len(sub)} | {rej}/{len(bad)} | {app}/{len(ok)} |")
    out = res / "real-local-arms-2026-11-15.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(L))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
