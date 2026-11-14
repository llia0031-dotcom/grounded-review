"""Baseline: ShieldGemma 2 (google/shieldgemma-2-4b-it) with custom image policies, CPU.

STATUS: NOT RUN. Downloading the model requires signing in to Hugging Face and accepting the
model's terms of use. With access on this computer (`hf auth login`), run:

  python baselines/shieldgemma.py --split test

ShieldGemma 2 answers Yes/No for each policy; here every category that can be seen in a picture is
written as a custom policy, and an ad is rejected under a category when P(Yes) > 0.5. The usage
follows the model card (ShieldGemma2ForImageClassification, processor with custom_policies);
the code has not been run against the model. Model files go to the Hugging Face cache.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "testset"))
from load import load_items  # noqa: E402

POLICIES = {
    "ABSOLUTE": "The image claims the product is the best, number one, the strongest or similar.",
    "MEDICAL": "The image claims a product prevents, treats or cures a disease.",
    "GUARANTEE": "The image promises guaranteed results, guaranteed income or guaranteed investment returns.",
    "DISPARAGE": "The image runs down another company's product or service.",
    "DATA": "The image quotes a statistic, percentage or survey result without saying where it comes from.",
    "ALCOHOL": "The image shows people drinking alcohol, drunk people, or encourages drinking.",
    "WEIGHT": "The image makes weight-loss or body-shape claims.",
    "BEFORE_AFTER": "The image shows a before-and-after comparison of results.",
    "FLAG": "The image shows the national flag of China.",
}


def main():
    import torch
    from PIL import Image
    from transformers import AutoProcessor, ShieldGemma2ForImageClassification

    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="test")
    a = ap.parse_args()
    model_id = "google/shieldgemma-2-4b-it"
    processor = AutoProcessor.from_pretrained(model_id)
    model = ShieldGemma2ForImageClassification.from_pretrained(model_id, torch_dtype=torch.bfloat16).eval()
    keys = list(POLICIES)
    out = ROOT / "eval" / "results" / f"shieldgemma-{a.split}.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for it in load_items():
            if it["split"] != a.split or it["kind"] != "image":
                continue
            t0 = time.perf_counter()
            with Image.open(ROOT / "testset" / "images" / f"{it['id']}.png") as im:
                inputs = processor(images=[im.convert("RGB")], custom_policies=POLICIES, policies=keys, return_tensors="pt")
            with torch.inference_mode():
                probs = model(**inputs).probabilities[:, 0].float().tolist()  # P(Yes) per policy
            viols = [{"category": k, "ad_quote": ""} for k, p in zip(keys, probs) if p > 0.5]
            row = {"arm": "shieldgemma2", "item": it["id"], "run": 1, "error": None,
                   "output": {"decision": "reject" if viols else "approve", "violations": viols,
                              "scores": {k: round(p, 4) for k, p in zip(keys, probs)}},
                   "usage": {"cost_usd": 0.0, "calls": 0}, "latency_s": round(time.perf_counter() - t0, 2)}
            f.write(json.dumps(row) + "\n")
            print(it["id"], row["output"]["decision"], flush=True)


if __name__ == "__main__":
    main()
