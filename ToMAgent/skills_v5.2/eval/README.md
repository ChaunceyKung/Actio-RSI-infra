# skills_v5 evaluation

Evaluate the 76-skill library against ToMBench (2860 items × EN + ZH).

## Layout

```
skills_v5/
├── data/
│   ├── build_dataset.py        # split source ToMBench → bilingual jsonl
│   ├── ToMBench_en.jsonl       # 2860 items
│   └── ToMBench_zh.jsonl       # 2860 items
├── eval/
│   ├── eval_tombench.py        # main runner
│   ├── runs/<run_id>/
│   │   ├── config.json
│   │   ├── results.jsonl       # one row per item (resumable)
│   │   └── summary.json
│   ├── README.md
│   └── .env.example
└── skills/                     # 20 macros + 56 micros (4 L0 + 52 others)
```

## Pipeline (per item)

```
[1] route prep      inject micro-01 (task routing) as router system prompt
[2] route           pick 0+ skills (depends on --route-mode)
[3] solve + reroute  picked skills injected; if --reroute-budget > 0 the solver
                     checks each skill's boundary exits and, on a misfit, emits
                     `REROUTE: <skill-id> | <capability>` naming the misfitting
                     skill instead of answering. That skill is dropped and never
                     answers: with budget left it is replaced by a layer-aware
                     re-pick (micro exit keeps the macro, re-picks its expandable
                     subset; macro exit re-runs the full two-stage route); with
                     no budget left the solver commits using the remaining
                     skills. Bounded by the budget. Otherwise it outputs the
                     draft letter.
[4] review (opt)    if --review-mode on: inject micro-02 + micro-03 + micro-04
                    with the draft, LLM outputs final letter (= draft if no
                    change needed). Both draft and final are recorded so the
                    review lift can be measured without a second run.
```

L0 micros (`micro-01..04`) are reserved for stages 1 and 4. They never appear
as candidates in stages 2–3; the 52 non-L0 micros + 20 macros are the
route-able pool.

**Thinking mode:** every request sends `extra_body={"enable_thinking": false}`,
so all models run non-thinking (providers that gate native reasoning on this
flag answer directly). This keeps results comparable across models.

**Reroute (`--reroute-budget`, default 1):** the skill self-correction loop in
stage 3. `0` disables it (and reproduces the pre-reroute flow). The solver names
the misfitting skill (`REROUTE: <skill-id> | <capability>`); only that skill is
excluded (not the whole picked set), and it never produces the final answer.
The re-pick is faithful to the **route_mode's own router** and to which layer
exited: for `hierarchical`, a micro exit keeps the macro and re-picks within its
expandable subset, while a macro exit re-runs the full two-stage (macro-gated
micro) flow — so every routing decision in a `hierarchical` run stays
hierarchical. If the budget is spent and the solver still flags a misfit, the
flagged skill is dropped and the answer is committed using the remaining skills
(no router call). The same drop-and-commit applies when the solver names a
misfitting skill but gives no capability hint — there is nothing to guide a
re-pick, so the skill is simply dropped. If no skill can be identified at all
(and a capability was given with budget left), all picked skills are dropped and
re-picked from scratch. Each item records `reroute_count` and `initial_picked` →
`picked_skills`, and the summary reports `n_rerouted` and `acc_by_reroute_count`.
Inactive for `baseline`.

## Routing modes (`--route-mode`)

| mode           | candidate pool                                              | LLM router calls | output |
| -------------- | ----------------------------------------------------------- | ---------------- | ------ |
| `baseline`     | (none — stage 2 skipped)                                    | 0                | none   |
| `macro_only`   | 20 macros                                                   | 1                | 0+ macros |
| `micro_only`   | 52 non-L0 micros                                            | 1                | 0+ micros |
| `hierarchical` | step1: 20 macros; step2: UNION of `expandable_micro_ids` of picked macros, OR all 52 non-L0 micros if step1 picked nothing | 1–2 | 0+ macros + 0+ micros |
| `flat_all`     | 72 skills (20 macros + 52 non-L0 micros)                    | 1                | 0+ skills |

Every routing step is allowed to answer `none`. In `hierarchical`, picking
`none` (or `[]`) in step 1 does NOT skip step 2 — instead step 2's candidate
pool widens to the full 52 non-L0 micros, so the LLM can still pick
diagnostic micros when no scene-prototype macro fits. To pick no skill at
all, the LLM must answer `none` at BOTH steps.

## Injection mode (`--inject-mode`)

Controls how ALL skill content is rendered — stage 1 micro-01, stage 3 routed
skills, and stage 4 review micros — uniformly per run. **Both modes are
value-curated, never a raw dump:** routing-time signals (`use_when` /
`trigger_checklist` / `route_signal`) and maintainer metadata (`notes` /
`validation_seed` / `hard_boundary`) are excluded from both, because over-long
skill context dilutes the model's judgement.

