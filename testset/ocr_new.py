"""OCR only the images that have no entry yet in testset/ocr.json (the harder set's images), with the
same engine and settings as agent/ocr.py. Entries already in the file are left exactly as they are.

  python testset/ocr_new.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "agent"))
sys.path.insert(0, str(ROOT / "testset"))
import ocr  # noqa: E402
from load import image_words, load_items  # noqa: E402


def main():
    cache = json.loads(ocr.CACHE.read_text(encoding="utf-8"))
    ocr.engine()
    new = []
    for item in load_items():
        if item["kind"] != "image" or item["id"] in cache:
            continue
        path = ROOT / "testset" / "images" / f"{item['id']}.png"
        text, secs = ocr.read_text(path)
        ref = "\n".join(image_words(item))
        cache[item["id"]] = {"text": text, "seconds": round(secs, 3), "cer": round(ocr.cer(ref, text), 4)}
        new.append(item["id"])
        print(f"{item['id']}: CER {cache[item['id']]['cer']:.3f} | {text!r}", flush=True)
    ocr.CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"added {len(new)} entries")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
