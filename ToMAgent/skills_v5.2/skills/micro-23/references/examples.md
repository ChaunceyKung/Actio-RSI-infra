# micro-23 Examples and Boundaries

## Decision Variable
what the character is most likely to do next

## Route Signal
Use this capability when the answer must be an observable NEXT behavior derived from the character's belief state plus active goal. If the question instead asks WHY a behavior already shown is happening, route to the intention-recognition capability (micro-22).

## Hard Boundary
- This unit is future-facing - it predicts the next action. The intention-recognition capability (micro-22) is backward-facing - it explains a current or past behavior. 'What will she do?' is here; 'why did she do that?' routes away.
- Beware the phrasing trap: 'What does X want to do?' in these tasks usually means 'what is X's next move?' - still this unit. It does NOT mean explain a cue X already produced.
- This unit outputs an action; belief, desire, and goal units output an internal state or objective structure.
- This unit predicts ONE next action from ONE active goal. If the scene's question is which of several goals wins, route to the goal-conflict arbitration capability (micro-25).
- This unit uses the false-belief result; it does not replace false-belief reasoning - it predicts behavior from the belief that reasoning establishes.

## Shortcut To Avoid
- Do not predict from the real state of the world when the character holds a different belief (reality leak).
- Do not answer with a purpose or motive ('to help', 'to warn') when the question asks what the character will physically do next - that purpose answer belongs to the intention-recognition capability (micro-22).
- Do not invent an elaborate multi-step plan when the immediate next action is what is asked.
- Do not collapse a genuine goal conflict into a simple prediction; if two goals compete for the answer, route to the goal-conflict arbitration capability (micro-25).

## Common Failure Modes
- Reality leak: predicting from information the character never observed.
- Motive-action swap: giving the purpose of a cue instead of the next behavior (this is answering as if it were the intention-recognition capability).
- Overplanning: building a complex plan when the immediate next step is enough.
- Goal-conflict confusion: treating a scene whose real question is which goal wins as a plain next-action prediction (it belongs to the goal-conflict arbitration capability).
- Missing the 'what does X want to do?' framing and answering with a trait or feeling instead of the next move.

## Minimal Pair
- Case: Two friends discuss where to play but cannot decide; one stops a passing adult to ask his opinion, hoping a fresh perspective will point them to a good spot. Question: 'What does the friend want to do?' Answer: get the passerby to suggest where to play. | Why: Phrased 'what does X want to do?', but the answer is X's next move inferred from goal (find a destination) plus the situation. In scope for this unit.
- Case: Xiao Hong glances at the swing, then smiles at Xiao Fang, who nods. Question: 'Why does Xiao Hong smile at Xiao Fang?' | Why: This asks WHY a cue already shown is happening - its purpose (to suggest making a new friend together). That routes to the intention-recognition capability - the purpose behind a current behavior (micro-22), not next-action prediction.

## Boundary Stress Test
- The character wants an object but falsely believes it sits in its old place: predict a search at the OLD location (false-belief action).
- Two next actions are available but only one serves the active goal under the character's belief: choose that one.
- The scene gives the character two pulls - keep painting now versus go buy more paint versus study for tonight's exam - and asks what they choose: if the question is which goal wins, route to the goal-conflict arbitration capability (micro-25) rather than predicting a single goal's action.
- The question asks what the character is trying to accomplish by knocking, waving, or glancing: that is a purpose, so use the intention-recognition capability (micro-22), not this unit.

## Generalization Note
This unit generalizes across benchmark false-belief and intention tasks and real-world scenes by applying one rule: belief plus active goal yields the next observable action. The recurring boundary is time direction - predict the next move here; explain an already-shown cue with the intention-recognition capability (micro-22).
