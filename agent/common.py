"""Shared pieces for the two model arms (one prompt, tool-using agent).

Key handling: the Anthropic API key is read from an .env file whose path is given by
AD_REVIEW_ENV_FILE (relative to the project folder; default .env). Environment variables named
ANTHROPIC_* are removed from this process before the client is built, so credentials that belong
to other tools are never picked up. The key is never printed or written anywhere.
"""
from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "policies"))
sys.path.insert(0, str(ROOT / "testset"))
import library  # noqa: E402
from load import ad_text  # noqa: E402

MODEL = "claude-haiku-5-5"  # cheapest current model
EFFORT = "medium"
PRICE = {"input": 0.10 / 1e6, "output": 0.50 / 1e6}  # Claude Haiku 5.5 list price, prompts up to 100K tokens
# evidence-check (https://github.com/llia0031-dotcom/evidence-check) next to this folder, or set EVIDENCE_CHECK_SCRIPT.
CHECK_SCRIPT = Path(os.environ.get("EVIDENCE_CHECK_SCRIPT", ROOT.parent / "evidence-check" / "skills" / "evidence-check" / "scripts" / "check_evidence.py"))
IMAGES = ROOT / "testset" / "images"
CATEGORIES = list(library.categories().keys())  # the nine labelled categories
SCHEMA_CATEGORIES = CATEGORIES + ["OTHER"]  # OTHER: a library rule broken in a way no category describes


