"""Memory for the review agent: earlier confirmed decisions ("precedents"), looked up for each new ad.

Design (product/PRD.md, section 6.4):
- The store holds decisions that were confirmed, as a platform keeps them: the ad's words, the decision, each
  violation's category, clause and quoted words, and a one-line reason. Records go in through add() once a decision
  is confirmed; the model never writes to the store, so an ad's own words cannot turn into instructions for later
  reviews.
- Lookup is BM25 over the stored ads of the same language (the policy library's tokeniser: words, and Chinese
  character pairs), plus the advertiser's own most recent records. No embedding model, no extra model call.
- The records found are put in the review request, most similar first, with a rule in the system prompt: decide the
  same way when the new ad makes the same claim in the same way; the clauses decide when anything differs.

For the memory test the store is testset/precedents.yaml, written with the test items; it does not change during a
run, so every run of an item sees the same records.
"""
from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path

from rank_bm25 import BM25Okapi

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "policies"))
import library  # noqa: E402

STORE = ROOT / "testset" / "precedents.yaml"
K_SIMILAR = 3  # most similar records from any advertiser
K_SAME = 2  # plus up to this many of the advertiser's own most recent records not already found


@lru_cache(maxsize=1)
def load() -> tuple[dict, ...]:
    import yaml
    recs = yaml.safe_load(STORE.read_text(encoding="utf-8"))
    clauses = library.by_id()
    problems, seen = [], set()
    for r in recs:
        r["date"] = str(r["date"])
        if r["id"] in seen:
            problems.append(f"duplicate precedent {r['id']}")
        seen.add(r["id"])
        jur = "CN" if r["lang"] == "zh" else "TikTok"
        if r["decision"] not in ("approve", "reject") or (r["decision"] == "reject") != bool(r["violations"]):
            problems.append(f"{r['id']}: a rejection has violations and an approval has none")
        for v in r["violations"]:
            if v["quote"] not in r["copy"]:
                problems.append(f"{r['id']}: quote not in the ad: {v['quote']}")
            if v["clause"] not in clauses or clauses[v["clause"]].jurisdiction != jur:
                problems.append(f"{r['id']}: clause {v['clause']} is not a {jur} clause")
    if problems:
        raise ValueError("precedent store problems:\n" + "\n".join(problems))
    return tuple(recs)


@lru_cache(maxsize=2)
def _index(lang: str):
    recs = [r for r in load() if r["lang"] == lang]
    return recs, BM25Okapi([library._tokens(r["copy"]) for r in recs])


def lookup(ad_words: str, lang: str, advertiser: str | None) -> list[dict]:
    """The records to show for a new ad: the K_SIMILAR most similar, then the advertiser's own most recent ones."""
    recs, bm25 = _index(lang)
    scores = bm25.get_scores(library._tokens(ad_words))
    ranked = sorted(range(len(recs)), key=lambda i: -scores[i])
    out = [recs[i] for i in ranked[:K_SIMILAR] if scores[i] > 0]
    own = sorted((r for r in recs if advertiser and r["advertiser"] == advertiser and r not in out),
                 key=lambda r: r["date"], reverse=True)
    return out + own[:K_SAME]


def render(found: list[dict], lang: str, advertiser: str | None) -> str:
    if not found:
        return ""
    lines = ["Earlier confirmed decisions on similar ads (for consistency; the clauses decide):"]
    for n, r in enumerate(found, 1):
        who = f"same advertiser ({r['advertiser']})" if r["advertiser"] == advertiser else f"another advertiser ({r['advertiser']})"
        lines.append(f"[{n}] {who}, {r['date']}")
        lines.append("Ad: " + r["copy"])
        lines.append(f"Decision: {r['decision']}")
        for v in r["violations"]:
            lines.append(f"- {v['cat']}, {v['clause']}, ad words: “{v['quote']}”")
        lines.append("Reason: " + r["reason"])
    return "\n".join(lines)


def add(record: dict, path: Path) -> None:
    """Append a confirmed decision to a store file (JSON lines). Called by the program after a decision is
    confirmed, never by the model. Not used in the memory test, whose store is fixed."""
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
