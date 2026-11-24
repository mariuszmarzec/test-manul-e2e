"""String processing utilities for Team Flow E2E Child B.

This module provides deterministic string manipulation functions with
comprehensive type hints and documentation.
"""

from typing import List, Optional


def reverse_string(s: str) -> str:
    """Return the reversed version of the input string.

    Args:
        s: The string to reverse.

    Returns:
        The input string in reverse order.

    Examples:
        >>> reverse_string("hello")
        'olleh'
        >>> reverse_string("")
        ''
    """
    return s[::-1]


def count_vowels(s: str) -> int:
    """Count the number of vowels in the input string.

    Args:
        s: The string to analyze.

    Returns:
        The count of vowels (a, e, i, o, u, case-insensitive).

    Examples:
        >>> count_vowels("hello")
        2
        >>> count_vowels("xyz")
        0
        >>> count_vowels("AEIOU")
        5
    """
    vowels = set("aeiouAEIOU")
    return sum(1 for char in s if char in vowels)


def split_words(s: str, delimiter: Optional[str] = None) -> List[str]:
    """Split a string into words using the specified delimiter.

    Args:
        s: The string to split.
        delimiter: The delimiter to use for splitting. If None, splits on whitespace.

    Returns:
        A list of non-empty words from the string.

    Examples:
        >>> split_words("hello world")
        ['hello', 'world']
        >>> split_words("a,b,c", ",")
        ['a', 'b', 'c']
        >>> split_words("  a  b  ")
        ['a', 'b']
    """
    if delimiter is None:
        return s.split()
    return [word for word in s.split(delimiter) if word]


def is_palindrome(s: str, ignore_case: bool = True, ignore_spaces: bool = False) -> bool:
    """Check if a string is a palindrome.

    Args:
        s: The string to check.
        ignore_case: Whether to ignore case differences. Defaults to True.
        ignore_spaces: Whether to ignore spaces. Defaults to False.

    Returns:
        True if the string is a palindrome, False otherwise.

    Examples:
        >>> is_palindrome("racecar")
        True
        >>> is_palindrome("RaceCar")
        True
        >>> is_palindrome("RaceCar", ignore_case=False)
        False
        >>> is_palindrome("a man a plan a canal panama", ignore_spaces=True)
        True
    """
    processed = s
    if ignore_spaces:
        processed = processed.replace(" ", "")
    if ignore_case:
        processed = processed.lower()
    return processed == processed[::-1]