---
name: micro-09
level: micro
layer: L1
family: "perception-memory-knowledge"
description: "Diagnose a character's retained, lost, or distorted memory after prior exposure."
---

# Memory, Forgetting, and Misremembering

## Use When
- Use when the question asks what a character remembers, forgets, or misremembers after previously encountering the information.
- Use when the key issue is the character's current memory state, not whether the information was seen, understood, or believed.
- Use when the answer depends on retention, decay, reconstruction, confabulation, or recall error.

## Do Not Use When
- Do not use when the main issue is whether the person noticed the information in the first place; that is attention or salience.
- Do not use when the main issue is whether the person has the background needed to understand the information; that is knowledge boundary.
- Do not use when the main issue is what the person believes is true right now independent of prior exposure; that is belief.
- Do not use when the main issue is only event order or updating from one event to the next; that is temporal order.

## Decision Variable
current memory content and fidelity

## Trigger Checklist
- Did the person encounter the information before?
- Is the question about recall, forgetting, or distortion of that prior information?
- Is the task to tell whether the memory is accurate, partial, absent, or altered?
- Is the answer driven by what remains in memory rather than by perception or background knowledge?

## Workflow
- Confirm there was prior exposure to the relevant information.
- Ask whether the current question targets retention, loss, or distortion of that exposure.
- Check whether the person would recall it accurately, incompletely, or incorrectly.
- If the information was never attended to or never understood, exit to the neighboring skill instead of using memory.

## Special Case
**Sincere false report from a memory failure**: When a character had prior exposure but their current memory is incomplete or distorted, a false statement can be an honest memory error rather than a lie; the test is whether the fact is still accurately held in memory.

Scene: Feng Na is playing with her doll in the garden when sudden rain sends her rushing inside, leaving the doll behind. At lunch her mother asks whether she forgot the doll, and Feng Na says, 'No, I brought her in.'
Question: Why does Feng Na say this?
Answer logic: Feng Na had direct exposure - she was playing with the doll - so this is not an attention or knowledge gap. The frantic dash inside disrupted her memory of leaving it, so she sincerely misremembers having brought it in. The decisive variable is her distorted current memory, which marks this as a memory failure, not a deliberate lie.

## Boundary Exit Rule
- If the question is about whether the character ever noticed the cue, switch to attention and salience.
- If the question is about whether the character has the background to make sense of the cue, switch to knowledge boundary.
- If the question is about what the character currently thinks is true regardless of prior exposure, switch to first-order belief.
- If the question is about how one event changes another mental state over time, switch to temporal order and event updating.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use this micro unit when a question asks what survives, fades, or changes in a character's memory after prior exposure.
