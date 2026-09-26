---
name: evaluate-options
description: Screen and rank two or more supplied requirements, design, or refactor options against agreed constraints and priorities before their owner makes a decision.
---

# evaluate-options

## Invocation

Invoke when a Stakeholder, Architect, or author has already supplied at least two candidates and a stated objective. The skill evaluates the supplied set. For RDD elicitation, the Stakeholder owns intent; for design and refactoring, the Architect owns the decision. Record an accepted decision under `design/decisions/` when the project uses the [RDD decision record practice](../../../Standards/RDD_PROCESS.md#elicitation).

## Input and evidence

- One decision statement, candidate IDs and comparable descriptions, the decision owner, and the decision stage.
- Hard constraints, a decision-owner-supplied list of named fatal risks, and their source documents; priority dimensions and weights set by the Stakeholder or Architect **before** scoring.
- Only the RDD, SDD, module TDD, and Standards excerpts needed to evaluate those candidates.

If the objective, candidate set, or decision weights are missing, return `insufficient_evidence` and name the owner who must supply them. The decision owner explicitly supplies an empty fatal-risk list when none are named. Generate no candidates in this skill; a separate author or Stakeholder may create a new set after `no_acceptable_candidate`.

## Execute with Jev

Follow [ask-jev](../ask-jev/SKILL.md) for typed request shape and interpretation. Run `bash E:/work/.agents/skills/tools/jev.sh REQUEST.json` with a key-free local request. On failure, mark semantic judgments `not_run`; never invent probabilities.

Put the cited source excerpts and definitions in a compact state. Ask independent questions together in one request; give each question its full meaning, explicit criteria, and stable local ID. Use Noul for each independent suspected defect, Choice for exclusive statuses, and Score for ordered dimensions. Retain raw answers, distributions, model, question version, usage, artifact hash, and source spans. A typed response is not an approved disposition. Apply the rule-specific calibration and cost plan at [skills-evaluation-plan.md](../../../jev-try/skills-evaluation-plan.md); until a gate is approved, route semantic findings to the named reviewer or owner.

Follow the applicable Standards and project-local `AGENTS.md` before changing an artifact. This skill drafts findings and handoffs; the responsible process role approves changes and gates. Check every reported finding against the actual cited passage before handing it off.

## Judgment and workflow

1. Confirm at least two candidates, a shared comparison shape, explicit hard constraints and named risks, and fixed weights. At elicitation use **need fit** as the first dimension because the RDD is not yet written; at design or refactoring use **requirement fit** against current baselined requirements. Use simplicity, testability, and architecture fit only where the decision stage makes them meaningful. Preserve the candidate text and weight source. **Done when:** each option can be judged against the same applicable criteria without inventing a preference.
2. Build one compact state and ask Jev independent yes/no questions per candidate for each supplied hard-constraint breach and named fatal risk. Ask described Score questions for the stage's applicable dimensions. Pool candidate-by-dimension questions over the shared state in one request where supported; partition only for tool limits or excessive unrelated context. **Done when:** every candidate has all applicable typed probabilities, scores, confidence, and usage.
3. Present each suspected hard-constraint or named-risk breach as `inspect` to the decision owner. Before a rule has an approved calibrated gate, eliminate a candidate only after the owner confirms its breach against the cited evidence. Return `no_acceptable_candidate` only when confirmed breaches eliminate every candidate. Compare survivors with the conservative 90%-probability score-range rule in [skills-evaluation-plan.md](../../../jev-try/skills-evaluation-plan.md#option-score-uncertainty-rule): overlapping ranges yield `shortlist`; only a leader whose lower bound exceeds every other survivor's upper bound may receive an advisory `recommend`. Keep raw values visible. **Done when:** each elimination has an owner-confirmed reason and the remaining disposition is reproducible from the recorded inputs.
4. Draft a `design/decisions/` record with objective, candidates, constraints, weights, evidence, ranking, uncertainty, and the owner's eventual decision slot. **Done when:** the owner can accept, reject, or request new options without reconstructing the comparison.

Set thresholds from labelled decisions before proposing any automatic elimination policy. A Jev probability is evidence for the owner, not a substitute for approval. Re-evaluate if the candidates, constraints, or weights change. The conservative range rule will often return `shortlist`; that is a useful handoff for close decisions.

## Result contract

`decision_id`, `stage`, `objective`, `candidate_ids`, `constraints`, `named_fatal_risks`, `weights`, `judgments[{candidate_id, constraint_probabilities, scores, confidence, triage: finding|clear|inspect, confirmed_breaches}]`, `ranking`, `uncertainty_comparison`, `disposition: no_acceptable_candidate|shortlist|recommend`, `decision_record_draft`, `next_owner`, `artifact_hash`, `question_set_version`, `model`, `usage`.

## Acceptance examples

- Two design options are compared after the Architect fixes simplicity and testability weights; changing a weight afterward starts a new evaluation rather than silently re-ranking the old decision.
- Jev flags both options as likely to breach a required no-I/O-in-core constraint: mark both `inspect`. After the Architect confirms both breaches from the cited design passages, return `no_acceptable_candidate` and request a new set.
- A candidate is absent from the supplied set: it never appears as an invented Jev option.
- One candidate satisfies all hard constraints, and its weighted score-range lower bound exceeds every other survivor's upper bound: return an advisory `recommend` with the underlying ranges and a decision-record draft.
- During elicitation, candidates are scored for fit to the Stakeholder's stated need; no unwritten requirement is invented.
- Two survivors have overlapping uncertainty under the chosen comparison rule: return `shortlist`, leaving the decision to its owner.
