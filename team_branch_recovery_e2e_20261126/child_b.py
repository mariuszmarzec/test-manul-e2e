"""
Deterministic text-processing utility for TEAM-BRANCH-RECOVERY-E2E-20261126 Child B.

This module provides a collection of pure, deterministic text processing functions
with comprehensive type hints and docstrings. All functions are side-effect free
and produce consistent outputs for given inputs.
"""

import re
from collections import Counter
from typing import Dict, List, Optional, Set, Tuple


# Module-level constants for default configurations
DEFAULT_WORD_SEPARATORS = r"[\s\p{P}]+"  # Unicode-aware word splitting
DEFAULT_MAX_TOKEN_LENGTH = 100
DEFAULT_TRUNCATION_SUFFIX = "…"


def count_words(text: str, *, case_sensitive: bool = False) -> Dict[str, int]:
    """
    Count occurrences of each word in the given text.

    Words are split on whitespace and punctuation. Empty strings are ignored.

    Args:
        text: Input text to analyze.
        case_sensitive: If False (default), words are lowercased before counting.

    Returns:
        Dictionary mapping each word to its count.

    Examples:
        >>> count_words("Hello hello world")
        {'hello': 2, 'world': 1}
        >>> count_words("Hello hello world", case_sensitive=True)
        {'Hello': 1, 'hello': 1, 'world': 1}
    """
    if not text:
        return {}

    # Split on non-word characters (Unicode-aware)
    words = re.split(r"[\W_]+", text, flags=re.UNICODE)
    words = [w for w in words if w]  # Remove empty strings

    if not case_sensitive:
        words = [w.lower() for w in words]

    return dict(Counter(words))


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text: collapse runs of whitespace to single spaces,
    strip leading/trailing whitespace, and convert all whitespace chars to space.

    Args:
        text: Input text possibly containing tabs, newlines, multiple spaces.

    Returns:
        Text with normalized whitespace.

    Examples:
        >>> normalize_whitespace("  hello\\t\\nworld  ")
        'hello world'
        >>> normalize_whitespace("")
        ''
    """
    if not text:
        return ""
    # Replace all whitespace sequences with a single space, then strip
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str, *, max_token_length: int = DEFAULT_MAX_TOKEN_LENGTH) -> List[str]:
    """
    Split text into tokens (words), filtering out empty tokens and truncating long ones.

    Args:
        text: Input text to tokenize.
        max_token_length: Maximum allowed token length; longer tokens are truncated.

    Returns:
        List of tokens in order of appearance.

    Examples:
        >>> tokenize("Hello, world! This is a test.")
        ['Hello', 'world', 'This', 'is', 'a', 'test']
        >>> tokenize("supercalifragilisticexpialidocious", max_token_length=10)
        ['supercalif']
    """
    if not text:
        return []

    # Split on non-word characters
    tokens = re.split(r"[\W_]+", text, flags=re.UNICODE)
    tokens = [t for t in tokens if t]  # Remove empty strings

    # Truncate tokens that exceed max length
    if max_token_length > 0:
        tokens = [t[:max_token_length] for t in tokens]

    return tokens


def extract_patterns(
    text: str,
    pattern: str,
    *,
    flags: int = 0,
    max_matches: Optional[int] = None,
) -> List[str]:
    """
    Extract all non-overlapping matches of a regex pattern from text.

    Args:
        text: Input text to search.
        pattern: Regular expression pattern with at least one capturing group.
                 If no capturing group exists, the entire match is returned.
        flags: Regex flags (e.g., re.IGNORECASE, re.MULTILINE).
        max_matches: Maximum number of matches to return (None for unlimited).

    Returns:
        List of matched strings (capture group 1 if present, else full match).

    Examples:
        >>> extract_patterns("abc123def456", r"(\\d+)")
        ['123', '456']
        >>> extract_patterns("User: alice, User: bob", r"User:\\s*(\\w+)")
        ['alice', 'bob']
    """
    if not text or not pattern:
        return []

    compiled = re.compile(pattern, flags)
    matches = []

    for match in compiled.finditer(text):
        if match.groups():
            # Use first capturing group
            matches.append(match.group(1))
        else:
            # No capturing groups, use full match
            matches.append(match.group(0))

        if max_matches is not None and len(matches) >= max_matches:
            break

    return matches


def compute_text_statistics(text: str) -> Dict[str, object]:
    """
    Compute various statistics about the input text.

    Args:
        text: Input text to analyze.

    Returns:
        Dictionary containing:
        - 'char_count': Total characters including whitespace
        - 'char_count_no_space': Characters excluding whitespace
        - 'word_count': Number of words (split on whitespace/punctuation)
        - 'line_count': Number of lines
        - 'sentence_count': Estimated sentence count (split on .!?)
        - 'avg_word_length': Average word length (float)
        - 'unique_words': Number of unique words (case-insensitive)
        - 'most_common_word': Tuple of (word, count) or None if no words

    Examples:
        >>> stats = compute_text_statistics("Hello world. Hello!")
        >>> stats['word_count']
        3
        >>> stats['unique_words']
        2
    """
    if not text:
        return {
            "char_count": 0,
            "char_count_no_space": 0,
            "word_count": 0,
            "line_count": 0,
            "sentence_count": 0,
            "avg_word_length": 0.0,
            "unique_words": 0,
            "most_common_word": None,
        }

    char_count = len(text)
    char_count_no_space = len(re.sub(r"\s", "", text))

    words = tokenize(text)
    word_count = len(words)

    line_count = text.count("\n") + 1 if text else 0

    # Estimate sentences by counting sentence-ending punctuation
    sentence_count = len(re.findall(r"[.!?]+", text))

    avg_word_length = sum(len(w) for w in words) / word_count if word_count > 0 else 0.0

    word_counts = count_words(text, case_sensitive=False)
    unique_words = len(word_counts)
    most_common = max(word_counts.items(), key=lambda x: x[1]) if word_counts else None

    return {
        "char_count": char_count,
        "char_count_no_space": char_count_no_space,
        "word_count": word_count,
        "line_count": line_count,
        "sentence_count": sentence_count,
        "avg_word_length": round(avg_word_length, 2),
        "unique_words": unique_words,
        "most_common_word": most_common,
    }


def truncate_text(
    text: str,
    max_length: int,
    *,
    suffix: str = DEFAULT_TRUNCATION_SUFFIX,
    respect_word_boundary: bool = True,
) -> str:
    """
    Truncate text to a maximum length, optionally respecting word boundaries.

    Args:
        text: Input text to truncate.
        max_length: Maximum length of returned string (including suffix).
        suffix: String to append when truncation occurs.
        respect_word_boundary: If True, truncate at last word boundary before max_length.

    Returns:
        Truncated text with suffix if truncation occurred, otherwise original text.

    Examples:
        >>> truncate_text("Hello world", 8)
        'Hello…'
        >>> truncate_text("Hello world", 8, respect_word_boundary=False)
        'Hello w…'
    """
    if max_length <= 0:
        return ""

    if not text or len(text) <= max_length:
        return text

    if len(suffix) >= max_length:
        return suffix[:max_length]

    if respect_word_boundary:
        # Find the last space within the allowed length (minus suffix)
        limit = max_length - len(suffix)
        truncated = text[:limit]
        last_space = truncated.rfind(" ")
        if last_space > 0:
            return truncated[:last_space] + suffix

    # Fallback: hard truncate
    return text[: max_length - len(suffix)] + suffix


def remove_duplicate_lines(text: str, *, case_sensitive: bool = True) -> str:
    """
    Remove duplicate lines from text while preserving order of first occurrence.

    Args:
        text: Input text with potentially duplicate lines.
        case_sensitive: If False, comparison is case-insensitive.

    Returns:
        Text with duplicate lines removed, joined by newlines.

    Examples:
        >>> remove_duplicate_lines("a\\nb\\na\\nc")
        'a\\nb\\nc'
        >>> remove_duplicate_lines("A\\na\\nB", case_sensitive=False)
        'A\\nB'
    """
    if not text:
        return ""

    lines = text.splitlines()
    seen: Set[str] = set()
    result: List[str] = []

    for line in lines:
        key = line if case_sensitive else line.lower()
        if key not in seen:
            seen.add(key)
            result.append(line)

    return "\n".join(result)


def find_common_prefix(strings: List[str]) -> str:
    """
    Find the longest common prefix among a list of strings.

    Args:
        strings: List of strings to compare.

    Returns:
        Longest common prefix (empty string if no common prefix or list is empty).

    Examples:
        >>> find_common_prefix(["flower", "flow", "flight"])
        'fl'
        >>> find_common_prefix(["dog", "racecar", "car"])
        ''
    """
    if not strings:
        return ""

    if len(strings) == 1:
        return strings[0]

    # Sort and compare first and last (min and max lexicographically)
    sorted_strings = sorted(strings)
    first = sorted_strings[0]
    last = sorted_strings[-1]

    min_len = min(len(first), len(last))
    i = 0
    while i < min_len and first[i] == last[i]:
        i += 1

    return first[:i]


def split_into_chunks(
    text: str,
    chunk_size: int,
    *,
    overlap: int = 0,
    separator: str = " ",
) -> List[str]:
    """
    Split text into overlapping chunks of approximately equal size.

    Attempts to split at word boundaries (separator) when possible.

    Args:
        text: Input text to split.
        chunk_size: Target size of each chunk in characters.
        overlap: Number of characters to overlap between adjacent chunks.
        separator: Character used to find word boundaries (default: space).

    Returns:
        List of text chunks.

    Examples:
        >>> split_into_chunks("one two three four five", 10)
        ['one two', 'three four', 'five']
        >>> split_into_chunks("one two three four five", 10, overlap=3)
        ['one two', 'two three', 'three four', 'four five']
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("overlap must be non-negative")
    if overlap >= chunk_size:
        raise ValueError("overlap must be less than chunk_size")

    if not text:
        return []

    words = text.split(separator)
    if not words:
        return []

    chunks: List[str] = []
    current_chunk: List[str] = []
    current_length = 0

    for word in words:
        word_len = len(word)
        # +1 for separator if not first word
        needed = word_len + (1 if current_chunk else 0)

        if current_length + needed > chunk_size and current_chunk:
            # Finalize current chunk
            chunks.append(separator.join(current_chunk))
            # Start new chunk with overlap
            if overlap > 0:
                # Take words from end of previous chunk for overlap
                overlap_text = separator.join(current_chunk)
                overlap_words = overlap_text[-overlap:].split(separator)
                # Keep only complete words from overlap
                current_chunk = [w for w in overlap_words if w]
                current_length = sum(len(w) for w in current_chunk) + len(current_chunk) - 1
            else:
                current_chunk = []
                current_length = 0

        if current_chunk:
            current_chunk.append(word)
            current_length += 1 + word_len
        else:
            current_chunk = [word]
            current_length = word_len

    if current_chunk:
        chunks.append(separator.join(current_chunk))

    return chunks


