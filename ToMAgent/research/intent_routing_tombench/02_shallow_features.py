"""Stage 1 of sample-level routing: pure-Python SHALLOW feature extraction.

Goal: a first-class set of features that vary WITHIN a task (not the
task-disambiguation features in features_v5.jsonl). These probe:

  * surface complexity (story / question / option lengths)
  * belief-nesting depth (counts of mental-state verbs)
  * lexical content cues (quantifier / nonverbal / hint / mask / surprise /
    anti-guilt / mental-verb keyword counts)
  * character introductions (rough proper-name count)
  * option-vs-story lexical overlap, option-vs-option distinctness
  * question-form indicators (feel / will / where / why / what / how many)

No LLM calls. Cheap to compute on 2860 samples.
"""
import sys, json, re
from pathlib import Path
sys.path.insert(0, "/workspace/OVERNIGHT_2026-06-05/task1_classifier")
from run_classifier import load_source

OUT_PATH = "/workspace/OVERNIGHT_2026-06-05/task3_sample_level/shallow.jsonl"

# Keyword groups — all lowercase, matched on lowered text.
QUANTIFIER_WORDS = {"some","most","all","none","few","many","several","each","every",
                    "half","quarter","third","one of","two of","three of","four of",
                    "five of","majority","minority","fraction","proportion"}
NONVERBAL_CUE_WORDS = {"smile","smiled","smiles","wink","winked","glance","glanced",
                       "nod","nodded","gesture","gestured","shrug","shrugged",
                       "raise an eyebrow","eye contact","look at"}
HINT_WORDS = {"it's cold","the door","i wonder","could you","would you mind",
              "don't you think","hmm","sigh"}
MASK_WORDS = {"hide","hides","hiding","hid","pretend","pretends","pretended",
              "suppress","suppresses","mask","masking","tries not to","didn't show",
              "kept it inside","held back","force a smile","fake","faked"}
SURPRISE_WORDS = {"suddenly","unexpectedly","to his surprise","to her surprise",
                  "turned out","turns out","reveal","revealed","realised","realized",
                  "discovered","find out","found out","actually","in fact"}
ANTI_GUILT_WORDS = {"might","maybe","perhaps","not sure","unsure","young","little",
                    "small","child","kid","without realizing","accidentally",
                    "didn't mean","by mistake"}
MENTAL_VERBS = {"think","thinks","thought","thinking","believe","believes","believed",
                "know","knows","knew","knowing","expect","expects","expected",
                "want","wants","wanted","feel","feels","felt","feeling",
                "remember","remembered","forget","forgot","assume","assumed",
                "guess","guessed","suspect","suspected","wonder","wondered"}
PERSUASION_WORDS = {"convince","persuade","convinces","persuades","try to",
                    "attempt to","encourage","encourages"}
MORAL_WORDS = {"wrong","right","guilty","blame","fault","sorry","apologize",
               "rule","should","should not","shouldn't","ought to","punish"}
EMOTION_LABEL_WORDS = {"happy","sad","angry","afraid","scared","anxious","worried",
                       "excited","disappointed","embarrassed","proud","ashamed",
                       "jealous","surprised","confused","relieved","calm",
                       "frustrated","upset","delighted"}

# Question-form: cheap regex on lowered question text.
QUESTION_PATTERNS = {
    "q_what_feel":      re.compile(r"\b(feel|mood|emotion)"),
    "q_will_look":      re.compile(r"\b(where will|where would|look for)"),
    "q_what_think":     re.compile(r"\b(think|thinks|believe|believes)\b"),
    "q_what_know":      re.compile(r"\b(know|knows|aware|remember)"),
    "q_why":            re.compile(r"\bwhy\b"),
    "q_what_mean":      re.compile(r"\b(really mean|mean by|what does .* mean)"),
    "q_how_many":       re.compile(r"\bhow many\b|\bhow much\b"),
    "q_what_do_next":   re.compile(r"\b(do next|will .* do|do after|next step)"),
    "q_inappropriate":  re.compile(r"\b(inappropriate|something wrong|right or wrong|said something)"),
    "q_how":            re.compile(r"\bhow (does|do|to|should|would)"),
    "q_true_or_false":  re.compile(r"\b(true|truth|honest|real|really)"),
}

