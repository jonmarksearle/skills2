"""Shared Markdown parsing for jev_define_compliance.py and jev_code_compliance.py."""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping

_SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_LIST_ITEM_RE = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+(.+)$")
_LEADING_NUMBER_RE = re.compile(r"^(\d+)\)\s*")
_TERM_MAX_CHARS = 70

# Order matters: longest match first, so "prefer to use " doesn't leave a
# dangling "to use " when "prefer " would also match.
_NEUTRAL_PREFIXES = (
    "prefer to use ",
    "prefer using ",
    "prefer to ",
    "prefer ",
    "only use ",
    "only allow ",
    "default ",
    "always ",
    "keep ",
    "allow ",
    "use ",
)
# These invert the sentence's meaning if simply deleted ("Avoid X" is not "X").
# Normalised to a short "No " form instead, so the term keeps the polarity.
_NEGATION_PREFIXES = (
    "avoid using ",
    "avoid ",
    "do not ",
    "don't ",
    "never ",
)


def split_sections(markdown: str) -> Mapping[str, str]:
    """Map each `## Title` heading to its body text, in document order."""
    matches = list(_SECTION_RE.finditer(markdown))
    ends = [match.start() for match in matches[1:]] + [len(markdown)]
    return {
        match.group(1): markdown[match.end() : end].strip()
        for match, end in zip(matches, ends)
    }


def list_items(body: str) -> Iterator[str]:
    """The text of every top-level `- ` or `N. ` list item in `body`, in order.

    A caller that needs to check emptiness or iterate more than once (e.g.
    `if not bullets`) materialises with `tuple(list_items(...))` itself --
    that need doesn't belong to this function.
    """
    matches = (_LIST_ITEM_RE.match(line) for line in body.splitlines())
    return (match.group(1).strip() for match in matches if match is not None)


def leading_number(title: str) -> int | None:
    """The `N` in a `"N) Title"` heading, or None for a heading with no such prefix."""
    match = _LEADING_NUMBER_RE.match(title)
    return int(match.group(1)) if match is not None else None


def slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")


def _strip_leading_directive(text: str) -> str:
    """Drop a leading directive verb, preserving polarity.

    "Prefer X" and "Avoid X" both direct behaviour, but only one can be
    shortened by deleting the verb: "Avoid deep nesting" -> "deep nesting"
    silently reverses the rule, and "Don't X" -> "No X" is often not even
    grammatical ("Don't Repeat Yourself" -> "No Repeat Yourself"). Negation
    prefixes (`_NEGATION_PREFIXES`) are left untouched; only the neutral ones
    are safe to delete outright.
    """
    lowered = text.lower()
    if lowered.startswith(_NEGATION_PREFIXES):
        return text
    for prefix in _NEUTRAL_PREFIXES:
        if lowered.startswith(prefix):
            return text[len(prefix) :]
    return text


def _truncate_at_word(text: str, limit: int) -> str:
    """Cut to at most `limit` characters, never mid-word and never leaving an
    unmatched opening bracket dangling (drop back to before it instead)."""
    if len(text) <= limit:
        return text
    truncated = text[:limit].rsplit(" ", 1)[0]
    open_paren = truncated.rfind("(")
    if open_paren != -1 and ")" not in truncated[open_paren:]:
        truncated = truncated[:open_paren].rstrip()
    return truncated


def derive_term(text: str) -> str:
    """A short, plain-English name for a bullet or section title, e.g. for a
    reference table where the full wording would be too long to scan. Strips
    the "N) " section-number prefix and a leading directive verb, keeping
    negation ("Avoid ", "Do not ") intact as "No " rather than deleting it,
    then truncates to a scannable length without breaking mid-word or
    mid-parenthesis."""
    stripped = _LEADING_NUMBER_RE.sub("", text).rstrip(".")
    stripped = _strip_leading_directive(stripped)
    term = _truncate_at_word(stripped.strip(), _TERM_MAX_CHARS).rstrip(".,;:")
    return term[:1].upper() + term[1:] if term else text
