# EmoBench Adaptation Design

**Date:** 2026-06-02  
**Author:** Kiro  
**Status:** Draft

## Overview

This document specifies the adaptation of the EmoBench dataset (Emotional Intelligence evaluation benchmark) into the tom_harness framework, following the established patterns from ToMBench and TactfulToM adaptations. EmoBench evaluates LLMs on two distinct emotional intelligence tasks: Emotional Understanding (EU) and Emotional Application (EA).

## Background

**EmoBench** is a bilingual (English/Chinese) benchmark with 400 hand-crafted scenarios designed to evaluate emotional intelligence:

- **EU (Emotional Understanding)**: 200 samples per language (400 total)
  - Recognizing emotions and their causes in complex scenarios
  - Dual-question format: emotion identification + cause identification
  - Categories: complex_emotions, emotional_cues, personal_beliefs, perspective_taking
  
- **EA (Emotional Application)**: 200 samples per language (400 total)
  - Recommending effective emotional responses or actions
  - Single multiple-choice format
  - Categories by relationship (Personal/Social), problem (Self/Others), question type (Response/Action)

## Goals

1. Create a unified data loader for both EU and EA tasks
2. Implement a harness runner supporting ablation experiments (baseline, +skill, +rag, +memory, +fusion)
3. Handle EU's dual-question format with strict scoring (both answers must be correct)
4. Generate comprehensive statistics: overall, per-task (EU/EA), and per-category breakdowns
5. Provide an ablation experiment shell script matching the ToMBench/TactfulToM patterns

## Architecture

### Component 1: Data Loader (`benchmark/load_emobench.py`)

**Purpose:** Load EmoBench JSONL files and convert to harness-compatible format.

**Input:**
- `data/EU.jsonl`: 400 samples (200 en, 200 zh)
- `data/EA.jsonl`: 400 samples (200 en, 200 zh)

**Output:** List of sample dictionaries compatible with `HarnessRuntime.answer_one()`

**Sample Format:**

EU samples:
```python
{
    "id": "EU_en_001",
    "story": "<scenario>",
    "question": "What emotion is <subject> feeling?\n\nWhat caused this emotion?",
    "options": {
        "A": "Delight",
        "B": "Anger",
        "C": "Embarrassment",
        "D": "Hopeless",
        "E": "Pride",
        "F": "Disappointment",
        "G": "Her daughter tried to make her feel better...",
        "H": "Her daughter enjoyed the Baklava...",
        "I": "The Baklava was not ruined",
        "J": "Her daughter just arrived home"
    },
    "answer": "A|H",  # emotion_letter|cause_letter
    "metadata": {
        "task": "EU",
        "category": "complex_emotions",
        "finegrained_category": "emotion_transition",
        "lang": "en",
        "qid": "1",
        "emotion_answer": "A",
        "cause_answer": "H"
    }
}
```

EA samples:
```python
{
    "id": "EA_en_001",
    "story": "<scenario>",
    "question": "<question for subject>",
    "options": {
        "A": "Promise to keep the secret",
        "B": "Inform their parents anyway",
        "C": "Confront the bullies herself",
        "D": "Suggest her brother to talk to a teacher or counselor"
    },
    "answer": "D",
    "metadata": {
        "task": "EA",
        "category": "Personal-Others",
        "question_type": "Action",
        "lang": "en",
        "qid": "1"
    }
}
```

**API:**
```python
def load_emobench(
    data_dir: Path | str | None = None,
    *,
    tasks: set[str] | None = None,  # {"EU", "EA"}, None = both
    languages: set[str] | None = None,  # {"en", "zh"}, None = both
    categories: set[str] | None = None,  # Filter by category
) -> list[dict]:
    """Load EmoBench dataset and return harness-compatible samples."""
```

**Implementation Details:**
- Default data_dir: `benchmark/EmoBench/data/`
- Combine emotion_choices + cause_choices into unified options dict for EU
- Use letters A-Z for option labels (EU needs ~10 options total)
- Store both emotion/cause answers separately in metadata for detailed analysis
- Handle bilingual support (filter by language)
- Map finegrained categories to broader categories for EU

### Component 2: Harness Runner (`examples/run_emobench_harness.py`)

**Purpose:** Run EmoBench evaluation with module ablation support.

**Command-line Interface:**
```bash
python examples/run_emobench_harness.py \
  --limit 20 \                    # samples per task (0 = all)
  --offset 0 \
  --tasks "EU,EA" \                # or "EU" or "EA"
  --lang "en" \                    # or "zh" or "all"
  --categories "complex_emotions,Personal-Others" \
  --skill \                        # enable skill routing
  --rag \                          # enable RAG retrieval
  --memory \                       # enable memory playbook
  --workers 8 \
  --out_dir results/emobench
```