# Proper-name heuristic (English title-case names + "Xiao X" / "Li X" / "Zhang X").
NAME_RE = re.compile(r"\b(?:Xiao|Li|Zhang|Wang|Wu|Sun|Liu|Yang|Zhao|Chen|Lin|Huang|Zhou|Yu)\s+[A-Z][a-z]+|"
                     r"\b[A-Z][a-z]{2,}(?=\s)")
SENT_RE = re.compile(r"[.!?]+\s")
WORD_RE = re.compile(r"\b\w+\b")


def keyword_count(text_l, vocab):
    """Count distinct vocab words present (not raw frequency, to avoid scaling)."""
    return sum(1 for w in vocab if w in text_l)


def jaccard(a, b):
    if not a or not b: return 0.0
    a, b = set(a), set(b)
    return len(a & b) / len(a | b)


def option_distinctness(opts):
    """Max Jaccard pair distance: 1 - max overlap between any 2 options."""
    keys = list(opts.keys())
    if len(keys) < 2: return 0.0
    overlaps = []
    for i in range(len(keys)):
        for j in range(i+1, len(keys)):
            w_i = WORD_RE.findall(opts[keys[i]].lower())
            w_j = WORD_RE.findall(opts[keys[j]].lower())
            overlaps.append(jaccard(w_i, w_j))
    return 1.0 - max(overlaps)


def belief_nesting_depth(text_l):
    """Crude proxy: count consecutive mental-verb tokens within a sliding 8-word window."""
    words = text_l.split()
    max_depth = 0
    for i in range(len(words)):
        depth = sum(1 for w in words[i:i+8] if w in MENTAL_VERBS)
        max_depth = max(max_depth, depth)
    return max_depth


def extract(s):
    story = s["story"] or ""
    q = s["question"] or ""
    opts = {k: (v if isinstance(v, str) else "") for k, v in (s["options"] or {}).items()}
    story_l = story.lower()
    q_l = q.lower()

    story_words = WORD_RE.findall(story_l)
    q_words = WORD_RE.findall(q_l)
    opt_words_all = {k: WORD_RE.findall(v.lower()) for k, v in opts.items()}

    f = {
        # surface
        "story_len_words": len(story_words),
        "question_len_words": len(q_words),
        "n_sentences": len(SENT_RE.split(story)),
        "opt_mean_len": sum(len(v) for v in opt_words_all.values()) / max(len(opts), 1),
        "opt_max_len": max((len(v) for v in opt_words_all.values()), default=0),
        # character / event
        "n_proper_names": len(set(NAME_RE.findall(story))),
        # lexical cue groups (binary count of distinct keywords from each group)
        "kw_quantifier":  keyword_count(story_l + " " + q_l, QUANTIFIER_WORDS),
        "kw_nonverbal":   keyword_count(story_l, NONVERBAL_CUE_WORDS),
        "kw_hint":        keyword_count(story_l, HINT_WORDS),
        "kw_mask":        keyword_count(story_l, MASK_WORDS),
        "kw_surprise":    keyword_count(story_l, SURPRISE_WORDS),
        "kw_anti_guilt":  keyword_count(story_l, ANTI_GUILT_WORDS),
        "kw_persuade":    keyword_count(story_l + " " + q_l, PERSUASION_WORDS),
        "kw_moral":       keyword_count(story_l + " " + q_l, MORAL_WORDS),
        "kw_emotion_lbl": keyword_count(story_l, EMOTION_LABEL_WORDS),
        # belief nesting
        "mental_verb_count":  sum(1 for w in story_words if w in MENTAL_VERBS),
        "belief_depth_proxy": belief_nesting_depth(story_l),
        # option-level
        "opt_distinctness": option_distinctness(opts),
        "opt_story_overlap_max": max(jaccard(o, story_words) for o in opt_words_all.values()),
        "opt_story_overlap_mean": sum(jaccard(o, story_words) for o in opt_words_all.values()) / max(len(opts), 1),
    }
    # question-form indicators (0/1)
    for name, pat in QUESTION_PATTERNS.items():
        f[name] = int(bool(pat.search(q_l)))
    return f


def main():
    src = load_source()
    print(f"Loaded {len(src)} samples", flush=True)
    fout = open(OUT_PATH, "w", encoding="utf-8")
    for sid, s in src.items():
        f = extract(s)
        fout.write(json.dumps({"id": sid, "true_task": s["task"], "features": f}) + "\n")
    fout.close()
    print(f"Wrote {OUT_PATH}", flush=True)


if __name__ == "__main__":
    main()
