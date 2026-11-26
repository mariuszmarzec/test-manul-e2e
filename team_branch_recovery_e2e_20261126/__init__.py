"""
TEAM-BRANCH-RECOVERY-E2E-20261126 Child B package.

Deterministic text-processing utilities with comprehensive type hints and tests.
"""

from .child_b import (
    count_words,
    normalize_whitespace,
    tokenize,
    extract_patterns,
    compute_text_statistics,
    truncate_text,
    remove_duplicate_lines,
    find_common_prefix,
    split_into_chunks,
    compare_texts,
    process_document,
)

__all__ = [
    "count_words",
    "normalize_whitespace",
    "tokenize",
    "extract_patterns",
    "compute_text_statistics",
    "truncate_text",
    "remove_duplicate_lines",
    "find_common_prefix",
    "split_into_chunks",
    "compare_texts",
    "process_document",
]

__version__ = "1.0.0"