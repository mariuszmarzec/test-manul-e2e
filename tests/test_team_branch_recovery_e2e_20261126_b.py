"""
Tests for team_branch_recovery_e2e_20261126.child_b text processing utilities.

Covers normal operation, edge cases, and error conditions.
"""

import re
import pytest
from team_branch_recovery_e2e_20261126.child_b import (
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
    DEFAULT_MAX_TOKEN_LENGTH,
    DEFAULT_TRUNCATION_SUFFIX,
)


# =============================================================================
# count_words tests
# =============================================================================

class TestCountWords:
    """Tests for count_words function."""

    def test_basic_counting(self):
        text = "hello world hello"
        result = count_words(text)
        assert result == {"hello": 2, "world": 1}

    def test_case_insensitive_default(self):
        text = "Hello HELLO hello"
        result = count_words(text)
        assert result == {"hello": 3}

    def test_case_sensitive_option(self):
        text = "Hello HELLO hello"
        result = count_words(text, case_sensitive=True)
        assert result == {"Hello": 1, "HELLO": 1, "hello": 1}

    def test_punctuation_handling(self):
        text = "Hello, world! Hello... world?"
        result = count_words(text)
        assert result == {"hello": 2, "world": 2}

    def test_empty_string(self):
        assert count_words("") == {}
        assert count_words("   ") == {}
        assert count_words("\n\t") == {}

    def test_unicode_words(self):
        text = "café naïve résumé café"
        result = count_words(text)
        assert result == {"café": 2, "naïve": 1, "résumé": 1}

    def test_numbers_and_symbols(self):
        text = "version 2.0 beta-1 test_2"
        result = count_words(text)
        # Numbers and hyphens/underscores are split
        assert "version" in result
        assert "2" in result
        assert "0" in result
        assert "beta" in result
        assert "1" in result
        assert "test" in result


# =============================================================================
# normalize_whitespace tests
# =============================================================================

class TestNormalizeWhitespace:
    """Tests for normalize_whitespace function."""

    def test_multiple_spaces(self):
        assert normalize_whitespace("hello    world") == "hello world"

    def test_tabs_and_newlines(self):
        assert normalize_whitespace("hello\t\nworld") == "hello world"

    def test_leading_trailing(self):
        assert normalize_whitespace("  hello world  ") == "hello world"

    def test_mixed_whitespace(self):
        assert normalize_whitespace("\t  hello \n\n world \r\n ") == "hello world"

    def test_empty_string(self):
        assert normalize_whitespace("") == ""
        assert normalize_whitespace("   ") == ""

    def test_no_whitespace(self):
        assert normalize_whitespace("helloworld") == "helloworld"

    def test_unicode_whitespace(self):
        # Non-breaking space and other unicode whitespace
        assert normalize_whitespace("hello\u00A0world") == "hello world"


# =============================================================================
# tokenize tests
# =============================================================================

class TestTokenize:
    """Tests for tokenize function."""

    def test_basic_tokenization(self):
        text = "Hello, world! This is a test."
        tokens = tokenize(text)
        assert tokens == ["Hello", "world", "This", "is", "a", "test"]

    def test_empty_string(self):
        assert tokenize("") == []
        assert tokenize("   ") == []

    def test_punctuation_only(self):
        assert tokenize("!!! ??? ...") == []

    def test_max_token_length_truncation(self):
        text = "supercalifragilisticexpialidocious"
        tokens = tokenize(text, max_token_length=10)
        assert tokens == ["supercalif"]

    def test_max_token_length_zero_disables(self):
        text = "hello world"
        tokens = tokenize(text, max_token_length=0)
        assert tokens == ["hello", "world"]

    def test_hyphenated_words(self):
        text = "state-of-the-art"
        tokens = tokenize(text)
        assert tokens == ["state", "of", "the", "art"]

    def test_unicode_tokens(self):
        text = "café naïve résumé"
        tokens = tokenize(text)
        assert tokens == ["café", "naïve", "résumé"]


# =============================================================================
# extract_patterns tests
# =============================================================================

