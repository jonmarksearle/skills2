---
name: review-design-element
description: Review the proposed classes, interfaces, patterns, adapters, and dependency seams of a new or changed module against its current responsibilities and requirements.
---

# review-design-element

## Invocation

Invoke at feature SDD review for module-level responsibilities, boundaries, and proposed patterns; at module TDD review for interface-level operations, invariants, and seams; when Outer Refactoring proposes adding or extracting a pattern; or when [review-code-module](../review-code-module/SKILL.md) questions an existing structural element. Re-check changed or questioned elements and any affected by a changed shared contract. Pool independent questions over one relevant module state. The Architect owns design decisions under [design_standards.md](../../../Standards/design_standards.md#5-module-types--when-to-use-them-no-pattern-tourism).

## Input and evidence

- Each proposed or questioned existing element's name, role, public contract, and defining SDD or module TDD passage; include its current source span for an existing element.
- Current requirements allocated to its module; the module's in-scope, out-of-scope, dependencies, seams, and invariants.
- Any existing alternatives directly relevant to the decision, such as a pure function, constructor parameter, or existing adapter. Show their actual stated responsibilities.
- Only the applicable clauses of `design_standards.md`: core/peripheral boundary, dependency direction, current need for a pattern, explicit seams, and public contracts.

If the module allocation or proposed contract is absent, return `insufficient_evidence` naming that source. Inspect import direction mechanically when implementation exists.

## Execute with Jev

Follow [ask-jev](../ask-jev/SKILL.md) for typed request shape and interpretation. Run `bash E:/work/.agents/skills/tools/jev.sh REQUEST.json` with a key-free local request. On failure, mark semantic judgments `not_run`; never invent probabilities.

Put the cited source excerpts and definitions in a compact state. Ask independent questions together in one request; give each question its full meaning, explicit criteria, and stable local ID. Use Noul for each independent suspected defect, Choice for exclusive statuses, and Score for ordered dimensions. Retain raw answers, distributions, model, question version, usage, artifact hash, and source spans. A typed response is not an approved disposition. Apply the rule-specific calibration and cost plan at [skills-evaluation-plan.md](../../../jev-try/skills-evaluation-plan.md); until a gate is approved, route semantic findings to the named reviewer or owner.

Follow the applicable Standards and project-local `AGENTS.md` before changing an artifact. This skill drafts findings and handoffs; the responsible process role approves changes and gates. Check every reported finding against the actual cited passage before handing it off.

## Judgment and workflow

1. Enumerate the changed or questioned elements for this stage: module-level elements at SDD review, interface-level elements at module TDD review, or a proposed or existing pattern raised during refactoring. State each claimed job and cite the requirement, invariant, or boundary that motivates it. **Done when:** every selected element has an attributable job or a missing-rationale finding.
2. Give Jev one compact module state and ask independent yes/no questions per element: `lacks_current_requirement`, `duplicates_existing_responsibility`, `violates_module_boundary`, `adds_unneeded_abstraction`, and `substitution_unsupported` when substitution is claimed. Yes always means a suspected defect. Partition only if the module state exceeds the selected interface's useful context. **Done when:** each applicable question has a probability and usage recorded.
3. Return `retain`, `simplify`, `move`, or `architect_review` per element with the rule and evidence behind any proposed change. If alternatives have already been supplied, first have the Architect supply the objective, hard constraints, named fatal-risk list (explicitly empty if none), criteria, and weights; then pass the option set to [evaluate-options](../evaluate-options/SKILL.md). **Done when:** the Architect can accept or reject each finding and any comparison has every required input.

The disposition combines evidence and configurable policy; the Architect decides. An accepted `simplify` or `move` is reflected in the SDD or module TDD and a breadcrumb before corresponding code changes. Use labelled design examples before automating dispositions. Keep mechanically detected dependency violations separate.

## Result contract

`module`, `elements[{name, source, claimed_job, requirement_spans, judgments[{id, probability, triage: finding|clear|inspect}], disposition, reason_spans}]`, `mechanical_findings`, `next_owner: Architect`, `artifact_hash`, `question_set_version`, `model`, `usage`.

## Acceptance examples

- A Strategy with one present algorithm and no stated variant flags `adds_unneeded_abstraction`; the result cites the requirement set and proposed interface.
- An adapter shielding a required external boundary identifies the current boundary and supports `retain`.
- Core code proposed to import an I/O adapter produces a mechanical dependency finding, regardless of Jev's semantic answer.
- An interface whose needed substitution cannot be established from the supplied TDD returns `architect_review` with the missing evidence.
