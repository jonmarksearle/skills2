---
name: code-compliance
description: Score a Python file's constructs against predefined ask-jev principle tables (decomposed from CODE_STANDARDS.md and CODE_STANDARDS.pytest.md, one principle per bullet, worked examples included) and produce a compliance report of candidate gaps. Project-independent -- point it at any project's .py file. Use at a module's Outer Refactoring gate after its tests are green, before moving to the next module.
---

# code-compliance

## Invocation

Invoke at each module's Outer Refactoring gate (TDD_PROCESS.md), after that module's Code Reviewer
gate has passed and before starting the next module. Run it once per audited file: the module's
production source file(s) and its test file. Follow
[TDD_PROCESS.md](../../../Standards/TDD_PROCESS.md) and
[CODE_STANDARDS.md](../../../Standards/CODE_STANDARDS.md).

This replaces hand-running `jq`/`ask-jev` against the raw Standards documents. The tables and
batching it depends on exist because that approach doesn't scale: a full `CODE_STANDARDS.md` +
`CODE_STANDARDS.examples.md` pass is too large for one Jev request regardless of how it's split, and
asking one construct about a whole multi-bullet section produces low-confidence noise instead of a
real judgment. This skill's tools already solve both problems; do not re-derive the mechanism.

## Run the audit

Score the target file, then render its report:

```
uv run E:/work/.agents/skills/code-compliance/scripts/jev_code_compliance.py \
  <path/to/module.py> --out <tmp>/matrix.json
uv run E:/work/.agents/skills/code-compliance/scripts/jev_code_compliance_report.py \
  --matrix <tmp>/matrix.json --out <path/to/module.py>.jev.compliance-report.{n}.md
```

`jev_code_compliance.py` takes only the target file: it infers src vs. test from the path (a file
under a `tests` directory, or named `test_*`, is a test file) and already has the Standards content
baked in, so there is no criteria file or Standards path to pass. A `test*`-named function is scored
only against `test` (pytest) principles; a `@pytest.fixture`-decorated function or any other
test-file helper, including a support class, is scored against both `test` and `src` principles,
since it is still ordinary Python the general standard governs.

Write the report next to the audited file, incrementing `{n}` on a re-run so an earlier report stays
as review evidence instead of being overwritten.

## Read the report

Each report has three sections. **Principles** lists every principle this run actually scored: its
ID, a short plain-English term, and which Standards document(s) it cites — the legend the other two
tables cite by ID rather than repeating. **Needs inspection** lists every construct/principle pair
the model judged probably applicable, not clearly compliant, and scored with real confidence, sorted
worst-first by an attention score. A **Full matrix** appendix follows, grouped by which principles
applied to each construct (src constructs and test-file helpers see different principle sets than
`test*` functions).

Every row is a model judgment, not a finding. Score runs 0 (not applicable) to 3 (fully compliant); a
low score paired with a high not-applicable probability means the principle probably doesn't apply to
that construct, not that it's violated. The report's `Applicability` column and the "Needs
inspection" filter already screen for likely-applicable, confidently-scored rows; still treat every
row as a lead, never a verdict, until checked against the real source.

## Judgment and workflow

1. Open "Needs inspection". For each flagged row, look up the cited principle's ID in
   [jev_code_compliance.md](references/jev_code_compliance.md) for its full definition, then read
   the actual construct in the audited file. **Done when:** every flagged row has been checked
   against real source, not decided from the report table alone.
2. Confirm or dismiss each flagged row. A confirmed gap gets fixed in a normal Refactor step (green
   stays green; rerun the module's format/lint/type/pytest gate after each fix). A dismissed row is a
   model miss, not a defect: leave the code unchanged. If one principle keeps producing dismissed
   flags across several constructs, that is a signal to reconsider its definition (see
   [references/setup.md](references/setup.md)), not a code problem to chase. **Done when:** every
   flagged row has a recorded disposition and every confirmed gap is fixed.
3. Preserve each report as review evidence; a later run for the same file gets a new `{n}`, not an
   overwrite. Close the module's Outer Refactoring gate once every confirmed gap from both its src
   and test reports is fixed and the module's quality gate is green. **Done when:** the module's row
   in the feature implementation plan is checked off and the next module can start.

## Result contract

One `{file}.jev.compliance-report.{n}.md` per audited src or test file, self-contained: a Principles
legend, a Needs-inspection table (construct, principle ID, score, confidence, applicability), and a
full matrix. The matrix JSON passed via `--out` to `jev_code_compliance.py` is disposable working
data between the two scripts, not evidence to keep on its own.

## Acceptance examples

- A function scores low on a principle at confidence 0.8, applicability 0.95: a real, worth-checking
  candidate gap.
- A function scores low on a principle at confidence 0.1: the model couldn't form an opinion; dismiss
  it as a miss. If the same principle does this across most of a module, its definition is probably
  too broad for construct-level judgment (a codebase-wide principle like "Write Tests for
  Everything"), not a defect in every construct it touched.
- A `test_*` function is never scored against `CODE_STANDARDS.md`'s general Python principles; a
  `@pytest.fixture` function in the same file is scored against both tables.
- A src-only file's audit costs at least two Jev calls per construct even for a small file, because
  the full `src` principle table (131 principles, every worked example, at full fidelity) does not
  fit in one request; this is expected, not a bug to chase by shortening the principles.

## Setup and evaluations

The principle tables are already baked in; regenerating them (only needed after a Standards edit) is
a separate, occasional task, not part of ordinary use — see
[references/setup.md](references/setup.md). [evaluations/](evaluations/README.md) has scenario-based
checks of role classification, report structure, and the generator's behaviour on a Standards edit.
