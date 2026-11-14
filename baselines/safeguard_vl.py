"""Baseline: an open, policy-aware image guardrail model, SafeGuard-VL-RL (CPU).

Model: tyodd/SafeGuard-VL-RL (Apache-2.0; base Qwen/Qwen2.5-VL-7B-Instruct, Apache-2.0), from the
CVPR 2026 paper "Towards Policy-Adaptive Image Guardrail: Benchmark and Method". It reads a policy
written in natural language and judges an image against it. It is downloadable without signing in
or accepting terms. It replaces ShieldGemma 2 in this comparison.

Each image ad gets one request: the nine violation categories written as a policy (same wording as
the category list the model arms see), the prompt format of the model card, and a request to end
with the category and Safe/Unsafe. Image ads only; the caption is not shown (like CLIP).
Model files go to the Hugging Face cache (set HF_HOME to move it).

  python baselines/safeguard_vl.py --split test            (resumable; writes eval/results/safeguard-vl-<split>.jsonl)
  python baselines/safeguard_vl.py --split dev --limit 2   (timing check)
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

MODEL_ID = "tyodd/SafeGuard-VL-RL"
CODES = list(library.categories().keys())


def policy_text() -> str:
    cats = library.categories()
    lines = ["This is an advertising policy. An ad image is Unsafe if it falls under any of these categories:"]
    for i, (k, v) in enumerate(cats.items(), 1):
        lines.append(f"O{i}: {k} - {v['en']}.")
    lines.append("Otherwise the ad image is Safe.")
    return "\n".join(lines)


PROMPT = ("Based on the following safety policy, determine if this image is safe or unsafe.\n\nPolicy:\n{policy}\n\n"
          "Provide your reasoning and final judgment (Safe/Unsafe). End with two lines:\n"
          "Category: <O-number and name, or None>\nJudgment: <Safe or Unsafe>")


def parse(text: str) -> tuple[str, list[str]]:
    judg = re.findall(r"\b(Unsafe|Safe)\b", text)
    decision = "reject" if judg and judg[-1] == "Unsafe" else "approve"
    cats = []
    m = re.search(r"Category:\s*(.+)", text)
    seg = m.group(1) if m else text[-300:]
    for i, k in enumerate(CODES, 1):
        if re.search(rf"\bO{i}\b", seg) or k in seg:
            cats.append(k)
    if decision == "approve":
        cats = []
    return decision, cats


def main():
    import torch
    from PIL import Image
    from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="test")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--max-pixels", type=int, default=640 * 640)
    ap.add_argument("--threads", type=int, default=16)
    a = ap.parse_args()
    torch.set_num_threads(a.threads)
    out = ROOT / "eval" / "results" / f"safeguard-vl-{a.split}.jsonl"
    done = {json.loads(l)["item"] for l in out.read_text(encoding="utf-8").splitlines()} if out.exists() else set()
    items = [it for it in load_items() if it["split"] == a.split and it["kind"] == "image" and it["id"] not in done]
    if a.limit:
        items = items[: a.limit]
    t0 = time.perf_counter()
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(MODEL_ID, torch_dtype=torch.bfloat16).eval()
    processor = AutoProcessor.from_pretrained(MODEL_ID, max_pixels=a.max_pixels)
    print(f"model loaded in {time.perf_counter() - t0:.0f} s; {len(items)} images to do", flush=True)
    prompt = PROMPT.format(policy=policy_text())
    with out.open("a", encoding="utf-8") as f:
        for it in items:
            t1 = time.perf_counter()
            with Image.open(ROOT / "testset" / "images" / f"{it['id']}.png") as im:
                image = im.convert("RGB")
            messages = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": prompt}]}]
            text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = processor(text=[text], images=[image], return_tensors="pt")
            with torch.inference_mode():
                gen = model.generate(**inputs, max_new_tokens=320, do_sample=False)
            answer = processor.batch_decode(gen[:, inputs.input_ids.shape[1]:], skip_special_tokens=True)[0]
            decision, cats = parse(answer)
            row = {"arm": "safeguard-vl", "item": it["id"], "run": 1, "error": None,
                   "output": {"decision": decision, "violations": [{"category": c, "ad_quote": ""} for c in cats]
                              or ([{"category": "OTHER", "ad_quote": ""}] if decision == "reject" else []),
                              "raw": answer},
                   "usage": {"cost_usd": 0.0, "calls": 0, "input_tokens": int(inputs.input_ids.shape[1]),
                             "output_tokens": int(gen.shape[1] - inputs.input_ids.shape[1])},
                   "latency_s": round(time.perf_counter() - t1, 1)}
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            print(f"{it['id']}: {decision} {cats} {row['latency_s']} s, {row['usage']['output_tokens']} tokens", flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
