---
name: review-rdd-scenario
description: Review new or amended RDD scenarios for ambiguity, missing observable outcomes, mixed behaviours, and design decisions before the Requirements Reviewer cycle.
---

# review-rdd-scenario

## Invocation

Invoke after Scenario Writing Tiptoe A and before Tiptoe B for all new or amended scenarios in one feature RDD. During Refinement, review only amended scenarios. The unit of work is this scenario set with its shared feature context. The Requirements Reviewer owns the review under [RDD_PROCESS.md](../../../Standards/RDD_PROCESS.md#scenario-writing-cycle).

## Input and evidence

- Each changed scenario's ID, name, Given, When, Then, and any And clauses, copied with source line references.
- Expanded text of any referenced Shared Given, the RDD's Need, Actors, Out of Scope, Constraints, and relevant glossary definitions or recorded stakeholder decisions.
- The scenario expectations in [RDD_PROCESS.md](../../../Standards/RDD_PROCESS.md#scenario-expectations); consult [RDD_PROCESS_SCENARIOS.md](../../../Standards/RDD_PROCESS_SCENARIOS.md#part-2--scenarios) for ambiguous cases. The process document owns the rule.

If a scenario or cited Shared Given is missing, report the missing source for that scenario and continue with complete scenarios. Parse ID shape, required clauses, and reference existence locally before Jev.

## Execute with Jev

Follow [ask-jev](../ask-jev/SKILL.md) for typed request shape and interpretation. Run `bash E:/work/.agents/skills/tools/jev.sh REQUEST.json` with a key-free local request. On failure, mark semantic judgments `not_run`; never invent probabilities.

Put the cited source excerpts and definitions in a compact state. Ask independent questions together in one request; give each question its full meaning, explicit criteria, and stable local ID. Use Noul for each independent suspected defect, Choice for exclusive statuses, and Score for ordered dimensions. Retain raw answers, distributions, model, question version, usage, artifact hash, and source spans. A typed response is not an approved disposition. Apply the rule-specific calibration and cost plan at [skills-evaluation-plan.md](../../../jev-try/skills-evaluation-plan.md); until a gate is approved, route semantic findings to the named reviewer or owner.

Follow the applicable Standards and project-local `AGENTS.md` before changing an artifact. This skill drafts findings and handoffs; the responsible process role approves changes and gates. Check every reported finding against the actual cited passage before handing it off.

## Judgment and workflow

1. Build a compact state with `scenarios`, expanded `shared_givens`, `feature_frame`, `terms`, and `rules`. Quote the shared context once and retain file and line references. Partition by scenario group if one request would carry excessive unrelated text. **Done when:** each cited precondition and rule used in a judgment has source text.
2. For each scenario, ask seven independent yes/no questions, where yes means a suspected defect: `ambiguous_precondition`, `ambiguous_outcome`, `unobservable_outcome`, `multiple_behaviours`, `implementation_detail`, `property_not_event`, and `solution_not_need`. Define each in words; IDs alone carry no meaning. Pool the questions over shared state when the selected interface supports it. **Done when:** every complete scenario has seven typed probabilities and request usage.
3. Inspect the words behind each suspected defect and assign a correction route from [RDD_PROCESS_SCENARIOS.md](../../../Standards/RDD_PROCESS_SCENARIOS.md#part-2--scenarios): rewrite an ambiguous or unobservable outcome around observable behaviour; split independent outcomes; move a continuous property into Constraints; move an engineering quality rule to its design standard; or take a prescribed solution back to the Stakeholder's need. If `property_not_event` and `unobservable_outcome` describe the same source span and cause, report one finding with the route supported by the text. Keep distinct defects separate; do not choose a route by comparing raw probabilities from different questions. If recorded evidence cannot resolve Stakeholder intent, mark `needs_stakeholder_decision` and formulate one focused question with a recommended answer. For an unavailable external Stakeholder, mark affected scenarios provisional and record their open questions. **Done when:** every finding cites a scenario line, correction route, and owner without inventing intent.
4. Return findings as draft entries for `{file}.review.{n}.md`; the Requirements Reviewer decides what enters the review. **Done when:** every changed scenario has a `finding`, `clear`, or `inspect` disposition and an identified next owner.

Keep thresholds configurable until evaluated on labelled RDD examples; uncertain answers go to Requirements Reviewer inspection.

## Result contract

`scenarios[{scenario_id, source, judgments[{id, probability, triage: finding|clear|inspect}], disposition, findings[{rule, source_span, explanation, correction_route, next_owner}], unresolved_question?, provisional}]`, `review_draft`, `artifact_hash`, `question_set_version`, `model`, `usage`. Disposition is a workflow decision applied to raw probabilities.

## Acceptance examples

- `Then the user sees an error message` flags an ambiguous outcome if the expected message or effect is material to the recorded intent.
- `Then the import stores the record and emails the owner` flags two behaviours unless the documented requirement treats them as one indivisible outcome.
- A continuous property such as `records remain available for seven years` flags `property_not_event` for consideration as a framing constraint.
- If that property also receives `unobservable_outcome`, the review reports one finding when both refer to the same statement, with `move to Constraints` as the evidence-based route.
- A scenario prescribing a dropdown rather than the region decision it supports flags `solution_not_need`.
- A clear scenario produces no finding; the output still shows all seven judgments and usage.
- Missing stakeholder policy is reported as a question, with no invented outcome.
