# Reliability audit: finding where Jev can't judge a principle

Not part of ordinary skill use — see [SKILL.md](../SKILL.md) for that. This is a separate,
occasional investigation: run it when a principle keeps producing dismissed or no-confidence flags
and you need to know whether that is one unlucky construct or a real blind spot in how Jev scores
that principle.

## Why this exists

Some principle/construct combinations produce weak or no signal from Jev regardless of which way
the code actually goes. But "weak signal in a real audit" has at least two different causes, and
they need different fixes — conflating them wastes effort. Confirmed today with paired before/after
evidence, not assumption:

- **Genuine wording problem.** `CS-12-02` ("avoid `Any`/`object`") on `_build_state` scored
  confidence 0.00 with `state: dict[str, object]` in the signature and confidence 0.37 after
  changing it to `dict[str, str]`, *even tested in isolation* (a single-criterion request, no other
  principles competing for attention). The principle's baked-in wording — the Standards bullet
  verbatim, plus a generic whole-section worked example — genuinely didn't give the model enough to
  work with. Fixed; see "Confirmed wording fixes" below.
- **Batch dilution, not wording.** `CS-08-08` ("prefer `Iterator[T]` over concrete containers") on
  `_decompose_section` scored confidence 0.00 in the real, full-file, ~30-principle-per-call audit —
  looked identical to a wording blind spot. But the *same, unmodified* wording tested in isolation
  (one criterion, one request) scored confidence 0.49 on the violating version and 0.87 on the fixed
  one — a strong, correctly-directed signal. Nothing was wrong with this principle's wording; bundling
  it with ~20+ other criteria in one request was enough on its own to erase the signal. This needs a
  batching-strategy fix (smaller batches, or fewer principles per call), not a wording fix — and a
  wording fix would not have caught it, which is exactly why step 2 of the procedure below insists on
  isolation before you conclude anything.

This is the reason the procedure below is single-criterion and isolated by default: a full-audit
comparison alone cannot tell you which of these two you're looking at.

## When to run this

