# macro-03 Examples and Boundaries

## Decision Variable
how appearance, reality, and a character's knowledge boundary jointly determine the answer

## Route Signal
A character can only know, identify, or correctly pretend what their perceptual access plus background knowledge supports; the answer depends on that boundary, not on the omniscient real state.

## Hard Boundary
- This is not false-belief action prediction; if the question asks where a character will search or act after an unseen move, treat it as a belief-guided action problem and predict from their outdated belief.
- This is not pure spatial visibility; if the question is only what is seen from a viewpoint, treat it as a line-of-sight problem about sightlines and occluders.
- The macro is not second-order belief unless the question explicitly asks what one mind thinks about another mind's knowledge.
- The macro is not hidden emotion unless the relevant hidden state is a feeling rather than a real identity, contents, or event.
- The macro is not social-cue interpretation unless a gesture or expression is the primary evidence.

## Shortcut To Avoid
- Do not credit a character with knowledge of a change, object, or substitution that happened while they were absent or looking away.
- Do not let a pretend/imitation/identity answer exceed what the character knows; rule out any option naming a category the scene says they lack.
- Do not answer with the narrator's known reality when the question asks what an uninformed character thinks, knows, or is imitating.
- Do not anchor on the option that best matches the surface action when the agent has no knowledge of that category; pick from categories the agent actually knows.
- Do not over-route to false belief whenever a character is wrong; check whether the core is identity/knowledge boundary rather than search or action.

## Common Failure Modes
- Access leak: crediting a character with knowledge of an event they had no perceptual access to (they were absent, left, or arrived late), e.g., answering that the returning child knows where the object was moved.
- Pretend overreach: letting an imitation or identity answer name a category the agent cannot know, e.g., saying the plant-ignorant robot imitates a sunflower because the motion looks floral.
- Surface-match bias: choosing the option that most resembles the described action/appearance instead of the option bounded by the agent's actual knowledge.
- Reality leak: using the hidden real state for a character who never learned it.
- Boundary drift: treating the scene as a search/action prediction, a pure line-of-sight visibility question, an emotion inference, or a nonverbal-intention reading when the central variable is actually knowledge bounded by access plus background.

## Minimal Pair
- Case: A robot with no plant knowledge makes a motion that looks like a flower swaying, and is asked what it is imitating; options include a sunflower and a robot bending over. | Why: In-scope: imitation is bounded by the agent's knowledge, so the floral-looking option is impossible and the answer is the robot-category option (an imitation-bounded-by-knowledge case).
- Case: An object is moved from a handbag to a backpack while Xiaoming is out of the room, and the question asks where Xiaoming will look for it. | Why: Near miss: the same access gap exists, but the question asks where he will SEARCH, so the core is belief-guided action - predict the location from his outdated belief - and it is solved as a false-belief action problem, not with the knowledge-boundary procedure here (a first-order belief-guided-action case).

## Boundary Stress Test
- If a character left before a new object appeared, they do not know about it; 'which new toy is X excited about?' is the item that appeared while X was away.
- If asked 'does X know where it is now?' after an unseen move, the answer is 'does not know', because X lacks perceptual access to the move.
- If an agent imitates or pretends, eliminate every option naming a category the scene says the agent has never encountered, then choose among the rest.
- If a label or container is misleading and the character only saw the surface, answer with the ordinary/labelled meaning; if they witnessed the substitution, answer with the real contents.
- If the scene mixes a knowledge gap with a later search action, split by the asked question: an identity/knowledge question is solved here with the knowledge boundary; a search-location question is solved as belief-guided action from the outdated belief; a pure what-is-visible question is solved as a line-of-sight problem.

## Generalization Note
This macro generalizes the rule 'a character can only know, identify, or correctly pretend what their perceptual access plus background knowledge supports' across deceptive containers, disguises, labels, pretend/imitation, absent-then-changed scenes, expertise gaps, and private reveals. The reusable prior is to compute each character's knowledge boundary from access-plus-background, then answer from that boundary rather than from the omniscient real state.
