#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["typer"]
# ///

"""Render a Markdown report from a `jev_code_compliance.py` scoring matrix.

Cites principles by their stable ID (`CS-07-01`, `PT-02-03`, ...) rather than
repeating each one's full term or definition in every row -- see the
code-compliance skill's `references/jev_code_compliance.md` for what an ID means.

Three sections: "Principles" lists every principle this report actually
used (ID, a short plain-English term, and which Standards document(s) it
cites) as a legend for the tables that follow. "Needs inspection" lists
every (construct, principle) cell where the principle is probably
applicable but the construct is not clearly compliant, or the model itself
was unsure -- sorted by an attention score (`(3 - score) * confidence *
applicability`, worst first) so the top rows are the most worth a human's
time. A full-matrix appendix follows, one table per role group, since
`test*` constructs are scored against different principles than fixtures,
helpers, and src constructs (see `jev_code_compliance.py`'s role rules).
"""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from typing import cast

import typer

from _jev_types import ConstructRow, LintReport, Matrix, PrincipleInfo

_NOT_APPLICABLE_THRESHOLD = 0.5
_LOW_SCORE_THRESHOLD = 2.5
_MIN_TRUSTED_CONFIDENCE = 0.3


@dataclass(frozen=True, slots=True)
class Cell:
    construct: str
    criterion_id: str
    score: float
    confidence: float
    not_applicable_probability: float


def _row_cells(construct: str, row: ConstructRow) -> Iterator[Cell]:
    """Every scored cell for one construct's row."""
    return (
        Cell(
            construct=construct,
            criterion_id=criterion_id,
            score=answer["score"],
            confidence=answer["confidence"],
            not_applicable_probability=answer["probabilities"]["0"],
        )
        for criterion_id, answer in row["answers"].items()
    )


def _iter_cells(matrix: Matrix) -> Iterator[Cell]:
    return chain.from_iterable(
        _row_cells(construct, row) for construct, row in matrix["rows"].items()
    )


def _likely_applicable(cell: Cell) -> bool:
    return cell.not_applicable_probability < _NOT_APPLICABLE_THRESHOLD


def _needs_inspection(cell: Cell) -> bool:
    """A confident, likely-applicable low score: a real candidate gap to inspect."""
    return (
        _likely_applicable(cell)
        and cell.score < _LOW_SCORE_THRESHOLD
        and cell.confidence >= _MIN_TRUSTED_CONFIDENCE
    )


def _iter_flagged(cells: Sequence[Cell]) -> Iterator[Cell]:
    return (cell for cell in cells if _needs_inspection(cell))


def _applicability(cell: Cell) -> float:
    """1 minus the not-applicable probability: how likely this criterion applies at all."""
    return 1 - cell.not_applicable_probability


def _attention(cell: Cell) -> float:
    """Higher means more worth a human's time: bad, confident, and applicable."""
    severity = 3 - cell.score
    return severity * cell.confidence * _applicability(cell)


def _inspection_row(cell: Cell) -> str:
    return (
        f"| `{cell.construct}` | `{cell.criterion_id}` "
        f"| {cell.score:.2f} | {cell.confidence:.2f} | {_applicability(cell):.2f} |\n"
    )


def _inspection_table(cells: Sequence[Cell]) -> str:
    flagged = sorted(_iter_flagged(cells), key=_attention, reverse=True)
    if not flagged:
        return (
            "No cell fell below the score or confidence threshold. Nothing flagged.\n"
        )
    header = "| Construct | Principle | Score /3 | Confidence | Applicability |\n| --- | --- | --- | --- | --- |\n"
    return header + "".join(_inspection_row(cell) for cell in flagged)


def _principle_row(criterion_id: str, info: PrincipleInfo) -> str:
    return f"| `{criterion_id}` | {info['term']} | {', '.join(info['sources'])} |\n"


