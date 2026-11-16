"""Load and validate the test set (items_zh.yaml, items_en.yaml; the harder set written later,
split "hard", is in items_hard_zh.yaml and items_hard_en.yaml; the real ads from published regulator
and court decisions, split "real", are not redistributed: see real-sources.md; the memory test,
split "memory", is in items_memory_<lang>.yaml, written against the earlier decisions in precedents.yaml).

Checks: unique ids; every span is a verbatim part of the ad's words; every clause id exists and
belongs to the ad's jurisdiction; categories are known; traps have no labels and name a basis.
`python testset/load.py` prints counts per split, language, kind and category.
"""
from __future__ import annotations

import collections
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "policies"))
import library  # noqa: E402


# Product drawings that carry the brand name on the pack (see render.draw_product).
LABEL_SHAPES = {"bottle", "liquor", "wine", "oil", "beer", "pills", "tube", "jar", "candle", "tumbler",
                "teaware", "phone", "card", "powerbank", "book", "box", "tea", "blender", "bag", "jacket",
                "sofa", "bedding"}


def image_words(item: dict, revised: bool = False) -> list[str]:
    """The words in the image: the ad lines, the small print, then the brand printed on the pack."""
    spec = item["image"]
    lines = list(item["revision"]["image_lines"]) if revised and "image_lines" in item["revision"] else list(spec["lines"])
    lines += spec.get("small", [])  # small print at the bottom of the image
    if spec["layout"] in {"poster", "banner"} and spec.get("shape") in LABEL_SHAPES and spec.get("brand"):  # not "frames"
        lines.append(spec["brand"])
    return lines


def ad_text(item: dict, revised: bool = False) -> str:
    """All words of the ad: the caption, then each line in the image. This is the 'ad' source
    file that ad-side quotes are checked against."""
    copy = item["revision"].get("copy", item["copy"]) if revised else item["copy"]
    lines = image_words(item, revised) if item["kind"] == "image" else []
    parts = [f"Caption: {copy}"] if item["lang"] == "en" else [f"文案：{copy}"]
    if lines:
        parts.append(("Words in the image:" if item["lang"] == "en" else "图片中的文字：") + "\n" + "\n".join(lines))
    return "\n".join(parts) + "\n"


def _check_labels(item, labels, text, problems, where):
    clauses = library.by_id()
    cats = library.categories()
    jur = "CN" if item["lang"] == "zh" else "TikTok"
    for lab in labels:
        if lab["cat"] not in cats:
            problems.append(f"{where}: unknown category {lab['cat']}")
        for cid in lab["clauses"]:
            if cid not in clauses:
                problems.append(f"{where}: unknown clause {cid}")
            elif clauses[cid].jurisdiction != jur:
                problems.append(f"{where}: clause {cid} is not {jur}")
        kinds = [k for k in ("span", "visual", "absence") if k in lab]
        if len(kinds) != 1:
            problems.append(f"{where}: a label needs exactly one of span/visual/absence")
        if "span" in lab and lab["span"] not in text:
            problems.append(f"{where}: span not in ad text: {lab['span']}")


def load_items() -> list[dict]:
    items = []
    for lang in ("zh", "en"):
        for name in (f"items_{lang}.yaml", f"items_hard_{lang}.yaml", f"items_real_{lang}.yaml", f"items_memory_{lang}.yaml"):
            if not (HERE / name).exists():
                continue
            for it in yaml.safe_load((HERE / name).read_text(encoding="utf-8")):
                it["lang"] = lang
                it.setdefault("labels", [])
                items.append(it)
    problems = []
    seen = set()
    for it in items:
        if it["id"] in seen:
            problems.append(f"duplicate id {it['id']}")
        seen.add(it["id"])
        if it["kind"] == "image" and "image" not in it:
            problems.append(f"{it['id']}: image item without image spec")
        _check_labels(it, it["labels"], ad_text(it), problems, it["id"])
        if "trap" in it and (it["labels"] or not it.get("basis")):
            problems.append(f"{it['id']}: a trap has no labels and names a basis")
        if "revision" in it:
            _check_labels(it, it["revision"]["labels"], ad_text(it, revised=True), problems, it["id"] + "/rev")
            for fact in it.get("must_keep", []):
                if fact not in ad_text(it):
                    problems.append(f"{it['id']}: must_keep {fact} not in the ad")
    if problems:
        raise ValueError("test set problems:\n" + "\n".join(problems))
    return items


def summary(items: list[dict]) -> str:
    out = []
    for split in ("dev", "test", "hard", "real", "memory"):
        sub = [i for i in items if i["split"] == split]
        c = collections.Counter((i["lang"], i["kind"]) for i in sub)
        viol = sum(1 for i in sub if i["labels"])
        traps = sum(1 for i in sub if "trap" in i)
        cats = collections.Counter((i["lang"], l["cat"]) for i in sub for l in i["labels"])
        how = collections.Counter(next(k for k in ("span", "visual", "absence") if k in l) for i in sub for l in i["labels"])
        out.append(f"{split}: {len(sub)} items {dict(c)}; violating {viol}, compliant {len(sub) - viol} (traps {traps}); "
                   f"labels {sum(cats.values())} {dict(how)}")
        out.append("  " + ", ".join(f"{k[0]}-{k[1]}:{v}" for k, v in sorted(cats.items())))
        out.append(f"  revisions: {sum(1 for i in sub if 'revision' in i)}")
    return "\n".join(out)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(summary(load_items()))