class TestExtractPatterns:
    """Tests for extract_patterns function."""

    def test_capturing_group(self):
        text = "abc123def456"
        matches = extract_patterns(text, r"(\d+)")
        assert matches == ["123", "456"]

    def test_no_capturing_group_returns_full_match(self):
        text = "abc123def456"
        matches = extract_patterns(text, r"\d+")
        assert matches == ["123", "456"]

    def test_multiple_capturing_groups_uses_first(self):
        text = "name: alice, age: 30"
        matches = extract_patterns(text, r"name:\s*(\w+),\s*age:\s*(\d+)")
        assert matches == ["alice"]

    def test_max_matches_limit(self):
        text = "1 2 3 4 5"
        matches = extract_patterns(text, r"(\d)", max_matches=3)
        assert matches == ["1", "2", "3"]

    def test_flags_ignore_case(self):
        text = "USER: alice, user: bob"
        matches = extract_patterns(text, r"user:\s*(\w+)", flags=re.IGNORECASE)
        assert matches == ["alice", "bob"]

    def test_empty_text(self):
        assert extract_patterns("", r"(\w+)") == []

    def test_empty_pattern(self):
        assert extract_patterns("hello", "") == []

    def test_no_matches(self):
        assert extract_patterns("hello world", r"\d+") == []

    def test_overlapping_not_supported(self):
        # finditer finds non-overlapping matches
        text = "aaa"
        matches = extract_patterns(text, r"(aa)")
        assert matches == ["aa"]  # Only one non-overlapping match


# =============================================================================
# compute_text_statistics tests
# =============================================================================

class TestComputeTextStatistics:
    """Tests for compute_text_statistics function."""

    def test_basic_statistics(self):
        text = "Hello world. Hello!"
        stats = compute_text_statistics(text)
        assert stats["char_count"] == len(text)
        assert stats["word_count"] == 3
        assert stats["sentence_count"] == 2
        assert stats["line_count"] == 1
        assert stats["unique_words"] == 2
        assert stats["most_common_word"] == ("hello", 2)

    def test_empty_text(self):
        stats = compute_text_statistics("")
        assert stats["char_count"] == 0
        assert stats["word_count"] == 0
        assert stats["line_count"] == 0
        assert stats["sentence_count"] == 0
        assert stats["avg_word_length"] == 0.0
        assert stats["unique_words"] == 0
        assert stats["most_common_word"] is None

    def test_multiline_text(self):
        text = "Line 1\nLine 2\nLine 3"
        stats = compute_text_statistics(text)
        assert stats["line_count"] == 3
        assert stats["word_count"] == 6

    def test_avg_word_length_calculation(self):
        text = "a bb ccc"
        stats = compute_text_statistics(text)
        # (1 + 2 + 3) / 3 = 2.0
        assert stats["avg_word_length"] == 2.0

    def test_whitespace_char_count(self):
        text = "hello world"
        stats = compute_text_statistics(text)
        assert stats["char_count"] == 11
        assert stats["char_count_no_space"] == 10

    def test_only_whitespace(self):
        text = "   \n\t  "
        stats = compute_text_statistics(text)
        assert stats["word_count"] == 0
        assert stats["char_count"] > 0
        assert stats["char_count_no_space"] == 0


# =============================================================================
# truncate_text tests
# =============================================================================

class TestTruncateText:
    """Tests for truncate_text function."""

    def test_no_truncation_needed(self):
        text = "Hello world"
        assert truncate_text(text, 20) == "Hello world"

    def test_truncation_with_suffix(self):
        text = "Hello world"
        result = truncate_text(text, 8)
        assert result == "Hello…"
        assert len(result) <= 8

    def test_respect_word_boundary_true(self):
        text = "Hello world"
        # Limit allows "Hello" but not "Hello w"
        result = truncate_text(text, 8, respect_word_boundary=True)
        assert result == "Hello…"

    def test_respect_word_boundary_false(self):
        text = "Hello world"
        result = truncate_text(text, 8, respect_word_boundary=False)
        assert result == "Hello w…"

    def test_custom_suffix(self):
        text = "Hello world"
        result = truncate_text(text, 10, suffix="---")
        assert result.endswith("---")

    def test_suffix_longer_than_max(self):
        text = "Hello world"
        result = truncate_text(text, 2, suffix="---")
        assert result == "--"

    def test_max_length_zero(self):
        assert truncate_text("hello", 0) == ""

    def test_max_length_negative(self):
        assert truncate_text("hello", -5) == ""

    def test_exact_fit(self):
        text = "Hello"
        assert truncate_text(text, 5) == "Hello"

    def test_unicode_handling(self):
        text = "café naïve"
        result = truncate_text(text, 6)
        # "café" is 4 chars, " naï" would be 4 more
        assert len(result) <= 6


# =============================================================================
# remove_duplicate_lines tests
# =============================================================================

