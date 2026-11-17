---
name: micro-12
level: micro
layer: L2
family: "belief-models"
description: "Use this unit to diagnose whether a character holds a belief that conflicts with reality."
---

# False Belief

## Use When
- Use when the question asks what a specific character believes is true after the world has changed.
- Use when the answer depends on whether one person's mental model is outdated, mistaken, or based on incomplete evidence.
- Use when you must judge a reality-belief mismatch for a particular agent, not merely state the real facts.

## Do Not Use When
- Do not use when the character's belief is consistent with reality, even if the character lacks extra background knowledge.
- Do not use when the main issue is who saw what, who noticed what, or what information was available.
- Do not use when the question is about appearance versus reality without asking what any character believes.
- Do not use when the target is one mind modeling another mind; that is second-order belief.

## Decision Variable
whether the character's belief mismatches the actual state

## Trigger Checklist
- Is there a named character whose belief is being queried?
- Has reality changed, been hidden, or been misrepresented relative to that character's knowledge?
- Would the character answer incorrectly if asked about the current state?
- Is the task about that character's belief, not about what is actually true?
- Is the mismatch direct, not nested inside another person's belief about it?

## Workflow
- Identify the target character and the proposition they believe.
- Compare the belief to the actual current state of the world.
- Check whether the character had access to the update or only an older view.
- If belief and reality differ, label it false belief; otherwise route elsewhere.
- If another person's belief about this belief is being asked, escalate to second-order belief.

## Special Case
**Outdated belief after an unseen change**: If a character saw the world one way, then the world changed without them noticing, this counts as false belief when the question targets that character's current belief AND that belief conflicts with the changed reality.

Scene: Xiaogang and Xiaoming see cabbage placed in the handbag. Xiaoming then leaves the room, and while he is away Xiaogang moves the cabbage to the backpack.
Question: After Xiaoming returns, where does Xiaoming look for the cabbage?
Answer logic: Xiaoming's belief is fixed at the last state he perceived (handbag), while reality has changed (backpack). Because the question targets Xiaoming's own belief and it conflicts with the actual location, this is a false belief: he looks in the handbag. Contrast Xiaogang, who made the move and therefore holds a true first-order belief.

## Boundary Exit Rule
- Exit to knowledge boundary if the issue is missing background competence rather than a mistaken fact about the world.
- Exit to appearance-reality if the question asks what something really is versus what it looks like, with no character belief target.
- Exit to first-order belief if the character's belief is asked but it may be true or false and no reality mismatch is required.
- Exit to second-order belief if the question is about what one person thinks another person believes.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use when a scene asks for one person's incorrect belief about a changed or hidden state of affairs.
