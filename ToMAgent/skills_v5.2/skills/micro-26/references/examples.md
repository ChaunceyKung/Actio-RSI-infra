# micro-26 Examples and Boundaries

## Decision Variable
event impact on the character's goals or interests

## Route Signal
Use this micro unit when an event's direct impact on a character's goal, interest, safety, or loss/gain is enough to infer the character's basic emotion.

## Hard Boundary
- This unit does not resolve action selection or priority among goals.
- This unit does not explain why an emotion is atypical or surprising.
- This unit does not infer hidden feelings behind a controlled or misleading expression.
- This unit does not handle guilt, shame, blame, or moral responsibility as the main determinant.
- This unit does not require benchmark-specific object locations or memorized story templates.

## Shortcut To Avoid
- Do not assign the emotion that an outside observer would feel; use the target character's own goal impact and knowledge.
- Do not jump from a smile, silence, or polite phrase to true emotion when display management is part of the scene.

## Common Failure Modes
- Ignoring that the character does not know the good or bad outcome yet.
- Confusing a goal-conflict action choice with an emotion appraisal.
- Reflexively answering with the default emotion when the story actually states a special wish, value, or expectation that reverses it (which should route to the atypical-emotion capability).
- Missing relief when a feared bad outcome is avoided, and answering plain happiness instead.
- Importing moral blame language (guilt, shame) when the scene only requires basic loss, threat, or success appraisal.

## Minimal Pair
- Case: Xiao Ming receives a bicycle on his birthday and the story states no other wish. | Why: A desirable gift advances an ordinary goal with no contrary expectation, so default appraisal applies and the emotion is happiness. This is in scope for basic appraisal.
- Case: Xiao Ming hoped for a computer or a new game, but on his birthday he receives a bicycle. | Why: The same gift now lands against a stated wish, so the genuine feeling is disappointment rather than the default happiness. Because a character-specific expectation reverses the ordinary reaction, this routes to the atypical-emotion capability (micro-27).

## Boundary Stress Test
- If a character receives a gift they wanted, infer happiness from goal satisfaction unless the story says they dislike that gift or value something unusual.
- If a character loses a valued object, infer sadness or frustration from loss unless blame, guilt, or responsibility is the explicit focus.
- If a character avoids a danger they feared, infer relief rather than simple happiness when threat removal is the key appraisal.
- If two goals conflict and the question asks what the character will do, do not answer with emotion; exit to goal-conflict routing.

## Generalization Note
The unit generalizes across social and nonsocial scenes by asking one narrow question: how does the known event affect this character's goals or interests right now?
