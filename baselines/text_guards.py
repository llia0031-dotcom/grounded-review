"""Baseline: two open text guardrail models on the text ads (CPU, no API calls).

  qwen3guard  Qwen/Qwen3Guard-Gen-4B (Apache-2.0). A general safety classifier with a fixed list of
              categories (violence, illegal acts, sexual content, personal data, self-harm, unethical
              acts, politically sensitive topics, copyright, jailbreak); it cannot take a custom
              policy. The ad copy is sent as the user message, as in the model card's prompt
              moderation example. It answers Safe, Controversial or Unsafe; Unsafe or Controversial
              counts as reject (the stricter reading; the looser one, Unsafe only, is also reported).
  granite     ibm-granite/granite-guardian-3.3-8b (Apache-2.0). Takes a custom criterion in natural
              language ("bring your own criteria"); the model card says it was trained and tested on
              English data only. The criterion is the nine categories, in the same words the model
              arms see. The ad copy is the user message; thinking off; it answers yes or no.

Both run once per ad, greedy decoding, on the text ads of a split (the caption is the whole ad).
Neither names a category of this test set, cites a clause or quotes the ad, so a reject is stored
as one violation of category OTHER and only the decision measures apply.
Model files go to the Hugging Face cache (set HF_HOME to move it).

  python baselines/text_guards.py --model qwen3guard --split test   (resumable; eval/results/qwen3guard-<split>.jsonl)
  python baselines/text_guards.py --model granite --split dev --limit 2
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "testset"))
sys.path.insert(0, str(ROOT / "policies"))
import library  # noqa: E402
from load import load_items  # noqa: E402

MODELS = {"qwen3guard": "Qwen/Qwen3Guard-Gen-4B", "granite": "ibm-granite/granite-guardian-3.3-8b"}
ARMS = {"qwen3guard": "qwen3guard", "granite": "granite-guardian"}


def criterion() -> str:
    lines = ["The text is an advertisement that breaks an advertising policy, because it falls under at least one of these categories:"]
    for i, (k, v) in enumerate(library.categories().items(), 1):
        lines.append(f"{i}. {v['en']}.")
    return "\n".join(lines)


def prompt_text(tok, which: str, copy: str) -> str:
    messages = [{"role": "user", "content": copy}]
    if which == "granite":
        return tok.apply_chat_template(messages, guardian_config={"custom_criteria": criterion()}, think=False,
                                       tokenize=False, add_generation_prompt=True)
    return tok.apply_chat_template(messages, tokenize=False)


def parse(which: str, text: str) -> tuple[str, dict]:
    if which == "granite":
        m = re.findall(r"<score>\s*(yes|no)\s*</score>", text, re.I)
        score = m[-1].lower() if m else None
        return ("reject" if score == "yes" else "approve"), {"score": score}
    s = re.search(r"Safety:\s*(Safe|Unsafe|Controversial)", text)
    c = re.search(r"Categories:\s*(.+)", text)
    safety = s.group(1) if s else None
    return ("reject" if safety in ("Unsafe", "Controversial") else "approve"), \
        {"safety": safety, "categories": c.group(1).strip() if c else None}


def main():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=list(MODELS), required=True)
    ap.add_argument("--split", default="test")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--threads", type=int, default=16)
    a = ap.parse_args()
    torch.set_num_threads(a.threads)
    arm = ARMS[a.model]
    out = ROOT / "eval" / "results" / f"{arm}-{a.split}.jsonl"
    done = {json.loads(l)["item"] for l in out.read_text(encoding="utf-8").splitlines()} if out.exists() else set()
    items = [it for it in load_items() if it["split"] == a.split and it["kind"] == "text" and it["id"] not in done]
    if a.limit:
        items = items[: a.limit]
    t0 = time.perf_counter()
    tok = AutoTokenizer.from_pretrained(MODELS[a.model])
    model = AutoModelForCausalLM.from_pretrained(MODELS[a.model], dtype=torch.bfloat16).eval()
    print(f"model loaded in {time.perf_counter() - t0:.0f} s; {len(items)} ads to do", flush=True)
    with out.open("a", encoding="utf-8") as f:
        for it in items:
            t1 = time.perf_counter()
            inputs = tok([prompt_text(tok, a.model, it["copy"])], return_tensors="pt", add_special_tokens=False)
            with torch.inference_mode():
                gen = model.generate(**inputs, max_new_tokens=64, do_sample=False)
            answer = tok.decode(gen[0, inputs.input_ids.shape[1]:], skip_special_tokens=True)
            decision, parsed = parse(a.model, answer)
            row = {"arm": arm, "item": it["id"], "run": 1, "error": None,
                   "output": {"decision": decision,
                              "violations": [{"category": "OTHER", "ad_quote": ""}] if decision == "reject" else [],
                              "parsed": parsed, "raw": answer},
                   "usage": {"cost_usd": 0.0, "calls": 0, "input_tokens": int(inputs.input_ids.shape[1]),
                             "output_tokens": int(gen.shape[1] - inputs.input_ids.shape[1])},
                   "latency_s": round(time.perf_counter() - t1, 1)}
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            print(f"{it['id']}: {decision} {parsed} {row['latency_s']} s", flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
