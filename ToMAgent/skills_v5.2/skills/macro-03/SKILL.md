---
name: macro-03
level: macro
layer: macro
family: "appearance-reality"
description: "Directly route here when a scene asks what a character can know, identify, or correctly pretend, given that their knowledge is bounded by their perceptual access plus their background knowledge rather than by the omniscient real state."
---

# Appearance-Reality and Knowledge Boundary

## Use When
- Use when the answer depends on what a character can know, identify, or correctly pretend given their perceptual access plus their background knowledge.
- Use when a character was absent, left the room, looked away, or arrived late, and the question turns on whether they know about an object, change, or new item that appeared outside their access.
- Use when a character imitates, pretends to be, or names something, and the correct option is bounded by what that character actually knows (e.g., a robot with no plant knowledge cannot be imitating a flower).
- Use when an object, label, container, disguise, or situation looks like one thing but is actually another, and the question asks what an uninformed character thinks it is.
- Use when world knowledge, expertise, prior experience, or restricted information creates a boundary between what is really true and what a particular character can know.

## Do Not Use When
- Do not use when the question asks where a character will SEARCH or ACT after an unseen move; that is a belief-guided action problem - predict the location from the character's outdated belief, not from the knowledge boundary here.
- Do not use when the question is purely what is geometrically VISIBLE from a viewpoint (what can X see from position Y, who is in whose line of sight); that is a spatial line-of-sight problem - reason about sightlines and occluders, not about identity or knowledge.
- Do not use when the main question is what one character thinks ANOTHER character knows or believes (a nested, second-order belief); solve it as a second-order belief problem - model the second character's belief first, then the first character's belief about it - unless an appearance-reality conflict remains the main driver.
- Do not use when the main evidence is a wink, glance, smile, gesture, or other nonverbal cue conveying intention; that is a nonverbal-cue reading problem - infer the intended meaning from the gesture in context, not from access-versus-reality.
- Do not use when the central task is to infer a hidden or atypical emotion rather than to separate reality from a character's knowledge boundary; that is a hidden-emotion problem - reason about the gap between displayed and felt emotion.
- Do not use when a single narrower diagnostic question can be answered without the full appearance-reality / knowledge-boundary scene prototype.

## Decision Variable
how appearance, reality, and a character's knowledge boundary jointly determine the answer

## Direct Route Rule
Route immediately when the answer depends on a character's knowledge boundary - what their perceptual access plus background knowledge lets them know, identify, or pretend - rather than on the omniscient real state.

## Expand With Micro Units
- Sensory Access: whether the character can directly perceive the information through a sensory channel (micro-05)
- Knowledge Boundary: whether the character has the background required to interpret the information (micro-10)
- Appearance-Reality Distinction: surface appearance versus true state (micro-14)
- Evidence-Availability Updating: the direction of belief change caused by newly available evidence (micro-15)
- Source Credibility: source reliability (micro-18)

## Trigger Checklist
- A character's perceptual access is explicitly limited: they were absent, left the room, looked away, arrived late, or only saw a surface/label while a change happened out of view.
- Or the scene states a background-knowledge limit: the character has never seen X, knows nothing about category Y, or lacks the expertise the answer would require.
- There is a real state (real identity, real contents, real category, what really happened) that the character's access plus knowledge may or may not support.
- The question asks what the character thinks, says, identifies, selects, knows, or is imitating/pretending - not where they will search or what is purely visible from a viewpoint.
- Solving requires keeping separate the real state, the narrator's omniscient view, and what this character's access-plus-background can support.