| mode    | fields injected (per skill)                                                                 |
| ------- | ------------------------------------------------------------------------------------------- |
| `light` | decision_variable + direct_route_rule (macro) + workflow + special_case.worked_example + **common_failure_modes + shortcut_to_avoid** + boundary_exit_rule |
| `full`  | `light` **+ minimal_pair + do_not_use_when + generalization_note**                          |

`light` is the highest-ROI solve-time core (procedure + worked example +
anti-error nudges + exit conditions). `full` adds value-curated discrimination
(near-miss pairs, do-not-use) and transfer (generalization). `light` vs `full`
is therefore a clean ablation of whether the extra content raises accuracy or
merely dilutes it — more is not assumed to be better. `boundary_exit_rule` is in
both because the stage-3 reroute self-check relies on it.

## Review mode (`--review-mode`)

| value | stage 3 solver output                                       | stage 4                                                                                                                                                           | LLM calls per item |
| ----- | ----------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ |
| `off` | letter only                                                 | skipped; final letter == draft                                                                                                                                    | —                  |
| `on`  | structured `REASONING: …\nANSWER: <letter>` (forced format) | reviewer sees the solver's picked skills + reasoning + draft letter, audits via micro-02/03/04, outputs its own `REASONING + ANSWER`. Final letter = reviewer's. | +1                 |

When `on`, the reviewer audits the solver's chain (not the question from
scratch), so it can actually check evidence chain (02), competing
interpretations (03), and bias (04). The result row records `draft_pred`,
`pred`, `draft_correct`, `correct`, `review_changed`, plus `draft_reasoning`
and `review_reasoning` so the audit trail is inspectable. `draft_reasoning`
and `review_reasoning` are empty when `--review-mode off`.

## Setup

```
pip install openai
export OPENAI_API_KEY=sk-...
export SKILL_V5_BASE_URL=https://api.openai.com/v1     # or your gateway
export SKILL_V5_MODEL=gpt-4o-mini                      # or claude-* via gateway
```

## Run

Smoke (50 items):
```
python eval/eval_tombench.py --route-mode baseline                            --lang en --limit 50
python eval/eval_tombench.py --route-mode macro_only   --inject-mode light --review-mode on  --lang en --limit 50
python eval/eval_tombench.py --route-mode hierarchical --inject-mode full  --review-mode on  --lang en --limit 50
```

Full run:
```
python eval/eval_tombench.py --route-mode hierarchical --inject-mode light --review-mode on --lang en --workers 8
```

Resume:
```
python eval/eval_tombench.py --route-mode flat_all --inject-mode full --review-mode on --lang en \
    --workers 8 --run-id flat_all_full_review-on_en_gpt-4o-mini_1735000000 --resume
```

Re-summarize:
```
python eval/eval_tombench.py --summarize-only --run-id <run_id>
```

## Datasets (beyond ToMBench)

By default the runner loads `data/ToMBench_<lang>.jsonl`. To evaluate **any other
MCQ dataset**, point `--data` at its jsonl file (absolute or relative path) — no
code change needed:

```
python eval/eval_tombench.py --route-mode hierarchical --inject-mode light \
    --data D:/datasets/my_tom_set.jsonl --dataset-name my_tom --workers 8
```

Each line is one record. Records are normalized onto the internal schema, so a
new dataset rarely needs reshaping:

| internal field | accepted source keys | notes |
| --- | --- | --- |
| story    | `story`, `context`, `passage`, `scenario`, `background`, `text` | optional; omitted cleanly if absent |
| question | `question`, `query`, `prompt`, `ques`, `q` | |
| options  | `options`, `choices`, `candidates`, `answers` | **dict** `{"A":...}` or **list** `["..."]` (list → A,B,C,…); **any number of options** (A–Z) |
| gold     | `gold`, `answer`, `answers`, `label`, `labels`, `gold_answer`, `target`, `correct` | a **letter** (`"B"`), **numeric index** (see `--gold-index-base`), **option text**, OR for **multi-answer** a list (`["A","C"]`) / delimited (`"A,C"` / `"A、C"`) / concatenated (`"AC"`) value |
| type     | `题型`, `答案类型`, `answer_type`, `question_type`, `multi`, `is_multiple`, … | optional; single vs multi (bilingual values: `单选题`/`多选题`, `single`/`multiple`, `true`/`false`, a count) |
| task     | `task`, `category`, `subset` | per-task breakdown; defaults to `default` (note: `type` is NOT a task alias) |
| ability  | `ability`, `skill`, `subtask`, `dimension` | optional |
| lang     | `lang`, `language` | falls back to `--lang` |

