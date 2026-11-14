"""Score stored outputs against the answers fixed in the test set.

  python eval/score.py eval/results/test-2026-11-13.jsonl [more .jsonl files] --split test --out eval/results/test-2026-11-13.summary.md

Every arm (model or baseline) is stored in the same shape: per (arm, item, run) an output
{"decision", "violations": [{"category", "clause_id", "ad_quote", "visual_evidence", "policy_quote"}]}.
Rules (fixed before the held-out run, see eval/PREREGISTRATION.md):
  item decision     reject if the output names at least one violation; the answer is reject if the item has labels
  category          an (item, category) pair; predicted if any violation has that category
  clause cited      for a gold label whose category was predicted: does a predicted violation of that
                    category cite one of the label's accepted clause ids
  located           for a gold span label whose category was predicted: does that violation's ad_quote
                    overlap the span (one contains the other, or they share 4 Chinese / 8 other characters)
  quotes verbatim   evidence-check's script on every non-empty ad_quote (against the ad's true words)
                    and every policy_quote (against the text of the clause it cites)
"""
from __future__ import annotations

import argparse
import collections
import json
import statistics
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "agent"))
import common  # noqa: E402
from load import load_items  # noqa: E402

CATS = common.CATEGORIES


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "").lower()
    return "".join(ch for ch in s if ch.isalnum())


def lcs_len(a: str, b: str) -> int:
    best, prev = 0, [0] * (len(b) + 1)
    for ca in a:
        cur = [0]
        for j, cb in enumerate(b, 1):
            v = prev[j - 1] + 1 if ca == cb else 0
            cur.append(v)
            best = max(best, v)
        prev = cur
    return best


def overlaps(quote: str, span: str, lang: str) -> bool:
    q, s = norm(quote), norm(span)
    if not q or not s:
        return False
    if s in q or q in s:
        return True
    return lcs_len(q, s) >= (4 if lang == "zh" else 8)


def load_runs(paths: list[Path]) -> list[dict]:
    rows = []
    for p in paths:
        for line in p.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r.get("output") is not None and not r.get("error"):
                rows.append(r)
    # keep the last stored result per (arm, item, run)
    last = {}
    for r in rows:
        last[(r["arm"], r["item"], r["run"])] = r
    return list(last.values())


