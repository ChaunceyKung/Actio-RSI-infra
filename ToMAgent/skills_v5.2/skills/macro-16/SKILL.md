---
name: macro-16
level: macro
layer: macro
family: "dialogue-misunderstanding-repair-and-clarification"
description: "Route here when a live conversational misunderstanding must be clarified on the spot."
---

# Dialogue Misunderstanding Repair and Clarification

## Use When
- Use when two people are in a live conversation and one party has taken an utterance to mean something different from what the speaker intended, so a real mismatch between intended meaning and received meaning is present right now.
- Use when the listener shows confusion, pushes back on a wrong reading, or says something like 'What do you mean?' / 'I thought you said...' and the task is to recover shared meaning.
- Use when the best move is an in-the-moment clarification, restatement, or check for understanding that can fix the mismatch before any damage is done.
- Use when the key task is to spot that a misread has occurred and pick the lightest move that corrects it.

## Do Not Use When
- Do not use when there is no actual misunderstanding and the only task is to decode what an indirect or hinted utterance means; if both parties are still aligned and you merely need to infer the intended meaning of a hint or irony, that is plain indirect-meaning decoding, which needs inference of speaker intent, not repair of a mismatch.
- Do not use when meaning was understood correctly but harm has already landed and the relationship is damaged; if what remains is making amends after offense, that is after-the-fact apology and reconciliation, which needs sincere apology, taking responsibility, and rebuilding trust, not a quick clarification.
- Do not use when the scene is mainly about persuasion, negotiation, or adapting a message to an audience rather than fixing a misread.
- Do not use when the question is about whether a statement is true, deceptive, or concealed rather than simply misunderstood.

## Decision Variable
how to detect and clarify a live misunderstanding in conversation

## Direct Route Rule
Route immediately when one party has taken an utterance differently from what the speaker meant and the mismatch can still be cleared up on the spot by clarifying.

## Expand With Micro Units
- Second-Order or Recursive Belief: which belief is embedded inside which other belief (micro-13)
- Literal Meaning: the sentence's explicit semantic content (micro-34)
- Conversational Implicature: the implicit information derived from context (micro-36)
- Audience Calibration: how well the expression fits the listener's knowledge, age, identity, or stance (micro-40)

## Trigger Checklist
- One party says or does something, and the other party takes it to mean something the first party did not intend (a live mismatch is on the table).
- The scene shows a sign of the misread: the listener looks confused, reacts to a wrong reading, or says 'What do you mean?', 'I thought you said...', or 'No, I meant...'.
- The correct answer turns on the gap between what the speaker intended and what the listener understood, not on the literal surface content alone.
- The mismatch can still be fixed on the spot by clarifying, because no real harm or offense has yet hardened the situation.
- The key uncertainty is conversational meaning, reference, or assumption in the moment, not truth, trust, or aftermath repair.

## Workflow
- Detect the mismatch: state in one line what the speaker actually intended versus what the other party took the utterance to mean. If those two are the same, there is no misunderstanding to repair, so stop and treat the scene as plain meaning inference instead.
- Locate the cause: find the exact ambiguous expression (a vague referent like 'it', a word with two senses, a hint) or the false assumption the listener brought, that produced the wrong reading.
- Recover the intended meaning from context, the speaker's goal, and what was actually said, so you know what the correct shared interpretation should be.
- Choose the lightest clarifying move that closes the gap: ask a focused clarifying question when you are the confused party, restate the intended meaning when you are the misread speaker, or correct the false assumption directly when the listener's premise is wrong.
- Confirm that both sides now share the same interpretation, then stop; do not escalate a simple confusion into blame or apology.
- Only if the misread has already caused real hurt, embarrassment, or offense that clarification alone cannot undo does the scene leave this skill; at that point it becomes after-the-fact apology and relationship repair, which needs acknowledging the harm and rebuilding trust, not just restating what was meant.

## Special Case
**Live misread caught before any harm**: When you can see that one party has taken an utterance differently from what the speaker intended, name the mismatch and the expression that caused it, then pick the lightest move that closes the gap (ask, restate, or correct the wrong assumption); do not add apology or moral blame unless the scene actually contains harm.

Scene: In a meeting Dana says, 'We should drop the launch.' Kai hears 'cancel the whole project' and starts arguing against it. Dana, who only meant removing the word 'launch' from a slide title, sees Kai react and realizes he has misread her.
Question: What should Dana do?
Answer logic: Detect the mismatch: Dana intended 'remove the word from the title' but Kai understood 'cancel the project.' Locate the cause: the phrase 'drop the launch' is ambiguous. Choose the lightest move: since Dana is the misread speaker, she restates her intended meaning ('I mean drop the word launch from the slide title, not cancel anything'). No one was harmed, so apology logic is wrong; arguing the literal cancel-or-not topic would miss that the real problem is the misread, not the decision.

## Boundary Exit Rule
- If meaning was already understood correctly and what remains is mending hurt, embarrassment, or offense, this is no longer a live clarification; solve it as after-the-fact apology and reconciliation, which requires acknowledging the harm, taking responsibility, and rebuilding trust rather than restating what was meant.
- If there is no actual misread and the task is only to figure out what an indirect, hinted, or ironic utterance means while both parties stay aligned, solve it as plain indirect-meaning decoding, which requires inferring the speaker's intended meaning, not repairing a mismatch between two interpretations.
- If the main task becomes winning a point, bargaining, or tailoring a message to a particular audience, treat it as persuasion or audience adaptation, which requires shaping the message to move the listener, not recovering shared meaning.
- If the core question is whether a statement is true, a lie, or concealed, treat it as a truth-and-deception judgment about the speaker's honesty, not a misunderstanding to clarify.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
One party visibly takes an utterance differently from what the speaker intended, and the scene shows the misread live: confusion, a reaction to the wrong reading, or repair language like 'What do you mean?', 'I thought you said...', 'No, I meant...'.
