# Code Compliance Skill Evaluations

Evaluation scenarios for the `code-compliance` skill, grounded in the module it was actually built
and run against (`beansmeans`'s `period_state` module).

## Evaluation Files

### src-outer-refactoring-audit.json
Tests the basic src-file audit path: run the tool chain, produce a report, present it as leads for
a human to check, not as confirmed defects.

### test-file-role-based-scoring.json
Tests the part most likely to regress silently: role classification. A `test*` function, a
`@pytest.fixture` function, and a plain support class must each get the right principle set, and a
fixture sharing a name with a real function in the src file must not be confused with it.

### criteria-table-regeneration.json
Tests the principle-table generator itself after a Standards edit: one principle per bullet, no
duplicated example text, and no reversed-meaning terms on negated bullets.

## Running Evaluations

1. Enable the `code-compliance` skill.
2. Submit the query from the evaluation file, with the stated context true of the working repo.
3. Check every `expected_behavior` and `success_criteria` item against what actually happened:
   the commands run, the files written, and their content -- not against what the report claims
   about itself.
4. Record which items held and which didn't; a partial pass still needs every unmet item named.

## Example Success Criteria

**Good** (specific, testable): "No test_*-named function's row set includes any CS-* principle ID."

**Bad** (vague, untestable): "Test functions are scored correctly."

## Creating New Evaluations

When adding an evaluation, ground it in a real file in a real project rather than a hypothetical one
-- this skill's behaviour (batching, role classification, example deduplication) only shows up
against actual Standards documents and actual construct shapes, not a synthetic one-liner.
