"""Run the model arms over a split and store every output.

  AD_REVIEW_ENV_FILE=../launchpad-tracedesk/app/.env python eval/run.py --split dev --repeat 1 --out dev-1
  ... --split test --repeat 2 --out test-2026-11-13

Writes eval/results/<out>.jsonl, one line per (arm, item, run). Lines already in the file are
skipped, so an interrupted run can be continued. --budget stops before the stored cost passes it.
--batch sends the requests through the Message Batches API at half price (common.BatchPool): every
task runs at once and each round of requests goes out as one batch; prompts, tools and parameters
are unchanged, and latency is not measured (it would be queue time).
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "agent"))
import common  # noqa: E402,F401  (sets import paths)
import library  # noqa: E402
import oneshot  # noqa: E402
import review_agent  # noqa: E402
from load import load_items  # noqa: E402

ARMS = {"oneshot": oneshot.review, "agent": review_agent.review}
LOCK = threading.Lock()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "test", "hard", "real"], required=True)
    ap.add_argument("--arms", default="oneshot,agent")
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ids", default="", help="comma-separated item ids (default: the whole split)")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--budget", type=float, default=1.5, help="US$ cap for this results file")
    ap.add_argument("--batch", action="store_true", help="send requests through the Message Batches API (half price)")
    a = ap.parse_args(argv)

    out = ROOT / "eval" / "results" / f"{a.out}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    done, spent = set(), 0.0
    if out.exists():
        for line in out.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if not r.get("error"):
                done.add((r["arm"], r["item"], r["run"]))
            spent += r["usage"]["cost_usd"]
    items = [i for i in load_items() if i["split"] == a.split]
    library.load()
    if library.MISSING and any(i["lang"] == "en" for i in items):
        sys.exit("TikTok policy pages missing (" + ", ".join(sorted(library.MISSING)) + "): see README, Run it")
    if a.ids:
        keep = set(a.ids.split(","))
        items = [i for i in items if i["id"] in keep]
    todo = [(arm, it, run) for run in range(1, a.repeat + 1) for arm in a.arms.split(",") for it in items
            if (arm, it["id"], run) not in done]
    print(f"{len(todo)} tasks to run, US${spent:.4f} already spent in {out.name}")

    pool = None
    if a.batch and todo:
        pool = common.POOL = common.BatchPool(log=lambda m: print(m, flush=True))
        for _ in todo:
            pool.enter()  # every task counts as running from the start, so the first batch holds all first requests
        pool.start()

    def task(arm, it, run):
        t0 = time.time()
        try:
            r = ARMS[arm](it)
        except Exception as e:  # keep going; the failure is stored and retried next time
            r = {"arm": arm, "output": None, "error": f"{type(e).__name__}: {e}", "usage": {"cost_usd": 0.0}, "latency_s": None}
        finally:
            if pool:
                pool.leave()
        if pool:
            r["latency_s"] = None  # queue time, not a measurement
        r.update({"item": it["id"], "run": run, "started": round(t0, 1)})
        return r

    with ThreadPoolExecutor(len(todo) if pool else a.workers) as ex, out.open("a", encoding="utf-8") as f:
        futs = [ex.submit(task, *t) for t in todo]
        for n, fut in enumerate(as_completed(futs), 1):
            r = fut.result()
            with LOCK:
                f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
                f.flush()
                spent += r["usage"]["cost_usd"]
            print(f"[{n}/{len(todo)}] {r['arm']:8s} {r['item']:8s} run {r['run']} "
                  f"{'ERROR ' + r['error'][:80] if r.get('error') else r['output']['decision']}  total US${spent:.4f}", flush=True)
            if spent > a.budget:
                print(f"budget US${a.budget} reached, stopping")
                for fu in futs:
                    fu.cancel()
                break
    if pool:
        pool.close()
        print("batches:", json.dumps(pool.batches), flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
