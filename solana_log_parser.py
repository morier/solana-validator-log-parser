#!/usr/bin/env python3
"""Solana validator log parser.

Parses validator logs and produces an operational summary focused on:
- error frequency
- warning frequency
- vote success/failure indicators
- RPC and consensus-related signal counts
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import IO
from typing import Any

ERROR_PATTERNS = [
    r"\berror\b",
    r"panic",
    r"failed",
    r"connection reset",
]

WARNING_PATTERNS = [
    r"\bwarn(ing)?\b",
    r"retry",
    r"slow",
]

SIGNAL_PATTERNS = {
    "votes": [r"\bvote\b", r"tower"],
    "slots": [r"\bslot\b", r"bank"],
    "rpc": [r"\brpc\b", r"json-rpc", r"gethealth", r"getslot"],
    "gossip": [r"gossip", r"cluster"],
}


@dataclass
class ParseSummary:
    total_lines: int
    error_lines: int
    warning_lines: int
    signal_counts: dict[str, int]
    top_error_fragments: list[tuple[str, int]]


def _matches_any(line: str, patterns: list[str]) -> bool:
    lower = line.lower()
    return any(re.search(pattern, lower) for pattern in patterns)


def _extract_fragment(line: str) -> str:
    stripped = line.strip()
    if not stripped:
        return "<empty line>"
    if len(stripped) <= 120:
        return stripped
    return stripped[:117] + "..."


def _init_counters() -> tuple[int, int, Counter[str], dict[str, int]]:
    return 0, 0, Counter(), {name: 0 for name in SIGNAL_PATTERNS}


def _accumulate_line(
    line: str,
    errors: int,
    warnings: int,
    error_fragments: Counter[str],
    signal_counts: dict[str, int],
) -> tuple[int, int]:
    if _matches_any(line, ERROR_PATTERNS):
        errors += 1
        error_fragments[_extract_fragment(line)] += 1

    if _matches_any(line, WARNING_PATTERNS):
        warnings += 1

    for signal_name, patterns in SIGNAL_PATTERNS.items():
        if _matches_any(line, patterns):
            signal_counts[signal_name] += 1

    return errors, warnings


def parse_log_lines(lines: list[str]) -> ParseSummary:
    total = len(lines)
    errors, warnings, error_fragments, signal_counts = _init_counters()

    for line in lines:
        errors, warnings = _accumulate_line(line, errors, warnings, error_fragments, signal_counts)

    top_error_fragments = error_fragments.most_common(5)

    return ParseSummary(
        total_lines=total,
        error_lines=errors,
        warning_lines=warnings,
        signal_counts=signal_counts,
        top_error_fragments=top_error_fragments,
    )


def parse_log_file(path: Path) -> ParseSummary:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return parse_log_lines(lines)


def parse_log_stream(stream: IO[str]) -> ParseSummary:
    total = 0
    errors, warnings, error_fragments, signal_counts = _init_counters()

    for line in stream:
        total += 1
        errors, warnings = _accumulate_line(line, errors, warnings, error_fragments, signal_counts)

    top_error_fragments = error_fragments.most_common(5)

    return ParseSummary(
        total_lines=total,
        error_lines=errors,
        warning_lines=warnings,
        signal_counts=signal_counts,
        top_error_fragments=top_error_fragments,
    )


def as_dict(summary: ParseSummary) -> dict[str, Any]:
    error_rate = 0.0
    warning_rate = 0.0
    if summary.total_lines > 0:
        error_rate = (summary.error_lines / summary.total_lines) * 100
        warning_rate = (summary.warning_lines / summary.total_lines) * 100

    return {
        "total_lines": summary.total_lines,
        "error_lines": summary.error_lines,
        "warning_lines": summary.warning_lines,
        "error_rate_pct": round(error_rate, 2),
        "warning_rate_pct": round(warning_rate, 2),
        "signal_counts": summary.signal_counts,
        "top_error_fragments": summary.top_error_fragments,
    }


def print_text(summary_data: dict[str, Any]) -> None:
    print("Solana Validator Log Summary")
    print(f"  Total Lines    : {summary_data['total_lines']}")
    print(f"  Error Lines    : {summary_data['error_lines']} ({summary_data['error_rate_pct']:.2f}%)")
    print(f"  Warning Lines  : {summary_data['warning_lines']} ({summary_data['warning_rate_pct']:.2f}%)")
    print("  Signal Counts  :")
    for signal_name, value in summary_data["signal_counts"].items():
        print(f"    - {signal_name}: {value}")

    print("  Top Error Fragments:")
    fragments = summary_data["top_error_fragments"]
    if not fragments:
        print("    - none")
    else:
        for fragment, count in fragments:
            print(f"    - ({count}) {fragment}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Solana validator log parser")
    parser.add_argument("--file", required=True, help="Path to validator log file")
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    args = parser.parse_args()

    if args.file == "-":
        summary = parse_log_stream(sys.stdin)
    else:
        path = Path(args.file)
        if not path.exists() or not path.is_file():
            print(f"Log file not found: {path}")
            return 2
        summary = parse_log_file(path)

    summary_data = as_dict(summary)

    if args.output == "json":
        print(json.dumps(summary_data, indent=2))
    else:
        print_text(summary_data)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
