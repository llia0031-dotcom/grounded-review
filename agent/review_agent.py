"""Arm 2, the review agent: the model sees the image and the caption, and works through tools.

Tools
  read_image_text  OCR of the ad image (RapidOCR, see ocr.py)
  search_policy    BM25 search over the clauses of the ad's jurisdiction (policies/library.py)
  get_clause       full text of one clause by id
  check_quotes     evidence-check's script: are the quoted ad words and clause words verbatim?
  submit_review    final answer (same schema as the one-prompt arm)
  submit_advice    final answer when the advertiser asks what is wrong and how to fix it

Versions: v1 (the main run); v1.1 adds the advice rule and check_revision; v1.2 adds to v1.1 a check
of the submitted advice fields (common.advice_problems): a malformed submit_advice is sent back once.
v1.3 is v1.1 with the corrected caption and image lines asked for before the answer (field order of
submit_advice), and common.clean_advice applied to the submitted advice; no send-back.

Multi-turn: the conversation is kept, so an advertiser can ask for fixes after a review and then
submit a new version for another review (see conversation()).
"""
from __future__ import annotations

import json
import time

import library
from common import (REVIEW_SCHEMA, Usage, ad_image, advice_problems, category_list, check_quotes, clean_advice,
                    create, image_block, jurisdiction, placeholders)
from load import ad_text
from ocr import cached as ocr_cached

MAX_ROUNDS = 10

SYSTEM = """You review ads before they run, for the {jurisdiction} policy library. You have tools; use them.

How to work:
1. If the ad has an image, call read_image_text to get its exact words. Look at the image yourself too: some problems are only in the picture.
2. Find the clauses that may apply with search_policy (several short queries are fine) or get_clause. Only clauses marked "rule" can be broken; clauses marked "guidance" say when a rule does not apply, so check them before flagging words that only look risky.
3. Before you answer, call check_quotes on every quote you plan to give. A quote fails if it is not copied character for character. Fix failing quotes by copying again from the ad text or the clause text.
4. Finish with submit_review. One violation per problem; if nothing is broken, decide "approve" with no violations. Write explanations in the language of the ad.

Categories:
{categories}

Clause index (call get_clause or search_policy for the text):
{index}"""

# With memory (memory.py): the review request may list earlier confirmed decisions; this step is added to the system prompt.
MEMORY_RULE = """
5. The request may list earlier confirmed decisions on similar ads. Use them for consistency: if the new ad makes the same claim in the same way, decide the same way and cite the same clause. They do not override the clauses: if the wording, a qualifier, a source or the product differs, decide from the clauses, and say in notes which earlier decision you did not follow and why."""

ADVICE_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string", "description": "to the advertiser, in the language of the ad: what breaks which clause, and how to fix it"},
        "revised_caption": {"type": "string", "description": "a corrected caption that keeps the product facts"},
        "revised_image_lines": {"type": "array", "items": {"type": "string"}, "description": "corrected words for the image, one line per item, in the same order as now; empty if the ad has no image"},
    },
    "required": ["answer", "revised_caption", "revised_image_lines"],
    "additionalProperties": False,
}
# v1.3: the same fields, the corrected version first and the free-text answer last.
ADVICE_SCHEMA_V13 = {**ADVICE_SCHEMA, "properties": {k: ADVICE_SCHEMA["properties"][k] for k in ("revised_caption", "revised_image_lines", "answer")},
                     "required": ["revised_caption", "revised_image_lines", "answer"]}


CHECK_REVISION = {"name": "check_revision", "description": "Check a corrected version before you give it: lists unfilled template text (brackets, blanks, XX) and any words from your review's ad quotes that are still in it.",
                  "input_schema": {"type": "object", "properties": {"caption": {"type": "string"}, "image_lines": {"type": "array", "items": {"type": "string"}}},
                                   "required": ["caption", "image_lines"], "additionalProperties": False}}

# v1.1: said to the agent when the advertiser asks how to fix the ad (a mid-conversation system message).
ADVICE_RULES_V11 = ("When you write the corrected version: it must be ready to run as it is. Never leave blanks or template text such as "
                    "[licence number], [X]% ABV or 【数据来源】. If a fix needs a fact the advertiser has not given (a strength, a source, a licence), "
                    "leave that statement out of the corrected version and tell the advertiser in your answer what to add. Keep the product facts. "
                    "Call check_revision on the corrected version and fix what it reports before you call submit_advice.")


