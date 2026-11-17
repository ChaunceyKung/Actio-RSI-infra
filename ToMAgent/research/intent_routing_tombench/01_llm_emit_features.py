"""Task 1*: LLM-emit feature exploration.

We test multiple LLM-emit architectures for sample-level config routing.
Each architecture produces per-sample JSON which is then mapped to a config.

Architectures (–arch flag selects):

  A_4prob        — LLM emits P(skill helps), P(rag helps), P(memory helps),
                   P(all3 helps). argmax → config.

  B_need8        — LLM emits 8 need scores (procedural / domain_knowledge /
                   similar_case / multi_hop_belief / nonverbal_cue / emotion /
                   intent / quantitative). Trained GBT on top picks config.

  D_need3        — LLM emits 3 need scores (procedural / retrieval /
                   memory_lookup). Simpler version of B; thresholds directly
                   pick config without learning.

  C_reason_prob  — Chain-of-thought: first 1-2 sentences of reasoning about
                   WHAT this sample needs, THEN A_4prob JSON. Tests whether
                   reasoning improves calibration.

  E_judge        — LLM sees sample + the 4 cached predictions and the
                   "thinking" field of each config. Picks which config's
                   reasoning is most defensible → that config.

  F_combined     — Concatenate A + B + D into one JSON output (1 call).
                   Trained GBT on top.

Common output: per-sample {features: {...}, config: "skill|rag|memory|all3"}.

Smoke-first design: a --limit flag for fast iteration on 200 samples.
"""
import sys, json, time, os, threading, re, argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, "/workspace/ToMAgent")
sys.path.insert(0, "/workspace/OVERNIGHT_2026-06-05/task1_classifier")
from tom_harness.llm import LLMClient
from run_classifier import load_source

API_BASE = "http://10.208.62.27:3000/v1"
API_KEY  = os.environ.get("LLM_API_KEY", "")
MODEL    = "Qwen/Qwen3.6-27B"

CFGS = ["skill", "rag", "memory", "all3"]

CFG_CACHES_V4 = {
    "skill":  "/workspace/OVERNIGHT_2026-06-02/task5_full/v4_skill_only_full/results.jsonl",
    "all3":   "/workspace/OVERNIGHT_2026-06-02/task5_full/v4_full/results.jsonl",
    "rag":    "/workspace/OVERNIGHT_2026-06-02/task7_quadrant/rag_only_full/results.jsonl",
    "memory": "/workspace/OVERNIGHT_2026-06-02/task7_quadrant/memory_only_full/results.jsonl",
}
CFG_CACHES_V5 = {
    "skill":  "/workspace/OVERNIGHT_2026-06-05/v5_cache/skill_only/results.jsonl",
    "all3":   "/workspace/OVERNIGHT_2026-06-05/v5_cache/all3/results.jsonl",
    "rag":    "/workspace/OVERNIGHT_2026-06-05/v5_cache/rag_only/results.jsonl",
    "memory": "/workspace/OVERNIGHT_2026-06-05/v5_cache/memory_only/results.jsonl",
}

# ──────────────────────────────────────────────────────────────────
# Prompt definitions
# ──────────────────────────────────────────────────────────────────

A_SYSTEM = """You are estimating which external reasoning supports would help a model solve this Theory-of-Mind multiple-choice item.

SUPPORT TYPES:
- skill: a domain-specific procedural reasoning skill (e.g., 'how to detect false belief', 'how to interpret nonverbal cues')
- rag: retrieved general ToM rules from a corpus (e.g., 'when X smiles at Y after a polite remark, the smile usually masks discomfort')
- memory: bullets from similar past cases stored in long-term memory ('item ph-00065: A character lying about a hidden gift => check both intent and effect')
- all3: skill + rag + memory injected together (more context but can dilute focus)

Estimate P(<each> support will help give the correct answer) — four floats in [0, 1]. These are NOT a probability distribution; they sum to whatever.

Output ONLY a JSON object on one line:
{"p_skill": <float>, "p_rag": <float>, "p_memory": <float>, "p_all3": <float>}
"""

