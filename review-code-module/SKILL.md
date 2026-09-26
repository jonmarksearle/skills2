---
name: review-code-module
description: Review one Python module against its module TDD contract and semantic code rules after a green gate, returning focused findings for the Code Reviewer or Architect.
---

# review-code-module

## Invocation

Invoke at the inner Refactor step for constructs changed in that tiptoe, during the first Outer Refactoring review for the affected module, and during Late Outer Refactoring for constructs changed since Outer review closed plus concerns named by the Architect. Enter from a documented green gate under [TDD_PROCESS.md](../../../Standards/TDD_PROCESS.md#quality-gate). A proposed public-contract change follows the Outer Refactoring Cycle and Architect review.

## Input and evidence

- One source module, module role (core or peripheral), its relevant module TDD contract, affected tests, and any allocated RDD or SDD passages needed to judge a proposed change.
- Applicable clauses of [CODE_STANDARDS.md](../../../Standards/CODE_STANDARDS.md) and [design_standards.md](../../../Standards/design_standards.md); current format, lint, test, and type-check results where the project defines them.
- An AST inventory of changed functions, classes, types, and imports; prior review-response findings when this is round `n+1`; duplicate-logic comparison candidates selected from this module and named shared libraries only.

Run mechanical checks locally for line counts, naming shape, import direction, and available lint/type results. If the gate is red or evidence is stale, return `gate_required` and identify the missing current result.

## Execute with Jev

Follow [ask-jev](../ask-jev/SKILL.md) for typed request shape and interpretation. Run `bash E:/work/.agents/skills/tools/jev.sh REQUEST.json` with a key-free local request. On failure, mark semantic judgments `not_run`; never invent probabilities.

Put the cited source excerpts and definitions in a compact state. Ask independent questions together in one request; give each question its full meaning, explicit criteria, and stable local ID. Use Noul for each independent suspected defect, Choice for exclusive statuses, and Score for ordered dimensions. Retain raw answers, distributions, model, question version, usage, artifact hash, and source spans. A typed response is not an approved disposition. Apply the rule-specific calibration and cost plan at [skills-evaluation-plan.md](../../../jev-try/skills-evaluation-plan.md); until a gate is approved, route semantic findings to the named reviewer or owner.

Follow the applicable Standards and project-local `AGENTS.md` before changing an artifact. This skill drafts findings and handoffs; the responsible process role approves changes and gates. Check every reported finding against the actual cited passage before handing it off.

## Judgment and workflow

1. Select the module and constructs: changed constructs at the inner Refactor step; relevant constructs in the first Outer review; changed constructs and Architect-named concerns at Late Outer review or later rounds. Expand the selection when a shared contract changed. Keep contract and rule excerpts close to source. **Done when:** each selected construct has a source span and relevant contract span.
2. Ask Jev independent yes/no defect questions over the shared module state. Module questions: core performs I/O, dependency is hidden, business logic and error translation are mixed, public API exceeds contract, or semantically equivalent logic is duplicated in candidates retrieved from this module and explicitly named shared libraries. Construct questions: responsibility is mixed, mutation or materialisation lacks a contract need, public type obscures the contract, name hides domain intent, or an optional docstring merely repeats the name without clarifying behaviour. Ask only where relevant evidence is present. **Done when:** every applicable question has a typed result and usage without repeating module state unnecessarily.
3. Separate deterministic violations from semantic findings. Return high-impact semantic findings for Code Reviewer inspection with source, contract, and rule spans; present clarity and naming findings as review suggestions. Route doubts about whether a class, interface, or pattern should exist to [review-design-element](../review-design-element/SKILL.md). A raw Jev probability does not itself block a green workflow. A confirmed contract change enters Outer Refactoring and goes to Architect. **Done when:** each finding has evidence, severity rationale, and next owner.
4. Draft `{file}.review.{n}.md` entries for the Code Reviewer. In later rounds, inspect the response document and re-check only changed or disputed constructs unless a shared contract changed. The Refactorer edits code; the Code Author maintains the green gate. **Done when:** each open review point has an accepted, disputed, or unresolved path through the existing review-response process.

Automatic blocking is eligible only for a named hard rule after rule-specific calibration and Architect acceptance of a gate policy recorded in [TDD_PROCESS.md Pragmatics](../../../Standards/TDD_PROCESS.md#pragmatics); if command targets change, update [JUSTFILE_STANDARDS.md](../../../Standards/JUSTFILE_STANDARDS.md) through its owner. No such policy is established by this specification. Until then semantic results receive Code Reviewer inspection. Deterministic failures follow the project's quality gate.

## Result contract

`module`, `gate_state`, `review_round`, `constructs_reviewed`, `mechanical_findings`, `semantic_judgments[{rule_id, probability_or_choice, triage: finding|clear|inspect, source_span, contract_span, severity, next_owner}]`, `review_draft`, `artifact_hash`, `question_set_version`, `model`, `usage`. The review draft contains supported findings; the judgment list also retains clear and uncertain results.

## Acceptance examples

- A core function reads the filesystem directly: local import/call evidence and a focused semantic finding cite the core boundary rule.
- An inner refactor changes a public return contract: route to Architect and Outer Refactoring instead of treating it as behaviour-preserving cleanup.
- An unchanged construct from the prior review round is omitted from `n+1` when its contract is unchanged.
- Late Outer review omits constructs unchanged since Outer closed unless the Architect names a concern about one.
- A possible duplicated calculation is compared with locally retrieved code before Jev judges whether the behaviours are truly the same.
- A naming concern with uncertain Jev evidence remains a suggestion for reviewer inspection; it does not silently block a green gate.
