"""
Tests for team_guard_e2e_20261124.child_b text utilities.

Covers normal inputs and at least two edge cases per function.
"""

import pytest
from team_guard_e2e_20261124.child_b import (
    slugify,
    normalize_whitespace,
    truncate_with_ellipsis,
    extract_words,
    count_words,
    reverse_words,
    is_palindrome,
)

# ==================== slugify Tests ====================

class TestSlugify:
    """Tests for slugify function."""

    def test_basic_slugify(self):
        """Test basic slug conversion."""
        assert slugify("Hello World") == "hello-world"
        assert slugify("Test Case") == "test-case"

    def test_slugify_with_special_chars(self):
        """Test slugify handles special characters."""
        assert slugify("Test@#$% Case") == "test-case"
        assert slugify("Hello!!! World???") == "hello-world"

    def test_slugify_custom_separator(self):
        """Test slugify with custom separator."""
        assert slugify("Hello World", separator="_") == "hello_world"
        assert slugify("Test Case", separator=".") == "test.case"

    def test_slugify_max_length(self):
        """Test slugify respects max_length."""
        assert slugify("Hello World Test", max_length=10) == "hello-worl"
        assert slugify("Hello World", max_length=5) == "hello"

    def test_slugify_max_length_preserves_separator_boundary(self):
        """Test slugify doesn't cut mid-word when possible."""
        # With max_length=8, "hello-world" (11 chars) becomes "hello" (5 chars)
        # because "hello-w" would be 7 chars but we strip trailing separator
        result = slugify("hello world", max_length=8)
        assert len(result) <= 8
        assert not result.endswith("-")

    def test_slugify_empty_string(self):
        """Test slugify with empty string."""
        assert slugify("") == ""
        assert slugify("   ") == ""

    def test_slugify_only_special_chars(self):
        """Test slugify with only special characters."""
        assert slugify("@#$%") == ""
        assert slugify("!!!") == ""

    def test_slugify_unicode_like(self):
        """Test slugify with unicode-like characters."""
        assert slugify("café résumé") == "caf-r-sum"

    def test_slugify_numbers(self):
        """Test slugify preserves numbers."""
        assert slugify("Version 2.0 Release") == "version-2-0-release"
        assert slugify("Item 123") == "item-123"

# ==================== normalize_whitespace Tests ====================

class TestNormalizeWhitespace:
    """Tests for normalize_whitespace function."""

    def test_basic_normalization(self):
        """Test basic whitespace normalization."""
        assert normalize_whitespace("  hello   world  ") == "hello world"
        assert normalize_whitespace("multiple    spaces") == "multiple spaces"

    def test_newlines_and_tabs(self):
        """Test normalization handles newlines and tabs."""
        assert normalize_whitespace("line1\n\nline2\tline3") == "line1 line2 line3"
        assert normalize_whitespace("a\nb\tc\rd") == "a b c d"

    def test_empty_string(self):
        """Test with empty string."""
        assert normalize_whitespace("") == ""
        assert normalize_whitespace("   ") == ""
        assert normalize_whitespace("\n\t\r") == ""

    def test_no_extra_whitespace(self):
        """Test string with no extra whitespace unchanged."""
        assert normalize_whitespace("hello world") == "hello world"
        assert normalize_whitespace("single") == "single"

    def test_leading_trailing_only(self):
        """Test only leading/trailing whitespace."""
        assert normalize_whitespace("  hello") == "hello"
        assert normalize_whitespace("hello  ") == "hello"

# ==================== truncate_with_ellipsis Tests ====================

class TestTruncateWithEllipsis:
    """Tests for truncate_with_ellipsis function."""

    def test_basic_truncation(self):
        """Test basic truncation with ellipsis."""
        assert truncate_with_ellipsis("Hello World", 8) == "Hello..."
        # max_length=10, ellipsis="..." (3 chars) -> text[:7] + "..." = "Long te..."
        assert truncate_with_ellipsis("Long text here", 10) == "Long te..."

    def test_no_truncation_needed(self):
        """Test when text is shorter than max_length."""
        assert truncate_with_ellipsis("Hi", 10) == "Hi"
        assert truncate_with_ellipsis("Hello", 10) == "Hello"

    def test_exact_length(self):
        """Test when text length equals max_length."""
        assert truncate_with_ellipsis("Hello", 5) == "Hello"

    def test_custom_ellipsis(self):
        """Test with custom ellipsis string."""
        # max_length=8, ellipsis=">>" (2 chars) -> text[:6] + ">>" = "Hello >>"
        assert truncate_with_ellipsis("Hello World", 8, ">>") == "Hello >>"
        assert truncate_with_ellipsis("Test", 6, "...") == "Test"

    def test_empty_string(self):
        """Test with empty string."""
        assert truncate_with_ellipsis("", 10) == ""

    def test_max_length_equals_ellipsis(self):
        """Test when max_length equals ellipsis length."""
        assert truncate_with_ellipsis("Hello", 3) == "..."

    def test_error_when_max_length_less_than_ellipsis(self):
        """Test ValueError when max_length < len(ellipsis)."""
        with pytest.raises(ValueError):
            truncate_with_ellipsis("Hello", 2, "...")

    def test_edge_case_single_char_ellipsis(self):
        """Test with single character ellipsis."""
        assert truncate_with_ellipsis("Hello", 3, ".") == "He."