B_SYSTEM = """You are estimating what kind of cognitive support a Theory-of-Mind multiple-choice item needs.

Rate each dimension on integer scale 0-5 (0 = not at all, 5 = strongly required):

- procedural_reasoning: needs a step-by-step ToM procedure (e.g., "first identify X's belief state, then..."). High when the question requires structured perspective-taking.
- domain_knowledge: needs external rules / facts about social interaction (e.g., "people usually feel embarrassed when..."). High when the question hinges on background social commonsense.
- similar_case_lookup: would benefit from seeing similar past cases / examples. High when the situation is unusual and a precedent would anchor judgment.
- multi_hop_belief: requires tracking nested mental states (X thinks Y thinks Z). High for higher-order belief questions.
- nonverbal_cue: hinges on body language / facial expression / gesture interpretation.
- emotion_appraisal: requires inferring how a character emotionally appraises an event.
- intent_inference: requires inferring a character's underlying motive or goal.
- quantitative_reasoning: requires counting, fractions, or proportional reasoning about a set.

Output ONLY a JSON object on one line, each value an integer 0-5:
{"procedural_reasoning": <int>, "domain_knowledge": <int>, "similar_case_lookup": <int>, "multi_hop_belief": <int>, "nonverbal_cue": <int>, "emotion_appraisal": <int>, "intent_inference": <int>, "quantitative_reasoning": <int>}
"""

D_SYSTEM = """You are estimating what kind of cognitive support a Theory-of-Mind multiple-choice item needs.

Rate each on integer 0-5:
- need_procedural: does the question call for a step-by-step ToM technique (perspective-taking, false-belief tracking, ...)?
- need_retrieval: does the question call for external commonsense rules about social behaviour?
- need_memory: would similar past examples help anchor the judgment?

Output ONLY: {"need_procedural": <int>, "need_retrieval": <int>, "need_memory": <int>}
"""

C_SYSTEM = """You are estimating which external reasoning supports would help solve a Theory-of-Mind MCQ.

Step 1: In ONE sentence, identify the most distinctive cognitive demand (e.g., "tracking second-order belief about a moved object", "inferring why an indirect remark is being made").
Step 2: Output JSON with four probabilities (0-1) for each support type:
- skill: procedural ToM technique
- rag: external rule retrieval
- memory: similar past cases lookup
- all3: combine all three

Output format (exactly two lines):
REASON: <1 sentence>
JSON: {"p_skill": <float>, "p_rag": <float>, "p_memory": <float>, "p_all3": <float>}
"""

F_SYSTEM = """You are estimating both WHAT a Theory-of-Mind MCQ needs and WHICH external support will help.

Output ONLY one JSON object combining both:
{
  "p_skill": <float 0-1>, "p_rag": <float 0-1>, "p_memory": <float 0-1>, "p_all3": <float 0-1>,
  "need_procedural": <int 0-5>, "need_retrieval": <int 0-5>, "need_memory": <int 0-5>,
  "need_multi_hop_belief": <int 0-5>, "need_nonverbal_cue": <int 0-5>,
  "need_emotion_appraisal": <int 0-5>, "need_intent_inference": <int 0-5>,
  "need_quantitative": <int 0-5>
}
"""


# ──────────────────────────────────────────────────────────────────
# I/O
# ──────────────────────────────────────────────────────────────────
def build_user(s):
    opts = "\n".join(f"{k}. {v}" for k, v in s["options"].items())
    return f"STORY:\n{s['story']}\n\nQUESTION:\n{s['question']}\n\nOPTIONS:\n{opts}"


def build_user_judge(s, candidates):
    """For arch E. candidates: dict {config: {pred, thinking}}"""
    opts = "\n".join(f"{k}. {v}" for k, v in s["options"].items())
    cand_str = "\n\n".join(
        f"--- candidate from {c} (chosen letter = {v['pred']}) ---\n{v['thinking']}"
        for c, v in candidates.items()
    )
    return (f"STORY:\n{s['story']}\n\nQUESTION:\n{s['question']}\n\nOPTIONS:\n{opts}\n\n"
            f"FOUR CANDIDATE REASONINGS:\n{cand_str}\n\n"
            "Which config's reasoning is most defensible? Output ONLY one of: skill, rag, memory, all3")


E_SYSTEM = """You are a Theory-of-Mind reasoning judge. You see a ToM multiple-choice item and FOUR independent candidate reasonings (skill / rag / memory / all3). Pick the config whose reasoning is most likely correct based on the story.

Output ONLY one word: skill, rag, memory, or all3.
"""

_BRACES = re.compile(r"\{[\s\S]*\}")
def parse_json(text):
    if not text: return None
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try: return json.loads(text)
    except: pass
    m = _BRACES.search(text)
    if m:
        try: return json.loads(m.group(0))
        except: pass
    return None


def make_llm(max_tokens=256):
    return LLMClient(api_base=API_BASE, api_key=API_KEY, model=MODEL,
                     temperature=0.0, max_tokens=max_tokens, timeout=120.0, max_retries=3)


