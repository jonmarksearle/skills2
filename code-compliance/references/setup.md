# Setup: regenerating the baked-in principle data

Not part of ordinary skill use — see [SKILL.md](../SKILL.md) for that. This is a separate,
occasional maintenance task: run it only when `Standards/CODE_STANDARDS.md`,
`Standards/CODE_STANDARDS.pytest.md`, or `Standards/CODE_STANDARDS.examples.md` change.

`scripts/jev_code_compliance.py` never reads those Standards files itself — everything it needs is
baked into `scripts/jev_code_compliance_data.json` ahead of time. That file, and the parallel
human-readable [jev_code_compliance.md](jev_code_compliance.md), are generated output. Do not
hand-edit either; regenerate them instead.

## Running it

From the project whose Standards changed (its `../Standards/CODE_STANDARDS*.md` are the defaults;
override with `--code-standards`/`--examples`/`--pytest-standard` if that project's Standards live
elsewhere):

```
uv run E:/work/.agents/skills/code-compliance/scripts/jev_define_compliance.py
```

This overwrites `scripts/jev_code_compliance_data.json` and `references/jev_code_compliance.md` in
place. Both outputs are shared across every project that uses this skill — there is one baked-in
table, not one per project.

## What it does

One principle per bullet point in the Standards, not one per section: a single bullet is a narrow,
self-contained judgment, closer to what ask-jev's own guidance calls for ("ask one narrow, coherent
judgment per question") than an entire multi-bullet section bundled into one question. A section
with no bullets (pure prose) becomes one whole-section principle instead, since there's nothing to
decompose. A bullet's worked example, when `CODE_STANDARDS.examples.md` has one for that section, is
referenced (`example_ref`) rather than copied — every bullet from a 17-bullet section cites the same
example once, not 17 separate copies of it.

Two tables in the JSON: `src_criteria`/`src_examples` (`CS-*`, from `CODE_STANDARDS.md`) and
`test_criteria`/`test_examples` (`PT-*`, from `CODE_STANDARDS.pytest.md`, which has no
section-by-section `CODE_STANDARDS.examples.md` counterpart).

## Verifying a change

After regenerating, spot-check: the principle count for the section you edited should have changed
by exactly the number of bullets you added or removed, and a negated bullet ("Avoid ...", "Do not
...", "Don't ...", "Never ...") should still read as a negation in its generated term — a prior bug
here silently reversed rules by stripping the negating word. `evaluations/criteria-table-regeneration.json`
exercises this end to end.
