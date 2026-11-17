"""Export stored results for the demo pages: demo/src/data/demo.json (Chinese page) and demo.en.json
(English page); images to demo/public/ads/.

Everything shown on the pages comes from files written by the evaluation; nothing calls a model.
- Workspace: the agent's run-1 review of six test ads in the page's language.
- Follow-up: two stored multi-turn conversations (eval/results/multiturn-2026-11-13.jsonl).
- Results: the scored summaries in eval/results/.
Display clean-up only: clause ids in brackets such as "（CN-AL-17）" are dropped from the agent's prose,
since the page names every clause in words. Quotes are marked where they occur verbatim.
Platform policy text is not reproduced: for those clauses the page gets the section name and a link to
the policy page (clauseText empty, clauseUrl set).

  python eval/export_demo.py
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "agent"))
import common  # noqa: E402
import library  # noqa: E402
from load import ad_text, image_words, load_items  # noqa: E402

OUT = {"zh": ROOT / "demo" / "src" / "data" / "demo.json", "en": ROOT / "demo" / "src" / "data" / "demo.en.json"}
IMG_OUT = ROOT / "demo" / "public" / "ads"
RESULTS = ROOT / "eval" / "results"

WORKSPACE = {
    "zh": [("zh-t22", "云栖草本足贴"), ("zh-t29", "青禾浓缩洗衣液"), ("zh-t44", "云栖草本代茶饮"),
           ("zh-t37", "青禾手机 X5"), ("zh-t10", "云栖冷萃咖啡"), ("zh-t46", "木朴床垫")],
    "en": [("en-t21", "Nuvola Skin Balm"), ("en-t30", "Lumeo Spot Serum"), ("en-t35", "Harbor Lager"),
           ("en-t41", "Lumeo sunscreen"), ("en-t12", "Nuvola headphones"), ("en-t32", "Brightfold Kids Club")],
}
CONVERSATIONS = {"zh": [("zh-t22", 1, "云栖草本足贴"), ("zh-t06", 2, "青禾美白牙膏")],
                 "en": [("en-t07", 1, "Lumeo cream"), ("en-t05", 2, "Slimora drops")]}
CAT_NAMES = {
    "zh": {"ABSOLUTE": "绝对化用语", "MEDICAL": "宣称治疗疾病", "GUARANTEE": "保证效果或收益", "DISPARAGE": "贬低其他商家",
           "DATA": "数据没有出处", "ALCOHOL": "酒类广告禁止的内容", "WEIGHT": "减重和体型", "BEFORE_AFTER": "使用前后对比",
           "FLAG": "使用国旗、国徽", "OTHER": "其他条款"},
    "en": {"ABSOLUTE": "Absolute claim", "MEDICAL": "Medical claim", "GUARANTEE": "Guaranteed outcome",
           "DISPARAGE": "Running down a competitor", "DATA": "Data without a source", "ALCOHOL": "Alcohol rules",
           "WEIGHT": "Weight and body image", "BEFORE_AFTER": "Before-and-after comparison", "FLAG": "National flag or emblem",
           "OTHER": "Other rule"},
}
CHART_NAMES = {
    "zh": {"agent": "审核助手（带工具）", "oneshot": "单个提示词", "wordlist": "违禁词表", "clip": "CLIP",
           "siglip2": "SigLIP 2", "safeguard-vl": "SafeGuard-VL"},
    "en": {"agent": "Review agent (tools)", "oneshot": "One prompt", "wordlist": "Banned-word list", "clip": "CLIP",
           "siglip2": "SigLIP 2", "safeguard-vl": "SafeGuard-VL"},
}
CN_NUM = "零一二三四五六七八九"


def clause_url(cid: str) -> str | None:
    """The public page of a platform policy clause (the "- Source:" line of its source file)."""
    c = library.by_id().get(cid)
    if c is None or not cid.startswith("TT-"):
        return None
    head = (ROOT / "policies" / "sources" / c.source).read_text(encoding="utf-8")[:600]
    m = re.search(r"- Source: (\S+)", head)
    return m.group(1) if m else None


def clause_ref(cid: str) -> str:
    """《广告法》第十七条 / 《广告法》第九条第三项 / 《广告绝对化用语执法指南》第六条;
    platform clauses: "Misleading and false content · Misleading claims", "Alcohol"."""
    c = library.by_id().get(cid)
    if c is None:
        return ""
    if cid.startswith("TT-"):
        page, _, section = c.title.removeprefix("TikTok ").partition(": ")
        return page if section in ("", "Policy", page) else f"{page} · {section}"
    head = c.title.split("：")[0]
    if head.startswith("广告法"):
        return "《广告法》" + head[len("广告法"):]
    if head.startswith("执法指南"):
        return "《广告绝对化用语执法指南》" + head[len("执法指南"):]
    return head


def tidy(text: str) -> str:
    text = re.sub(r"\s*[（(]\s*(?:CN|TT)-[A-Z0-9-]+\s*[)）]", "", text or "")
    return re.sub(r"(?:CN|TT)-[A-Z0-9-]+", lambda m: clause_ref(m.group(0)) or m.group(0), text).strip()


def _norm_map(s: str):
    """Normalised text (NFKC, no whitespace) and, for each of its characters, the index in s."""
    chars, idx = [], []
    for i, ch in enumerate(s):
        n = unicodedata.normalize("NFKC", ch)
        for c in n:
            if not c.isspace():
                chars.append(c)
                idx.append(i)
    return "".join(chars), idx


def find(hay: str, needle: str):
    """[start, end) of needle in hay in UTF-16 units, ignoring whitespace and width differences; None if absent."""
    if not needle:
        return None
    h, hi = _norm_map(hay)
    n, _ = _norm_map(needle.strip("“”\"'"))
    if not n:
        return None
    k = h.find(n)
    if k < 0:
        return None
    start, end = hi[k], hi[k + len(n) - 1] + 1
    # The page slices JavaScript strings, which count UTF-16 units: a character outside the BMP
    # (such as the Unicode bold letters in "𝗯𝗲𝘀𝘁") is two units there and one here.
    return [len(hay[:start].encode("utf-16-le")) // 2, len(hay[:end].encode("utf-16-le")) // 2]


def verdict(item: dict, out: dict, revised: bool = False, lang: str = "zh") -> dict:
    lines = ([item["revision"].get("copy", item["copy"])] if revised else [item["copy"]])
    words = image_words(item, revised) if item["kind"] == "image" else []
    checks = common.check_quotes(ad_text(item, revised), out["violations"]) if out["violations"] else []
    viols = []
    for v, chk in zip(out["violations"], checks):
        cid = v.get("clause_id", "")
        c = library.by_id().get(cid)
        url = clause_url(cid)
        clause_text = c.text if c and not url else ""
        marks = []
        for li, line in enumerate(lines + words):
            span = find(line, v.get("ad_quote", ""))
            if span:
                marks.append({"line": li, "span": span})
                break
        viols.append({
            "cat": v["category"], "catName": CAT_NAMES[lang].get(v["category"], CAT_NAMES[lang]["OTHER"]),
            "clauseRef": clause_ref(cid), "clauseText": clause_text, "clauseUrl": url,
            "policySpan": find(clause_text, v.get("policy_quote", "")),
            "adQuote": v.get("ad_quote", "").strip(), "visual": tidy(v.get("visual_evidence", "")) if not v.get("ad_quote", "").strip() else "",
            "why": tidy(v.get("explanation", "")),
            "verified": (chk["ad"] in (None, "supported")) and chk["policy"] == "supported",
            "marks": marks,
        })
    return {"decision": out["decision"], "violations": viols, "notes": tidy(out.get("notes", ""))}


def ad_block(item: dict, revised: bool = False, image_name: str | None = None) -> dict:
    copy = item["revision"].get("copy", item["copy"]) if revised else item["copy"]
    words = image_words(item, revised) if item["kind"] == "image" else []
    image, size = None, None
    if item["kind"] == "image":
        from PIL import Image
        src = ROOT / "testset" / "images" / f"{item['id']}{'-rev' if revised else ''}.png"
        image = f"ads/{src.name}"
        shutil.copy2(src, IMG_OUT / src.name)
        with Image.open(src) as im:
            size = list(im.size)
    return {"caption": copy, "words": words, "image": image, "size": size}


def runs(path: Path):
    rows = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if not r.get("error") and not r.get("errors"):
            rows[(r.get("arm", "multiturn"), r["item"], r["run"])] = r
    return rows


def results_block(lang: str = "zh") -> dict:
    s_all = json.loads((RESULTS / "test-2026-11-13.summary.json").read_text(encoding="utf-8"))
    s_img = json.loads((RESULTS / "test-2026-11-13.images.summary.json").read_text(encoding="utf-8"))
    mt = runs(RESULTS / "multiturn-2026-11-13.jsonl")

    def c(arm, s=s_all):
        from collections import defaultdict
        return defaultdict(int, s[arm]["counts"])  # counts of zero are not stored

    names = CHART_NAMES[lang]
    chart = []
    for arm in ["agent", "oneshot", "safeguard-vl", "clip", "siglip2", "wordlist"]:
        if arm not in s_img:
            continue
        k = c(arm, s_img)
        chart.append({"arm": arm, "name": names[arm], "right": k.get("tp", 0) + k.get("tn", 0), "n": k["items"],
                      "violRejected": k.get("tp", 0), "viol": k.get("tp", 0) + k.get("fn", 0),
                      "trapsOk": k.get("traps_approved", 0), "traps": k.get("traps", 0)})
    img_items = [i for i in load_items() if i["split"] == "test" and i["kind"] == "image"]
    always = sum(1 for i in img_items if i["labels"])
    a, o = c("agent"), c("oneshot")
    conv = list(mt.values())
    return {
        "ads": 96, "zh": 48, "en": 48, "images": len(img_items), "runs": 2,
        "violRejected": {"agent": [a["tp"], a["tp"] + a["fn"]], "oneshot": [o["tp"], o["tp"] + o["fn"]]},
        "clauseRight": {"agent": [a["clause_right"], a["clause_checked"]], "oneshot": [o["clause_right"], o["clause_checked"]]},
        "trapsOk": {"agent": [a["traps_approved"], a["traps"]], "oneshot": [o["traps_approved"], o["traps"]]},
        "cost": {"agent": round(s_all["agent"]["cost_per_item"], 4), "oneshot": round(s_all["oneshot"]["cost_per_item"], 4)},
        "latency": {"agent": round(s_all["agent"]["latency_median"], 1), "oneshot": round(s_all["oneshot"]["latency_median"], 1)},
        "chart": chart, "alwaysReject": [always, len(img_items)],
        "fixPassed": [sum(1 for r in conv if not r["fix_independent_review"]["violations"]), len(conv)],
    }


def main():
    IMG_OUT.mkdir(parents=True, exist_ok=True)
    items = {i["id"]: i for i in load_items()}
    test = runs(RESULTS / "test-2026-11-13.jsonl")
    mt = runs(RESULTS / "multiturn-2026-11-13.jsonl")
    for lang in ("zh", "en"):
        ads = []
        for iid, name in WORKSPACE[lang]:
            it = items[iid]
            out = test[("agent", iid, 1)]["output"]
            ads.append({"id": iid, "name": name, "kind": it["kind"], **ad_block(it), **verdict(it, out, lang=lang)})
        convs = []
        for iid, run, name in CONVERSATIONS[lang]:
            it = items[iid]
            r = mt[("multiturn", iid, run)]
            adv = r["turn2"]
            convs.append({
                "id": iid, "name": name,
                "first": {**ad_block(it), **verdict(it, r["turn1"], lang=lang)},
                "answer": tidy(adv["answer"]), "fixCaption": adv["revised_caption"], "fixWords": adv["revised_image_lines"],
                "second": {**ad_block(it, revised=True), **verdict(it, r["turn3"], revised=True, lang=lang)},
            })
        data = {"ads": ads, "conversations": convs, "results": results_block(lang)}
        OUT[lang].parent.mkdir(parents=True, exist_ok=True)
        OUT[lang].write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print(f"wrote {OUT[lang]} ({len(ads)} ads, {len(convs)} conversations)")
        for a in ads:
            print(a["id"], a["decision"], [(v["catName"], v["clauseRef"], bool(v["marks"]), v["policySpan"] is not None, v["verified"]) for v in a["violations"]])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
