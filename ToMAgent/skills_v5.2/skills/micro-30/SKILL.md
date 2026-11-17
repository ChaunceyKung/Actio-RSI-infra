---
name: micro-30
level: micro
layer: L4
family: "emotion-appraisal"
description: "Infers guilt, shame, pride, anger, or gratitude from a moral, norm-based, or responsibility-based appraisal."
---

# Moral Emotion

## Use When
- Use when the question asks which moral emotion someone feels after judging responsibility, blame, credit, obligation, fairness, harm, or thanks.
- Use when the emotion depends on whether the person sees themselves or another as responsible, deserving, at fault, benefitted, or norm-violating.
- Use when the key clue is a moral appraisal rather than a basic feeling trigger like pain, loss, surprise, or fear.
- Use when the answer requires inferring guilt, shame, pride, anger, or gratitude from a social or moral evaluation.

## Do Not Use When
- Do not use when the task is only to detect hidden emotion without needing the moral reason behind it.
- Do not use when the task is about display rules, politeness, or why emotion is masked rather than which moral emotion is felt.
- Do not use when the emotion is regret, relief, disappointment, or pleasant surprise from a comparison with an alternative outcome.
- Do not use when the emotion is a basic affect caused by direct events with no norm, blame, credit, or obligation appraisal.
- Do not use when the question is about empathy or emotional contagion from another person's feeling.

## Decision Variable
the responsibility or norm appraisal behind the emotion

## Trigger Checklist
- Is there blame, fault, credit, duty, fairness, harm, apology, or thanks in the scene?
- Does the person evaluate themselves or someone else as responsible or deserving?
- Is the emotion better explained by moral standing than by raw outcome or physical event?
- Would the answer change if the responsibility or norm judgment changed?

## Workflow
- Confirm a moral or normative appraisal is present: blame, fault, credit, duty, fairness, harm, a violated rule, an apology, or a received benefit. If none exists and the feeling is just a reaction to an event, this is not the right capability.
- Identify whose conduct is being judged and how: self at fault, self deserving credit, another person doing wrong, or another person providing help or benefit.
- Map the appraisal to the moral emotion: self-blame for harm or a broken rule = guilt; the self exposed as falling short of a standard before others = shame; self-credit for a worthy achievement = pride; another person's wrongdoing or unfairness = anger; a benefit received from another = gratitude.
- Distinguish guilt (I did a bad thing) from shame (I am exposed as bad), and anger-at-wrongdoing from mere annoyance at an inconvenience that involves no blameworthy agent.
- Verify the label would change if the responsibility or norm judgment changed; if the emotion survives even with no blame or credit, re-route to the basic-emotion-from-an-event capability (micro-26).

## Special Case
**Mixed appraisal with one dominant moral driver**: If multiple feelings are possible, choose the one most directly caused by the responsibility or norm judgment. Use this unit only when a moral appraisal is the main driver, even if a basic emotion is also present.

Scene: Ming takes home a cute puppy he finds on a mountain. He later learns the puppy actually belongs to old Mr. Wang in the village, who has been searching for it.
Question: What emotion does Ming feel once he realizes whose dog it is?
Answer logic: The decisive variable is a self-responsibility appraisal: Ming sees that his own action deprived another person of their pet. Self-attributed harm fixes the moral emotion as guilt (and regret over the deed), which beats the outcome-based distractors of happiness (he got a cute dog) or indifference (he likes it). It would not be guilt if no one had been wronged.

## Boundary Exit Rule
- If there is no responsibility, blame, credit, duty, fairness, or norm appraisal at all, and the feeling comes straight from a direct event, exit to the basic-emotion-from-an-event capability (micro-26).
- If the emotion comes from comparing what actually happened with a better or worse alternative that could have happened, exit to the reality-versus-alternative comparison capability that diagnoses regret, relief, disappointment, and pleasant surprise (micro-31).
- If the question is about what someone truly feels beneath a neutral or false surface, rather than which moral emotion they feel, exit to the hidden-emotion capability (micro-28).
- If the question is about WHY the person hides or shows the feeling in public (the display or concealment rule), not which moral emotion it is, exit to the emotional-display-rules capability (micro-29).
- If the feeling is caught from absorbing another person's emotion rather than produced by a moral judgment, exit to the empathy-and-emotional-contagion capability (micro-32).

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Route here when emotion inference depends on moral responsibility or norm evaluation rather than on simple event-based affect.