## Workflow
- Step 1 - Real state: state what is actually true in the scene (the real identity, the real contents, the real category, or what really happened), independent of any character.
- Step 2 - Perceptual access: for the target character, list exactly what they perceived and when. Did they see/hear the substitution, the new object, the reveal? If they were absent, looked away, or arrived after an event, mark that event as OUTSIDE their access.
- Step 3 - Background knowledge: list what the character knows from world knowledge, prior experience, expertise, or category familiarity. If the scene says they have never seen X or know nothing about category Y, mark X/Y as OUTSIDE their knowledge.
- Step 4 - Knowledge boundary = access + background: the character can only know, identify, correctly pretend, or correctly select something that BOTH their perceptual access AND their background knowledge support. Anything requiring access they lacked, or knowledge they lack, is unknowable to them.
- Step 5 - Answer from the boundary, not from reality: if the question asks what the character thinks, says, identifies, selects, knows, or is imitating, answer with the option that fits inside their knowledge boundary - even if the reader knows the real state is different.
- Step 6 - Pretend/identity rule: when the character pretends to be, imitates, or names something, the answer must be something they actually know. Discard any option naming a category the scene says they lack (e.g., a robot with no plant knowledge cannot be imitating a flower).
- Step 7 - Absent-then-changed rule: if a character left or was absent while a new object appeared or an object moved, they do not know about that change; for 'does X know where it is?' the answer is 'does not know', and for 'which new thing is X excited about?' it is the item that appeared while they were away.
- Step 8 - Objective-fact branch: only if the question explicitly asks what is REALLY true, answer with the Step 1 real state instead of the character's belief.
- Step 9 - Boundary check: confirm the answer turns on knowledge/identity bounded by access+background. If it instead turns on where the character will SEARCH or ACT after an unseen move, switch to a belief-guided action approach and predict from their outdated belief; if it turns purely on line-of-sight geometry from a viewpoint, switch to a spatial visibility approach and reason about sightlines and occluders.

## Special Case
**Pretend and identity are bounded by the agent's knowledge**: When a character imitates, pretends to be, or names something, the correct answer must be something that character actually knows. Even if the surface action resembles category X, discard X if the scene says the character lacks any knowledge of X; choose the option drawn from a category the character does know.

Scene: A robot named Tinklo lives on a space station with no plant life, so it knows nothing about plants. The station is full of machines and robots. Tinklo sways from side to side and bends to the ground, motions that look like flowers swaying and a person smelling a flower.
Question: What is Tinklo most likely imitating?
Answer logic: The action LOOKS like plant behavior, but imitation is bounded by what Tinklo knows. Sunflowers and rose-smelling require plant knowledge Tinklo lacks, so they are impossible. Within Tinklo's known world (machines and robots), 'a robot bending over to pick up objects' is the only option it could be imitating.

## Boundary Exit Rule
- Exit if the asked answer is a search or action LOCATION based on a first-order false belief after an unseen move (where will X look / go); solve it as a belief-guided action problem - predict the location from the character's outdated belief.
- Exit if the question is purely line-of-sight visibility from a position (what can X see from here, is Y in X's view) with no identity or knowledge inference; solve it as a spatial line-of-sight problem - trace sightlines and occluders.
- Exit if the main variable is one character's model of another character's belief, knowledge, or ignorance; solve it as a nested, second-order belief problem - model the second character's belief first, then the first character's belief about it.
- Exit if the main inference comes from a nonverbal social cue (wink, glance, smile, gesture) rather than from access-versus-reality; solve it as a nonverbal-cue reading problem - infer the intended meaning from the gesture in context.
- Exit if the key mismatch is between outward emotional display and true feeling; solve it as a hidden-emotion problem - reason about the gap between displayed and felt emotion.
- For diagnosis or explanation, separately reason about basic appearance-reality (what it really is versus what it looks like) when the case needs that split spelled out.
- For diagnosis, reason explicitly about the perceptual-access boundary - which character could directly see, hear, or touch the information, and when - when access is the crux or is disputed.
- For diagnosis, reason explicitly about world knowledge, object identity, category knowledge, or expertise when those determine what a character can infer, imitate, or name.
- For diagnosis, track shared versus private knowledge - what every character knows versus what only some know - when that distinction is needed to repair the answer.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
A character can only know, identify, or correctly pretend what their perceptual access plus background knowledge supports; the answer depends on that boundary, not on the omniscient real state.