class TestRemoveDuplicateLines:
    """Tests for remove_duplicate_lines function."""

    def test_basic_deduplication(self):
        text = "a\nb\na\nc"
        result = remove_duplicate_lines(text)
        assert result == "a\nb\nc"

    def test_case_sensitive_default(self):
        text = "A\na\nB"
        result = remove_duplicate_lines(text)
        assert result == "A\na\nB"

    def test_case_insensitive_option(self):
        text = "A\na\nB"
        result = remove_duplicate_lines(text, case_sensitive=False)
        assert result == "A\nB"

    def test_empty_string(self):
        assert remove_duplicate_lines("") == ""

    def test_no_duplicates(self):
        text = "a\nb\nc"
        assert remove_duplicate_lines(text) == "a\nb\nc"

    def test_all_duplicates(self):
        text = "a\na\na"
        assert remove_duplicate_lines(text) == "a"

    def test_preserves_order(self):
        text = "z\na\nz\nb\na"
        result = remove_duplicate_lines(text)
        assert result == "z\na\nb"

    def test_empty_lines(self):
        text = "a\n\nb\n\nc"
        result = remove_duplicate_lines(text)
        # Empty line is a valid line
        assert result == "a\n\nb\nc"


# =============================================================================
# find_common_prefix tests
# =============================================================================

class TestFindCommonPrefix:
    """Tests for find_common_prefix function."""

    def test_common_prefix_exists(self):
        assert find_common_prefix(["flower", "flow", "flight"]) == "fl"

    def test_no_common_prefix(self):
        assert find_common_prefix(["dog", "racecar", "car"]) == ""

    def test_single_string(self):
        assert find_common_prefix(["hello"]) == "hello"

    def test_empty_list(self):
        assert find_common_prefix([]) == ""

    def test_identical_strings(self):
        assert find_common_prefix(["hello", "hello", "hello"]) == "hello"

    def test_one_string_is_prefix(self):
        assert find_common_prefix(["hello", "hello world"]) == "hello"

    def test_unicode_strings(self):
        assert find_common_prefix(["café", "cafétéria"]) == "café"


# =============================================================================
# split_into_chunks tests
# =============================================================================

class TestSplitIntoChunks:
    """Tests for split_into_chunks function."""

    def test_basic_splitting(self):
        text = "one two three four five"
        chunks = split_into_chunks(text, 10)
        # Should split at word boundaries near 10 chars
        assert len(chunks) >= 2
        assert all(len(c) <= 10 for c in chunks)

    def test_overlap(self):
        text = "one two three four five"
        chunks = split_into_chunks(text, 10, overlap=3)
        assert len(chunks) >= 2

    def test_empty_text(self):
        assert split_into_chunks("", 10) == []

    def test_single_word_longer_than_chunk(self):
        text = "supercalifragilisticexpialidocious"
        chunks = split_into_chunks(text, 10)
        # Will create chunks even if word is longer
        assert len(chunks) >= 1

    def test_invalid_chunk_size_zero(self):
        with pytest.raises(ValueError, match="chunk_size must be positive"):
            split_into_chunks("hello", 0)

    def test_invalid_chunk_size_negative(self):
        with pytest.raises(ValueError, match="chunk_size must be positive"):
            split_into_chunks("hello", -5)

    def test_invalid_overlap_negative(self):
        with pytest.raises(ValueError, match="overlap must be non-negative"):
            split_into_chunks("hello", 10, overlap=-1)

    def test_invalid_overlap_ge_chunk_size(self):
        with pytest.raises(ValueError, match="overlap must be less than chunk_size"):
            split_into_chunks("hello", 10, overlap=10)

    def test_custom_separator(self):
        text = "one,two,three,four,five"
        chunks = split_into_chunks(text, 10, separator=",")
        assert len(chunks) >= 2


# =============================================================================
# compare_texts tests
# =============================================================================

class TestCompareTexts:
    """Tests for compare_texts function."""

    def test_identical_texts(self):
        text = "hello world"
        result = compare_texts(text, text)
        assert result["equal"] is True
        assert result["jaccard_similarity"] == 1.0
        assert result["length_ratio"] == 1.0

    def test_completely_different(self):
        result = compare_texts("hello world", "foo bar")
        assert result["equal"] is False
        assert result["jaccard_similarity"] == 0.0
        assert result["common_words"] == set()

    def test_partial_overlap(self):
        result = compare_texts("hello world", "hello there")
        assert result["common_words"] == {"hello"}
        assert result["unique_to_text1"] == {"world"}
        assert result["unique_to_text2"] == {"there"}
        assert result["jaccard_similarity"] == pytest.approx(1/3, rel=0.01)

    def test_empty_strings(self):
        result = compare_texts("", "")
        assert result["equal"] is True
        assert result["jaccard_similarity"] == 1.0

    def test_one_empty(self):
        result = compare_texts("hello", "")
        assert result["equal"] is False
        assert result["jaccard_similarity"] == 0.0
        assert result["length_ratio"] == 0.0

    def test_case_insensitive_comparison(self):
        result = compare_texts("HELLO WORLD", "hello world")
        assert result["jaccard_similarity"] == 1.0
        # But exact equality is False
        assert result["equal"] is False


