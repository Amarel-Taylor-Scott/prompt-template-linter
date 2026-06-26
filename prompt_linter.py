"""A tiny, dependency-free linter for system prompt templates.

It scans a template string for:

* ``{{placeholder}}`` variables
* instruction-like lines (bullets or numbered steps)
* unsafe keywords/phrases (e.g. "ignore previous", "system prompt")
* a simple complexity score
"""

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


# Placeholders like {{name}}, {{ user_name }}, etc.
PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")

# Lines that look like instructions: "- ..." or "1. ..." / "2) ..."
INSTRUCTION_RE = re.compile(r"^\s*(?:-\s+|\d+[\.\)]\s+)")

# Phrases that may indicate prompt injection or unsafe requests.
UNSAFE_PATTERNS = [
    "ignore previous",
    "system prompt",
    "ignore all",
    "disregard",
    "override instructions",
    "previous instructions",
    "leak",
    "confidential",
]

# Precompiled word-boundary regexes, one per phrase. Matching on word
# boundaries (rather than plain substring containment) avoids false-positive
# warnings such as flagging "leak" inside "bleak" or "confidential" inside
# "confidentially". Kept in lockstep with ``UNSAFE_PATTERNS`` so each hit can be
# reported with the human-readable phrase that triggered it.
UNSAFE_RES = [re.compile(r"\b" + re.escape(p) + r"\b") for p in UNSAFE_PATTERNS]


@dataclass
class LintReport:
    """Result of linting a single template."""

    placeholders: list[str] = field(default_factory=list)
    instruction_count: int = 0
    warnings: list[str] = field(default_factory=list)
    complexity_score: int = 0

    def to_dict(self) -> dict:
        return {
            "placeholders": self.placeholders,
            "instruction_count": self.instruction_count,
            "warnings": self.warnings,
            "complexity_score": self.complexity_score,
        }


def lint_template(template: str) -> LintReport:
    """Analyze *template* and return a ``LintReport``."""
    placeholders: list[str] = []
    seen: set[str] = set()
    for match in PLACEHOLDER_RE.finditer(template):
        name = match.group(1)
        if name not in seen:
            seen.add(name)
            placeholders.append(name)

    instruction_count = 0
    for line in template.splitlines():
        if INSTRUCTION_RE.match(line):
            instruction_count += 1

    warnings: list[str] = []
    lowered = template.lower()
    unsafe_hits = 0
    for pattern, regex in zip(UNSAFE_PATTERNS, UNSAFE_RES):
        if regex.search(lowered):
            unsafe_hits += 1
            warnings.append(f"Flagged unsafe keyword/phrase: {pattern!r}")

    if not placeholders:
        warnings.append("No placeholders found; template may be missing dynamic fields.")

    # Simple heuristic: placeholders + instructions + a penalty for unsafe content.
    complexity_score = len(placeholders) + instruction_count + 2 * unsafe_hits

    return LintReport(
        placeholders=placeholders,
        instruction_count=instruction_count,
        warnings=warnings,
        complexity_score=complexity_score,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Lint a system prompt template for placeholders, instructions, and unsafe keywords."
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Path to the template file. Reads from stdin if omitted.",
    )
    args = parser.parse_args(argv)

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()

    report = lint_template(text)

    print(f"Placeholders: {', '.join(report.placeholders) if report.placeholders else '(none)'}")
    print(f"Instructions: {report.instruction_count}")
    print(f"Complexity:   {report.complexity_score}")

    if report.warnings:
        print("Warnings:")
        for warning in report.warnings:
            print(f"  - {warning}")

    # Note: any warning — including the benign "No placeholders found" case —
    # makes the process exit non-zero. A static prompt with no placeholders is
    # therefore treated as a lint failure by design; callers that want to allow
    # placeholder-free templates must check the report themselves.
    return 1 if report.warnings else 0


if __name__ == "__main__":
    raise SystemExit(main())