Not after one borderline flag — a single 2.3–2.5 score at confidence 0.3–0.5 is ordinary noise (see
SKILL.md's Acceptance examples) and does not by itself justify this audit. Run it when:

- The same principle produces weak or no-confidence results across most constructs in a file's
  Needs Inspection table, or
- You changed code specifically to satisfy a principle, re-ran the audit, and the score did not
  move the way a compliance fix should move it (up, with confidence, on that construct).

## Procedure

Do this with single-criterion requests, never a full-file audit rerun — a full audit re-scores
every principle against every construct and wastes calls on everything except the one comparison
you need.

1. **Get two real versions of the same construct**, one that clearly violates the candidate
   principle and one that clearly complies. Prefer two genuine states of the same code — a `git
   show <commit>:<path>` of the pre-fix version plus the current post-fix file, or a deliberate
   revert of just the change in question — over a synthesized strawman. A synthetic example that is
   exaggeratedly bad or exaggeratedly clean can bias the result; a real fix's before/after pair is
   the fairer test.

2. **Isolate one criterion.** Import `jev_code_compliance.py` as a module (it is on `scripts/`'s own
   path) and find the target `Criterion` from `jcc._BAKED.src_criteria` (or `.test_criteria`) by its
   `id`. Do not use the CLI here — it batches every applicable principle per construct, which is the
   right behaviour for a real audit and the wrong behaviour for isolating one principle's signal.

3. **Build and send one request per (version, construct) pair** using the runner's own
   `Construct`, `_build_request`, and `_call_jev` — the same request shape the real audit uses, so
   the comparison is apples-to-apples with what a real run would send:

   ```python
   import sys
   sys.path.insert(0, r"E:\work\.agents\skills\code-compliance\scripts")
   import jev_code_compliance as jcc

   criterion = next(c for c in jcc._BAKED.src_criteria if c.id == "CS-12-02")
   construct = jcc.Construct(name="_build_state", kind="function", role="src")

   for label, module_text in [("before", before_text), ("after", after_text)]:
       request = jcc._build_request(construct, (criterion,), module_text)
       answer = jcc._call_jev(request)["answers"][criterion.id]
       print(label, answer["score"], answer["confidence"])
   ```

   `module_text` is the whole file's source in each state, not just the construct's own body — Jev
   scores the named construct in the context of the full file, same as a real audit does. Six calls
   (three constructs × two versions) is a typical, cheap size for this kind of check; do not expand
   the construct list beyond what the original flag actually named.

4. **Classify the result:**
   - **Reliable**: confidence clears ~0.3 on at least the violating version, and the score moves in
     the expected direction between versions (down toward 0–1 for the violation, up toward 2.5–3
     for the fix). Trust this principle's flags for this construct shape; no further action.
   - **Batch dilution**: confidence is weak or zero in a real full-file audit but clears ~0.3 with
     the *same, unmodified* wording once isolated. Not a wording problem — do not touch the JSON for
     this one. Record it as a batching case; the real fix is a smaller batch size or fewer principles
     per call, out of scope for this doc.
   - **Genuine blind spot**: confidence stays under ~0.3 even in isolation, or the score barely moves
     despite an unambiguous code change. Try tightening the wording (step 5) before giving up on it.

5. **If it's a genuine blind spot, try tightening the wording before falling back to a static
   check.** Build a variant `instructions` string by hand (bypass `_instructions_for` — construct the
   string directly so you control exactly what's sent) and re-run the same before/after pair against
   it. What has actually worked, cheapest first:
   - Dropping the shared whole-section example (`example_note`) if it's generic relative to this one
     bullet — it can dilute rather than help.
   - Adding one concrete `Bad: <code snippet>` example specific to this bullet, plus one short
     plain-language checkable rule ("flag X in the construct; absence of X is compliant"). This is
     the combination that has actually worked — a bad-example anchor plus a checkable rule, nothing
     more. A tight version *without* the bad snippet reliably confirms compliance but not violations,
     which is backwards for a tool whose job is flagging violations — don't drop the bad snippet to
     save length.
   - Verify a promising variant survives being batched with ~10–15 other real criteria from the same
     table before trusting it — an isolated-only win can still evaporate in the size a real audit
     actually sends.
   Once a variant is confirmed reliable isolated, batched, and in a real full-file audit run, apply
   it to `scripts/jev_code_compliance_data.json`'s `definition` field for that criterion. **This file
   is generated** — `jev_define_compliance.py` overwrites it from `CODE_STANDARDS.md` with no field
   for this kind of judge-tuning text, so a hand-edit here is silently lost on the next regeneration.
   As of today that tension is unresolved by design (deliberately deferred, not an oversight) — every
   hand-patched criterion must be listed below so a future regeneration doesn't lose it unnoticed.

6. **Record every result** — reliable, batch-dilution, blind spot, or fixed — in the tables below,
   with the evidence, so the next audit of a similar construct doesn't re-run the same question from
   zero.

## Confirmed wording fixes (hand-patched into `jev_code_compliance_data.json`)

**⚠ These are hand-edits to a generated file and will be silently lost on the next
`jev_define_compliance.py` regeneration** (see step 5). Re-apply from this table after any
regeneration until a durable storage mechanism exists.

Real "before" text for every row below is git's pre-session commit (`d1cf87d`) of the file in
question, not a synthesized strawman — `git show d1cf87d:./scripts/<file>.py`.

Each was tightened a second time after the first pass — dropping the "good" example and explanatory
prose that the first version included, keeping only the `Bad:` snippet and the checkable rule (see
step 5). Shorter and at least as reliable in every case tested; the table shows the current (lean)
wording and its evidence, with the shrink noted.

| Principle | Construct | Change | Evidence |
| --- | --- | --- | --- |
| `CS-12-02` | `_build_state` | `definition` appended (206 chars added, down from an initial 273-char version with a "good" example and prose): `" Bad: `def f(x: object) -> None: ...`. Flag a literal `Any`/`object` in any annotation; absent is compliant."` | Isolated: 1.21/conf 0.74 → 2.91/conf 0.91 (both better than the longer first version). Real full-file self-audit of `jev_code_compliance.py`: `_build_state` 2.67/conf 0.67 (was 0.15 pre-fix). |
| `CS-08-18` (mutating containers) | `_role_groups` | `definition` appended (283 chars, down from 595): `" Bad: `d.setdefault(k, []).append(x)`. Flag `.append/.extend/.update/.add/.insert()` or `d[k] = v` mutating after creation; none present is compliant."` | Isolated: 1.10/conf 0.85 → 2.85/conf 0.85 (both better than the longer version, up from 2.02/conf **0.02** unmodified). Real full-file self-audit of `jev_code_compliance_report.py`: `_role_groups` 2.80/conf 0.80. |
| `CS-07-07` (break up nested loops) | `_iter_cells` | `definition` appended (217 chars, down from 766 — dropped the "good" example entirely): `" Bad: `(f(a, b) for a in xs for b in ys(a))` or nested `for`/`if`. Flag 2+ nested iteration/conditional levels not split into a helper; 1 level is compliant."` | Isolated: 1.06/conf 0.92 → 2.83/conf 0.83 (matches the longer version at under a third the length), up from 2.25/conf 0.25 unmodified. Real full-file self-audit: `_iter_cells` 2.73/conf 0.73, `_row_cells` (the extracted helper) 2.73/conf 0.73. |

### A fix that works isolated but doesn't survive the real batch

| Principle | Construct | Change | Evidence |
| --- | --- | --- | --- |
| `CS-05-01` (FP/OOP blend, purity) | `_build_table` | `definition` appended (502 chars): `" Bad: `r = []` (or `{}`/`set()`) followed by a loop that calls `.append()`/`.extend()`/`.update()`/`[key] = value` on it to build the return value. Flag any construct containing that pattern; a construct with no such empty-container-then-loop-mutation pattern is compliant..."` | Isolated: 1.64/conf **0.32** → 2.89/conf **0.89** — a genuinely reliable result on its own, up from conf 0.00/wrong-direction with unmodified wording. But the **real full-file self-audit** (batched with ~25 other criteria) gave `_build_table` only 2.06/conf **0.06** — barely above the 0.00 it scored before this wording change at all. This principle survives isolation but not the real batch size; skipped the intermediate 15-criteria batch check this fix would have needed before calling it done, and that check would have caught this. Left the improved wording in place (it can't make things worse, and may help in a different batch composition) but it has **not** resolved the real-world symptom — do not report this as fixed. |

## Confirmed batch-dilution cases (wording is fine — do not edit)

| Principle | Construct shape | Evidence |
| --- | --- | --- |
| `CS-08-08` | Small module-local generator/helper function (`_decompose_section`) | Real full-file audit: confidence 0.00. Isolated, same unmodified wording: 0.49/conf on the `list[Criterion]`-returning version, 0.87/conf on the `Iterator[Criterion]`-returning fix. Needs a batching-strategy fix, not a wording fix. |

## Confirmed genuine blind spots (isolated, wording tried, still weak or wrong-directioned)

| Principle | Construct shape | Evidence |
| --- | --- | --- |
| `CS-08-01` (iterator pipelines, materialised contracts not preferred) | `_build_table`, mutation loop vs. its pure/comprehension equivalent | Unmodified wording: conf 0.24 → conf 0.23 (correct direction, real 1.47-point score swing, confidence never clears 0.3). A retried, more mechanical `Bad:`-snippet variant (same recipe that worked for `CS-05-01` on this exact construct) made it *worse*: conf dropped to **0.00** and not-applicable probability rose to **0.57** — the model increasingly reads this principle as not applicable to `_build_table` at all, in either version. Likely a construct mismatch, not a wording gap: `_build_table`'s own outer contract is a legitimately materialized `CriteriaTable` regardless of which version, and this principle's own definition carries a materialized-contract exception clause — the internal mutation-to-comprehension rewrite never touched the part of the construct this principle actually judges. Don't keep tuning wording here; test this principle against a construct whose own return type is supposed to be an iterator instead. |
| `CS-08-01` (same) | `render_report`, `lines` list-literal-with-splat vs. `itertools.chain` | Isolated, unmodified wording: conf 0.48 (list literal) → conf 0.56 (chain) — decent confidence both sides, but the score barely moved and went the *wrong* direction (2.34 → 2.28). Plausible explanation: `[*a, *b, *c]` is a reasonably idiomatic single-expression construction already, so this may not have been as clear a violation as assumed going in — not chasing a wording fix to manufacture a flag for a marginal style call. |

## Not a finding — mismatched principle/construct pairing

`CS-09-04` ("prefer `Iterator[T]` whenever possible") was tested against `_build_table`'s mutation-loop
vs. comprehension rewrite and scored confidently *low* on both versions (0.28/conf 0.72, then 0.75/conf
0.25). This is not evidence of anything: `_build_table`'s own return type is `CriteriaTable` in both
versions, unchanged by the internal mutation-to-comprehension rewrite — the principle is about a
function's own return-type contract, which this fix never touched. Picked the wrong construct to test
this principle against; not a real data point either way.

If a principle accumulates several confirmed (isolated) blind-spot rows across unrelated construct
shapes, that is itself a signal its Standards definition may be too structural or too abstract for
per-construct scoring (compare `CS-00-13`, "Write Tests for Everything", already known to be file-
or module-scale, not construct-scale) — worth raising as a candidate for
`jev_define_compliance.py`'s decomposition, not something to keep re-testing construct by construct.