# ──────────────────────────────────────────────────────────────────
# Per-architecture extractor
# ──────────────────────────────────────────────────────────────────
def run_arch(arch, samples, out_path, workers=12, max_tokens=256, judge_cache=None):
    """judge_cache: for arch E, dict {sid: {cfg: {pred, thinking}}}"""
    done = set()
    if os.path.exists(out_path):
        for line in open(out_path):
            try: done.add(json.loads(line)["id"])
            except: pass
    pending = [s for s in samples if s["id"] not in done]
    print(f"[{arch}] resume {len(done)} done, {len(pending)} pending", flush=True)
    if not pending: return

    llm = make_llm(max_tokens)
    lock = threading.Lock()
    fout = open(out_path, "a", encoding="utf-8")
    t0 = time.time(); n = 0

    SYS_MAP = {"A_4prob": A_SYSTEM, "B_need8": B_SYSTEM, "D_need3": D_SYSTEM,
               "C_reason_prob": C_SYSTEM, "F_combined": F_SYSTEM, "E_judge": E_SYSTEM}
    sys_prompt = SYS_MAP[arch]

    def one(s):
        if arch == "E_judge":
            if not judge_cache or s["id"] not in judge_cache:
                return {"id": s["id"], "true_task": s["task"], "raw": "ERR no judge cache",
                        "features": None, "config": "skill"}
            user = build_user_judge(s, judge_cache[s["id"]])
        else:
            user = build_user(s)
        t0_ = time.time()
        try:
            text = llm.chat(sys_prompt, user, max_tokens=max_tokens)
            if arch == "E_judge":
                txt = text.strip().lower()
                pick = next((c for c in CFGS if c in txt), "skill")
                return {"id": s["id"], "true_task": s["task"], "raw": text[:200],
                        "features": {"judge_pick": pick}, "config": pick,
                        "elapsed": time.time() - t0_}
            elif arch == "C_reason_prob":
                # Split REASON / JSON lines
                feats = parse_json(text)
                reason = ""
                for ln in text.split("\n"):
                    if ln.upper().startswith("REASON"):
                        reason = ln.split(":", 1)[-1].strip()
            else:
                feats = parse_json(text)
                reason = ""
            return {"id": s["id"], "true_task": s["task"], "raw": text[:300],
                    "features": feats, "reason": reason, "elapsed": time.time() - t0_}
        except Exception as e:
            return {"id": s["id"], "true_task": s["task"],
                    "raw": f"ERR {type(e).__name__}: {str(e)[:200]}",
                    "features": None, "elapsed": time.time() - t0_}

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(one, s): s for s in pending}
        for fut in as_completed(futs):
            r = fut.result()
            with lock:
                fout.write(json.dumps(r, ensure_ascii=False) + "\n")
                fout.flush()
            n += 1
            if n % 100 == 0:
                rate = n / (time.time() - t0)
                eta = (len(pending) - n) / max(rate, 1e-6)
                print(f"  [{arch}] {n}/{len(pending)} ({rate:.2f}/s, ETA {eta:.0f}s)", flush=True)
    fout.close()


def load_judge_cache():
    """Load thinking + pred from v4 caches keyed by sid → {cfg: {pred, thinking}}."""
    out = {}
    for cfg, path in CFG_CACHES_V4.items():
        for line in open(path):
            d = json.loads(line)
            sid = d["id"]
            out.setdefault(sid, {})[cfg] = {
                "pred": d.get("predicted",""),
                "thinking": (d.get("thinking") or "")[:400]
            }
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--arch", required=True, choices=["A_4prob","B_need8","D_need3","C_reason_prob","F_combined","E_judge"])
    ap.add_argument("--limit", type=int, default=0, help="0 = all 2860; >0 = first-per-task-balanced subset")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    src = load_source()
    samples = list(src.values())
    if args.limit > 0:
        # task-balanced subset
        per_task = {}
        for s in samples:
            per_task.setdefault(s["task"], []).append(s)
        bal = []
        target = max(args.limit // len(per_task), 1)
        for t, lst in per_task.items():
            bal.extend(lst[:target])
        samples = bal
        print(f"Balanced subset: {len(samples)} samples", flush=True)

    out = args.out or f"/workspace/OVERNIGHT_2026-06-05/task1_llm_emit/{args.arch}.jsonl"
    max_tokens = {"A_4prob": 96, "D_need3": 96, "B_need8": 192, "C_reason_prob": 192,
                  "F_combined": 320, "E_judge": 32}[args.arch]
    judge_cache = load_judge_cache() if args.arch == "E_judge" else None
    run_arch(args.arch, samples, out, workers=args.workers, max_tokens=max_tokens,
             judge_cache=judge_cache)
