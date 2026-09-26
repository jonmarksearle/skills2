---
name: verify-completion-claim
description: Verify separate agent completion claims against current files and command results; diagnose unexpected strict-xfail passes before a TDD handoff.
---

# verify-completion-claim

## Invocation

- **Claim check:** invoke before a handoff claiming green, done, or ready; the unit is a fixed list of atomic claims and evidence.
- **Unexpected-pass diagnosis:** invoke when strict xfail reports XPASS and the gate goes red; the unit is the affected test, current diff, prior green state, and test definition.

[TDD_PROCESS.md](../../../Standards/TDD_PROCESS.md#quality-gate) owns the quality gate; this skill checks reports and diagnoses the unexpected-pass state.

## Input and evidence

- One claim per line in a fixed template: `claim_id | claim_text | evidence_refs`; plus task objective, scope, and named files or gates. Return compound claims for separation by the author before judging them.
- Relevant changed artifact list, source excerpts for claimed behaviour, command lines, exit codes, and unedited output excerpts with timestamps where available.
- Known unresolved findings and deferred strict-xfail state, if the claim includes test or completion status.

Check file existence, Git status, command exit codes, failure counts, and timestamps locally. A gate result predating the last relevant file change is `insufficient_evidence` for current green state. If the report lacks raw output, exit code, or chronology, name the missing evidence.

## Execute with Jev

Follow [ask-jev](../ask-jev/SKILL.md) for typed request shape and interpretation. Run `bash E:/work/.agents/skills/tools/jev.sh REQUEST.json` with a key-free local request. On failure, mark semantic judgments `not_run`; never invent probabilities.

Put the cited source excerpts and definitions in a compact state. Ask independent questions together in one request; give each question its full meaning, explicit criteria, and stable local ID. Use Noul for each independent suspected defect, Choice for exclusive statuses, and Score for ordered dimensions. Retain raw answers, distributions, model, question version, usage, artifact hash, and source spans. A typed response is not an approved disposition. Apply the rule-specific calibration and cost plan at [skills-evaluation-plan.md](../../../jev-try/skills-evaluation-plan.md); until a gate is approved, route semantic findings to the named reviewer or owner.

Follow the applicable Standards and project-local `AGENTS.md` before changing an artifact. This skill drafts findings and handoffs; the responsible process role approves changes and gates. Check every reported finding against the actual cited passage before handing it off.

## Judgment and workflow

1. Validate the fixed claim list and attach the strongest evidence to each. Check that gate outputs postdate the last relevant changes. **Done when:** every atomic claim has a current evidence span or named missing source.
2. Resolve deterministic claims locally. For semantic claims, give Jev the exact claim and supporting passages and ask `supported`, `contradicted`, or `insufficient_evidence`. When strict xfail reports an unexpected pass, first classify the pytest outcome locally; then ask Jev whether supplied test and diff evidence supports `over_implementation`, `duplicate_coverage`, `behaviour_pre_existed`, or `insufficient_evidence`. Over-implementation routes to Code Author to restore the last green state and implement a smaller change; duplicate coverage routes to Architect to inspect the test definitions; pre-existing behaviour routes to Architect and Test Author to review the redundant definition and test. For red from import, syntax, collection, or fixture failure, report the local cause before code work proceeds. **Done when:** every claim and unexpected-pass event has a fact or typed judgment, usage, next owner, and action.
3. Produce a corrected statement and a proposed breadcrumb entry with suite colour, observed failure or pass, commands, and next owner. A claim of requirement or test coverage with missing semantic evidence routes to [check-requirement-preservation](../check-requirement-preservation/SKILL.md) or [check-test-definition-coverage](../check-test-definition-coverage/SKILL.md), respectively. Keep the deferral marker until the unexpected pass has been diagnosed and the responsible role has resolved it. **Done when:** another reviewer can verify each statement and handoff from cited records.

`supported` means the supplied evidence supports the precise claim. It does not certify the entire project. A failing command is conclusive for a claimed passing run; an absent command is `insufficient_evidence`, not a pass. The skill does not rerun quality gates unless the user has requested verification or the project's workflow requires a run.

## Result contract

`mode: claim_check|unexpected_pass`, `claims[{id, text, method: local|jev, status, triage: finding|clear|inspect, evidence_spans, missing_evidence}]`, `gate_freshness`, `red_or_xpass_diagnosis?`, `corrected_statement`, `breadcrumb_draft`, `next_owner`, `next_action`, `artifact_hash`, `question_set_version`, `model?`, `usage?`. Keep status distinct from Jev confidence.

## Acceptance examples

- Claim: `The unit tests passed.` Output: `2 failed, 18 passed.` Local exit/output check returns `contradicted`. [Smoke-test case 4](../../../jev-try/jev-smoke-test-prompts.md#4-verify-a-completion-claim) exercised Jev connectivity, not the production decision path.
- Claim: `The suite passed.` Only a prose sentence is available. Result: `insufficient_evidence`; request the command result.
- Claim: `The worktree is clean.` A current local `git status --short` has no entries. Result: locally supported with command and timestamp.
- Claim: `All scenarios are behaviourally verified.` Test collection alone gives `insufficient_evidence`; use the requirement and test coverage skills for the missing semantic evidence.
- A green gate from before the last test edit yields `insufficient_evidence` for a current-green claim.
- A strict XPASS yields a diagnosis request; the deferral marker remains until the cause is resolved.
- An XPASS caused by duplicate coverage routes to Architect; one caused by pre-existing behaviour routes to Architect and Test Author.
