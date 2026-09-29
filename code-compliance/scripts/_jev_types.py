"""The scoring-matrix output contract, shared by `jev_code_compliance.py` (which
writes it) and `jev_code_compliance_report.py` (which reads it). Split out so
the report renderer doesn't import the runner module and trigger its
module-level load of `jev_code_compliance_data.json`, which it doesn't need."""

from __future__ import annotations

from typing import TypedDict


class ScoreAnswer(TypedDict):
    """The one Jev answer shape either script reads; the real response carries
    more (`legend`, `type`), left out since nothing here consumes them."""

    score: float
    confidence: float
    probabilities: dict[str, float]


class ConstructRow(TypedDict):
    kind: str
    role: str
    criteria_groups: list[str]
    answers: dict[str, ScoreAnswer]


class PrincipleInfo(TypedDict):
    term: str
    sources: list[str]


class LintReport(TypedDict):
    """`ruff check` and `ruff format --check --diff` output for the scored file.

    Mechanical PEP 8 / line-length / import-order issues that ruff catches
    outright, so Jev's fuzzy judgment isn't asked to guess at them too."""

    check_output: str
    format_diff: str
    clean: bool


class Matrix(TypedDict):
    module_file: str
    lint: LintReport
    principles: dict[str, PrincipleInfo]
    jev_call_count: int
    rows: dict[str, ConstructRow]