def compare_texts(text1: str, text2: str) -> Dict[str, object]:
    """
    Compare two texts and return similarity metrics.

    Args:
        text1: First text.
        text2: Second text.

    Returns:
        Dictionary containing:
        - 'jaccard_similarity': Jaccard index of word sets (0.0 to 1.0)
        - 'common_words': Set of words appearing in both texts
        - 'unique_to_text1': Set of words only in text1
        - 'unique_to_text2': Set of words only in text2
        - 'length_ratio': Ratio of lengths (min/max, 0.0 to 1.0)
        - 'equal': Boolean indicating exact equality

    Examples:
        >>> result = compare_texts("hello world", "hello there")
        >>> result['jaccard_similarity']
        0.333...
        >>> result['common_words']
        {'hello'}
    """
    words1 = set(tokenize(text1.lower()))
    words2 = set(tokenize(text2.lower()))

    intersection = words1 & words2
    union = words1 | words2

    jaccard = len(intersection) / len(union) if union else 1.0

    len1, len2 = len(text1), len(text2)
    length_ratio = min(len1, len2) / max(len1, len2) if max(len1, len2) > 0 else 1.0

    return {
        "jaccard_similarity": round(jaccard, 4),
        "common_words": intersection,
        "unique_to_text1": words1 - words2,
        "unique_to_text2": words2 - words1,
        "length_ratio": round(length_ratio, 4),
        "equal": text1 == text2,
    }


# Convenience function for common workflow
def process_document(
    text: str,
    *,
    normalize: bool = True,
    remove_duplicates: bool = False,
    max_length: Optional[int] = None,
) -> Tuple[str, Dict[str, object]]:
    """
    Process a document through a standard pipeline.

    Args:
        text: Input document text.
        normalize: Whether to normalize whitespace.
        remove_duplicates: Whether to remove duplicate lines.
        max_length: Optional maximum length for truncation.

    Returns:
        Tuple of (processed_text, statistics_dict).
    """
    processed = text

    if normalize:
        processed = normalize_whitespace(processed)

    if remove_duplicates:
        processed = remove_duplicate_lines(processed)

    if max_length is not None and max_length > 0:
        processed = truncate_text(processed, max_length)

    stats = compute_text_statistics(processed)
    return processed, stats