def tools_for(has_image: bool, version: str = "v1") -> list[dict]:
    tools = [
        {"name": "search_policy", "description": "Search the policy library of this ad's jurisdiction. Returns up to 4 clauses with id, title, kind and full text.",
         "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"], "additionalProperties": False}},
        {"name": "get_clause", "description": "Get the full text of one clause by id.",
         "input_schema": {"type": "object", "properties": {"clause_id": {"type": "string"}}, "required": ["clause_id"], "additionalProperties": False}},
        {"name": "check_quotes", "description": "Check quotes character for character. source is \"ad\" for words of the ad (caption or image text) or a clause id for words of that clause. Returns supported / quote_not_found / quote_too_short per quote.",
         "input_schema": {"type": "object", "properties": {"quotes": {"type": "array", "items": {"type": "object", "properties": {"source": {"type": "string"}, "quote": {"type": "string"}}, "required": ["source", "quote"], "additionalProperties": False}}},
                          "required": ["quotes"], "additionalProperties": False}},
        {"name": "submit_review", "description": "Submit the final review of the ad.", "strict": True, "input_schema": REVIEW_SCHEMA},
        {"name": "submit_advice", "description": "Answer the advertiser's question about what is wrong and how to fix it, with a corrected version.", "strict": True,
         "input_schema": ADVICE_SCHEMA_V13 if version == "v1.3" else ADVICE_SCHEMA},
    ]
    if version in ("v1.1", "v1.2", "v1.3"):
        tools.insert(-2, CHECK_REVISION)
    if has_image:
        tools.insert(0, {"name": "read_image_text", "description": "OCR of the ad image: its words, line by line, top to bottom.",
                         "input_schema": {"type": "object", "properties": {}, "additionalProperties": False}})
    return tools


