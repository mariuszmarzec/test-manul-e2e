"""Pytest tests for Team Flow E2E Child B string utilities."""

import pytest

from team_flow_e2e.child_b import (
    reverse_string,
    count_vowels,
    split_words,
    is_palindrome,
)


class TestReverseString:
    """Tests for reverse_string function."""

    def test_normal_input(self) -> None:
        """Test reversing a normal string."""
        assert reverse_string("hello") == "olleh"
        assert reverse_string("world") == "dlrow"
        assert reverse_string("Python") == "nohtyP"

    def test_empty_string(self) -> None:
        """Test reversing an empty string (edge case)."""
        assert reverse_string("") == ""

    def test_single_character(self) -> None:
        """Test reversing a single character string (edge case)."""
        assert reverse_string("a") == "a"
        assert reverse_string("Z") == "Z"

    def test_unicode_string(self) -> None:
        """Test reversing a string with unicode characters."""
        assert reverse_string("café") == "éfac"
        assert reverse_string("🎉🎊") == "🎊🎉"


class TestCountVowels:
    """Tests for count_vowels function."""

    def test_normal_input(self) -> None:
        """Test counting vowels in normal strings."""
        assert count_vowels("hello") == 2
        assert count_vowels("world") == 1
        assert count_vowels("beautiful") == 5

    def test_no_vowels(self) -> None:
        """Test string with no vowels (edge case)."""
        assert count_vowels("xyz") == 0
        assert count_vowels("bcdfg") == 0
        assert count_vowels("") == 0

    def test_all_vowels(self) -> None:
        """Test string with only vowels (edge case)."""
        assert count_vowels("aeiou") == 5
        assert count_vowels("AEIOU") == 5
        assert count_vowels("AaEeIiOoUu") == 10

    def test_mixed_case(self) -> None:
        """Test counting vowels with mixed case."""
        assert count_vowels("HeLLo") == 2
        assert count_vowels("WoRLD") == 1


class TestSplitWords:
    """Tests for split_words function."""

    def test_normal_whitespace(self) -> None:
        """Test splitting on default whitespace."""
        assert split_words("hello world") == ["hello", "world"]
        assert split_words("  a  b  c  ") == ["a", "b", "c"]

    def test_custom_delimiter(self) -> None:
        """Test splitting with a custom delimiter."""
        assert split_words("a,b,c", ",") == ["a", "b", "c"]
        assert split_words("one|two|three", "|") == ["one", "two", "three"]

    def test_empty_string(self) -> None:
        """Test splitting an empty string (edge case)."""
        assert split_words("") == []
        assert split_words("", ",") == []

    def test_delimiter_at_edges(self) -> None:
        """Test delimiter at start/end of string (edge case)."""
        assert split_words(",a,b,", ",") == ["a", "b"]
        assert split_words("|start|middle|end|", "|") == ["start", "middle", "end"]

    def test_consecutive_delimiters(self) -> None:
        """Test consecutive delimiters producing empty words (edge case)."""
        assert split_words("a,,b", ",") == ["a", "b"]
        assert split_words("a|||b", "|") == ["a", "b"]


class TestIsPalindrome:
    """Tests for is_palindrome function."""

    def test_simple_palindrome(self) -> None:
        """Test simple palindromes."""
        assert is_palindrome("racecar") is True
        assert is_palindrome("level") is True
        assert is_palindrome("radar") is True

    def test_non_palindrome(self) -> None:
        """Test non-palindromes."""
        assert is_palindrome("hello") is False
        assert is_palindrome("world") is False

    def test_case_insensitive_default(self) -> None:
        """Test case insensitivity (default behavior)."""
        assert is_palindrome("RaceCar") is True
        assert is_palindrome("LeVeL") is True

    def test_case_sensitive(self) -> None:
        """Test case sensitive mode (edge case)."""
        assert is_palindrome("RaceCar", ignore_case=False) is False
        assert is_palindrome("racecar", ignore_case=False) is True

    def test_with_spaces_ignored(self) -> None:
        """Test palindrome with spaces ignored (edge case)."""
        assert is_palindrome("a man a plan a canal panama", ignore_spaces=True) is True
        assert is_palindrome("never odd or even", ignore_spaces=True) is True

    def test_with_spaces_not_ignored(self) -> None:
        """Test palindrome with spaces not ignored."""
        assert is_palindrome("a man a plan a canal panama", ignore_spaces=False) is False
        assert is_palindrome("race car", ignore_spaces=False) is False

    def test_empty_string(self) -> None:
        """Test empty string (edge case)."""
        assert is_palindrome("") is True

    def test_single_character(self) -> None:
        """Test single character (edge case)."""
        assert is_palindrome("a") is True
        assert is_palindrome("Z") is True