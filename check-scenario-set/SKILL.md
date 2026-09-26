---
name: check-scenario-set
description: Check a feature RDD's scenario set for contradictions, overlaps, missing actors, missing error or boundary behaviours, and scope breaches before baseline or re-baseline.
---

# check-scenario-set

## Invocation

Invoke after individual scenarios are reviewed and before Architect baselining in [RDD_PROCESS.md](../../../Standards/RDD_PROCESS.md#scenario-writing-cycle). Re-run at Refinement propagation when an amended scenario may affect the set, then before re-baseline. The unit is one feature RDD and a small set of related existing-feature scenarios. The Architect owns readiness and baseline.

## Input and evidence

- Current RDD frame, all active scenario IDs and text, expanded Shared Givens, glossary, and open questions.
- `forgotten` scenario IDs and lifecycle evidence from [check-requirement-preservation](../check-requirement-preservation/SKILL.md) when assessing Refinement readiness.
- Relevant **baselined** existing-feature scenarios identified by local retrieval using shared actors, terms, Givens, or triggers. Keep their source references and baseline status.
- [RDD_PROCESS.md](../../../Standards/RDD_PROCESS.md#completeness) completeness and scenario rules; consult [RDD_PROCESS_SCENARIOS.md](../../../Standards/RDD_PROCESS_SCENARIOS.md#part-2--scenarios) for contradiction and overlap handling.

Parse IDs and Shared Given references locally. Check explicit Out of Scope and actor-name coverage locally, then inspect meaning where a name match is not enough. Mark provisional scenarios and unresolved stakeholder questions before computing readiness.

## Execute with Jev

Follow [ask-jev](../ask-jev/SKILL.md) for typed request shape and interpretation. Run `bash E:/work/.agents/skills/tools/jev.sh REQUEST.json` with a key-free local request. On failure, mark semantic judgments `not_run`; never invent probabilities.

Put the cited source excerpts and definitions in a compact state. Ask independent questions together in one request; give each question its full meaning, explicit criteria, and stable local ID. Use Noul for each independent suspected defect, Choice for exclusive statuses, and Score for ordered dimensions. Retain raw answers, distributions, model, question version, usage, artifact hash, and source spans. A typed response is not an approved disposition. Apply the rule-specific calibration and cost plan at [skills-evaluation-plan.md](../../../jev-try/skills-evaluation-plan.md); until a gate is approved, route semantic findings to the named reviewer or owner.

Follow the applicable Standards and project-local `AGENTS.md` before changing an artifact. This skill drafts findings and handoffs; the responsible process role approves changes and gates. Check every reported finding against the actual cited passage before handing it off.

## Judgment and workflow

1. Build a feature inventory of actors, triggers, errors, boundaries, active scenarios, and Shared Givens. State a local pair-selection rule using meaningful shared Given, When, actor, or domain term; include related baselined existing-feature pairs. Report total possible pairs, selected pairs, and omitted pairs, with the rule and any known recall limitation. **Done when:** every active scenario is inventoried and the pair counts reconcile.
2. Check Shared Givens: a state definition containing a trigger or outcome is a defect under [RDD_PROCESS.md](../../../Standards/RDD_PROCESS.md#shared-givens); compare the usages of a reused Shared Given for preconditions that merely look alike. Give Jev the selected pairs and relevant Shared Given usages with exact feature context. Ask one Choice per scenario pair: `independent`, `overlapping`, `contradictory`, or `insufficient_evidence`. Ask separate yes/no questions for missing required error or boundary behaviour, Out of Scope breaches, and unjustified Shared Given reuse where evidence supports them. The per-scenario `property_not_event` check belongs to [review-rdd-scenario](../review-rdd-scenario/SKILL.md) and is repeated only for a scenario changed since that review. Pool questions over relevant shared state when supported; partition large sets. **Done when:** each candidate pair, Shared Given, and applicable gap has a typed or deterministic result and usage.
3. Inspect findings against source spans. Route a contradiction to the Stakeholder through the Architect; represent overlap with an existing feature by citing the existing scenario rather than restating it. The Author may revise clear wording defects through the review-response cycle. **Done when:** every non-independent result names the exact pair, evidence, and owner.
4. Combine local completeness facts, received `forgotten` IDs, and reviewed Jev findings into `ready`, `not_ready`, or `insufficient_evidence` for Architect review. A received `forgotten` ID prevents `ready` until its allocation is resolved. **Done when:** every actor, forgotten ID, and open question is accounted for and no unresolved contradiction is hidden by the verdict.

Readiness supports the Architect's decision; it does not baseline the RDD. Where the Stakeholder is unavailable, open questions and dependent scenarios remain provisional.

## Result contract

`feature`, `actor_coverage`, `out_of_scope_present`, `forgotten_ids`, `pair_selection_rule`, `pair_counts`, `pair_matrix[{left_id, right_id, choice, probabilities, confidence, source_spans, triage: finding|clear|inspect}]`, `shared_given_findings`, `missing_error_or_boundary`, `scope_findings`, `open_questions`, `readiness`, `next_owner: Architect`, `artifact_hash`, `question_set_version`, `model`, `usage`.

## Acceptance examples

- Two scenarios share Given and When but specify incompatible Then outcomes: `contradictory`, routed to Stakeholder via Architect.
- A new feature repeats an existing feature's behaviour: `overlapping`, with a proposed citation to the existing scenario.
- An actor in framing appears in no scenario: local coverage finding, regardless of Jev output.
- All reviewed scenarios are individually clear but an error path is missing: `not_ready` with the missing trigger and boundary named.
- A Shared Given containing `When` or an outcome is flagged; two usages with different required starting states prompt a separate reuse finding.