def score_arm(rows: list[dict], items: dict, check_quotes_on: bool = True) -> dict:
    s = collections.Counter()
    per_cat = {c: collections.Counter() for c in CATS}
    per_lang = {l: collections.Counter() for l in ("zh", "en")}
    quote_fail = []
    costs, lats, calls = [], [], []
    errors = []
    for r in rows:
        it = items[r["item"]]
        out = r["output"]
        allv = out.get("violations", [])
        viols = [v for v in allv if v.get("category") in CATS]
        pred_reject = bool(allv)  # a hit outside the nine categories (word lists: OTHER) still rejects
        gold_reject = bool(it["labels"])
        s["items"] += 1
        s["tp" if pred_reject and gold_reject else "fp" if pred_reject else "fn" if gold_reject else "tn"] += 1
        pl = per_lang[it["lang"]]
        pl["items"] += 1
        pl["correct"] += pred_reject == gold_reject
        if "trap" in it:
            s["traps"] += 1
            s["traps_approved"] += not pred_reject
        gold_cats = {l["cat"] for l in it["labels"]}
        pred_cats = {v["category"] for v in viols}
        for c in CATS:
            pc = per_cat[c]
            if c in gold_cats and c in pred_cats:
                pc["tp"] += 1
            elif c in pred_cats:
                pc["fp"] += 1
            elif c in gold_cats:
                pc["fn"] += 1
        if gold_cats == pred_cats:
            s["exact_categories"] += 1
        # labels: clause cited, located, visual recall
        for lab in it["labels"]:
            kind = next(k for k in ("span", "visual", "absence") if k in lab)
            s[f"labels_{kind}"] += 1
            match = [v for v in viols if v["category"] == lab["cat"]]
            if not match:
                errors.append({"item": it["id"], "run": r["run"], "type": "missed", "cat": lab["cat"], "kind": kind})
                continue
            s[f"found_{kind}"] += 1
            if "clause_id" in match[0]:
                s["clause_checked"] += 1
                s["clause_right"] += any(v.get("clause_id") in lab["clauses"] for v in match)
            if kind == "span":
                s["located"] += any(overlaps(v.get("ad_quote", ""), lab["span"], it["lang"]) for v in match)
        for c in pred_cats - gold_cats:
            errors.append({"item": it["id"], "run": r["run"], "type": "extra", "cat": c, "trap": "trap" in it})
        # quotes
        if check_quotes_on and allv and "policy_quote" in allv[0]:
            res = common.check_quotes(common.gold_ad_source(it), allv)
            for v, q in zip(allv, res):
                if q["ad"] is not None:
                    s["ad_quotes"] += 1
                    s["ad_quotes_ok"] += q["ad"] == "supported"
                    if q["ad"] != "supported":
                        quote_fail.append({"item": it["id"], "run": r["run"], "side": "ad", "status": q["ad"], "quote": v["ad_quote"]})
                s["policy_quotes"] += 1
                s["policy_quotes_ok"] += q["policy"] == "supported"
                if q["policy"] != "supported":
                    quote_fail.append({"item": it["id"], "run": r["run"], "side": "policy", "status": q["policy"], "clause": v.get("clause_id"), "quote": v.get("policy_quote")})
        u = r.get("usage", {})
        costs.append(u.get("cost_usd", 0.0))
        calls.append(u.get("calls", 0))
        if r.get("latency_s") is not None:
            lats.append(r["latency_s"])
    s["cost_total"] = round(sum(costs), 4)
    return {"counts": dict(s), "per_cat": {c: dict(v) for c, v in per_cat.items()}, "per_lang": {k: dict(v) for k, v in per_lang.items()},
            "cost_per_item": sum(costs) / max(1, len(costs)), "latency_median": statistics.median(lats) if lats else None,
            "calls_mean": sum(calls) / max(1, len(calls)), "errors": errors, "quote_fail": quote_fail}


def agreement(rows: list[dict]) -> dict:
    by = collections.defaultdict(dict)
    for r in rows:
        allv = r["output"].get("violations", [])
        by[r["item"]][r["run"]] = (bool(allv), frozenset(v["category"] for v in allv if v.get("category") in CATS))
    pairs = [v for v in by.values() if 1 in v and 2 in v]
    if not pairs:
        return {}
    return {"items": len(pairs), "same_decision": sum(p[1][0] == p[2][0] for p in pairs),
            "same_categories": sum(p[1][1] == p[2][1] for p in pairs)}


def pct(a, b):
    return f"{a}/{b} ({a / b:.0%})" if b else "n/a"


def prf(c):
    tp, fp, fn = c.get("tp", 0), c.get("fp", 0), c.get("fn", 0)
    p = tp / (tp + fp) if tp + fp else None
    r = tp / (tp + fn) if tp + fn else None
    f = lambda x: "–" if x is None else f"{x:.2f}"
    return f(p), f(r)


