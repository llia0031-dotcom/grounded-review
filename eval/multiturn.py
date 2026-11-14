"""Multi-turn task: review -> the advertiser asks what is wrong and how to fix it -> the advertiser
submits their own new version -> review again. Items: the test items that have a `revision`.

Per conversation:
  turn 1  review of the original ad (scored like the main run)
  turn 2  advice: answer + a corrected caption and image words. Checked three ways:
          (a) every labelled offending span of the original is gone from the corrected words,
          (b) every must_keep fact (brand, price) is still there,
          (c) a separate review of the corrected ad by the one-prompt arm (image re-rendered with
              the corrected words, OCR run on it) approves it.
  turn 3  review of the advertiser's version written into the test set (answers fixed in advance).

  AD_REVIEW_ENV_FILE=../launchpad-tracedesk/app/.env python eval/multiturn.py --repeat 2 --out multiturn-2026-11-13
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "agent"))
import common  # noqa: E402
import oneshot  # noqa: E402
import review_agent  # noqa: E402
from load import load_items  # noqa: E402
from score import norm  # noqa: E402

sys.path.insert(0, str(ROOT / "testset"))
import render  # noqa: E402

SCRATCH = Path(os.environ.get("AD_REVIEW_SCRATCH", Path(tempfile.gettempdir()) / "ad-review-multiturn-images"))


def cats(out) -> set:
    return {v["category"] for v in (out or {}).get("violations", []) if v.get("category") in common.CATEGORIES}


def rejected(out) -> bool:
    return bool((out or {}).get("violations"))


def load_mt2(name: str = "mt2") -> dict:
    """Multi-turn sets 2 and 3 (testset/items_<name>.yaml), checked with the same rules as the main test set."""
    import yaml
    from load import _check_labels, ad_text
    items, problems = {}, []
    for it in yaml.safe_load((ROOT / "testset" / f"items_{name}.yaml").read_text(encoding="utf-8")):
        _check_labels(it, it["labels"], ad_text(it), problems, it["id"])
        _check_labels(it, it["revision"]["labels"], ad_text(it, revised=True), problems, it["id"] + "/rev")
        problems += [f"{it['id']}: must_keep {f}" for f in it.get("must_keep", []) if f not in ad_text(it)]
        items[it["id"]] = it
    if problems:
        raise ValueError(chr(10).join(problems))
    return items


def conversation(item: dict, run: int, version: str = "v1") -> dict:
    t0 = time.perf_counter()
    s = review_agent.Session(item, version)
    t1 = s.review()
    t2 = s.advise()
    t3 = s.review(revised=True)
    rec = {"item": item["id"], "run": run, "turn1": t1["output"], "turn2": t2["output"], "turn3": t3["output"],
           "errors": [t["error"] for t in (t1, t2, t3) if t["error"]], "agent_usage": s.usage.as_dict(),
           "latency_s": round(time.perf_counter() - t0 + s.ocr_seconds, 2)}
    adv = t2["output"] or {}
    cap = adv.get("revised_caption", "")
    lines = adv.get("revised_image_lines", []) or []
    words = norm(cap + " " + " ".join(lines))
    rec["fix_spans_removed"] = all(norm(l["span"]) not in words for l in item["labels"] if "span" in l)
    rec["fix_facts_kept"] = all(norm(f) in words for f in item.get("must_keep", []))
    rec["fix_placeholders"] = common.placeholders(cap + " " + " ".join(lines))
    rec["fix_field_problems"] = common.advice_problems(t2["output"])
    rec["advice_sent_back"] = s.advice_sent_back
    rec["advice_raw_problems"] = common.advice_problems(s.advice_raw if s.advice_raw is not None else t2["output"])
    rec["advice_cleanup"] = s.advice_cleanup
    rec["version"] = version
    # independent review of the corrected ad
    image_path = None
    if item["kind"] == "image":
        SCRATCH.mkdir(parents=True, exist_ok=True)
        image_path = SCRATCH / f"{item['id']}-run{run}-fix.png"
        render.render_item(item, lines or item["image"]["lines"], image_path)
    check = oneshot.review(item, copy=cap or item["copy"], image_path=image_path)
    rec["fix_independent_review"] = check["output"]
    rec["fix_independent_usage"] = check["usage"]
    return rec


def summarise(rows: list[dict], items: dict) -> str:
    n = len(rows)
    t1 = sum(rejected(r["turn1"]) == bool(items[r["item"]]["labels"]) for r in rows)
    removed = sum(r["fix_spans_removed"] for r in rows)
    kept = sum(r["fix_facts_kept"] for r in rows)
    passed = sum(not rejected(r["fix_independent_review"]) for r in rows)
    all3 = sum(r["fix_spans_removed"] and r["fix_facts_kept"] and not rejected(r["fix_independent_review"]) for r in rows)
    holes = sum(bool(common.placeholders(" ".join([(r["turn2"] or {}).get("revised_caption", "")] + list((r["turn2"] or {}).get("revised_image_lines", []))))) for r in rows)
    t3_right = sum(rejected(r["turn3"]) == bool(items[r["item"]]["revision"]["labels"]) for r in rows)
    t3_cats = sum(cats(r["turn3"]) == {l["cat"] for l in items[r["item"]]["revision"]["labels"]} for r in rows)
    fixed = [r for r in rows if not items[r["item"]]["revision"]["labels"]]
    still = [r for r in rows if items[r["item"]]["revision"]["labels"]]
    cost = sum(r["agent_usage"]["cost_usd"] for r in rows)
    cost_check = sum(r["fix_independent_usage"]["cost_usd"] for r in rows)
    lat = sorted(r["latency_s"] for r in rows)
    L = ["# Multi-turn results", "",
         f"{n} conversations ({len(set(r['item'] for r in rows))} ads × runs). Errors: {sum(bool(r['errors']) for r in rows)}.", "",
         "| Measure | Result |", "|---|---|",
         f"| Turn 1: decision right | {t1}/{n} |",
         f"| Turn 2: offending words removed from the corrected version | {removed}/{n} |",
         f"| Turn 2: brand and price kept | {kept}/{n} |",
         f"| Turn 2: corrected version with unfilled template text | {holes}/{n} |",
         f"| Turn 2: advice fields filled in wrongly (tool markup in a field, empty or one-word caption) | {sum(bool(common.advice_problems(r['turn2'])) for r in rows)}/{n} |",
         f"| Turn 2: advice sent back once by the field check (v1.2 only) | {sum(bool(r.get('advice_sent_back')) for r in rows)}/{n} |",
         f"| Turn 2: advice as submitted, fields filled in wrongly (before the v1.3 cleanup) | {sum(bool(r.get('advice_raw_problems', common.advice_problems(r['turn2']))) for r in rows)}/{n} |",
         f"| Turn 2: advice repaired by the v1.3 cleanup | {sum(bool(r.get('advice_cleanup')) for r in rows)}/{n} |",
         f"| Turn 2: corrected version approved by a separate one-prompt review | {passed}/{n} |",
         f"| Turn 2: all three | {all3}/{n} |",
         f"| Turn 3: decision right on the advertiser's version | {t3_right}/{n} |",
         f"|   versions that fix everything, approved | {sum(not rejected(r['turn3']) for r in fixed)}/{len(fixed)} |",
         f"|   versions that still break a rule, rejected | {sum(rejected(r['turn3']) for r in still)}/{len(still)} |",
         f"| Turn 3: exact categories | {t3_cats}/{n} |",
         f"| Agent cost per conversation (3 turns) | US${cost / max(1, n):.4f} |",
         f"| Cost of the separate reviews | US${cost_check:.4f} total |",
         f"| Median time per conversation | {lat[len(lat) // 2]:.0f} s |", ""]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeat", type=int, default=2)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--set", choices=["test", "mt2", "mt3", "mt4"], default="test")
    ap.add_argument("--version", choices=["v1", "v1.1", "v1.2", "v1.3"], default="v1")
    a = ap.parse_args(argv)
    items = load_mt2(a.set) if a.set in ("mt2", "mt3", "mt4") else {i["id"]: i for i in load_items() if i["split"] == "test" and "revision" in i}
    out = ROOT / "eval" / "results" / f"{a.out}.jsonl"
    rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines()] if out.exists() else []
    done = {(r["item"], r["run"]) for r in rows if not r["errors"]}
    todo = [(it, run) for run in range(1, a.repeat + 1) for it in items.values() if (it["id"], run) not in done]
    print(f"{len(todo)} conversations to run")
    def safe(t):  # a failed conversation is stored with its error and retried on the next run
        try:
            return conversation(*t, a.version)
        except Exception as e:
            return {"item": t[0]["id"], "run": t[1], "errors": [f"{type(e).__name__}: {str(e)[:200]}"]}

    with ThreadPoolExecutor(a.workers) as ex, out.open("a", encoding="utf-8") as f:
        for rec in ex.map(safe, todo):
            f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
            f.flush()
            print(rec["item"], rec["run"], "errors" if rec["errors"] else "ok", flush=True)
    rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines()]
    last = {(r["item"], r["run"]): r for r in rows if not r["errors"]}
    text = summarise(list(last.values()), items)
    text = text.replace("# Multi-turn results", f"# Multi-turn results ({a.set}, agent {a.version})")
    print(text)
    out.with_suffix(".summary.md").write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
