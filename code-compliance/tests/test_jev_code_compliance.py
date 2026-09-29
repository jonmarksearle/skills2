"""Local request-size regressions for the compliance scorer."""

import pytest
from jev_code_compliance import (
    Construct,
    Criterion,
    _module_context,
    _size_safe_batches,
)


def test__module_context__large_file_keeps_target_and_direct_helper__success() -> None:
    source = (
        "import pytest\n"
        + "UNRELATED = 'padding'\n" * 5000
        + "def helper():\n    return 1\n"
        + "def test_target():\n    assert helper() == 1\n"
    )
    context = _module_context(source, Construct("test_target", "function", "test"))
    assert "def test_target()" in context and "def helper()" in context
    assert len(context.encode("utf-8")) < 32 * 1024


def test__size_safe_batches__oversized_single_principle__fail() -> None:
    criterion = Criterion("X", "term", "label", "x" * 70_000, (), None)
    with pytest.raises(ValueError, match=r"single principle"):
        tuple(
            _size_safe_batches(
                (criterion,),
                "def target(): pass",
                Construct("target", "function", "src"),
            )
        )
