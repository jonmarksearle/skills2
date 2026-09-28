#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["typer"]
# ///

"""Bake the Standards into `jev_code_compliance_data.json` and `jev_code_compliance.md`.

Run this once and re-run it only when `Standards/CODE_STANDARDS.md`,
`Standards/CODE_STANDARDS.pytest.md`, or `Standards/CODE_STANDARDS.examples.md`
change. `jev_code_compliance_data.json` holds the tailored constructs actually
fed to Jev -- one principle per bullet, its definition, sources, and example
reference -- so it, not this generator script, is the artifact worth
reviewing. Everything `jev_code_compliance.py` needs to score a construct is
in that file; the runner has no Standards file to locate at scoring time,
only the target `.py` file and this JSON.

One principle = one stable ID, one definition (kept verbatim from the
Standards, not shortened -- fidelity over compactness), and a citation to
the document(s) it came from.

One principle per bullet point, not one per section -- a single bullet is a
narrow, concrete, self-contained judgment, closer to what ask-jev's own
guidance calls for ("ask one narrow, coherent judgment per question") than
an entire multi-bullet section bundled into one question. A section with no
bullets
(pure prose, e.g. "3) TDD roles") becomes one whole-section principle
instead, since there is nothing to decompose. Every bullet drawn from a
section is paired with that section's worked example, where one exists in
`CODE_STANDARDS.examples.md` -- the example illustrates the whole section,
not one bullet in isolation, so it is reused (by reference, not copied) across
that section's bullets rather than split further.

Two separate tables, because src and test Python are judged differently:

- `src` principles (`CS-*`): decomposed from `CODE_STANDARDS.md`, each
  bullet's principle citing `CODE_STANDARDS.examples.md`'s same-titled
  section too when one exists.
- `test` principles (`PT-*`): decomposed from `CODE_STANDARDS.pytest.md`,
  which has no section-by-section `CODE_STANDARDS.examples.md` counterpart,
  so these cite one document each.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import typer
from _jev_markdown import derive_term, leading_number, list_items, slug, split_sections

_SKILL_DIR = Path(__file__).resolve().parent.parent
_DATA_FILE = _SKILL_DIR / "scripts" / "jev_code_compliance_data.json"
_REFERENCE_DOC = _SKILL_DIR / "references" / "jev_code_compliance.md"


@dataclass(frozen=True, slots=True)
class Criterion:
    id: str
    term: str
    label: str
    definition: str
    sources: tuple[str, ...]
    example_ref: str | None


@dataclass(frozen=True, slots=True)
class CriteriaTable:
    criteria: list[Criterion]
    examples: dict[str, str]
    """Each shared worked example's text, once, keyed by the `example_ref` its
    criteria point at -- so a section's 17 bullets cite the same ref instead of
    each carrying their own copy of that section's example."""


def _decompose_section(
    id_prefix: str,
    section_number: int,
    title: str,
    body: str,
    document: str,
    example_document: str,
    example_ref: str | None,
) -> list[Criterion]:
    """One principle per bullet under `title`; the whole section if it has none."""
    sources: tuple[str, ...] = (f"{document} §{title}",)
    if example_ref is not None:
        sources += (f"{example_document} §{title}",)
    bullets = tuple(list_items(body))
    if not bullets:
        return [
            Criterion(
                f"{id_prefix}-{section_number:02d}",
                derive_term(title),
                title,
                body,
                sources,
                example_ref,
            )
        ]
    return [
        Criterion(
            f"{id_prefix}-{section_number:02d}-{index:02d}",
            derive_term(bullet),
            bullet,
            bullet,
            sources,
            example_ref,
        )
        for index, bullet in enumerate(bullets, start=1)
    ]


