"""Baseline: zero-shot image classification with CLIP and SigLIP 2 (PyTorch, CPU).

Each image ad is compared with one text prompt per violation category and one prompt for an
ordinary, compliant ad (two phrasings each, embeddings averaged). The top-scoring prompt is the
prediction: if it is the compliant prompt the ad is approved, otherwise it is rejected with that
category. Pure zero-shot: nothing is tuned on the test set, and the prompts were written before
any image was scored. Image ads only; these models do not read captions.

Models (Hugging Face, not gated): openai/clip-vit-base-patch32, google/siglip2-base-patch16-224.
Model files go to the Hugging Face cache (set HF_HOME to move it).
`python baselines/clip_zeroshot.py --split test` writes eval/results/clip-<split>.jsonl and siglip2-<split>.jsonl.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

import torch  # noqa: E402
from PIL import Image  # noqa: E402
from transformers import AutoModel, AutoProcessor  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "testset"))
from load import load_items  # noqa: E402

PROMPTS = {
    "COMPLIANT": ["an ordinary product advertisement", "a simple ad showing a product and its price"],
    "ABSOLUTE": ["an advertisement claiming the product is the best or number one", "an ad saying the product is the strongest in the world"],
    "MEDICAL": ["an advertisement claiming a product cures or treats a disease", "an ad promising to heal an illness"],
    "GUARANTEE": ["an advertisement promising guaranteed results or guaranteed money", "an ad promising guaranteed investment returns"],
    "DISPARAGE": ["an advertisement insulting a competitor's product", "an ad saying another brand is bad"],
    "DATA": ["an advertisement quoting a statistic or percentage", "an ad with a survey number"],
    "ALCOHOL": ["people drinking alcohol", "a person drinking beer or liquor from a glass"],
    "WEIGHT": ["a weight loss advertisement", "an ad promising to burn fat"],
    "BEFORE_AFTER": ["a before and after comparison", "two side-by-side photos showing before and after results"],
    "FLAG": ["the national flag of China", "a red flag with yellow stars"],
}
MODELS = {"clip": "openai/clip-vit-base-patch32", "siglip2": "google/siglip2-base-patch16-224"}


def _vec(out):
    """transformers 5 returns a model output from get_*_features; the projected embedding is pooler_output."""
    return out if isinstance(out, torch.Tensor) else out.pooler_output


def text_embeddings(model, proc, name):
    labels, embs = [], []
    for lab, texts in PROMPTS.items():
        kw = {"padding": "max_length", "max_length": 64} if name == "siglip2" else {"padding": True}
        inp = proc(text=texts, return_tensors="pt", **kw)
        with torch.no_grad():
            e = _vec(model.get_text_features(**inp))
        e = e / e.norm(dim=-1, keepdim=True)
        labels.append(lab)
        embs.append(e.mean(0))
    t = torch.stack(embs)
    return labels, t / t.norm(dim=-1, keepdim=True)


def run(name: str, split: str):
    model = AutoModel.from_pretrained(MODELS[name]).eval()
    proc = AutoProcessor.from_pretrained(MODELS[name])
    labels, temb = text_embeddings(model, proc, name)
    out = ROOT / "eval" / "results" / f"{name}-{split}.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for it in load_items():
            if it["split"] != split or it["kind"] != "image":
                continue
            path = ROOT / "testset" / "images" / f"{it['id']}.png"
            if not path.exists():
                print(f"skip {it['id']}: no image")
                continue
            t0 = time.perf_counter()
            with Image.open(path) as im:
                inp = proc(images=im.convert("RGB"), return_tensors="pt")
            with torch.no_grad():
                e = _vec(model.get_image_features(**inp))
            e = e / e.norm(dim=-1, keepdim=True)
            sims = (e @ temb.T)[0].tolist()
            best = max(range(len(labels)), key=lambda i: sims[i])
            viols = [] if labels[best] == "COMPLIANT" else [{"category": labels[best], "ad_quote": ""}]
            row = {"arm": name, "item": it["id"], "run": 1, "error": None,
                   "output": {"decision": "reject" if viols else "approve", "violations": viols,
                              "scores": {l: round(s, 4) for l, s in zip(labels, sims)}},
                   "usage": {"cost_usd": 0.0, "calls": 0}, "latency_s": round(time.perf_counter() - t0, 3)}
            f.write(json.dumps(row) + "\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="test")
    ap.add_argument("--models", default="clip,siglip2")
    a = ap.parse_args()
    torch.set_num_threads(8)
    for m in a.models.split(","):
        run(m, a.split)