- **Multi-select & >4 options:** answers are scored as a **set of option keys**
  (exact match), so both work out of the box. `--answer-mode {auto,single,multi}`
  (default `auto`) sets the framing: `auto` = per-item type field → else gold
  cardinality → else let the model decide; `single`/`multi` force it dataset-wide.
  Per-item `jaccard` and summary `mean_jaccard` / `acc_by_answer_kind` quantify
  partial overlap on multi-answer items.
- `--dataset-name NAME` labels the run dir / `config.json` (default: file stem).
  The run id and `config.json` record `dataset` + `data_path` so multiple
  datasets never collide.
- `--gold-index-base {0,1}` — when `gold` is a numeric index, treat it as 0- or
  1-based (default `0`). Ignored when gold is a letter or option text.
- `--lang` is the prompt language for records without a `lang` field (and selects
  the default ToMBench file when `--data` is omitted).
- On load, any item whose `gold` maps to no option key is reported as a warning
  (check the schema or `--gold-index-base`).

## summary.json fields

- `overall_acc`           — accuracy of `pred` (final, post-review if on).
- `draft_acc`             — accuracy of `draft_pred` (pre-review). Lets one
                            run answer "did review help".
- `review_changed`        — number of items where the reviewer changed the
                            letter.
- `review_flips_correct`  — draft wrong → final right (true wins).
- `review_flips_wrong`    — draft right → final wrong (review regressions).
- `n_routed_to_none`      — items where the router picked nothing.
- `errors`                — items that threw.
- `by_task`, `by_ability` — accuracy split by task / ability tag.
- `by_first_pick`         — accuracy when the listed skill was the first pick.
- `by_n_picked`           — accuracy by number of skills picked (0/1/2/3+).
- `pick_frequency`        — how often each skill was selected.
- `n_rerouted`            — items where ≥1 skill self-correction fired.
- `reroute_changed_pick`  — items where reroute changed the skill set.
- `acc_by_reroute_count`  — accuracy split by how many reroutes an item took.
- `mean_jaccard`          — mean per-item key-set overlap of `pred` vs `gold`
                            (1.0 for all-correct; <1 reveals partial multi hits).
- `acc_by_answer_kind`    — exact-match accuracy split by `single` vs `multi`
                            (only present when the dataset has multi-answer items).

## Diagnostic comparisons

- `baseline` vs `<route>` — total lift from skill content.
- `macro_only` vs `micro_only` — which granularity informs more.
- `hierarchical` vs `flat_all` — does macro-then-micro decomposition beat
  free choice from 76.
- `light` vs `full` injection — does the extra discrimination/transfer content
  help or merely dilute vs the high-ROI core (more is not assumed better).
- `--reroute-budget 0` vs `1+` — does skill self-correction help; read
  `acc_by_reroute_count` and `reroute_changed_pick` for where it fires.
- `draft_acc` vs `overall_acc` in any `--review-mode on` run — net review
  contribution. `review_flips_correct - review_flips_wrong` tells you if
  review is net-positive.
- `summary.by_n_picked` — accuracy by picks count; reveals whether extra
  skills are noise.
- `summary.pick_frequency` — rarely-picked skills are wasted load.

## Notes

- `SKILL.md` and `unit_pack.json` are read once and cached per process.
- Item failures get an `error` field; the runner does not abort.
- `--workers` controls in-flight LLM calls. Tune to your rate limit.
- LLM retries are configurable: `--max-attempts` sets the upper bound
  (default 3), `--retry-backoff-cap` caps exponential backoff between
  retries in seconds (default 8; use 0 to retry immediately).
- Per-stage token budgets are independent:
  - `--router-max-tokens` (default 128) — each router call
  - `--solver-max-tokens` (default 2048) — solver draft. With
    `--review-mode on` the solver also emits a REASONING block, so the
    default leaves headroom; for letter-only solving with `--review-mode off`
    you can drop to ~256.
  - `--reviewer-max-tokens` (default 2048) — L0 reviewer (also emits
    REASONING + ANSWER).
- `--timeout` (default 120s) sets the per-request HTTP timeout.
- `--review-mode on` doubles per-item LLM calls (router + solver + reviewer
  vs router + solver). Plan budget accordingly.
- `--reroute-budget N` (default 1) adds up to N extra (router + solver) call
  pairs only on items that hit a misfit; most items don't reroute. Set `0` to
  disable. Inactive for `baseline`.
- All requests run non-thinking via `extra_body={"enable_thinking": false}`.
- All prompts are authored in both Chinese and English (identical content,
  language switched on each item's `lang`).
