"""Audit of two required statements in the answer key (written 2026-11-18, after every run; changes no stored result).

Two clauses in the policy library require a statement in the ad, not only the absence of bad words:
- TT-ALC: an alcohol ad must state the drink's alcohol content and strength and carry a responsible drinking disclaimer;
- CN-AL-18: a health-food (保健食品) ad must show 「本品不能代替药物」.
In the frozen answer key, a missing statement was labelled only where it was an ad's sole problem. This script lists
every ad in the test, harder and memory sets to which one of these requirements applies, says whether the ad carries
the statement and whether the key has a label for its absence, and counts how often each model arm listed it.

  python eval/key_audit.py      (writes eval/results/key-audit-2026-11-18.md)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "testset"))
from load import ad_text, load_items  # noqa: E402

RESULTS = {"test": ["test-2026-11-13.jsonl"], "hard": ["hard-2026-11-14.jsonl"], "memory": ["memory-2026-11-16.jsonl"]}
STRENGTH = re.compile(r"\d+(\.\d+)?\s*%\s*(abv|vol|alc)|alc\.?\s*\d|\bproof\b", re.I)
DISCLAIMER = re.compile(r"(drink|enjoy)\s+responsibly|please drink responsibly|responsible drinking", re.I)
ALCOHOL_PRODUCT = re.compile(r"\b(beer|lager|ale|gin|vodka|whisk(e)?y|rum|wine|shots?|cocktail|bar|brew(ery)?|cider|tequila|liquor|spirits?)\b|🍻|🍺|🍷|🍸", re.I)


def applies(item: dict) -> str | None:
    """Which requirement applies to this ad, if any."""
    words = ad_text(item)
    if item["lang"] == "en":
        alcohol_label = any(l["cat"] == "ALCOHOL" for l in item["labels"])
        alcohol_trap = "trap" in item and ALCOHOL_PRODUCT.search(item["copy"]) and "alcohol" in (item.get("trap", "") + " ".join(item.get("basis", []))).lower()
        if alcohol_label or alcohol_trap or ("TT-ALC" in item.get("basis", [])):
            return "TT-ALC"
    elif "保健食品" in words:
        return "CN-AL-18"
    return None


def carries(item: dict, req: str) -> bool:
    words = ad_text(item)
    if req == "TT-ALC":
        return bool(STRENGTH.search(words)) and bool(DISCLAIMER.search(words))
    return "本品不能代替药物" in words


# a negation and the missing item in the same sentence ("does not state the alcoholic content", "no responsible
# drinking disclaimer"); a sentence break ends the match, so "is not allowed. The 40% ABV ..." does not count
MISSING_EN = re.compile(r"\b(no|not|without|missing|lacks?|omits?|omission)\b[^.;:]{0,80}?"
                        r"(disclaimer|strength|alcohol(?:ic)? content|abv)", re.I)


def listed(output: dict | None, req: str) -> bool:
    """Did the review name the missing statement in one of its violations (in what it says about the evidence or why)?"""
    for v in (output or {}).get("violations", []) or []:
        if v.get("clause_id") != req:
            continue
        said = " ".join(str(v.get(k, "")) for k in ("visual_evidence", "explanation"))
        if req == "TT-ALC" and MISSING_EN.search(said):
            return True
        if req == "CN-AL-18" and "本品不能代替药物" in said:
            return True
    return False


def main():
    items = [i for i in load_items() if i["split"] in RESULTS]
    rows = {}
    for split, files in RESULTS.items():
        for f in files:
            for line in (ROOT / "eval" / "results" / f).read_text(encoding="utf-8").splitlines():
                r = json.loads(line)
                if not r.get("error"):
                    rows.setdefault(r["item"], []).append(r)
    L = ["# Answer-key audit: required statements (2026-11-18)", "",
         "Two clauses require a statement in the ad: TT-ALC (alcohol strength and a responsible drinking disclaimer) and "
         "CN-AL-18 (「本品不能代替药物」 on health food). For every ad in the test, harder and memory sets that one of them "
         "applies to: does the ad carry the statement, does the frozen key label its absence, and in how many runs each "
         "arm listed it. Revisions (the advertiser's second version) are listed separately.", "",
         "| Ad | Split | Requirement | Ad carries it | Key labels its absence | Key decision | Runs that listed it, by arm |",
         "|---|---|---|---|---|---|---|"]
    gaps = []
    for it in items:
        req = applies(it)
        if not req:
            continue
        has = carries(it, req)
        keyed = any(("absence" in l) and req in l["clauses"] for l in it["labels"])
        dec = "reject" if it["labels"] else "approve"
        by_arm = {}
        for r in rows.get(it["id"], []):
            a = r["arm"]
            n, k = by_arm.get(a, (0, 0))
            by_arm[a] = (n + 1, k + listed(r.get("output"), req))
        arms = ", ".join(f"{a} {k}/{n}" for a, (n, k) in sorted(by_arm.items()))
        L.append(f"| `{it['id']}` | {it['split']} | {req} | {'yes' if has else 'no'} | {'yes' if keyed else 'no'} | {dec} | {arms} |")
        if not has and not keyed:
            gaps.append(it["id"])
    L += ["", f"Ads that lack the statement and have no label for it: {len(gaps)} ({', '.join('`' + g + '`' for g in gaps)})."]
    out = ROOT / "eval" / "results" / "key-audit-2026-11-18.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(L))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
