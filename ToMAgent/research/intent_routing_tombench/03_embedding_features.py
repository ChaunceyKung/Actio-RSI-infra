"""Re-extract embeddings for all 2860 ToMBench samples using a strong embedding model.

Endpoint: http://10.208.62.27:3000/v1  OpenAI-compatible /embeddings.
Default model: Qwen/Qwen3-Embedding-4B (2560-dim).

Concurrency: 12 workers. Resume-safe via partial save.
"""
import sys, json, os, time, threading, argparse, hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import requests

sys.path.insert(0, "/workspace/OVERNIGHT_2026-06-05/task1_classifier")
from run_classifier import load_source

API_BASE = "http://10.208.62.27:3000/v1"
API_KEY  = os.environ.get("LLM_API_KEY", "")


def sample_text(s):
    opts = "\n".join(f"{k}. {v}" for k, v in s["options"].items())
    return f"STORY: {s['story']}\nQUESTION: {s['question']}\nOPTIONS:\n{opts}"


def embed_one(text, model, max_retries=3):
    payload = {"model": model, "input": text}
    for attempt in range(max_retries):
        try:
            r = requests.post(f"{API_BASE}/embeddings",
                              headers={"Authorization": f"Bearer {API_KEY}",
                                       "Content-Type": "application/json"},
                              json=payload, timeout=120)
            r.raise_for_status()
            j = r.json()
            return j["data"][0]["embedding"]
        except Exception as e:
            if attempt == max_retries - 1:
                return None
            time.sleep(2.0 ** attempt)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen3-Embedding-4B")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--out_prefix", default="qwen4b")
    args = ap.parse_args()

    src = load_source()
    ids = list(src.keys())
    n = len(ids)
    print(f"Loaded {n} samples; model={args.model}", flush=True)

    out_dir = Path("/workspace/OVERNIGHT_2026-06-05/task3_embed_qwen")
    out_dir.mkdir(exist_ok=True)
    part_path = out_dir / f"partial_{args.out_prefix}.jsonl"
    npy_path  = out_dir / f"embeddings_{args.out_prefix}.npy"
    ids_path  = out_dir / f"ids_{args.out_prefix}.json"

    # Resume from partial
    done = {}
    if part_path.exists():
        for line in open(part_path):
            d = json.loads(line)
            done[d["id"]] = d["emb"]
    pending = [sid for sid in ids if sid not in done]
    print(f"Resume: {len(done)} done, {len(pending)} pending", flush=True)

    if pending:
        lock = threading.Lock()
        fout = open(part_path, "a", encoding="utf-8")
        t0 = time.time(); n_done = 0

        def work(sid):
            text = sample_text(src[sid])
            e = embed_one(text, args.model)
            return sid, e

        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(work, sid): sid for sid in pending}
            for fut in as_completed(futs):
                sid, e = fut.result()
                if e is None:
                    continue
                with lock:
                    fout.write(json.dumps({"id": sid, "emb": e}) + "\n")
                    fout.flush()
                    done[sid] = e
                n_done += 1
                if n_done % 100 == 0:
                    rate = n_done / (time.time() - t0)
                    eta = (len(pending) - n_done) / max(rate, 1e-6)
                    print(f"  {n_done}/{len(pending)} ({rate:.2f}/s, ETA {eta:.0f}s)", flush=True)
        fout.close()

    # Assemble final ordered npy
    arr = np.array([done[sid] for sid in ids], dtype=np.float32)
    np.save(npy_path, arr)
    json.dump(ids, open(ids_path, "w"))
    print(f"Wrote {npy_path} shape={arr.shape}, {ids_path}")


if __name__ == "__main__":
    main()