# ==================== extract_words Tests ====================

class TestExtractWords:
    """Tests for extract_words function."""

    def test_basic_extraction(self):
        """Test basic word extraction."""
        assert extract_words("Hello world test") == ["Hello", "world", "test"]
        assert extract_words("one two three") == ["one", "two", "three"]

    def test_min_length_filter(self):
        """Test filtering by minimum length."""
        assert extract_words("a bc def ghij", min_length=2) == ["bc", "def", "ghij"]
        assert extract_words("a bc def ghij", min_length=3) == ["def", "ghij"]

    def test_punctuation_handling(self):
        """Test punctuation is treated as word boundary."""
        assert extract_words("Hello, world!") == ["Hello", "world"]
        assert extract_words("test-case.example") == ["test", "case", "example"]

    def test_empty_string(self):
        """Test with empty string."""
        assert extract_words("") == []
        assert extract_words("   ") == []

    def test_numbers_as_words(self):
        """Test numbers are extracted as words."""
        assert extract_words("version 2.0 release") == ["version", "2", "0", "release"]
        assert extract_words("item 123") == ["item", "123"]

    def test_min_length_edge_case_zero(self):
        """Test min_length=0 includes all words."""
        assert extract_words("a bc", min_length=0) == ["a", "bc"]

    def test_min_length_greater_than_all_words(self):
        """Test min_length greater than all word lengths."""
        assert extract_words("a bc def", min_length=10) == []

# ==================== count_words Tests ====================

class TestCountWords:
    """Tests for count_words function."""

    def test_basic_count(self):
        """Test basic word counting."""
        assert count_words("Hello world") == 2
        assert count_words("One two three four") == 4

    def test_empty_string(self):
        """Test with empty string."""
        assert count_words("") == 0
        assert count_words("   ") == 0

    def test_punctuation(self):
        """Test punctuation doesn't affect count."""
        assert count_words("Hello, world!") == 2
        assert count_words("test-case") == 2

    def test_numbers(self):
        """Test numbers are counted as words."""
        assert count_words("version 2") == 2

# ==================== reverse_words Tests ====================

class TestReverseWords:
    """Tests for reverse_words function."""

    def test_basic_reverse(self):
        """Test basic word reversal."""
        assert reverse_words("Hello world test") == "test world Hello"
        assert reverse_words("one two three") == "three two one"

    def test_single_word(self):
        """Test single word unchanged."""
        assert reverse_words("Hello") == "Hello"

    def test_empty_string(self):
        """Test with empty string."""
        assert reverse_words("") == ""
        assert reverse_words("   ") == ""

    def test_punctuation_handled(self):
        """Test punctuation is handled correctly."""
        assert reverse_words("Hello, world!") == "world Hello"

# ==================== is_palindrome Tests ====================

class TestIsPalindrome:
    """Tests for is_palindrome function."""

    def test_basic_palindrome(self):
        """Test basic palindrome detection."""
        assert is_palindrome("racecar") is True
        assert is_palindrome("level") is True
        assert is_palindrome("radar") is True

    def test_non_palindrome(self):
        """Test non-palindrome returns False."""
        assert is_palindrome("hello") is False
        assert is_palindrome("world") is False

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert is_palindrome("Racecar") is True
        assert is_palindrome("RaCeCaR") is True

    def test_ignore_non_alnum(self):
        """Test ignoring non-alphanumeric characters."""
        assert is_palindrome("A man a plan a canal Panama") is True
        assert is_palindrome("Madam, I'm Adam") is True
        assert is_palindrome("Was it a car or a cat I saw?") is True

    def test_empty_string(self):
        """Test empty string is palindrome."""
        assert is_palindrome("") is True

    def test_single_char(self):
        """Test single character is palindrome."""
        assert is_palindrome("a") is True

    def test_case_sensitive_false(self):
        """Test case sensitive mode."""
        assert is_palindrome("Racecar", ignore_case=False) is False
        assert is_palindrome("racecar", ignore_case=False) is True

    def test_keep_non_alnum(self):
        """Test keeping non-alphanumeric characters."""
        assert is_palindrome("race car", ignore_non_alnum=False) is False
        assert is_palindrome("racecar", ignore_non_alnum=False) is True

    def test_numbers_palindrome(self):
        """Test numeric palindromes."""
        assert is_palindrome("12321") is True
        assert is_palindrome("1221") is True
        assert is_palindrome("123") is False