def _build_table(
    id_prefix: str, standard: Path, *, examples: Path | None
) -> CriteriaTable:
    sections = split_sections(standard.read_text(encoding="utf-8"))
    example_sections = (
        split_sections(examples.read_text(encoding="utf-8"))
        if examples is not None
        else {}
    )
    criteria: list[Criterion] = []
    example_texts: dict[str, str] = {}
    for order, (title, body) in enumerate(sections.items(), start=1):
        number = leading_number(title)
        number = order if number is None else number
        example_body = example_sections.get(title)
        example_ref = None
        if example_body is not None:
            example_ref = f"{slug(standard.name)}_{id_prefix}_{number:02d}"
            example_texts[example_ref] = example_body
        criteria.extend(
            _decompose_section(
                id_prefix,
                number,
                title,
                body,
                standard.name,
                examples.name if examples is not None else "",
                example_ref,
            )
        )
    return CriteriaTable(criteria, example_texts)


def build_src_criteria(code_standards: Path, examples: Path) -> CriteriaTable:
    """`CS-*`: one principle per `CODE_STANDARDS.md` bullet, its worked example
    referenced from `CODE_STANDARDS.examples.md` where that section has one."""
    return _build_table("CS", code_standards, examples=examples)


def build_test_criteria(pytest_standard: Path) -> CriteriaTable:
    """`PT-*`: one principle per `CODE_STANDARDS.pytest.md` bullet."""
    return _build_table("PT", pytest_standard, examples=None)


def render_data(src: CriteriaTable, test: CriteriaTable) -> str:
    """The tailored constructs actually fed to Jev, as plain JSON -- this is the
    artifact worth reviewing, not the generator script that produced it."""
    payload = {
        "src_criteria": [asdict(c) for c in src.criteria],
        "src_examples": src.examples,
        "test_criteria": [asdict(c) for c in test.criteria],
        "test_examples": test.examples,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def render_reference_doc(src: CriteriaTable, test: CriteriaTable) -> str:
    """One combined human-readable reference, both tables, for citing an ID's full
    definition -- `jev_code_compliance_data.json` is for the runner; this is for a person."""

    def table(criteria: list[Criterion]) -> str:
        header = "| ID | Term | Sources | Example ref | Definition |\n| --- | --- | --- | --- | --- |\n"
        rows = (
            f"| `{c.id}` | {c.term} | {', '.join(c.sources)} "
            f"| {f'`{c.example_ref}`' if c.example_ref else '-'} "
            f"| {c.definition.replace(chr(10), '<br>')} |\n"
            for c in criteria
        )
        return header + "".join(rows)

    def examples_table(examples: dict[str, str]) -> str:
        header = "| Ref | Text |\n| --- | --- |\n"
        rows = (
            f"| `{ref}` | {text.replace(chr(10), '<br>')} |\n"
            for ref, text in examples.items()
        )
        return header + "".join(rows)

    return (
        "# Jev code-compliance reference\n\n"
        "Every predefined principle `jev_code_compliance.py` scores a construct against, by ID.\n\n"
        "## Src principles (`CS-*`)\n\n" + table(src.criteria) + "\n"
        "## Test principles (`PT-*`)\n\n" + table(test.criteria) + "\n"
        "## Worked examples\n\n" + examples_table({**src.examples, **test.examples})
    )


app = typer.Typer(add_completion=False)


@app.command()
def main(
    code_standards: Path = typer.Option(Path("../Standards/CODE_STANDARDS.md")),  # noqa: B008
    examples: Path = typer.Option(  # noqa: B008
        Path("../Standards/CODE_STANDARDS.examples.md")
    ),
    pytest_standard: Path = typer.Option(  # noqa: B008
        Path("../Standards/CODE_STANDARDS.pytest.md")
    ),
) -> None:
    src = build_src_criteria(code_standards, examples)
    test = build_test_criteria(pytest_standard)
    _DATA_FILE.write_text(render_data(src, test), encoding="utf-8")
    _REFERENCE_DOC.write_text(render_reference_doc(src, test), encoding="utf-8")
    print(
        f"src: {len(src.criteria)} principles, {len(src.examples)} worked examples\n"
        f"test: {len(test.criteria)} principles, {len(test.examples)} worked examples\n"
        f"-> {_DATA_FILE}\n-> {_REFERENCE_DOC}"
    )


if __name__ == "__main__":
    app()
