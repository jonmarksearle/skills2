#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["typer"]
# ///

"""Score every construct in a Python file against the baked-in ask-jev principle tables.

Project-independent: point this at any project's `.py` file. Takes just the
target file -- the Standards content is baked into `jev_code_compliance_data.json`
by `jev_define_compliance.py`, so this script has no Standards file to locate
and no `--module-kind`/`--src-criteria`/`--test-criteria` to pass; it infers
src vs. test from the path and imports the rest.

Role-based principle selection: every construct in a src file gets the `src`
(general Python) principles. In a test file, a construct named `test*` gets
only the `test` (pytest) principles; a `@pytest.fixture`-decorated function
or any other helper gets both `test` and `src` principles, since a fixture or
helper is still ordinary Python code the general standard governs.

One Jev call per construct when its applicable principles fit comfortably
under jev.py's 64 KiB request cap; falls back to several size-safe batches
otherwise -- principle IDs are globally unique (`CS-*` vs `PT-*`), so every
batch's answers merge without collision regardless of which principles it mixed.
"""

from __future__ import annotations

import ast
import json
import subprocess
import tempfile
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypedDict, cast

import typer
from _jev_types import ConstructRow, Matrix, PrincipleInfo, ScoreAnswer

_DATA_FILE = Path(__file__).resolve().parent / "jev_code_compliance_data.json"
_JEV_PY = Path(__file__).resolve().parents[2] / "tools" / "jev.py"
_SAFE_REQUEST_BYTES = 60 * 1024
_REQUEST_HARD_LIMIT_BYTES = 64 * 1024
_SCORE_LEVELS = [
    "Not applicable: this standards point has no compliance-relevant rules for this construct",
    "Non-compliant: the construct clearly violates this standards point",
    "Partially compliant: the construct mostly follows this standards point but has at least one clear gap",
    "Fully compliant: the construct follows this standards point with no clear gap",
]

Role = Literal["src", "test", "fixture", "helper"]
ModuleKind = Literal["src", "test"]


@dataclass(frozen=True, slots=True)
class Criterion:
    id: str
    term: str
    label: str
    definition: str
    sources: tuple[str, ...]
    example_ref: str | None


@dataclass(frozen=True, slots=True)
class Construct:
    name: str
    kind: str
    role: Role


class CriterionRecord(TypedDict):
    """One principle exactly as stored in `jev_code_compliance_data.json`."""

    id: str
    term: str
    label: str
    definition: str
    sources: list[str]
    example_ref: str | None


class ComplianceData(TypedDict):
    """The whole baked-in JSON file's shape."""

    src_criteria: list[CriterionRecord]
    src_examples: dict[str, str]
    test_criteria: list[CriterionRecord]
    test_examples: dict[str, str]


@dataclass(frozen=True, slots=True)
class BakedPrinciples:
    """The tailored constructs fed to Jev, loaded once at import time.

    Tuples, not a lazy `Iterator`, because every construct's principle lookup
    reuses the same table -- genuine multi-pass consumption, the one case the
    Standards' "prefer Iterator" default yields to materialising at the edge.
    """

    src_criteria: tuple[Criterion, ...]
    test_criteria: tuple[Criterion, ...]
    examples: dict[str, str]


class ScoreQuestion(TypedDict):
    type: str
    instructions: str
    criteria: list[str]


class JevRequest(TypedDict):
    state: dict[str, object]
    questions: dict[str, ScoreQuestion]


class JevResponse(TypedDict):
    answers: dict[str, ScoreAnswer]


@dataclass(frozen=True, slots=True)
class Batch:
    """One size-safe group of principles to score together in a single Jev call."""

    criteria: tuple[Criterion, ...]


@dataclass(frozen=True, slots=True)
class BatchResult:
    answers: dict[str, ScoreAnswer]
    call_count: int


@dataclass(frozen=True, slots=True)
class PrincipleGroups:
    """Which named principle table(s) apply to a construct, and their union."""

    names: tuple[str, ...]
    criteria: tuple[Criterion, ...]


class TaskFields(TypedDict):
    """The fixed part of a Jev request's `state`. Not the whole of it: `state`
    also carries a variable number of `example_<ref>` keys, one per worked
    example the scored criteria cite, which no fixed TypedDict shape can
    express -- that part is why `_build_state` still returns a plain dict."""

    task: str
    construct_name: str
    module_file: str


def _criteria_from(records: Sequence[CriterionRecord]) -> Iterator[Criterion]:
    return (
        Criterion(
            id=record["id"],
            term=record["term"],
            label=record["label"],
            definition=record["definition"],
            sources=tuple(record["sources"]),
            example_ref=record["example_ref"],
        )
        for record in records
    )