def _principles_table(principles: Mapping[str, PrincipleInfo]) -> str:
    """ID, plain-English term, and Standards citation for every principle used
    in this report -- the legend the "Needs inspection" and "Full matrix"
    tables cite by ID rather than repeating."""
    header = "| ID | Term | Sources |\n| --- | --- | --- |\n"
    rows = (
        _principle_row(criterion_id, info)
        for criterion_id, info in sorted(principles.items())
    )
    return header + "".join(rows)


def _score_label(cell: Cell) -> str:
    if cell.not_applicable_probability >= _NOT_APPLICABLE_THRESHOLD:
        return "—"
    return f"{cell.score:.1f}"


@dataclass(frozen=True, slots=True)
class RoleGroup:
    """One `criteria_groups` combination (e.g. `("test", "src")`) and the
    constructs that used it -- one appendix table per group, since a `test*`
    function's row set differs from a fixture's."""

    names: tuple[str, ...]
    constructs: tuple[str, ...]


def _group_names(matrix: Matrix) -> Iterator[tuple[str, ...]]:
    """Every distinct `criteria_groups` combination used in `matrix`, deduplicated."""
    return iter({tuple(row["criteria_groups"]) for row in matrix["rows"].values()})


def _constructs_for_group(names: tuple[str, ...], matrix: Matrix) -> tuple[str, ...]:
    """Every construct whose `criteria_groups` matches `names`."""
    return tuple(
        construct
        for construct, row in matrix["rows"].items()
        if tuple(row["criteria_groups"]) == names
    )


def _role_groups(matrix: Matrix) -> Iterator[RoleGroup]:
    return (
        RoleGroup(names, _constructs_for_group(names, matrix))
        for names in _group_names(matrix)
    )


@dataclass(frozen=True, slots=True)
class CriterionIndex:
    """`{criterion_id: {construct: cell}}`, for an appendix table's per-cell lookup.
    A named type over the raw nested mapping so a lookup miss (`get` returning
    `None`) reads as the class's own contract, not a `dict.get(x, {}).get(y)`
    chain the reader has to trace back to its construction."""

    _cells: Mapping[str, Mapping[str, Cell]]

    def get(self, criterion_id: str, construct: str) -> Cell | None:
        return self._cells.get(criterion_id, {}).get(construct)


def _criterion_ids(cells: Sequence[Cell]) -> Iterator[str]:
    """Every criterion ID scored in `cells`, deduplicated."""
    return iter({cell.criterion_id for cell in cells})


def _cells_for_criterion(
    criterion_id: str, cells: Sequence[Cell]
) -> Mapping[str, Cell]:
    """Every cell for `criterion_id`, keyed by construct name."""
    return {cell.construct: cell for cell in cells if cell.criterion_id == criterion_id}


def _index_by_criterion(cells: Sequence[Cell]) -> CriterionIndex:
    return CriterionIndex(
        {
            criterion_id: _cells_for_criterion(criterion_id, cells)
            for criterion_id in _criterion_ids(cells)
        }
    )


def _appendix_row(
    criterion_id: str, constructs: Sequence[str], index: CriterionIndex
) -> str:
    scores = (
        _score_label(cell)
        if (cell := index.get(criterion_id, name)) is not None
        else "?"
        for name in constructs
    )
    return f"| `{criterion_id}` | " + " | ".join(scores) + " |\n"


def _appendix_table(matrix: Matrix, group: RoleGroup, index: CriterionIndex) -> str:
    criterion_ids = sorted(
        {cid for c in group.constructs for cid in matrix["rows"][c]["answers"]}
    )
    header = (
        "| Principle | " + " | ".join(f"`{name}`" for name in group.constructs) + " |\n"
    )
    header += "| --- | " + " | ".join("---" for _ in group.constructs) + " |\n"
    rows = "".join(_appendix_row(cid, group.constructs, index) for cid in criterion_ids)
    return f"### Criteria groups: {', '.join(group.names)}\n\n{header}{rows}\n"


