---
name: micro-05
level: micro
layer: L1
family: "perception-memory-knowledge"
description: "Sensory Access decides whether a character could perceptually obtain information through a channel such as sight, hearing, touch, smell, or taste."
---

# Sensory Access

## Use When
- Use when the question is whether a character could see, hear, touch, smell, taste, or otherwise directly perceive something.
- Use when the key issue is whether information was physically available to a sensory channel, regardless of whether the character paid attention.
- Use when you need to determine access before any inference, belief, or noticing judgment.

## Do Not Use When
- Do not use when the question is whether the character noticed, remembered, interpreted, or believed the information.
- Do not use when the issue is viewpoint transformation, left-right mapping, or what another person sees from a position.
- Do not use when the main question is attention, salience, or whether a cue entered awareness.
- Do not use when the scene is really about inference from partial evidence rather than direct perceptual access.

## Decision Variable
whether the character can directly perceive the information through a sensory channel

## Trigger Checklist
- Is there a usable sensory channel for the target information?
- Is the channel physically blocked, absent, or out of range?
- Is the information directly available, not merely implied or reported?
- Is the access judgment independent of whether the character noticed, understood, or later remembered it?

## Workflow
- Identify the target information and the relevant sensory channel.
- Check whether that channel is open, unobstructed, and within range.
- Decide access yes or no based only on direct perceptual availability.
- Do not upgrade the answer based on attention, belief, or interpretation.

## Special Case
**Channel closed during the change**: If a character is out of range of a sensory channel while the relevant event happens, they have no access to it, no matter what they perceived before or learn by report afterward.

Scene: Xiao Ming and Xiao Li see chalk placed in a handbag in the bank. Xiao Li then leaves the bank, and while she is gone Xiao Ming moves the chalk into the box.
Question: What does Xiao Li see in the box?
Answer logic: Nothing. Xiao Li was outside the bank when the chalk was moved, so her visual channel to the box was closed during the change. She had access to the original placement but no perceptual access to the move, so she does not see the chalk in the box. This is an access verdict only; whether she later believes or infers the new location is a separate question.

## Boundary Exit Rule
- If the question becomes whether the character noticed, switch to Attention and Salience.
- If the question becomes what the character thinks or believes, switch to a belief or knowledge unit.
- If the question is about what is visible from another person's position, switch to Spatial Perspective Transformation.
- If the question requires interpreting a cue, switch to a higher-level inference or pragmatics unit.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use this unit when the scene asks whether information was perceptually available through a sensory channel.