class Session:
    """One conversation with the agent about one ad (and its later versions)."""

    def __init__(self, item: dict, version: str = "v1", memory: bool = False):
        self.item = item
        self.version = version
        self.memory = memory
        self.recalled: list[str] = []  # ids of the earlier decisions shown (memory only)
        self.last_quotes: list[str] = []
        self.jur = jurisdiction(item)
        clauses = [c for c in library.load() if c.jurisdiction == self.jur]
        index = "\n".join(f"- {c.id}: {c.title} ({c.kind})" for c in clauses)
        self.system = SYSTEM.format(jurisdiction=self.jur, categories=category_list(item["lang"]), index=index)
        if memory:
            head, sep, tail = self.system.partition("\n\nCategories:")
            self.system = head + MEMORY_RULE + sep + tail
        self.messages: list[dict] = []
        self.usage = Usage()
        self.trace: list[dict] = []
        self.image_path = None
        self.ocr_text = ""
        self.ocr_seconds_pending = 0.0
        self.ocr_seconds = 0.0  # OCR is read from a cache; its measured time is added when the tool is called
        self.caption = ""
        self.advice_sent_back: list[list[str]] = []  # v1.2: problems found in advice that was sent back
        self.advice_raw: dict | None = None  # v1.3: advice as submitted, before clean_advice
        self.advice_cleanup: list[str] = []

    # ------------------------------------------------------------ tool execution
    def _ad_source(self) -> str:
        text = f"Caption: {self.caption}"
        if self.ocr_text:
            text += "\n" + self.ocr_text
        return text + "\n"

    def _run_tool(self, name: str, args: dict) -> str:
        if name == "read_image_text":
            if self.image_path is None:
                return "This ad has no image."
            self.ocr_seconds += self.ocr_seconds_pending
            self.ocr_seconds_pending = 0.0
            return self.ocr_text or "(no text found)"
        if name == "check_revision":
            text = " ".join([args.get("caption", "")] + list(args.get("image_lines", [])))
            norm = lambda x: "".join(ch for ch in x.lower() if ch.isalnum())
            still = [q for q in self.last_quotes if q and norm(q) and norm(q) in norm(text)]
            return json.dumps({"placeholders": placeholders(text), "still_present_from_review": still}, ensure_ascii=False)
        if name == "search_policy":
            hits = library.search(args.get("query", ""), self.jur, k=4)
            return library.render(hits)
        if name == "get_clause":
            c = library.by_id().get(args.get("clause_id", ""))
            if c is None or c.jurisdiction != self.jur:
                return f"No clause {args.get('clause_id')} in the {self.jur} library."
            return library.render([c])
        if name == "check_quotes":
            t0 = time.perf_counter()
            quotes = args.get("quotes", [])
            viol = []
            for q in quotes:
                if q.get("source") == "ad":
                    viol.append({"ad_quote": q.get("quote", ""), "clause_id": "", "policy_quote": ""})
                else:
                    viol.append({"ad_quote": "", "clause_id": q.get("source", ""), "policy_quote": q.get("quote", "")})
            res = check_quotes(self._ad_source(), viol)
            self.usage.tool_seconds += time.perf_counter() - t0
            out = []
            for q, r in zip(quotes, res):
                out.append({"source": q.get("source"), "quote": q.get("quote"), "result": r["ad"] if q.get("source") == "ad" else r["policy"]})
            return json.dumps(out, ensure_ascii=False)
        return f"Unknown tool {name}."

    # ------------------------------------------------------------ one user turn
    def _turn(self, user_content: list[dict], final_tool: str, system_note: str | None = None) -> dict:
        self.messages.append({"role": "user", "content": user_content})
        if system_note:
            self.messages.append({"role": "system", "content": system_note})
        tools = tools_for(self.image_path is not None, self.version)
        for _ in range(MAX_ROUNDS):
            resp = create(self.usage, max_tokens=8000, system=self.system, tools=tools, messages=self.messages)
            self.messages.append({"role": "assistant", "content": resp.content})
            calls = [b for b in resp.content if b.type == "tool_use"]
            self.trace.append({"stop": resp.stop_reason, "tools": [(b.name, b.input) for b in calls]})
            if not calls:
                self.messages.append({"role": "user", "content": [{"type": "text", "text": f"Please finish by calling {final_tool}."}]})
                continue
            results, final = [], None
            for b in calls:
                if b.name == final_tool and final_tool == "submit_advice" and self.version == "v1.2"                         and not self.advice_sent_back and advice_problems(b.input):
                    problems = advice_problems(b.input)
                    self.advice_sent_back.append(problems)
                    results.append({"type": "tool_result", "tool_use_id": b.id, "is_error": True, "content": (
                        "Not received: " + "; ".join(problems) + ". Each field holds only its own content: the reply to the "
                        "advertiser in answer, the full corrected caption in revised_caption, the corrected image words in "
                        "revised_image_lines. No tool or parameter tags inside a field. Call submit_advice again.")})
                elif b.name == final_tool:
                    final = b.input
                    results.append({"type": "tool_result", "tool_use_id": b.id, "content": "Received."})
                elif b.name in {"submit_review", "submit_advice"}:
                    results.append({"type": "tool_result", "tool_use_id": b.id, "is_error": True, "content": f"Use {final_tool} for this turn."})
                else:
                    results.append({"type": "tool_result", "tool_use_id": b.id, "content": self._run_tool(b.name, b.input)})
            self.messages.append({"role": "user", "content": results})
            if final is not None:
                if final_tool == "submit_advice" and self.version == "v1.3":
                    self.advice_raw = final
                    final, self.advice_cleanup = clean_advice(final)
                if final_tool == "submit_review":
                    self.last_quotes = [v.get("ad_quote", "") for v in final.get("violations", [])]
                return {"output": final, "error": None}
        return {"output": None, "error": f"no {final_tool} after {MAX_ROUNDS} rounds"}

    def _set_ad(self, caption: str, image_path, ocr_text: str | None = None):
        self.caption = caption
        self.image_path = image_path
        if image_path is None:
            self.ocr_text = ""
        elif ocr_text is not None:
            self.ocr_text = ocr_text
        else:
            cached = ocr_cached(image_path.stem)
            self.ocr_text = cached["text"]
            self.ocr_seconds_pending = cached["seconds"]

    def review(self, revised: bool = False, caption: str | None = None, image_path=None, ocr_text: str | None = None) -> dict:
        item = self.item
        if caption is None:
            caption = item["revision"].get("copy", item["copy"]) if revised else item["copy"]
        path = image_path if image_path is not None else ad_image(item, revised)
        self._set_ad(caption, path, ocr_text)
        first = not self.messages
        lead = "Review this ad." if first else "The advertiser submits a new version of the ad. Review this version."
        content = []
        if path is not None:
            content.append(image_block(path))
        lang = "Chinese" if item["lang"] == "zh" else "English"
        # The memory test gives each ad an advertiser account; both arms are told it, only the memory arm gets records.
        account = f"\nAdvertiser account: {item['advertiser']}" if item.get("advertiser") else ""
        content.append({"type": "text", "text": f"{lead} The ad is in {lang}; write explanations in {lang}.{account}\nCaption: {caption}"
                        + ("\n(The ad has an image, attached above.)" if path is not None else "\n(Text ad, no image.)")})
        if self.memory and first:
            import memory
            found = memory.lookup(ad_text(item, revised), item["lang"], item.get("advertiser"))
            self.recalled = [r["id"] for r in found]
            if found:
                content.append({"type": "text", "text": memory.render(found, item["lang"], item.get("advertiser"))})
        return self._turn(content, "submit_review")

    def advise(self) -> dict:
        q = ("我是广告主。请告诉我哪里违规、怎么改，并给一版修改后的文案（图片里的文字也一起给出）。"
             if self.item["lang"] == "zh" else
             "I'm the advertiser. What exactly is wrong, and how do I fix it? Please give me a corrected version, including the words in the image.")
        return self._turn([{"type": "text", "text": q}], "submit_advice", ADVICE_RULES_V11 if self.version in ("v1.1", "v1.2", "v1.3") else None)

    def result(self, extra: dict) -> dict:
        out = {"arm": "agent_memory" if self.memory else "agent", **extra, "usage": self.usage.as_dict(), "trace": self.trace}
        if self.version != "v1":
            out["version"] = self.version
        if self.memory:
            out["recalled"] = self.recalled
        return out


def review(item: dict, version: str = "v1", memory: bool = False) -> dict:
    t0 = time.perf_counter()
    s = Session(item, version, memory)
    r = s.review()
    out = s.result({"output": r["output"] or {"decision": "error", "violations": [], "notes": ""}, "error": r["error"]})
    out["latency_s"] = round(time.perf_counter() - t0 + s.ocr_seconds, 2)
    return out
