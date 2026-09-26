---
name: check-test-definition-coverage
description: Check whether a module's pytest tests verify every named TDD test definition and obey semantic pytest rules before approval or deferral.
---

# check-test-definition-coverage

## Invocation

Invoke at Test Writing Tiptoe B for changed tests and run a complete module pass before Tiptoe F defers the approved set. Re-run affected definitions when an implementation change reveals a gap. The unit is one module's TDD definitions and tests. Follow [TDD_PROCESS.md](../../../Standards/TDD_PROCESS.md#module-tdd-structure) and [CODE_STANDARDS.pytest.md](../../../Standards/CODE_STANDARDS.pytest.md#what-tests-must-cover).

## Input and evidence

- All module TDD test definitions, allocated RDD IDs, and the public operations, errors, constraints, or invariants they promise to verify.
- All candidate pytest test functions and used fixtures, with directly relevant contract excerpts and source lines.
- Local facts: test names, decorators, `pytest.raises(..., match=...)` presence, executable line counts, and strict xfail state. Include only facts relevant to a judgment.

Build a local definition-to-test map in both directions. Report a definition with no test as `no_candidate_test`. For each meaningful happy-path definition, identify corresponding failure and explicit edge-case definitions where applicable under the pytest standard; a missing definition goes to the Architect. Route a test with no definition to the Architect to determine whether the TDD needs a definition or the test is redundant. An unavailable required fixture yields `insufficient_evidence` for affected tests.

## Execute with Jev

Follow [ask-jev](../ask-jev/SKILL.md) for typed request shape and interpretation. Run `bash E:/work/.agents/skills/tools/jev.sh REQUEST.json` with a key-free local request. On failure, mark semantic judgments `not_run`; never invent probabilities.

Put the cited source excerpts and definitions in a compact state. Ask independent questions together in one request; give each question its full meaning, explicit criteria, and stable local ID. Use Noul for each independent suspected defect, Choice for exclusive statuses, and Score for ordered dimensions. Retain raw answers, distributions, model, question version, usage, artifact hash, and source spans. A typed response is not an approved disposition. Apply the rule-specific calibration and cost plan at [skills-evaluation-plan.md](../../../jev-try/skills-evaluation-plan.md); until a gate is approved, route semantic findings to the named reviewer or owner.

Follow the applicable Standards and project-local `AGENTS.md` before changing an artifact. This skill drafts findings and handoffs; the responsible process role approves changes and gates. Check every reported finding against the actual cited passage before handing it off.

## Judgment and workflow

1. Resolve each definition's required state, action, and observable assertions. Collect candidate tests and their executed fixture setup. Map happy-path definitions to applicable failure and edge-case definitions. **Done when:** every definition and test has a mapping status and every meaningful happy path has an accounted-for failure/edge counterpart or an explicit reason none applies.
2. At Tiptoe B ask the coverage Choice and applicable yes/no defect questions only for changed tests and their definitions. Before Tiptoe F, ask one Jev Choice for every definition: `fully_verified`, `partly_verified`, `not_verified`, `contradictory`, or `insufficient_evidence`, and for each test ask applicable defect questions for `assertion_mismatch`, `fixture_hides_required_state`, `implementation_detail_dependency`, `multiple_behaviours`, `mocks_internal`, and `success_side_effect_unasserted`. Pool over a relevant module state where supported; partition by test group for tool limits or context relevance. **Done when:** each selected definition and applicable test has typed judgments and usage.
3. Inspect findings against test lines and diagnose their source. Return draft `{file}.review.{n}.md` entries to the Test Reviewer at Tiptoe B; the Reviewer owns the review. Through the review-response cycle, an imprecise test goes to Test Author, while a missing definition or SDD allocation goes to Architect and may call [check-requirement-preservation](../check-requirement-preservation/SKILL.md). Report mechanical violations separately. **Done when:** every gap has an exact missing setup or assertion, root cause, reviewer-visible entry, and next owner.

The skill reviews the written test; pytest execution remains a separate quality gate. Strict xfail is a test state, not a reason to claim the defined behaviour is already implemented. A passing test with a weak assertion can still be `partly_verified`.

## Result contract

`module`, `pass_type: changed_tests|full_pre_deferral`, `definition_pairing`, `coverage_matrix[{definition_id, candidate_tests, choice, probabilities, confidence, triage: finding|clear|inspect, missing_setup_or_assertion}]`, `test_defects[{test_name, judgments, triage, source_spans}]`, `unmapped_tests`, `mechanical_findings`, `findings[{root_cause, next_owner}]`, `review_draft`, `artifact_hash`, `question_set_version`, `model`, `usage`.

## Acceptance examples

- A test asserts only that an error was raised, while the definition requires unchanged state after failure: `partly_verified`, naming the missing state assertion.
- A test uses a permissive error assertion when the contract specifies a distinct message: local `match=` check and semantic result both identify the gap without conflating them.
- A test that supplies the required setup and asserts the promised observable result: `fully_verified` for the cited definition.
- A test whose fixture is omitted from the supplied state: `insufficient_evidence`.
- Two semantically unrelated outcomes in one test flag `multiple_behaviours` even if its name and line count pass local checks.
- A test absent from the TDD mapping reaches Architect review before the approved set is deferred with strict xfail.
- A meaningful happy-path definition with no applicable failure definition produces an Architect finding during the full pass.
