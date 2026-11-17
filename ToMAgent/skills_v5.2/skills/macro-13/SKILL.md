---
name: macro-13
level: macro
layer: macro
family: "spatial-social-perspective-judgment"
description: "Direct-route macro for judging what a target character can physically see from their viewpoint, or how spatial relations (left/right, front/back, occlusion, orientation) appear from that character's facing direction."
---

# Spatial Social Perspective Judgment

## Use When
- Use when the answer is decided purely by what a specific character can physically see from their position and facing direction (line of sight), or by which object falls on their left, right, front, or behind.
- Use when an occluder (a wall, a screen, the back of an object, a container lid, another person, a corner, darkness, or distance) stands between the target and something, and the question asks whether the target can see it.
- Use when left/right or front/back must be reckoned relative to a named person's body orientation rather than the reader's camera angle, including cases where the target faces the reader or stands on the opposite side of an object.
- Use when the question is about the orientation a target perceives of a picture, sign, cube, die, or screen given which face or side points toward them.

## Do Not Use When
- Do not use when the question asks what the character KNOWS or can identify as a result of seeing something; deciding 'they saw it, therefore they now know X' is a knowledge-access scene, where you track who had perceptual access to information and conclude what each person is informed about. This macro stops at 'can they see it', it does not draw the knowledge conclusion.
- Do not use when the character saw an old state, then something changed while they were away, and the question asks where they will look or what they expect; that is an outdated-belief scene, solved by tracking the belief the character formed before the change and predicting they will act on that stale belief.
- Do not use when the question is which option a character will choose among competing goals, duties, or next actions; that requires weighing motives and commitments, not computing a sightline.
- Do not use when the question is whether a visible remark or act was rude, embarrassing, or a social misstep; that is a norm-and-offense judgment about appropriateness, not about geometry.
- Do not use when the answer requires inferring a quantity, probability, or base rate from partial observations; that is an estimation task, not a viewpoint computation.

## Decision Variable
what a target character can physically see from their viewpoint, or how a spatial relation (left/right, front/back, occlusion, orientation) appears relative to that character's facing direction

## Direct Route Rule
Route immediately when the question turns on a sightline, an occluder between a viewer and a target, or a left/right/front/back relation that must be read from a named character's facing direction rather than the reader's.

## Expand With Micro Units
- Sensory Access: whether the character can directly perceive the information through a sensory channel (micro-05)
- Spatial Perspective Transformation: the spatial relation visible from the target perspective (micro-06)
- Attention and Salience: whether the cue entered the character's attentional focus (micro-07)
- False Belief: whether the character's belief mismatches the actual state (micro-12)

## Trigger Checklist
- A specific viewer or perspective holder is named, and their position and facing direction are given or can be fixed from the scene.
- The question asks what that viewer can see, whether something is in their line of sight, or which side/object is on their left, right, front, or behind.
- The scene contains spatial structure that decides the answer: positions, a facing direction, an occluding object, distance, or an orientation of a face/side.
- The correct answer flips if computed from the reader's god's-eye view instead of the target character's viewpoint.
- Answering needs only the perceptual-access or spatial relation, with no further step about what the character then knows, believes, intends, or whether an act was appropriate.

## Workflow
- Identify the target character whose viewpoint controls the answer; if several people are present, pin down which single viewpoint the question asks about.
- Fix that target's position and body orientation: where they stand and which way they face. Their left, right, front, and behind are defined by THIS facing, not by the reader's.
- Locate every relevant object and every potential occluder (walls, screens, the closed or far side of a container, the back of an object, other people, corners, distance, darkness) with their positions.
- For a visibility question, trace the straight line from the target's eyes to the object: if any occluder sits on that line, or the object's relevant face points away from the target, the target cannot see it; otherwise it is in view.
- For a left/right or front/back question, rotate the layout into the target's frame, then read off the relation; if the target faces the reader or stands on the far side, the target's left maps to the reader's right and vice versa.
- For a picture, sign, cube, die, or screen, decide which face or side is turned toward the target and answer from that face, not from the face the reader sees.
- Answer ONLY the perceptual-access or spatial-relation question. Do not continue to 'therefore the character knows / believes / will do X', and do not switch to the reader's god's-eye view; if the prompt genuinely adds a knowledge, belief, or norm step, that step belongs to a different scene.

## Special Case
**Facing-the-reader left/right reversal**: When the target faces the reader, or stands on the opposite side of an object from the reader, the target's left is the reader's right and the target's right is the reader's left. Re-read every left/right (and any front/back that depends on facing) from the target's own body, never from the page.

Scene: Maya stands across a table directly facing Noah. From Noah's own point of view, a red cup sits on his left and a blue cup sits on his right. Maya is on the opposite side, facing him.
Question: Which cup is on Maya's left?
Answer logic: Maya faces the opposite way from Noah, so her left/right are mirrored relative to his. Noah's right side of the table is Maya's left side. The blue cup, on Noah's right, is therefore on Maya's left. The answer is the blue cup. Note we never ask what Maya knows or infers, only which cup falls on her left given her facing.

## Boundary Exit Rule
- If the question moves past 'can they see it' to 'and so what do they now know or can identify', solve it as a knowledge-access problem: list who had direct perceptual access to the information and when, and conclude only that those with access are informed and those without are not. This macro supplies the visibility fact; it does not draw that knowledge conclusion.
- If the character saw an earlier state, then a change happened out of their sight, and the question asks where they will search or what they expect, solve it as an outdated-belief problem: the character still holds the belief from before the change and will act on that stale belief, not on the current reality.
- If the scene only uses the spatial layout to set up which goal or next action a character should pick, solve it by weighing the character's competing commitments and motives, not by computing a sightline.
- If the central question is whether a visible remark or act was rude, awkward, or a faux pas, solve it as a social-appropriateness judgment about norms and likely offense, not as geometry.
- If the spatial detail is only evidence for inferring a count, probability, or base rate, solve it as an estimation problem from partial observations, not as a viewpoint computation.
- When the route to this visibility macro is correct but the answer needs a finer diagnosis of who has perceptual access, where attention is directed, how a spatial cue is being used, or how to transform between viewpoints, draw on the matching micro expansion.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
A scene asks for a named character's physical sightline or for a left/right/front/back/visible/hidden/facing relation that must be read from that character's own position and facing direction rather than the reader's.
