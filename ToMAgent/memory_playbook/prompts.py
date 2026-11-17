SELECTOR_PROMPT = """You are a strategy selector. Given a question and a curated playbook of strategies, pick the SMALLEST subset of bullets that are most likely to help answer the question correctly. Also predict which subtask the question belongs to.

**Instructions:**
- Read the question and the candidate playbook carefully.
- The playbook is grouped into `## <subtask>` sections; each line under a section is `[bullet_id](helpful/total) summary`, where the section name is the subtask that bullet helped with. Prefer bullets with a high helpful/total ratio under the section that best matches the question.
- Return at most {max_bullets} bullet ids. Fewer is better when sufficient.
- If the playbook is empty or no bullet looks relevant, return an empty list.
- Pick the subtask label from the provided list that best matches the question. If none fits, output "Others".

**Known subtasks (may be empty if training has not seen any yet):**
{known_subtasks}

**Target subtask for this question:**
{target_subtask}

**Playbook:**
{playbook}

**Question:**
{question}

**Context:**
{context}

**Output ONLY this JSON object (no markdown, no code blocks):**
{{
  "predicted_subtask": "<one label from the known subtasks list, or 'Others'>",
  "rationale": "<one short sentence explaining the picks>",
  "selected_bullet_ids": ["sai-00134", "sai-00128"]
}}
"""


# Generic reasoning guidance handed to the generator when the selector returns
# no bullets and the predicted subtask bucket is empty (tier-3 fallback). This
# default is Theory-of-Mind-flavored; override via SelectorConfig.fallback_text.
DEFAULT_FALLBACK_TEXT = """Before answering:
1. Identify whose mental state the question asks about.
2. Separate reality from each character's knowledge.
3. Track desire, intention, belief, emotion separately.
4. Eliminate options based on information unavailable to the target character.
"""
