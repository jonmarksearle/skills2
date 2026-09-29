---
name: ask-jev
description: Batch quick Jev judgments over shared evidence using Noul (yes/no), Choice (one of named options), and Score (ordered levels). Use when a user requests Jev or an agent needs several independent semantic evaluations outside a specialised review skill; report raw probabilities, uncertainty, and usage.
---

# Ask Jev

Use Jev as a fast judgment primitive. Its typed answers carry probabilities; local code and the responsible person own calculations, policy, and action. Follow [TypeSafe's live primitives guide](https://docs.typesafe.ai/primitives) when question or response shapes may have changed. The workspace [TypeSafe skill](../typesafe-ai/SKILL.md) has deeper design guidance.

## Build the batch

1. State the decision that the judgments will inform and gather the smallest cited evidence that answers it. Resolve exact counts, lookups, arithmetic, and known rules locally. Use public, synthetic, redacted, or explicitly authorised material when calling the external service. **Done when:** each proposed question has sufficient source evidence and a clear purpose.
2. Pick each answer shape:
   - **Noul:** one independently useful yes/no proposition; receive the probability of yes. Ask separate Nouls when several labels can all apply. Near 0.5 means uncertain truth, not medium intensity. When the yes/no line is fuzzy, name contrasting criteria for what clearly counts as yes and what clearly counts as no, so borderline cases don't all collapse into an uninformative 0.5.
   - **Choice:** one option from a closed set; describe what belongs to each option and include `none` or `other` when the set may be incomplete. Receive the winning option, every option's probability, and distribution confidence.
   - **Score:** a graded property on ordered, concrete levels. Receive a probability-weighted position, per-level probabilities, and distribution confidence. Ask comparable Scores per item or dimension, then combine weights locally.
   **Done when:** each question has one coherent judgment, stable ID, complete `instructions`, and meaningful `criteria` for its type.
3. Put independently answerable questions over the same compact `state` in one `questions` map. Mix primitives freely; questions in a batch cannot read each other's answers. Add a second request only when the first answer is needed to fetch evidence, form new state, or define new options. When judging several similar items against each other, give every item's question the same explicit rubric (shared criteria or Score levels) and enough contrasting context to place it, since none of them can see the others' answers to calibrate against. **Done when:** every needed judgment is in the first bounded request unless a real dependency is recorded.

## Call and interpret

4. Write a key-free JSON request with `state` and `questions` to a local temporary file. Check its structure first, e.g. `python -c "import json,sys; json.load(open(sys.argv[1]))" REQUEST.json`, since a malformed request fails opaquely at the helper. Run `bash E:/work/.agents/skills/tools/jev.sh REQUEST.json` from Git Bash; the helper handles execution details. Keep secrets out of the request, command arguments, logs, and answer. **Done when:** the response contains one typed answer per question plus model and usage; otherwise report the failed call without inventing answers.
5. Present the raw Noul values or Choice/Score distributions alongside the source span and a short interpretation. Treat `confidence` as distribution concentration, not correctness. Apply thresholds only when validated for the task, and don't default to 0.5 as the decision line: the right cutoff is application-specific, set by the cost of a false yes versus a false no for that task, and often sits well above or below the midpoint. Route uncertain or consequential judgments to a person or deeper review. Report request usage and cost when returned. Remove the temporary request after preserving any evidence the task requires. **Done when:** every requested judgment is answered or marked unavailable, and the user can see what Jev actually returned and what action remains theirs.

## Request shape

```json
{
  "state": {"message": "The parcel arrived broken; please replace it."},
  "questions": {
    "replacement_requested": {"type": "noul", "instructions": "Does `message` request a replacement?"},
    "request_kind": {"type": "choice", "instructions": "What is the main request in `message`?", "criteria": {"replacement": "A new item is requested", "refund": "Money back is requested", "other": "Neither request is expressed"}},
    "urgency": {"type": "score", "instructions": "How urgent is the need expressed in `message`?", "criteria": ["No time pressure stated", "Soon, but no deadline", "An explicit immediate deadline"]}
  }
}
```