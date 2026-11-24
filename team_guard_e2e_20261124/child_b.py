"""
Text normalization utilities for Team Guard E2E.

This module provides deterministic text processing functions
with comprehensive type hints and documentation.
"""

import re
from typing import Optional


def slugify(text: str, max_length: Optional[int] = None, separator: str = "-") -> str:
    """
    Convert text to a URL-friendly slug.

    Args:
        text: Input text to convert.
        max_length: Optional maximum length of the resulting slug.
        separator: Character to use as word separator (default: "-").

    Returns:
        A slugified version of the input text.

    Examples:
        >>> slugify("Hello World")
        'hello-world'
        >>> slugify("Test@#$% Case", separator="_")
        'test_case'
    """
    if not text:
        return ""

    # Convert to lowercase
    text = text.lower()

    # Replace non-alphanumeric characters with separator
    text = re.sub(r"[^a-z0-9]+", separator, text)

    # Remove leading/trailing separators
    text = text.strip(separator)

    # Collapse multiple consecutive separators
    text = re.sub(f"{re.escape(separator)}+", separator, text)

    # Truncate if max_length specified
    if max_length is not None and len(text) > max_length:
        text = text[:max_length].rstrip(separator)

    return text


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.

    Replaces all whitespace sequences with a single space
    and strips leading/trailing whitespace.

    Args:
        text: Input text to normalize.

    Returns:
        Text with normalized whitespace.

    Examples:
        >>> normalize_whitespace("  hello   world  ")
        'hello world'
        >>> normalize_whitespace("line1\n\nline2\tline3")
        'line1 line2 line3'
    """
    if not text:
        return ""

    # Replace all whitespace sequences with single space
    text = re.sub(r"\s+", " ", text)

    # Strip leading/trailing
    return text.strip()


def truncate_with_ellipsis(text: str, max_length: int, ellipsis: str = "...") -> str:
    """
    Truncate text to maximum length with ellipsis.

    Args:
        text: Input text to truncate.
        max_length: Maximum length including ellipsis.
        ellipsis: String to append when truncated (default: "...").

    Returns:
        Truncated text with ellipsis if truncation occurred.

    Raises:
        ValueError: If max_length is less than length of ellipsis.

    Examples:
        >>> truncate_with_ellipsis("Hello World", 8)
        'Hello...'
        >>> truncate_with_ellipsis("Hi", 10)
        'Hi'
    """
    if max_length < len(ellipsis):
        raise ValueError(f"max_length ({max_length}) must be >= len(ellipsis) ({len(ellipsis)})")

    if not text or len(text) <= max_length:
        return text

    return text[: max_length - len(ellipsis)] + ellipsis


def extract_words(text: str, min_length: int = 1) -> list[str]:
    """
    Extract words from text, filtering by minimum length.

    Args:
        text: Input text to extract words from.
        min_length: Minimum word length to include (default: 1).

    Returns:
        List of words meeting the minimum length requirement.

    Examples:
        >>> extract_words("Hello world test", min_length=4)
        ['Hello', 'world']
        >>> extract_words("a bc def", min_length=2)
        ['bc', 'def']
    """
    if not text:
        return []

    # Split on non-word characters
    words = re.findall(r"\b\w+\b", text)

    # Filter by minimum length
    return [word for word in words if len(word) >= min_length]


def count_words(text: str) -> int:
    """
    Count words in text.

    Args:
        text: Input text to count words in.

    Returns:
        Number of words in the text.

    Examples:
        >>> count_words("Hello world")
        2
        >>> count_words("")
        0
    """
    return len(extract_words(text))


def reverse_words(text: str) -> str:
    """
    Reverse the order of words in text.

    Args:
        text: Input text.

    Returns:
        Text with words in reverse order.

    Examples:
        >>> reverse_words("Hello world test")
        'test world Hello'
    """
    words = extract_words(text)
    return " ".join(reversed(words))


def is_palindrome(text: str, ignore_case: bool = True, ignore_non_alnum: bool = True) -> bool:
    """
    Check if text is a palindrome.

    Args:
        text: Input text to check.
        ignore_case: Whether to ignore case differences (default: True).
        ignore_non_alnum: Whether to ignore non-alphanumeric characters (default: True).

    Returns:
        True if text is a palindrome, False otherwise.

    Examples:
        >>> is_palindrome("racecar")
        True
        >>> is_palindrome("A man a plan a canal Panama")
        True
        >>> is_palindrome("hello")
        False
    """
    if not text:
        return True

    processed = text
    if ignore_case:
        processed = processed.lower()
    if ignore_non_alnum:
        processed = re.sub(r"[^a-z0-9]", "", processed)

    return processed == processed[::-1]