def _load_baked_principles() -> BakedPrinciples:
    """Everything `jev_code_compliance.py` needs to score a construct, read once
    from this script's own JSON -- no Standards file to locate at scoring time."""
    payload = cast(ComplianceData, json.loads(_DATA_FILE.read_text(encoding="utf-8")))
    return BakedPrinciples(
        src_criteria=tuple(_criteria_from(payload["src_criteria"])),
        test_criteria=tuple(_criteria_from(payload["test_criteria"])),
        examples={**payload["src_examples"], **payload["test_examples"]},
    )


_BAKED = _load_baked_principles()


def detect_module_kind(path: Path) -> ModuleKind:
    """A file under a `tests` directory, or named `test_*`, is a test file; else src."""
    if "tests" in path.parts or path.stem.startswith("test_"):
        return "test"
    return "src"


def _is_fixture(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any("fixture" in ast.unparse(decorator) for decorator in node.decorator_list)


def _classify(node: ast.AST, module_kind: ModuleKind) -> Role:
    if module_kind == "src":
        return "src"
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return "helper"
    if node.name.startswith("test"):
        return "test"
    if _is_fixture(node):
        return "fixture"
    return "helper"


def iter_constructs(path: Path, module_kind: ModuleKind) -> Iterator[Construct]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            kind = "class" if isinstance(node, ast.ClassDef) else "function"
            yield Construct(node.name, kind, _classify(node, module_kind))


def criteria_groups_for(construct: Construct) -> PrincipleGroups:
    """Which principle table(s) apply to this construct, per the role rules above."""
    if construct.role == "src":
        return PrincipleGroups(("src",), _BAKED.src_criteria)
    if construct.role == "test":
        return PrincipleGroups(("test",), _BAKED.test_criteria)
    return PrincipleGroups(
        ("test", "src"), (*_BAKED.test_criteria, *_BAKED.src_criteria)
    )


def _instructions_for(criterion: Criterion) -> str:
    """`[id] term: definition`, plus an example pointer -- no per-question restatement
    of "how well does the construct comply", which is fixed once in `state["task"]`.
    `term` and `definition` carry different text for a whole-section fallback criterion
    (a short name vs the full section body), but are the same text for a bullet-derived
    one; repeating a bullet as its own "term" would just resend it, so `term` is skipped
    there and `definition` alone carries the principle."""
    header = (
        criterion.id
        if criterion.term == criterion.definition
        else f"{criterion.id} {criterion.term}"
    )
    example_note = (
        f" (see `example_{criterion.example_ref}`)"
        if criterion.example_ref is not None
        else ""
    )
    return f"[{header}] {criterion.definition}{example_note}"


def _used_example_refs(criteria: Sequence[Criterion]) -> Iterator[str]:
    return (
        criterion.example_ref
        for criterion in criteria
        if criterion.example_ref is not None
    )


def _build_state(
    construct: Construct, criteria: Sequence[Criterion], module_text: str
) -> dict[str, object]:
    """A plain dict, not a `TypedDict`: on top of `TaskFields`' fixed keys, this
    carries a variable number of `example_<ref>` keys, one per worked example
    `criteria` cites, which no fixed shape can express."""
    fields = TaskFields(
        task=(
            f"Score how well the {construct.kind} named `construct_name`, defined in "
            "`module_file`, complies with each principle below."
        ),
        construct_name=construct.name,
        module_file=module_text,
    )
    examples = {
        f"example_{ref}": _BAKED.examples[ref] for ref in _used_example_refs(criteria)
    }
    return {**fields, **examples}


def _build_questions(criteria: Sequence[Criterion]) -> dict[str, ScoreQuestion]:
    """`dict`, not `Mapping`: this feeds `JevRequest.questions`, itself a `dict`-typed
    field (for JSON output), so a `Mapping` return wouldn't satisfy it. The value
    type, `ScoreQuestion`, is the part that actually needed fixing; the container
    was already correct."""
    return {
        criterion.id: ScoreQuestion(
            type="score",
            instructions=_instructions_for(criterion),
            criteria=_SCORE_LEVELS,
        )
        for criterion in criteria
    }


def _build_request(
    construct: Construct, criteria: Sequence[Criterion], module_text: str
) -> JevRequest:
    """`criteria` is read twice (once for its example refs, once for its questions),
    so this takes a `Sequence`, not a one-shot `Iterable`."""
    return JevRequest(
        state=_build_state(construct, criteria, module_text),
        questions=_build_questions(criteria),
    )


def _request_size(request: JevRequest) -> int:
    return len(json.dumps(request, ensure_ascii=False).encode("utf-8"))


def _call_jev(request: JevRequest) -> JevResponse:
    """Submit one bounded request; the response is JSON, an unavoidable typing boundary."""
    size = _request_size(request)
    if size > _REQUEST_HARD_LIMIT_BYTES:
        raise ValueError(f"Request is {size} bytes; exceeds jev.py's 64 KiB cap.")
    payload = json.dumps(request, ensure_ascii=False)
    with tempfile.NamedTemporaryFile(
        "w", suffix=".json", delete=False, encoding="utf-8"
    ) as handle:
        handle.write(payload)
        request_path = Path(handle.name)
    try:
        result = subprocess.run(
            ["uv", "run", "--script", str(_JEV_PY), str(request_path)],
            capture_output=True,
            text=True,
            check=True,
        )
    finally:
        request_path.unlink(missing_ok=True)
    return cast(JevResponse, json.loads(result.stdout))


def not_applicable_probability(answer: ScoreAnswer) -> float:
    """The chance this standards point does not apply, read from level 0's probability."""
    return answer["probabilities"]["0"]


def _fits(
    batch: Batch, criterion: Criterion, module_text: str, construct: Construct
) -> bool:
    """Whether adding `criterion` to `batch` keeps the request under the safe size."""
    candidate = (*batch.criteria, criterion)
    return (
        _request_size(_build_request(construct, candidate, module_text))
        <= _SAFE_REQUEST_BYTES
    )


def _size_safe_batches(
    criteria: Iterable[Criterion], module_text: str, construct: Construct
) -> Iterator[Batch]:
    """Greedily pack `criteria` so every batch's request stays under the safe size.

    A single `src` table (131 principles, 16 worked examples) is already
    ~100 KB on its own -- too big for one call regardless of which other
    criteria it's grouped with -- so batching is size-driven across the
    whole applicable set, not "one call per named group". This is also the
    mechanism that puts a fixture or helper's `test` and `src` criteria
    through separate calls when combined they don't fit: whichever criteria
    land in the same batch share one call; the rest wait for the next batch.

    Not a comprehension: each decision depends on the running batch's size so
    far, which a comprehension has no way to thread through. `_fits` carries
    the one per-step judgment; this loop only sequences it. Yields `Batch`,
    not a bare `tuple`, so a batch of criteria reads as the named thing it is.
    """
    batch = Batch(())
    for criterion in criteria:
        if batch.criteria and not _fits(batch, criterion, module_text, construct):
            yield batch
            batch = Batch((criterion,))
        else:
            batch = Batch((*batch.criteria, criterion))
    if batch.criteria:
        yield batch


def _answers_for_construct(construct: Construct, module_text: str) -> BatchResult:
    """One call per size-safe batch across every applicable principle.

    Principle IDs are globally unique across the `src` and `test` tables
    (`CS-*` vs `PT-*`), so batches' answers merge directly with no key
    collision to resolve, whichever principle groups a batch mixed together.
    """
    all_criteria = criteria_groups_for(construct).criteria
    merged: dict[str, ScoreAnswer] = {}
    calls = 0
    for batch in _size_safe_batches(all_criteria, module_text, construct):
        merged.update(
            _call_jev(_build_request(construct, batch.criteria, module_text))["answers"]
        )
        calls += 1
    return BatchResult(answers=merged, call_count=calls)


def build_matrix(module_file: Path) -> Matrix:
    """Score every top-level construct in `module_file` against its applicable principles."""
    module_kind = detect_module_kind(module_file)
    module_text = module_file.read_text(encoding="utf-8")
    all_criteria_by_id = {
        c.id: c for c in (*_BAKED.src_criteria, *_BAKED.test_criteria)
    }
    constructs = list(iter_constructs(module_file, module_kind))
    rows: dict[str, ConstructRow] = {}
    total_calls = 0
    used_ids: set[str] = set()
    for construct in constructs:
        result = _answers_for_construct(construct, module_text)
        total_calls += result.call_count
        used_ids.update(result.answers)
        rows[construct.name] = ConstructRow(
            kind=construct.kind,
            role=construct.role,
            criteria_groups=list(criteria_groups_for(construct).names),
            answers=result.answers,
        )
    principles = {
        criterion_id: PrincipleInfo(
            term=all_criteria_by_id[criterion_id].term,
            sources=list(all_criteria_by_id[criterion_id].sources),
        )
        for criterion_id in sorted(used_ids)
    }
    return Matrix(
        module_file=str(module_file),
        principles=principles,
        jev_call_count=total_calls,
        rows=rows,
    )


app = typer.Typer(add_completion=False)


@app.command()
def main(
    module_file: Path = typer.Argument(..., help="The .py file to score"),  # noqa: B008
    out: Path = typer.Option(..., help="Where to write the scoring matrix JSON"),  # noqa: B008
) -> None:
    matrix = build_matrix(module_file)
    out.write_text(json.dumps(matrix, indent=2, ensure_ascii=False), encoding="utf-8")
    criteria_count = sum(len(row["answers"]) for row in matrix["rows"].values())
    print(
        f"Wrote {len(matrix['rows'])} constructs, {criteria_count} scored points, "
        f"{matrix['jev_call_count']} Jev calls, to {out}"
    )


if __name__ == "__main__":
    app()
