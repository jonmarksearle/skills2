---
name: check-requirement-preservation
description: Check whether every RDD scenario allocated to a changed module is preserved in its feature SDD and module TDD; trace invalidations during RDD Refinement.
---

# check-requirement-preservation

## Invocation

Invoke when a feature SDD or module TDD is drafted or changed, and during Refinement propagation. The unit is one module and every scenario allocated to it. The Architect owns design and any change to a baselined RDD under [RDD_PROCESS.md](../../../Standards/RDD_PROCESS.md#requirements-refinement-cycle-n1n).

## Input and evidence

- Every scenario allocated to the module, expanded Shared Givens, IDs, and baseline status.
- The SDD allocations and relevant responsibility, interaction, and cross-module contract passages.
- Module TDD interface behaviour and natural-language test definitions relevant to those allocations; during Refinement, include citing executable tests.
- Relevant rules from [design_standards.md](../../../Standards/design_standards.md#1-purpose--scope) and [TDD_PROCESS.md](../../../Standards/TDD_PROCESS.md#module-tdd-structure).
- Explicit current `stage` and `next_owner` supplied by the Architect or task handoff when an uncited scenario must be distinguished as pending or forgotten; include the source of that stage value.

Build the feature-wide citation graph locally before a module judgment. Missing or dangling IDs are deterministic findings. Use the explicit input stage, verified against the current feature breadcrumb in `breadcrumbs/` or task handoff where available; the SDD remains the durable allocation design. Mark an uncited scenario `not_yet_allocated` when its downstream stage has not begun, or `forgotten` when that stage is recorded complete. If the stage is absent or conflicts with current evidence, return `stage_unknown` for Architect clarification. Feature completeness comes from the graph, not a module Choice.

## Execute with Jev

Follow [ask-jev](../ask-jev/SKILL.md) for typed request shape and interpretation. Run `bash E:/work/.agents/skills/tools/jev.sh REQUEST.json` with a key-free local request. On failure, mark semantic judgments `not_run`; never invent probabilities.

Put the cited source excerpts and definitions in a compact state. Ask independent questions together in one request; give each question its full meaning, explicit criteria, and stable local ID. Use Noul for each independent suspected defect, Choice for exclusive statuses, and Score for ordered dimensions. Retain raw answers, distributions, model, question version, usage, artifact hash, and source spans. A typed response is not an approved disposition. Apply the rule-specific calibration and cost plan at [skills-evaluation-plan.md](../../../jev-try/skills-evaluation-plan.md); until a gate is approved, route semantic findings to the named reviewer or owner.

Follow the applicable Standards and project-local `AGENTS.md` before changing an artifact. This skill drafts findings and handoffs; the responsible process role approves changes and gates. Check every reported finding against the actual cited passage before handing it off.

## Judgment and workflow

1. For every allocated scenario, extract starting state, trigger, observable result, and error or boundary condition. Trace SDD, TDD, and when relevant test citations by path and line. **Done when:** every allocation and citation to this module is accounted for.
2. Give Jev the compact module state and ask one Choice per allocation: `fully_preserved`, `partly_preserved`, `absent`, `contradicted`, or `insufficient_evidence`. Ask a separate yes/no question for any TDD behaviour lacking a trace to an allocated scenario **or** a documented module contract, error, constraint, or invariant. Pool independent questions over this module's shared state. **Done when:** every allocation and relevant reverse check has a typed result and usage.
3. Compare statuses with quoted passages. Feed `forgotten` scenario IDs to [check-scenario-set](../check-scenario-set/SKILL.md) when Refinement readiness is assessed. On RDD Refinement Tiptoe D, follow citations downward and list affected SDD passages, TDD definitions, and executable tests; flag potential invalidations for Architect confirmation. For a contradiction against a baselined RDD, prepare the required Refinement review entry naming affected scenarios. **Done when:** every non-full result has an upstream and downstream span, and every traced downstream artifact is listed as affected or unaffected.

The skill reports `fully_preserved` only for the passages it received. A final feature claim also needs the local citation-graph check to show that every required allocation was included. Thresholds for automatic dispositions require labelled examples; low-confidence or contested results are for Architect review.

## Result contract

`module`, `stage`, `citation_graph_status`, `lifecycle_evidence`, `uncited_scenarios[{id, status: not_yet_allocated|forgotten|stage_unknown}]`, `allocations[{scenario_id, baseline_status, sdd_span, tdd_spans, choice, probabilities, confidence, triage: finding|clear|inspect, missing_or_changed_behaviour}]`, `untraced_behaviour`, `invalidation_list`, `refinement_review_draft?`, `next_owner`, `artifact_hash`, `question_set_version`, `model`, `usage`. Keep raw Jev output alongside local graph findings.

## Acceptance examples

- RDD: `Then the rejected import leaves the journal unchanged.` SDD assigns rejection to a module, but its TDD covers only an error message: `partly_preserved`, citing the missing no-mutation guarantee.
- RDD says an invalid amount is rejected; TDD specifies acceptance: `contradicted`.
- A cited SDD responsibility and TDD test definition both preserve the trigger and observable result: `fully_preserved` for that allocation.
- A dangling scenario ID is returned as a graph finding even when Jev is unavailable.
- A TDD invariant needed by its public contract is not flagged merely because it lacks a direct RDD citation.
- An amended baselined scenario reports the SDD passage, TDD definition, and pytest test that cite it for Architect propagation.
- An uncited scenario with no reliable lifecycle breadcrumb returns `stage_unknown`, rather than guessing whether work was forgotten.
