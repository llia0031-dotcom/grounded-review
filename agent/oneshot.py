"""Arm 1, one prompt: the whole policy library of the ad's jurisdiction, the image, the caption and
the OCR text go into one request; the model answers in the review schema. No tools."""
from __future__ import annotations

import json
import time

import library
from common import (REVIEW_SCHEMA, Usage, ad_image, category_list, create, image_block, jurisdiction)
from ocr import cached as ocr_cached

INSTRUCTIONS = """You review ads before they run. Decide whether the ad breaks any clause in the policy library below, and name every violation.

Rules:
- Only clauses marked "rule" can be broken. Clauses marked "guidance" say when a rule does not apply; use them to avoid flagging words that only look risky.
- Judge the ad as a whole: its caption, the words in the image, and what the image shows.
- For each violation give: the category, the id of the clause broken, the exact words of the ad that break it (copied character for character; leave empty if the problem is only in the picture or is something the ad leaves out), what in the picture or what missing element breaks it (otherwise empty), and the exact words of the clause that the ad breaks, copied character for character from the clause text.
- One violation per problem. If the ad breaks nothing, decide "approve" with no violations.
- Write explanations in the language of the ad.

Categories:
{categories}

Policy library ({jurisdiction}):

{library}"""


def system_prompt(item: dict) -> str:
    jur = jurisdiction(item)
    clauses = [c for c in library.load() if c.jurisdiction == jur]
    return INSTRUCTIONS.format(categories=category_list(item["lang"]), jurisdiction=jur, library=library.render(clauses))


def ad_message(item: dict, revised: bool = False, copy: str | None = None, image_path=None) -> list[dict]:
    """The ad as the one-prompt arm sees it: image, caption and the OCR text of the image."""
    content = []
    path = image_path or ad_image(item, revised)
    caption = copy if copy is not None else (item["revision"].get("copy", item["copy"]) if revised else item["copy"])
    lang = "Chinese" if item["lang"] == "zh" else "English"
    text = f"The ad is in {lang}; write explanations in {lang}.\nCaption: {caption}"
    if path is not None:
        content.append(image_block(path))
        ocr = ocr_cached(path.stem)["text"] if image_path is None else _ocr_live(path)
        text += f"\nText read from the image (OCR):\n{ocr}"
    content.append({"type": "text", "text": text})
    return content


def _ocr_live(path):
    from ocr import read_text
    return read_text(path)[0]


def review(item: dict, revised: bool = False, copy: str | None = None, image_path=None) -> dict:
    usage = Usage()
    t0 = time.perf_counter()
    resp = create(usage, max_tokens=8000, system=system_prompt(item),
                  messages=[{"role": "user", "content": ad_message(item, revised, copy, image_path)}],
                  output_config={"format": {"type": "json_schema", "schema": REVIEW_SCHEMA}})
    text = next((b.text for b in resp.content if b.type == "text"), "")
    try:
        out = json.loads(text)
        error = None
    except json.JSONDecodeError as e:
        out, error = {"decision": "error", "violations": [], "notes": ""}, f"bad JSON: {e}"
    path = image_path or ad_image(item, revised)
    ocr_secs = ocr_cached(path.stem)["seconds"] if (path is not None and image_path is None) else 0.0
    return {"arm": "oneshot", "output": out, "error": error, "stop_reason": resp.stop_reason,
            "usage": usage.as_dict(), "latency_s": round(time.perf_counter() - t0 + ocr_secs, 2)}