def _appendix_tables(matrix: Matrix, cells: Sequence[Cell]) -> str:
    index = _index_by_criterion(cells)
    return "\n".join(
        _appendix_table(matrix, group, index) for group in _role_groups(matrix)
    )


def _report_header(matrix: Matrix, cells: Sequence[Cell]) -> Iterator[str]:
    construct_count = len(matrix["rows"])
    yield f"# Jev code-compliance report: `{matrix['module_file']}`"
    yield ""
    yield f"{construct_count} constructs x {len(cells)} scored points, {matrix['jev_call_count']} Jev calls."
    yield ""
    yield "Score is 0 (not applicable) to 3 (fully compliant); a low score with a not-applicable"
    yield "probability below 0.5 means the model judged the principle as likely applicable and the"
    yield "construct as not clearly compliant. Verify every flagged row against the actual source"
    yield "before changing anything -- these are model judgments, not findings."
    yield ""


def _lint_section(lint: LintReport) -> Iterator[str]:
    yield "## Lint (ruff)"
    yield ""
    yield "`ruff check` and `ruff format --check --diff` against the scored file --"
    yield "mechanical PEP 8, line-length, and import-order findings, checked directly"
    yield "rather than left to Jev's judgment."
    yield ""
    if lint["clean"]:
        yield "Clean: no `ruff check` findings, already `ruff format`-clean.\n"
        return
    yield "```"
    yield (lint["check_output"] + lint["format_diff"]).rstrip("\n")
    yield "```\n"


def _principles_section(matrix: Matrix) -> Iterator[str]:
    yield "## Principles"
    yield ""
    yield "Every principle this report scored: its ID, a short plain-English term, and which"
    yield "Standards document(s) it cites. See the code-compliance skill's"
    yield "`references/jev_code_compliance.md` for the full definition behind each ID."
    yield ""
    yield _principles_table(matrix["principles"])


def _needs_inspection_section(cells: Sequence[Cell]) -> Iterator[str]:
    yield "## Needs inspection"
    yield ""
    yield (
        f"Flagged: score < {_LOW_SCORE_THRESHOLD}, confidence >= {_MIN_TRUSTED_CONFIDENCE}, "
        f"not-applicable probability < {_NOT_APPLICABLE_THRESHOLD}. This is the confident, "
        "likely-applicable, low-scoring set -- the actual candidate gaps -- sorted by an "
        "attention score, worst first."
    )
    yield ""
    yield _inspection_table(cells)


def _full_matrix_section(matrix: Matrix, cells: Sequence[Cell]) -> Iterator[str]:
    yield "## Full matrix"
    yield ""
    yield "Score per construct per principle, grouped by which principles applied to each construct"
    yield "(a `test*` function is scored only against `test` principles; a fixture or helper against"
    yield "both `test` and `src`). `—` means the model judged the principle mostly not applicable"
    yield "(probability >= 0.5) to that construct."
    yield ""
    yield _appendix_tables(matrix, cells)


def render_report(matrix: Matrix) -> str:
    """Build the Markdown report text for one compliance matrix."""
    cells = tuple(_iter_cells(matrix))
    lines = chain(
        _report_header(matrix, cells),
        _lint_section(matrix["lint"]),
        _principles_section(matrix),
        _needs_inspection_section(cells),
        _full_matrix_section(matrix, cells),
    )
    return "\n".join(lines).rstrip("\n") + "\n"


app = typer.Typer(add_completion=False)


@app.command()
def main(
    matrix: Path = typer.Option(  # noqa: B008
        ..., help="The scoring matrix JSON from jev_code_compliance.py"
    ),
    out: Path = typer.Option(..., help="Where to write the rendered Markdown report"),  # noqa: B008
) -> None:
    payload = cast(Matrix, json.loads(matrix.read_text(encoding="utf-8")))
    out.write_text(render_report(payload), encoding="utf-8")
    print(f"Wrote report to {out}")


if __name__ == "__main__":
    app()