**EU Task Processing:**

1. **Prompt Construction:**
   ```
   Story: <scenario>
   Subject: <subject>
   
   Question 1: What emotion is <subject> feeling?
   A) Delight
   B) Anger
   ...
   
   Question 2: What caused this emotion?
   G) Her daughter tried to make her feel better...
   H) Her daughter enjoyed the Baklava...
   ...
   
   Please answer both questions.
   ```

2. **Response Parsing:**
   - Extract two answers from LLM response
   - Handle formats: "A and H", "A, H", "Q1: A, Q2: H", JSON format
   - Fallback: regex matching for single letters

3. **Scoring:**
   - Strict: `correct = (predicted_emotion == answer_emotion) AND (predicted_cause == answer_cause)`
   - Store both individual predictions for analysis

**EA Task Processing:**
- Standard multiple-choice processing via `answer_one()`
- Single answer extraction

**Statistics Output (`stats.json`):**
```json
{
  "overall": {
    "total": 800,
    "correct": 450,
    "accuracy": 0.5625,
    "errors": 0
  },
  "per_task": {
    "EU": {
      "total": 400,
      "correct": 200,
      "accuracy": 0.5000,
      "errors": 0,
      "emotion_only_correct": 250,
      "cause_only_correct": 230
    },
    "EA": {
      "total": 400,
      "correct": 250,
      "accuracy": 0.6250,
      "errors": 0
    }
  },
  "per_category": {
    "EU": {
      "complex_emotions": {"total": 100, "correct": 50, "accuracy": 0.5000},
      "emotional_cues": {"total": 100, "correct": 55, "accuracy": 0.5500},
      ...
    },
    "EA": {
      "Personal-Others": {"total": 100, "correct": 65, "accuracy": 0.6500},
      "Personal-Self": {"total": 100, "correct": 60, "accuracy": 0.6000},
      ...
    }
  },
  "per_language": {
    "en": {"total": 400, "correct": 230, "accuracy": 0.5750},
    "zh": {"total": 400, "correct": 220, "accuracy": 0.5500}
  },
  "benchmark": "EmoBench"
}
```

**Per-sample Results (`results.jsonl`):**
```json
{
  "id": "EU_en_001",
  "task": "EU",
  "category": "complex_emotions",
  "lang": "en",
  "answer": "A|H",
  "predicted": "A|H",
  "predicted_emotion": "A",
  "predicted_cause": "H",
  "correct": true,
  "emotion_correct": true,
  "cause_correct": true,
  "skill_id": "micro_belief_track",
  "skill_ids": ["macro_emotional_reasoning", "micro_belief_track"],
  "n_llm_calls": 2,
  "elapsed_sec": 1.23
}
```

### Component 3: Ablation Script (`examples/run_emobench_ablation.sh`)

**Purpose:** Run systematic ablation experiments across module combinations.

**Configurations:**
1. `1_baseline` - No modules
2. `2_skill` - Skill routing only
3. `3_rag` - RAG retrieval only
4. `4_memory` - Memory playbook only
5. `8_skill_rag_memory` - All modules (fusion)

**Usage:**
```bash
# Full dataset
bash examples/run_emobench_ablation.sh

# Quick test (20 samples per task)
bash examples/run_emobench_ablation.sh --limit 20

# Specific language
bash examples/run_emobench_ablation.sh --lang en

# Specific tasks
bash examples/run_emobench_ablation.sh --tasks EU
```

**Output Structure:**
```
results/emobench_ablation_0602/
├── 1_baseline/
│   ├── results.jsonl
│   ├── stats.json
│   ├── run.log
│   └── console.log
├── 2_skill/
│   └── ...
├── 3_rag/
│   └── ...
├── 4_memory/
│   └── ...
└── 8_skill_rag_memory/
    └── ...
```

**Summary Report:**

The script generates a comprehensive comparison table:

```
============================================================
 EmoBench Ablation Summary — 2026-06-02
 Results dir: results/emobench_ablation_0602
============================================================

Config                     Total Correct      Acc Errors
------------------------- ------ ------- -------- ------
1_baseline                   800     440    55.00%      0
2_skill                      800     468    58.50%      0
3_rag                        800     456    57.00%      0
4_memory                     800     464    58.00%      0
8_skill_rag_memory           800     492    61.50%      0

Per-task accuracy:

Task            baseline    skill      rag   memory   fusion
---------------------------------------------------------
EU                 52.0     56.5     54.0     55.5     59.0
EA                 58.0     60.5     60.0     60.5     64.0

Per-category accuracy (EU):

Category                 baseline    skill      rag   memory   fusion
--------------------------------------------------------------------
complex_emotions            48.0     52.0     50.0     51.0     55.0
emotional_cues              54.0     58.0     56.0     57.0     60.0
personal_beliefs            50.0     55.0     52.0     54.0     58.0
perspective_taking          56.0     61.0     58.0     60.0     63.0

Per-category accuracy (EA):

Category                 baseline    skill      rag   memory   fusion
--------------------------------------------------------------------
Personal-Others             56.0     59.0     58.0     59.0     62.0
Personal-Self               55.0     58.0     57.0     58.0     61.0
Social-Others               60.0     62.0     62.0     62.0     66.0
Social-Self                 61.0     63.0     63.0     64.0     67.0

Per-language accuracy:

Language         baseline    skill      rag   memory   fusion
---------------------------------------------------------
en                  56.0     60.0     58.0     59.0     63.0
zh                  54.0     57.0     56.0     57.0     60.0
```

