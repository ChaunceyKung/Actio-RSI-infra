# macro-13 Examples and Boundaries

## Decision Variable
what a target character can physically see from their viewpoint, or how a spatial relation (left/right, front/back, occlusion, orientation) appears relative to that character's facing direction

## Route Signal
A scene asks for a named character's physical sightline or for a left/right/front/back/visible/hidden/facing relation that must be read from that character's own position and facing direction rather than the reader's.

## Hard Boundary
- Seeing is not knowing: this macro decides only whether the target can see something. Concluding that they therefore know, can identify, or are informed about it is a separate knowledge-access step.
- Current visibility is not outdated belief: if the character saw an old state and missed a later change, the answer turns on the stale belief they still hold, not on what is now in their line of sight.
- A sightline is not a social judgment: whether a visible act is rude, awkward, or a faux pas is a norms question, not a geometry question.
- Spatial layout alone is not estimation: if the answer needs a quantity or probability inferred from partial cues, that is estimation, not perspective-taking.

## Shortcut To Avoid
- Do not answer from the reader's god's-eye camera angle when a specific character's viewpoint is named; recompute from that character's position and facing.
- Do not assume everyone in the room sees the same thing; check each viewer's facing direction and the occluders between them and the target object.
- Do not slide from 'can see it' to 'therefore knows / believes it'; stop at the visibility fact, since the knowledge or belief step belongs to a different scene.
- Do not recall a memorized dice, cube, or mirror answer; recompute which face or side is turned toward this particular target.
- Do not mirror left/right the wrong way: a target facing you has their left on your right, so check facing before assigning sides.

## Common Failure Modes
- Jumping from 'the character can see it' straight to 'therefore the character knows / believes it' and answering the knowledge question instead of the visibility question.
- Using the reader's god's-eye view of the layout instead of reconstructing the scene from the target character's eyes.
- Mishandling left/right (and facing-dependent front/back) relative to the person's own facing versus the reader's, especially when the target faces the reader or stands across an object.
- Forgetting that an occluder, a closed or far container side, a turned-away face, distance, or darkness blocks the line of sight, and reporting an object as visible when it is not.
- Treating any person who is merely present in the scene as able to see every detail, without checking whether their facing direction or an obstruction excludes the target object.

## Minimal Pair
- Case: A child stands facing a shelf and is asked which toy is on her left; a screen blocks the rightmost toy from her line of sight, and the question is simply whether she can see that toy. | Why: The answer is fixed entirely by the child's facing direction and the occluding screen, a pure sightline-and-side computation with no further step about what she concludes.
- Case: A child leaves the room; while she is gone a toy is moved from a box to a cabinet, and the question is whether she sees it in the cabinet or knows where it now is. | Why: This is not a geometry question but a knowledge-access scene: because she had no perceptual access during the move, she sees nothing in the cabinet and does not know the new location. Solve it by tracking access to information, not by tracing a sightline.

## Boundary Stress Test
- If the target could have seen an object but did not attend to it, use this macro only to settle that it was within their line of sight; whether they noticed or now know it is a separate attention-and-knowledge step.
- If two characters stand on opposite sides of the same table, compute each one's left and right separately from their own facing, never sharing one frame.
- If a picture, sign, die, or cube is rotated, answer from the face or orientation turned toward the target, not the one the reader sees.
- If the prompt asks what the character should do after taking in the layout, separate the pure spatial reading from the later action-selection reasoning and let this macro own only the spatial reading.

## Generalization Note
This macro generalizes across perspective-taking scenes by applying one stable procedure: pin the target viewer's position and facing, rotate the layout into their frame, remove whatever an occluder or a turned-away face blocks, and report only the visibility or the left/right/front/back relation, never the downstream knowledge, belief, or social judgment.