def _read_key() -> str:
    env_file = (ROOT / os.environ.get("AD_REVIEW_ENV_FILE", ".env")).resolve()
    if not env_file.exists():
        raise SystemExit(f"API key file not found: {env_file}")
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("ANTHROPIC_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("ANTHROPIC_API_KEY missing in the key file")


@lru_cache(maxsize=1)
def client():
    for k in [k for k in os.environ if k.startswith("ANTHROPIC_")]:
        del os.environ[k]
    import anthropic

    return anthropic.Anthropic(api_key=_read_key(), base_url="https://api.anthropic.com", max_retries=4)


@dataclass
class Usage:
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    seconds: float = 0.0
    tool_seconds: float = 0.0
    batch: bool = False  # sent through the Message Batches API: half the list price, and seconds are queue time
    log: list = field(default_factory=list)

    def add(self, resp, secs: float):
        self.calls += 1
        self.input_tokens += resp.usage.input_tokens
        self.output_tokens += resp.usage.output_tokens
        self.seconds += secs

    @property
    def cost(self) -> float:
        full = self.input_tokens * PRICE["input"] + self.output_tokens * PRICE["output"]
        return full * BATCH_DISCOUNT if self.batch else full

    def as_dict(self) -> dict:
        d = {"calls": self.calls, "input_tokens": self.input_tokens, "output_tokens": self.output_tokens,
             "cost_usd": round(self.cost, 6), "model_seconds": round(self.seconds, 2),
             "tool_seconds": round(self.tool_seconds, 2)}
        if self.batch:
            d["pricing"] = "batch"
        return d


BATCH_DISCOUNT = 0.5  # Message Batches API: 50% of the standard price on all tokens
POOL = None  # a BatchPool while a batch run is going; None sends each request on its own


def create(usage: Usage, **kwargs):
    t0 = time.perf_counter()
    params = dict(model=MODEL, output_config={"effort": EFFORT, **kwargs.pop("output_config", {})}, **kwargs)
    if POOL is not None:
        resp = POOL.request(params)
        usage.batch = True
    else:
        resp = client().messages.create(**params)
    usage.add(resp, time.perf_counter() - t0)
    return resp


class BatchPool:
    """Sends the model requests of many concurrent workers as Message Batches (half price).

    Each worker (one ad, or one conversation) runs in its own thread and calls create() as usual; while
    a pool is set as POOL, create() hands the request to the pool and waits. When every running worker
    is waiting, the waiting requests go out as one batch; when it has ended, each worker gets its
    message back and carries on (runs its tools, asks again). Each round of the tool loops, across all
    workers, is one batch, so the prompts, tools and parameters are those of a normal run.
    Results are matched by custom_id. An errored or expired request is sent again in the next batch,
    up to three tries in all; an invalid request is not retried.
    """

    def __init__(self, poll_seconds: float = 15.0, log=print):
        self.cv = threading.Condition()
        self.waiting: dict[str, dict] = {}
        self.running = 0
        self.n = 0
        self.closing = False
        self.poll = poll_seconds
        self.log = log
        self.batches: list[dict] = []
        self.thread = threading.Thread(target=self._loop, daemon=True)

    def start(self):
        self.thread.start()

    def enter(self):
        with self.cv:
            self.running += 1

    def leave(self):
        with self.cv:
            self.running -= 1
            self.cv.notify_all()

    def close(self):
        with self.cv:
            self.closing = True
            self.cv.notify_all()
        self.thread.join()

    def request(self, params: dict):
        with self.cv:
            self.n += 1
            slot = {"params": params, "tries": 0, "done": False, "message": None, "error": None}
            self.waiting[f"req-{self.n}"] = slot
            self.cv.notify_all()
            while not slot["done"]:
                self.cv.wait()
        if slot["error"]:
            raise RuntimeError(slot["error"])
        return slot["message"]

    def _loop(self):
        while True:
            with self.cv:
                while not (self.waiting and len(self.waiting) >= self.running) and not (self.closing and not self.waiting):
                    self.cv.wait(timeout=5)
                if self.closing and not self.waiting:
                    return
                send, self.waiting = self.waiting, {}
            try:
                results = self._send(send)
            except Exception as e:  # the batch itself failed: its requests are tried again, then stored as failures
                results = {}
                self.log(f"batch failed: {type(e).__name__}: {e}")
            with self.cv:
                for cid, slot in send.items():
                    res = results.get(cid)
                    if res is not None and res.type == "succeeded":
                        slot["message"], slot["done"] = res.message, True
                        continue
                    slot["tries"] += 1
                    why = "missing" if res is None else res.type
                    if res is not None and res.type == "errored":
                        why += f" ({getattr(getattr(res.error, 'error', None), 'type', '')})"
                    if slot["tries"] < 3 and "invalid_request" not in why:
                        self.waiting[cid] = slot
                    else:
                        slot["error"], slot["done"] = f"batch request {why}", True
                self.cv.notify_all()

    def _send(self, send: dict) -> dict:
        from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
        from anthropic.types.messages.batch_create_params import Request

        c = client()
        batch = c.messages.batches.create(requests=[
            Request(custom_id=cid, params=MessageCreateParamsNonStreaming(**slot["params"])) for cid, slot in send.items()])
        t0 = time.time()
        while True:
            b = c.messages.batches.retrieve(batch.id)
            if b.processing_status == "ended":
                break
            time.sleep(self.poll)
        results = {r.custom_id: r.result for r in c.messages.batches.results(batch.id)}
        counts = b.request_counts
        self.batches.append({"requests": len(send), "minutes": round((time.time() - t0) / 60, 1),
                             "succeeded": counts.succeeded, "errored": counts.errored, "expired": counts.expired})
        self.log(f"batch {len(self.batches)}: {len(send)} requests, ended after {(time.time() - t0) / 60:.1f} min "
                 f"({counts.succeeded} succeeded, {counts.errored} errored, {counts.expired} expired)")
        return results


# ---------------------------------------------------------------- the ad as the model sees it
def jurisdiction(item: dict) -> str:
    return "CN" if item["lang"] == "zh" else "TikTok"


def image_block(path: Path) -> dict:
    data = base64.standard_b64encode(path.read_bytes()).decode()
    return {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": data}}


def ad_image(item: dict, revised: bool = False) -> Path | None:
    if item["kind"] != "image":
        return None
    return IMAGES / f"{item['id']}{'-rev' if revised else ''}.png"


# ---------------------------------------------------------------- output schema (both arms)
VIOLATION = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": SCHEMA_CATEGORIES},
        "clause_id": {"type": "string", "description": "id of the clause broken, e.g. CN-AL-9-3 or TT-MIS-CLAIMS"},
        "ad_quote": {"type": "string", "description": "the exact words of the ad that break the rule, copied character for character; empty if the problem is only in the picture or is something missing"},
        "visual_evidence": {"type": "string", "description": "what in the picture, or what missing element, breaks the rule; empty if ad_quote covers it"},
        "policy_quote": {"type": "string", "description": "the exact words of the clause that the ad breaks, copied character for character from the clause text"},
        "explanation": {"type": "string", "description": "one or two sentences, in the language of the ad"},
    },
    "required": ["category", "clause_id", "ad_quote", "visual_evidence", "policy_quote", "explanation"],
    "additionalProperties": False,
}
REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "decision": {"type": "string", "enum": ["approve", "reject"]},
        "violations": {"type": "array", "items": VIOLATION},
        "notes": {"type": "string", "description": "optional: words that look risky but are allowed, and why"},
    },
    "required": ["decision", "violations", "notes"],
    "additionalProperties": False,
}


def category_list(lang: str) -> str:
    cats = library.categories()
    lines = [f"- {k}: {v['en']} / {v['zh']}" for k, v in cats.items()]
    lines.append("- OTHER: another rule in the library is broken, and none of the categories above describes it")
    return "\n".join(lines)


# ---------------------------------------------------------------- quote checking (evidence-check)
@lru_cache(maxsize=1)
def python_exe() -> str:
    return sys.executable