## Implementation Plan

### Phase 1: Data Loader
1. Create `benchmark/load_emobench.py`
2. Implement EU sample builder (dual-question format)
3. Implement EA sample builder (standard MCQ)
4. Add filtering by task/language/category
5. Unit test with sample data

### Phase 2: Harness Runner
1. Create `examples/run_emobench_harness.py`
2. Implement EU response parsing (dual-answer extraction)
3. Implement EU strict scoring
4. Implement statistics computation with per-task breakdown
5. Add logging and progress tracking
6. Test with baseline configuration

### Phase 3: Ablation Script
1. Create `examples/run_emobench_ablation.sh`
2. Define 5 module configurations
3. Implement auto-skip for completed runs
4. Add Python summary script with multi-level reporting
5. Test full ablation pipeline

### Phase 4: Validation
1. Run quick test (--limit 5) on all configurations
2. Verify EU scoring correctness
3. Verify statistics computation
4. Check summary report formatting
5. Run full ablation on subset (--limit 20)

## Key Design Decisions

### EU Dual-Question Handling

**Decision:** Single LLM call with structured prompt requesting both answers.

**Rationale:**
- Mirrors original EmoBench evaluation methodology
- More efficient than two separate calls
- Tests model's ability to handle multi-part questions
- Better reflects real-world emotional intelligence scenarios

**Alternative Considered:** Two separate LLM calls (one for emotion, one for cause)
- Rejected: Doubles API costs, doesn't match original benchmark design

### EU Scoring Strategy

**Decision:** Strict scoring (both emotion AND cause must be correct)

**Rationale:**
- Matches user requirement
- Reflects holistic emotional understanding
- Aligns with EmoBench paper's evaluation protocol
- Provides clearer signal for ablation analysis

**Additional Tracking:** Store individual emotion/cause correctness for fine-grained analysis

### Option Label Scheme

**Decision:** Use letters A-Z for all options (EU needs ~10 total)

**Rationale:**
- Consistent with ToMBench/TactfulToM patterns
- Python's `string.ascii_uppercase` provides clean implementation
- Avoids confusion with numeric labels
- Supports up to 26 options (sufficient for EU's typical 6 emotions + 4 causes)

### Statistics Structure

**Decision:** Hierarchical structure with overall → per-task → per-category breakdown

**Rationale:**
- Matches existing harness patterns
- Enables multi-level ablation analysis
- Supports both aggregate and granular insights
- Facilitates cross-benchmark comparison

## Testing Strategy

### Unit Testing
- Test EU sample construction with all emotion/cause combinations
- Test EA sample construction with all categories
- Test response parsing with various LLM output formats
- Test scoring logic (strict EU, standard EA)

### Integration Testing
- Run baseline on 5 samples per task
- Run each module configuration on 5 samples
- Verify statistics correctness
- Check log output formatting

### Full Validation
- Run complete ablation with --limit 20
- Verify consistency across configurations
- Check for crashes or hangs
- Validate summary report accuracy

## Success Criteria

1. **Correctness:** EU strict scoring matches expected behavior
2. **Completeness:** All 800 samples (both tasks, both languages) load correctly
3. **Robustness:** Handles various LLM response formats for EU parsing
4. **Performance:** Completes full ablation (5 configs × 800 samples) within reasonable time
5. **Usability:** Summary report provides clear insights for ablation analysis
6. **Consistency:** Matches ToMBench/TactfulToM patterns and conventions

## Open Questions

None - design is complete and ready for implementation.

## References

- EmoBench Paper: [ACL 2024](https://aclanthology.org/2024.acl-long.326/)
- EmoBench Repository: https://github.com/Sahandfer/EmoBench
- ToMBench Adaptation: `benchmark/load_tombench.py`, `examples/run_tombench_harness.py`
- TactfulToM Adaptation: `benchmark/load_tactful_tom.py`, `examples/run_tactful_tom_harness.py`
