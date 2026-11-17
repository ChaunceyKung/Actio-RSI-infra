# macro-02 Examples and Boundaries

## Decision Variable
how one character understands another character's understanding

## Route Signal
The scene contains embedded belief, such as who thinks what about whom, or whether a fact is mutually known, privately known, or known to be known.

## Hard Boundary
- First-order false belief without nested belief
- Appearance-reality without model-of-mind structure
- Nonverbal social cue interpretation
- Literal pragmatics without epistemic nesting

## Shortcut To Avoid
- Do not jump straight to reality; preserve each character's represented knowledge state.
- Do not collapse second-order belief into the outer character's direct belief.
- Do not treat common knowledge as merely duplicated private knowledge.
- Do not use emotion or cue interpretation shortcuts when the question is about who thinks what.

## Common Failure Modes
- Answering from ground-truth reality (omniscience leak) instead of from the character's model of another mind
- The coincidence trap: routing on the landed answer instead of the question structure. When a character did not see the change, the second-order answer (what A thinks B believes) often numerically coincides with the first-order answer (what B believes), but the two require different reasoning; deciding a question is first-order just because the answer matches the old location is the error. Always route on whether the question embeds one mind inside another.
- Flattening second-order belief into the outer character's own first-order belief, so A's model of B collapses into what A believes
- Ignoring whether A knows that B was or was not informed of the change
- Treating a mutually known fact as if a false belief still survives, or treating one-sided knowledge as if it were common knowledge

## Minimal Pair
- Case: Both characters see an object in its first place; one character leaves, the other moves it while the first is away, and the question asks where the mover thinks the absent character will look for it. | Why: The question is nested: it asks for one character's model of another character's belief. The mover knows the absent character did not see the move, so the mover expects a search at the original place. This is the in-scope second-order case.
- Case: The same change occurs, but the question instead asks where the absent character himself will look for the object after returning. | Why: Near miss, not in scope: this is a single-level question about the absent character's OWN false belief and action, with no character modeling another character's mind. Note the trap: its correct answer (the original place) coincides with the second-order answer above, yet it is solved by the plain first-order false-belief procedure, not by nesting one mind inside another. Route on the nested question form, not on the matching answer.

## Boundary Stress Test
- If B knows the truth but A does not know that B knows the truth, this still belongs here when the question asks what A thinks B believes or will do, because A is still modeling B's mind from A's (incorrect) view of B's access.
- If the question asks only where a character will search based on that character's own mistaken belief, with no second mind being modeled, it is a first-order false-belief problem and should not be solved by nesting.
- If the only twist is a misleading appearance and no character models another character's mind, it is an appearance-versus-reality problem and does not belong here.

## Generalization Note
Treat this as a reusable prototype for nested belief and mutual awareness, not as a one-off trick; any scene with explicit mind-in-mind reasoning or shared knowledge can route directly here.