def check_quotes(ad_source_text: str, violations: list[dict]) -> list[dict]:
    """Run evidence-check's script on the quotes of each violation.

    The ad's words are one source file (ad.md); every clause is its own source file named after
    its id, so a policy quote passes only if it is a verbatim part of the clause it cites.
    Returns, per violation, {"ad": status or None, "policy": status}.
    """
    clauses = library.by_id()
    claims = []
    for i, v in enumerate(violations):
        if v.get("ad_quote", "").strip():
            claims.append({"id": f"{i}-ad", "text": v["ad_quote"], "evidence": [{"source": "ad.md", "quote": v["ad_quote"]}]})
        claims.append({"id": f"{i}-policy", "text": v.get("policy_quote", ""),
                       "evidence": [{"source": f"{v.get('clause_id', '')}.md", "quote": v.get("policy_quote", "")}]})
    if not claims:
        return []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        src = tmp / "sources"
        src.mkdir()
        (src / "ad.md").write_text(ad_source_text, encoding="utf-8")
        for c in clauses.values():
            (src / f"{c.id}.md").write_text(c.text + "\n", encoding="utf-8")
        (tmp / "claims.json").write_text(json.dumps({"claims": claims}, ensure_ascii=False), encoding="utf-8")
        env = {k: os.environ[k] for k in ("PATH", "SYSTEMROOT") if k in os.environ}
        env["PYTHONIOENCODING"] = "utf-8"
        r = subprocess.run([python_exe(), "-I", str(CHECK_SCRIPT), str(tmp / "claims.json"), "--sources", str(src),
                            "--format", "json"], capture_output=True, text=True, encoding="utf-8", env=env)
        if r.returncode == 2:
            raise RuntimeError(r.stderr)
        report = json.loads(r.stdout)
    status = {c["id"]: c["status"] for c in report["claims"]}
    out = []
    for i, v in enumerate(violations):
        out.append({"ad": status.get(f"{i}-ad"), "policy": status.get(f"{i}-policy")})
    return out


# Unfilled template text in a corrected ad: [..], 【..】, {{..}}, XX/xxx runs, blanks to fill.
PLACEHOLDER_RE = re.compile(r"\[[^\]]{0,60}\]|【[^】]{0,60}】|\{\{[^}]{0,60}\}\}|\bX{2,}\b|\bx{3,}\b|[_＿]{3,}|待填|此处填写|请填写")


def placeholders(text: str) -> list[str]:
    return PLACEHOLDER_RE.findall(text or "")


# Advice fields that were filled in wrongly: tool-call markup written into a field (seen as
# "...</answer> <parameter name="revised_caption">..." inside the answer), or a corrected caption
# that is empty or one word ("x", "ignored"). Used by agent v1.2 and by the multi-turn scorer.
MARKUP_RE = re.compile(r"</?(?:parameter|answer|revised_caption|revised_image_lines|invoke|function_calls)\b", re.I)


def advice_problems(adv: dict | None) -> list[str]:
    adv = adv or {}
    out = []
    fields = [("answer", adv.get("answer", "")), ("revised_caption", adv.get("revised_caption", ""))]
    fields += [("revised_image_lines", line) for line in adv.get("revised_image_lines", []) or []]
    for name, text in fields:
        if MARKUP_RE.search(text or "") and f"{name} contains tool markup" not in out:
            out.append(f"{name} contains tool markup")
    cap = (adv.get("revised_caption") or "").strip()
    if not cap:
        out.append("revised_caption is empty")
    elif len(re.findall(r"[一-鿿]", cap)) < 2 and len(re.findall(r"[^\W_]+", cap)) < 2:
        out.append("revised_caption is a single word")
    return out


LEAKED_PARAM_RE = re.compile(r'<parameter name="(\w+)">(.*?)(?:</parameter>|(?=<parameter name=)|\Z)', re.S)


def clean_advice(adv: dict | None) -> tuple[dict, list[str]]:
    """Agent v1.3: repair advice whose fields leaked into the answer as tool markup. The answer is cut
    where the markup starts; a corrected caption (or image lines) found in the markup is used only when
    the field itself is empty or one word (or, for lines, empty). Returns the repaired advice and notes."""
    adv = dict(adv or {})
    notes = []
    answer = adv.get("answer", "")
    m = MARKUP_RE.search(answer)
    if not m:
        return adv, notes
    tail = answer[m.start():]
    adv["answer"] = answer[:m.start()].rstrip()
    notes.append("answer cut at tool markup")
    leaked = {k: v.strip() for k, v in LEAKED_PARAM_RE.findall(tail)}
    cap_bad = any(p.startswith("revised_caption is") for p in advice_problems(adv))
    if cap_bad and leaked.get("revised_caption"):
        adv["revised_caption"] = leaked["revised_caption"]
        notes.append("caption taken from the markup")
    if not adv.get("revised_image_lines") and leaked.get("revised_image_lines"):
        try:
            lines = json.loads(leaked["revised_image_lines"])
        except ValueError:
            lines = None
        if isinstance(lines, list) and lines:
            adv["revised_image_lines"] = [str(x) for x in lines]
            notes.append("image lines taken from the markup")
    return adv, notes


def gold_ad_source(item: dict, revised: bool = False) -> str:
    return ad_text(item, revised)
