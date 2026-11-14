"""Offline checks (no model calls, no cost):  python -m unittest discover -s tests -v"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "agent"))
sys.path.insert(0, str(ROOT / "eval"))
import common  # noqa: E402
import library  # noqa: E402
import score  # noqa: E402
from load import ad_text, load_items  # noqa: E402


def perfect_output(item: dict, revised: bool = False) -> dict:
    labels = item["revision"]["labels"] if revised else item["labels"]
    clauses = library.by_id()
    viols = []
    for lab in labels:
        cid = lab["clauses"][0]
        viols.append({"category": lab["cat"], "clause_id": cid, "ad_quote": lab.get("span", ""),
                      "visual_evidence": lab.get("visual", lab.get("absence", "")),
                      "policy_quote": (clauses[cid].text.splitlines() or [""])[0][:60], "explanation": ""})
    return {"decision": "reject" if viols else "approve", "violations": viols, "notes": ""}


class TestPolicies(unittest.TestCase):
    def test_clause_text_is_verbatim(self):
        for c in library.load():
            if c.source in library.MISSING:
                continue
            doc = (library.SOURCES / c.source).read_text(encoding="utf-8")
            self.assertIn(c.text, doc, c.id)

    def test_search_finds_absolute_clause(self):
        self.assertEqual(library.search("全网最好 第一", "CN", 1)[0].id, "CN-AL-9-3")
        library.load()
        if not library.MISSING:
            self.assertIn("TT-WM-WEIGHT", [c.id for c in library.search("lose weight fast", "TikTok", 2)])


class TestTestSet(unittest.TestCase):
    def test_loads_and_validates(self):
        items = load_items()
        self.assertEqual(sum(i["split"] == "test" for i in items), 96)
        self.assertEqual(sum(i["split"] == "dev" for i in items), 24)

    def test_images_exist_and_have_ocr(self):
        ocr = json.loads((ROOT / "testset" / "ocr.json").read_text(encoding="utf-8"))
        for it in load_items():
            if it["kind"] == "image":
                self.assertTrue((common.IMAGES / f"{it['id']}.png").exists(), it["id"])
                self.assertIn(it["id"], ocr)

    def test_gold_spans_pass_the_quote_checker(self):
        for it in load_items():
            for revised in ([False, True] if "revision" in it else [False]):
                out = perfect_output(it, revised)
                if not out["violations"]:
                    continue
                res = common.check_quotes(ad_text(it, revised), out["violations"])
                for v, r in zip(out["violations"], res):
                    if v["ad_quote"]:
                        self.assertEqual(r["ad"], "supported", (it["id"], v["ad_quote"]))
                    if library.by_id()[v["clause_id"]].text:
                        self.assertEqual(r["policy"], "supported", (it["id"], v["clause_id"]))


class TestScorer(unittest.TestCase):
    def test_perfect_answers_score_perfectly(self):
        items = {i["id"]: i for i in load_items() if i["split"] == "test"}
        rows = [{"arm": "gold", "item": i, "run": 1, "output": perfect_output(it), "usage": {"cost_usd": 0, "calls": 0}, "latency_s": 0}
                for i, it in items.items()]
        res = score.score_arm(rows, items)
        c = res["counts"]
        self.assertEqual(c["tp"] + c["tn"], len(items))
        self.assertEqual(c["exact_categories"], len(items))
        self.assertEqual(c["clause_right"], c["clause_checked"])
        self.assertEqual(c["located"], c["found_span"])
        self.assertEqual(c["ad_quotes_ok"], c["ad_quotes"])
        if not library.MISSING:  # without the TikTok pages their clause quotes cannot be checked
            self.assertEqual(c["policy_quotes_ok"], c["policy_quotes"])

    def test_overlap_rule(self):
        self.assertTrue(score.overlaps("全网最舒服的枕头，睡过就回不去", "全网最舒服的枕头", "zh"))
        self.assertTrue(score.overlaps("最舒服的枕头", "全网最舒服的枕头", "zh"))
        self.assertFalse(score.overlaps("限时 ¥199", "全网最舒服的枕头", "zh"))

    def test_other_category_rejects_but_is_not_a_category(self):
        items = {i["id"]: i for i in load_items() if i["split"] == "test"}
        it = next(i for i in items.values() if not i["labels"])
        row = {"arm": "x", "item": it["id"], "run": 1, "usage": {}, "latency_s": 0,
               "output": {"decision": "reject", "violations": [{"category": "OTHER", "ad_quote": ""}]}}
        res = score.score_arm([row], {it["id"]: it}, check_quotes_on=False)
        self.assertEqual(res["counts"]["fp"], 1)
        self.assertTrue(all(v.get("fp", 0) == 0 for v in res["per_cat"].values()))


if __name__ == "__main__":
    unittest.main()
