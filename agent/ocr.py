"""OCR for ad images: RapidOCR with the PP-OCRv6 medium models.

The engine set-up and row grouping follow ../aigc-scene-eval/scripts/ocr_check.py (same author),
where the medium models read Chinese poster text far better than the default small ones.
`python agent/ocr.py` reads every test image once, stores the text and the time it took in
testset/ocr.json, and reports the character error rate against the known words of each image.
"""
from __future__ import annotations

import json
import re
import sys
import time
import unicodedata
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "testset" / "ocr.json"


@lru_cache(maxsize=1)
def engine():
    from rapidocr import ModelType, RapidOCR

    return RapidOCR(params={"Det.model_type": ModelType("medium"), "Rec.model_type": ModelType("medium")})


def run(path: Path) -> list[dict]:
    from PIL import Image

    with Image.open(path) as im:
        res = engine()(im.convert("RGB"))
    out = []
    if res.boxes is None:
        return out
    for box, txt, score in zip(res.boxes, res.txts, res.scores):
        xs, ys = [float(p[0]) for p in box], [float(p[1]) for p in box]
        out.append({"text": txt, "score": float(score), "x0": min(xs), "y0": min(ys), "x1": max(xs), "y1": max(ys)})
    return out


def rows(boxes: list[dict]) -> list[str]:
    """Group boxes into lines, top to bottom, left to right; a visible gap becomes a space."""
    lines: list[list[dict]] = []
    for b in sorted(boxes, key=lambda b: (b["y0"] + b["y1"]) / 2):
        cy, h = (b["y0"] + b["y1"]) / 2, b["y1"] - b["y0"]
        for row in lines:
            if min(x["y0"] for x in row) - 0.25 * h <= cy <= max(x["y1"] for x in row) + 0.25 * h:
                row.append(b)
                break
        else:
            lines.append([b])
    texts = []
    for row in lines:
        row.sort(key=lambda b: b["x0"])
        s = row[0]["text"]
        for prev, cur in zip(row, row[1:]):
            gap = cur["x0"] - prev["x1"]
            s += (" " if gap > 0.3 * (cur["y1"] - cur["y0"]) else "") + cur["text"]
        texts.append(s)
    return texts


def read_text(path: Path) -> tuple[str, float]:
    t0 = time.perf_counter()
    text = "\n".join(rows(run(path)))
    return text, time.perf_counter() - t0


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).lower()
    return "".join(ch for ch in s if ch.isalnum())


def cer(ref: str, hyp: str) -> float:
    a, b = _norm(ref), _norm(hyp)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1] / max(1, len(a))


def cached(image_name: str) -> dict:
    return json.loads(CACHE.read_text(encoding="utf-8"))[image_name]


def main():
    sys.path.insert(0, str(ROOT / "testset"))
    from load import image_words, load_items

    images = ROOT / "testset" / "images"
    out = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    engine()  # load models before timing
    rows_out = []
    for item in load_items():
        if item["kind"] != "image":
            continue
        variants = [(item["id"], image_words(item))]
        if item.get("revision", {}).get("image_lines"):
            variants.append((item["id"] + "-rev", image_words(item, revised=True)))
        for name, lines in variants:
            path = images / f"{name}.png"
            if not path.exists():
                continue
            text, secs = read_text(path)
            ref = "\n".join(lines)
            out[name] = {"text": text, "seconds": round(secs, 3), "cer": round(cer(ref, text), 4)}
            rows_out.append((name, out[name]["cer"], len(_norm(ref))))
    CACHE.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    total_chars = sum(n for _, _, n in rows_out)
    errors = sum(c * n for _, c, n in rows_out)
    print(f"{len(rows_out)} images, {total_chars} characters, CER {errors / total_chars:.3%}")
    for name, c, n in rows_out:
        if c > 0:
            print(f"  {name}: CER {c:.3f}  |  {out[name]['text']!r}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