# =============================================================================
# process_document tests
# =============================================================================

class TestProcessDocument:
    """Tests for process_document function."""

    def test_full_pipeline(self):
        text = "  Line 1\n\nLine 1\nLine 2  "
        processed, stats = process_document(
            text,
            normalize=True,
            remove_duplicates=True,
            max_length=20,
        )
        assert "Line 1" in processed
        assert "Line 2" in processed
        # Note: normalize runs first, converting newlines to spaces,
        # so remove_duplicates operates on a single line.
        # The result is normalized whitespace with truncation.
        assert stats["word_count"] > 0
        assert len(processed) <= 20

    def test_normalize_only(self):
        text = "  hello   world  "
        processed, stats = process_document(text, normalize=True, remove_duplicates=False)
        assert processed == "hello world"

    def test_remove_duplicates_only(self):
        text = "a\na\nb"
        processed, stats = process_document(text, normalize=False, remove_duplicates=True)
        assert processed == "a\nb"

    def test_truncation_only(self):
        text = "hello world"
        processed, stats = process_document(text, max_length=8)
        assert processed == "hello…"

    def test_no_processing(self):
        text = "hello world"
        processed, stats = process_document(
            text, normalize=False, remove_duplicates=False, max_length=None
        )
        assert processed == "hello world"

    def test_empty_text(self):
        processed, stats = process_document("")
        assert processed == ""
        assert stats["word_count"] == 0


# =============================================================================
# Integration / workflow tests
# =============================================================================

class TestIntegration:
    """Integration tests combining multiple functions."""

    def test_tokenize_then_count(self):
        text = "Hello, world! Hello again."
        tokens = tokenize(text)
        counts = count_words(text)
        assert len(tokens) == sum(counts.values())

    def test_stats_consistency(self):
        text = "This is a test. This is only a test."
        stats = compute_text_statistics(text)
        words = tokenize(text)
        assert stats["word_count"] == len(words)
        assert stats["unique_words"] == len(set(w.lower() for w in words))

    def test_truncate_then_stats(self):
        text = "This is a long text that will be truncated."
        truncated = truncate_text(text, 20)
        stats = compute_text_statistics(truncated)
        assert stats["char_count"] <= 20

    def test_deduplicate_then_chunk(self):
        text = "a b c\na b c\nd e f"
        deduped = remove_duplicate_lines(text)
        chunks = split_into_chunks(deduped, 10)
        assert len(chunks) >= 1


# =============================================================================
# Edge case stress tests
# =============================================================================

class TestEdgeCases:
    """Edge case and stress tests."""

    def test_very_long_text(self):
        text = "word " * 10000
        stats = compute_text_statistics(text)
        assert stats["word_count"] == 10000

    def test_many_unique_words(self):
        text = " ".join(f"word{i}" for i in range(1000))
        stats = compute_text_statistics(text)
        assert stats["unique_words"] == 1000

    def test_many_duplicate_lines(self):
        text = "\n".join(["same line"] * 1000)
        result = remove_duplicate_lines(text)
        assert result == "same line"

    def test_deeply_nested_punctuation(self):
        text = "((((hello))))"
        tokens = tokenize(text)
        assert tokens == ["hello"]

    def test_mixed_scripts(self):
        text = "hello 世界 привет мир"
        tokens = tokenize(text)
        assert len(tokens) == 4

    def test_emoji_handling(self):
        text = "Hello 👋 world 🌍"
        tokens = tokenize(text)
        # Emojis are split as separate "words" by \W
        assert "Hello" in tokens
        assert "world" in tokens


# =============================================================================
# Determinism tests
# =============================================================================

class TestDeterminism:
    """Verify functions are pure and deterministic."""

    def test_count_words_deterministic(self):
        text = "hello world hello"
        for _ in range(10):
            assert count_words(text) == {"hello": 2, "world": 1}

    def test_tokenize_deterministic(self):
        text = "Hello, world! Test."
        for _ in range(10):
            assert tokenize(text) == ["Hello", "world", "Test"]

    def test_statistics_deterministic(self):
        text = "Consistent results matter."
        for _ in range(10):
            assert compute_text_statistics(text) == compute_text_statistics(text)

    def test_compare_texts_deterministic(self):
        t1, t2 = "text one", "text two"
        for _ in range(10):
            assert compare_texts(t1, t2) == compare_texts(t1, t2)

    def test_no_side_effects_on_input(self):
        # Functions should not modify input strings
        text = "  hello   world  "
        original = text
        normalize_whitespace(text)
        tokenize(text)
        count_words(text)
        compute_text_statistics(text)
        truncate_text(text, 10)
        remove_duplicate_lines(text)
        assert text == original  # String unchanged (immutable in Python anyway)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])