"""Baseline: open-source banned-word lists, plain matching.

Chinese ads: rules.json of sdhack/ecommerce-content-review (v4.10, 2,104 rules; no licence file, so
it is used locally and not redistributed). Only "block" rule groups are used; industry groups apply
only when one of their trigger words is present, as the file specifies. The project's own context
rules (negation, disclaimers) are not used: this arm measures a word list on its own.
English ads: the signal lists of AdLint's policy files (ftchvs/AdLint, MIT): TikTok, Meta and
Google platform files and the FTC health-claims file. Signals of severity high or critical reject;
"*" in a signal matches up to three words.

The text checked is what a word list would see in production: the caption plus the OCR text.
Each rule group is mapped to one of the test set's categories, or to OTHER.
`python baselines/wordlist.py --split test` writes eval/results/wordlist-<split>.jsonl.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "testset"))
sys.path.insert(0, str(ROOT / "policies"))
from load import load_items  # noqa: E402

# Not redistributed. Save rules.json of https://github.com/sdhack/ecommerce-content-review as
# third_party/sdhack-rules.json and the policy files of https://github.com/ftchvs/AdLint as
# third_party/adlint-<name>.yml, or point AD_REVIEW_THIRDPARTY at another folder.
THIRD = Path(os.environ.get("AD_REVIEW_THIRDPARTY", ROOT / "third_party"))
OCR = json.loads((ROOT / "testset" / "ocr.json").read_text(encoding="utf-8"))

ZH_MAP = {
    "adlaw-absolute": "ABSOLUTE", "adlaw-false-promise": "GUARANTEE", "adlaw-comparative": "DISPARAGE",
    "industry-food": "MEDICAL", "industry-medical": "MEDICAL", "adlaw-medical-false": "MEDICAL",
    "industry-finance": "GUARANTEE", "industry-education": "GUARANTEE", "industry-liquor": "ALCOHOL",
    "adlaw-national-symbol": "FLAG",
}
EN_MAP = {
    "medical_cure_claim": "MEDICAL", "unsupported_health_claim": "MEDICAL", "guaranteed_outcome": "GUARANTEE",
    "tiktok_misleading_content": "GUARANTEE", "google_financial_claim_review": "GUARANTEE",
    "weight_loss_claim": "WEIGHT", "tiktok_weight_management_claim": "WEIGHT", "meta_health_appearance_results": "WEIGHT",
    "before_after_claim": "BEFORE_AFTER",
}


def zh_rules():
    data = json.loads((THIRD / "sdhack-rules.json").read_text(encoding="utf-8"))
    out = []
    for g in data["rule_groups"]:
        if g["severity"] != "block":
            continue
        pats = [(p["type"], p["value"]) for p in g["patterns"]]
        out.append({"id": g["id"], "cat": ZH_MAP.get(g["id"], "OTHER"), "triggers": g.get("triggers", []), "patterns": pats})
    return out


def en_rules():
    out = []
    for f in sorted(THIRD.glob("adlint-*.yml")):
        for p in yaml.safe_load(f.read_text(encoding="utf-8"))["policies"]:
            if p["severity"] not in {"high", "critical"}:
                continue
            pats = []
            for sig in p.get("signals", []):
                words = [re.escape(w) for w in sig.split(" ")]
                rx = r"\b" + r"\s+".join(r"(?:\S+\s+){0,2}\S+" if w == r"\*" else w for w in words) + r"\b"
                pats.append(("regex", rx))
            out.append({"id": p["id"], "cat": EN_MAP.get(p["id"], "OTHER"), "triggers": [], "patterns": pats})
    return out


def scan(text: str, rules: list[dict], ignore_case: bool) -> list[dict]:
    hits = []
    flags = re.IGNORECASE if ignore_case else 0
    for r in rules:
        if r["triggers"] and not any(t in text for t in r["triggers"]):
            continue
        for kind, val in r["patterns"]:
            if kind == "keyword":
                found = val in text or (ignore_case and val.lower() in text.lower())
                m = val if found else None
            else:
                try:
                    mm = re.search(val, text, flags)
                except re.error:
                    continue
                m = mm.group(0) if mm else None
            if m:
                hits.append({"category": r["cat"], "rule": r["id"], "ad_quote": m})
                break  # one hit per rule group is enough
    return hits


def text_seen(item: dict) -> str:
    text = item["copy"]
    if item["kind"] == "image":
        text += "\n" + OCR[item["id"]]["text"]
    return text


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="test")
    a = ap.parse_args(argv)
    rules = {"zh": zh_rules(), "en": en_rules()}
    out = ROOT / "eval" / "results" / f"wordlist-{a.split}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for it in load_items():
            if it["split"] != a.split:
                continue
            t0 = time.perf_counter()
            hits = scan(text_seen(it), rules[it["lang"]], ignore_case=it["lang"] == "en")
            secs = time.perf_counter() - t0 + (OCR[it["id"]]["seconds"] if it["kind"] == "image" else 0)
            viols = [{"category": h["category"], "ad_quote": h["ad_quote"], "rule": h["rule"]} for h in hits]
            row = {"arm": "wordlist", "item": it["id"], "run": 1, "error": None,
                   "output": {"decision": "reject" if viols else "approve", "violations": viols},
                   "usage": {"cost_usd": 0.0, "calls": 0}, "latency_s": round(secs, 3)}
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