def report(results: dict, split: str) -> str:
    arms = list(results)
    L = [f"# Results ({split})", ""]
    L.append("| | " + " | ".join(arms) + " |")
    L.append("|---|" + "---|" * len(arms))

    def row(name, fn):
        L.append(f"| {name} | " + " | ".join(fn(results[a]) for a in arms) + " |")

    c = lambda a: a["counts"]
    row("Runs scored (items × runs)", lambda a: str(c(a)["items"]))
    row("Decision right (approve / reject)", lambda a: pct(c(a).get("tp", 0) + c(a).get("tn", 0), c(a)["items"]))
    row("Violating ads rejected (recall)", lambda a: pct(c(a).get("tp", 0), c(a).get("tp", 0) + c(a).get("fn", 0)))
    row("Rejections that were right (precision)", lambda a: pct(c(a).get("tp", 0), c(a).get("tp", 0) + c(a).get("fp", 0)))
    row("Traps approved", lambda a: pct(c(a).get("traps_approved", 0), c(a).get("traps", 0)))
    row("Exact set of categories", lambda a: pct(c(a).get("exact_categories", 0), c(a)["items"]))
    row("Word violations found", lambda a: pct(c(a).get("found_span", 0), c(a).get("labels_span", 0)))
    row("Picture-only violations found", lambda a: pct(c(a).get("found_visual", 0), c(a).get("labels_visual", 0)))
    row("Missing-element violations found", lambda a: pct(c(a).get("found_absence", 0), c(a).get("labels_absence", 0)))
    row("Right clause cited (found labels)", lambda a: pct(c(a).get("clause_right", 0), c(a).get("clause_checked", 0)))
    row("Offending words located (found word labels)", lambda a: pct(c(a).get("located", 0), c(a).get("found_span", 0)))
    row("Ad quotes verbatim", lambda a: pct(c(a).get("ad_quotes_ok", 0), c(a).get("ad_quotes", 0)))
    row("Policy quotes verbatim (in the cited clause)", lambda a: pct(c(a).get("policy_quotes_ok", 0), c(a).get("policy_quotes", 0)))
    row("Decision right, Chinese ads", lambda a: pct(a["per_lang"]["zh"].get("correct", 0), a["per_lang"]["zh"].get("items", 0)))
    row("Decision right, English ads", lambda a: pct(a["per_lang"]["en"].get("correct", 0), a["per_lang"]["en"].get("items", 0)))
    row("Cost per ad (US$)", lambda a: f"{a['cost_per_item']:.5f}")
    row("Median latency per ad (s)", lambda a: "–" if a["latency_median"] is None else f"{a['latency_median']:.1f}")
    row("API calls per ad", lambda a: f"{a['calls_mean']:.1f}")
    row("Run 1 vs run 2: same decision", lambda a: pct(a["agree"].get("same_decision", 0), a["agree"].get("items", 0)) if a["agree"] else "–")
    row("Run 1 vs run 2: same categories", lambda a: pct(a["agree"].get("same_categories", 0), a["agree"].get("items", 0)) if a["agree"] else "–")
    L += ["", "## Per category: precision / recall over (ad × run, category) pairs", ""]
    L.append("| Category | " + " | ".join(arms) + " |")
    L.append("|---|" + "---|" * len(arms))
    for cat in CATS:
        cells = []
        for a in arms:
            pc = results[a]["per_cat"][cat]
            p, r = prf(pc)
            cells.append(f"{p} / {r} (tp {pc.get('tp', 0)}, fp {pc.get('fp', 0)}, fn {pc.get('fn', 0)})")
        L.append(f"| {cat} | " + " | ".join(cells) + " |")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--split", default="test")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--no-quotes", action="store_true")
    ap.add_argument("--kind", choices=["text", "image"], help="score only text ads or only image ads")
    a = ap.parse_args(argv)
    items = {i["id"]: i for i in load_items() if i["split"] == a.split and (a.kind is None or i["kind"] == a.kind)}
    rows = [r for r in load_runs(a.files) if r["item"] in items]
    results = {}
    for arm in dict.fromkeys(r["arm"] for r in rows):
        ar = [r for r in rows if r["arm"] == arm]
        res = score_arm(ar, items, not a.no_quotes)
        res["agree"] = agreement(ar)
        results[arm] = res
    text = report(results, a.split)
    print(text)
    if a.out:
        a.out.write_text(text, encoding="utf-8", newline="\n")
        detail = {arm: {k: v for k, v in res.items()} for arm, res in results.items()}
        a.out.with_suffix(".json").write_text(json.dumps(detail, ensure_ascii=False, indent=1, default=str), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
