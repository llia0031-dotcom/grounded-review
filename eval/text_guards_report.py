"""Decision results on the text ads only, by language: the two model arms, the word list and the two
open text guardrail models (baselines/text_guards.py). Reads stored outputs; no model calls.

  python eval/text_guards_report.py --split test   (writes eval/results/text-guards-<split>.md)

Counts are over (ad, run) pairs, as in eval/score.py: the model arms ran twice, the others once.
"qwen3guard (Unsafe only)" re-reads the stored Qwen3Guard answers, counting Controversial as approve.
"""
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))
sys.path.insert(0, str(ROOT / "agent"))
from score import load_runs  # noqa: E402
from load import load_items  # noqa: E402

FILES = {"test": ["test-2026-11-13", "wordlist-test", "qwen3guard-test", "granite-guardian-test"],
         "dev": ["dev-1", "dev-2", "wordlist-dev", "qwen3guard-dev", "granite-guardian-dev"]}
ORDER = ["oneshot", "agent", "wordlist", "qwen3guard", "qwen3guard (Unsafe only)", "granite-guardian"]


def decision(r: dict, arm: str) -> str:
    if arm == "qwen3guard (Unsafe only)":
        return "reject" if (r["output"].get("parsed") or {}).get("safety") == "Unsafe" else "approve"
    return "reject" if r["output"].get("violations") else "approve"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="test")
    a = ap.parse_args()
    items = {i["id"]: i for i in load_items() if i["split"] == a.split and i["kind"] == "text"}
    res = ROOT / "eval" / "results"
    rows = [r for r in load_runs([res / f"{n}.jsonl" for n in FILES[a.split] if (res / f"{n}.jsonl").exists()])
            if r["item"] in items]
    by_arm: dict[str, list] = {}
    for r in rows:
        by_arm.setdefault(r["arm"], []).append(r)
        if r["arm"] == "qwen3guard":
            by_arm.setdefault("qwen3guard (Unsafe only)", []).append(r)
    n_viol = sum(1 for i in items.values() if i.get("labels"))
    n_trap = sum(1 for i in items.values() if i.get("trap"))
    L = [f"# Text ads only ({a.split} split): decision by language", "",
         f"{len(items)} text ads: {n_viol} break a rule, {len(items) - n_viol} compliant ({n_trap} of them traps). "
         "Counts are over (ad, run) pairs; the model arms ran twice, the others once.", "",
         "| Arm | Language | Ad × run | Decision right | Violating ads rejected | Traps approved | Median latency (s) |",
         "|---|---|---|---|---|---|---|"]
    for arm in [x for x in ORDER if x in by_arm]:
        for lang in ["zh", "en", "all"]:
            rr = [r for r in by_arm[arm] if lang == "all" or items[r["item"]]["lang"] == lang]
            right = sum((decision(r, arm) == "reject") == bool(items[r["item"]].get("labels")) for r in rr)
            v = [r for r in rr if items[r["item"]].get("labels")]
            t = [r for r in rr if items[r["item"]].get("trap")]
            vc = sum(decision(r, arm) == "reject" for r in v)
            ta = sum(decision(r, arm) == "approve" for r in t)
            lat = [r["latency_s"] for r in rr if r.get("latency_s") is not None]
            med = f"{statistics.median(lat):.1f}" if lat else "—"
            name = f"**{arm}**" if lang == "all" else arm
            L.append(f"| {name} | {lang} | {len(rr)} | {right}/{len(rr)} ({100 * right / max(len(rr), 1):.0f}%) | "
                     f"{vc}/{len(v)} | {ta}/{len(t)} | {med} |")
    L += ["", "## Every answer of the two guardrail models", "",
          "| Ad | Answer is | qwen3guard | granite-guardian |", "|---|---|---|---|"]
    g = {(r["arm"], r["item"]): r for r in rows if r["arm"] in ("qwen3guard", "granite-guardian")}
    for iid, it in items.items():
        q, gr = g.get(("qwen3guard", iid)), g.get(("granite-guardian", iid))
        truth = "reject (" + ", ".join(x["cat"] for x in it["labels"]) + ")" if it.get("labels") else ("approve (trap)" if it.get("trap") else "approve")
        qs = " / ".join(str(x) for x in ((q["output"].get("parsed") or {}).values())) if q else "—"
        gs = str((gr["output"].get("parsed") or {}).get("score")) if gr else "—"
        L.append(f"| {iid} | {truth} | {qs} | {gs} |")
    out = res / f"text-guards-{a.split}.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(L[:30]))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
