"""
Tests for team_guard_e2e_20261124.child_c data utilities.

Covers normal inputs and at least two edge cases per function.
"""

import pytest
from team_guard_e2e_20261124.child_c import (
    validate_email,
    validate_url,
    format_phone,
    parse_json_safe,
    to_json_safe,
    flatten_dict_nested,
    unflatten_dict,
    format_timestamp,
    parse_duration,
    format_duration,
    mask_sensitive_data,
    generate_idempotency_key,
)


# ==================== validate_email Tests ====================

class TestValidateEmail:
    """Tests for validate_email function."""

    def test_valid_emails(self):
        """Test valid email formats."""
        assert validate_email("user@example.com") is True
        assert validate_email("test.email@domain.org") is True
        assert validate_email("user+tag@example.co.uk") is True
        assert validate_email("user123@test-domain.com") is True

    def test_invalid_emails(self):
        """Test invalid email formats."""
        assert validate_email("invalid-email") is False
        assert validate_email("@example.com") is False
        assert validate_email("user@") is False
        assert validate_email("user@.com") is False
        assert validate_email("user@domain") is False
        assert validate_email("user@domain.c") is False  # TLD too short

    def test_edge_cases(self):
        """Test edge cases."""
        assert validate_email("") is False
        assert validate_email("   ") is False
        assert validate_email(None) is False  # type: ignore
        assert validate_email(123) is False  # type: ignore


# ==================== validate_url Tests ====================

class TestValidateUrl:
    """Tests for validate_url function."""

    def test_valid_urls(self):
        """Test valid URL formats."""
        assert validate_url("https://example.com") is True
        assert validate_url("http://example.com") is True
        assert validate_url("https://sub.example.com/path") is True
        assert validate_url("https://example.com:8080/path?query=value") is True

    def test_invalid_urls(self):
        """Test invalid URL formats."""
        assert validate_url("not-a-url") is False
        assert validate_url("ftp://example.com") is False  # Only http/https
        assert validate_url("https://") is False
        assert validate_url("example.com") is False
        assert validate_url("") is False
        assert validate_url(None) is False  # type: ignore


# ==================== format_phone Tests ====================

class TestFormatPhone:
    """Tests for format_phone function."""

    def test_us_10_digit(self):
        """Test US 10-digit phone number."""
        assert format_phone("5551234567") == "(555) 123-4567"
        assert format_phone("555-123-4567") == "(555) 123-4567"
        assert format_phone("(555) 123-4567") == "(555) 123-4567"

    def test_us_11_digit_with_country(self):
        """Test US 11-digit with country code."""
        assert format_phone("15551234567") == "+1 (555) 123-4567"
        assert format_phone("1-555-123-4567") == "+1 (555) 123-4567"

    def test_international_format(self):
        """Test international format."""
        result = format_phone("442071234567", country_code="INTL")
        assert result.startswith("+44")

    def test_empty_string(self):
        """Test empty input."""
        assert format_phone("") == ""
        assert format_phone("   ") == ""

    def test_fallback_formatting(self):
        """Test fallback for non-standard lengths."""
        result = format_phone("123456")
        assert "123" in result and "456" in result


# ==================== parse_json_safe Tests ====================

class TestParseJsonSafe:
    """Tests for parse_json_safe function."""

    def test_valid_json(self):
        """Test parsing valid JSON."""
        assert parse_json_safe('{"key": "value"}') == {"key": "value"}
        assert parse_json_safe('{"a": 1, "b": [1, 2, 3]}') == {"a": 1, "b": [1, 2, 3]}
        assert parse_json_safe('"string"') == "string"
        assert parse_json_safe("123") == 123
        assert parse_json_safe("true") is True

    def test_invalid_json_returns_default(self):
        """Test invalid JSON returns default."""
        assert parse_json_safe("invalid", default={}) == {}
        assert parse_json_safe("{broken", default=[]) == []
        assert parse_json_safe("", default="fallback") == "fallback"

    def test_none_input(self):
        """Test None input returns default."""
        assert parse_json_safe(None, default="fallback") == "fallback"  # type: ignore

    def test_non_string_input(self):
        """Test non-string input returns default."""
        assert parse_json_safe(123, default={}) == {}  # type: ignore


# ==================== to_json_safe Tests ====================

class TestToJsonSafe:
    """Tests for to_json_safe function."""

    def test_valid_serialization(self):
        """Test serializing valid objects."""
        assert to_json_safe({"key": "value"}) == '{"key":"value"}'
        assert to_json_safe([1, 2, 3]) == "[1,2,3]"
        assert to_json_safe("string") == '"string"'

    def test_unserializable_object(self):
        """Test unserializable object returns default."""
        class Unserializable:
            pass

        assert to_json_safe(Unserializable(), default="{}") == "{}"

    def test_custom_default(self):
        """Test custom default value."""
        assert to_json_safe(object(), default='{"error":true}') == '{"error":true}'


# ==================== flatten_dict_nested Tests ====================

class TestFlattenDictNested:
    """Tests for flatten_dict_nested function."""

    def test_basic_flatten(self):
        """Test basic flattening."""
        data = {"a": {"b": 1, "c": 2}}
        assert flatten_dict_nested(data) == {"a.b": 1, "a.c": 2}

    def test_deep_nesting(self):
        """Test deep nesting."""
        data = {"a": {"b": {"c": {"d": 1}}}}
        assert flatten_dict_nested(data) == {"a.b.c.d": 1}

    def test_mixed_levels(self):
        """Test mixed nesting levels."""
        data = {"a": 1, "b": {"c": 2, "d": {"e": 3}}}
        assert flatten_dict_nested(data) == {"a": 1, "b.c": 2, "b.d.e": 3}

    def test_custom_separator(self):
        """Test custom separator."""
        data = {"a": {"b": 1}}
        assert flatten_dict_nested(data, separator="/") == {"a/b": 1}

    def test_empty_dict(self):
        """Test empty dictionary."""
        assert flatten_dict_nested({}) == {}

    def test_non_dict_values(self):
        """Test non-dict values preserved."""
        data = {"a": [1, 2], "b": {"c": "hello"}}
        result = flatten_dict_nested(data)
        assert result["a"] == [1, 2]
        assert result["b.c"] == "hello"


# ==================== unflatten_dict Tests ====================

class TestUnflattenDict:
    """Tests for unflatten_dict function."""

    def test_basic_unflatten(self):
        """Test basic unflattening."""
        data = {"a.b": 1, "a.c": 2}
        assert unflatten_dict(data) == {"a": {"b": 1, "c": 2}}

    def test_deep_unflatten(self):
        """Test deep unflattening."""
        data = {"a.b.c.d": 1}
        assert unflatten_dict(data) == {"a": {"b": {"c": {"d": 1}}}}

    def test_mixed_flat_and_nested(self):
        """Test mix of flat and nested keys."""
        data = {"a": 1, "b.c": 2, "b.d.e": 3}
        assert unflatten_dict(data) == {"a": 1, "b": {"c": 2, "d": {"e": 3}}}

    def test_custom_separator(self):
        """Test custom separator."""
        data = {"a/b": 1}
        assert unflatten_dict(data, separator="/") == {"a": {"b": 1}}

    def test_empty_dict(self):
        """Test empty dictionary."""
        assert unflatten_dict({}) == {}

    def test_round_trip(self):
        """Test flatten -> unflatten round trip."""
        original = {"a": 1, "b": {"c": 2, "d": {"e": 3}}}
        flattened = flatten_dict_nested(original)
        restored = unflatten_dict(flattened)
        assert restored == original


# ==================== format_timestamp Tests ====================

class TestFormatTimestamp:
    """Tests for format_timestamp function."""

    def test_unix_timestamp(self):
        """Test Unix timestamp formatting."""
        # 2024-01-01 00:00:00 UTC
        result = format_timestamp(1704067200)
        assert "2024-01-01" in result
        # Time may vary by timezone, just check it has time component
        assert ":" in result

    def test_iso_format_string(self):
        """Test ISO format string input."""
        result = format_timestamp("2024-01-01T00:00:00")
        assert "2024-01-01" in result

    def test_iso_format_with_z(self):
        """Test ISO format with Z suffix."""
        result = format_timestamp("2024-01-01T00:00:00Z")
        assert "2024-01-01" in result

    def test_custom_format(self):
        """Test custom format string."""
        result = format_timestamp(1704067200, "%Y/%m/%d")
        assert "2024/01/01" == result

    def test_invalid_string(self):
        """Test invalid string returns empty."""
        assert format_timestamp("not-a-timestamp") == ""

    def test_invalid_type(self):
        """Test invalid type returns empty."""
        assert format_timestamp([], ) == ""  # type: ignore


# ==================== parse_duration Tests ====================

class TestParseDuration:
    """Tests for parse_duration function."""

    def test_hours_and_minutes(self):
        """Test hours and minutes."""
        assert parse_duration("1h30m") == 5400.0
        assert parse_duration("2h") == 7200.0

    def test_minutes_only(self):
        """Test minutes only."""
        assert parse_duration("90m") == 5400.0
        assert parse_duration("45m") == 2700.0

    def test_seconds_only(self):
        """Test seconds only."""
        assert parse_duration("45s") == 45.0
        assert parse_duration("30.5s") == 30.5

    def test_full_format(self):
        """Test hours, minutes, and seconds."""
        assert parse_duration("1h30m45s") == 5445.0
        assert parse_duration("2h15m30s") == 8130.0

    def test_zero_values(self):
        """Test zero values."""
        assert parse_duration("0h0m0s") == 0.0

    def test_invalid_format(self):
        """Test invalid format raises ValueError."""
        with pytest.raises(ValueError):
            parse_duration("invalid")
        with pytest.raises(ValueError):
            parse_duration("")
        with pytest.raises(ValueError):
            parse_duration("1x30m")

    def test_whitespace_handling(self):
        """Test whitespace is handled."""
        assert parse_duration(" 1h30m ") == 5400.0


# ==================== format_duration Tests ====================

class TestFormatDuration:
    """Tests for format_duration function."""

    def test_hours_and_minutes(self):
        """Test formatting hours and minutes."""
        assert format_duration(5400) == "1h30m"
        assert format_duration(7200) == "2h"

    def test_minutes_only(self):
        """Test formatting minutes only."""
        assert format_duration(2700) == "45m"
        assert format_duration(60) == "1m"

    def test_seconds_only(self):
        """Test formatting seconds only."""
        assert format_duration(45) == "45s"
        assert format_duration(0) == "0s"

    def test_full_format(self):
        """Test formatting hours, minutes, seconds."""
        assert format_duration(3661) == "1h1m1s"
        assert format_duration(5445) == "1h30m45s"

    def test_negative_seconds(self):
        """Test negative seconds returns 0s."""
        assert format_duration(-10) == "0s"


# ==================== mask_sensitive_data Tests ====================

class TestMaskSensitiveData:
    """Tests for mask_sensitive_data function."""

    def test_basic_masking(self):
        """Test basic masking."""
        assert mask_sensitive_data("1234567890") == "******7890"
        # "secretpassword" = 14 chars, visible=4 -> 10 masked + "word"
        assert mask_sensitive_data("secretpassword") == "**********word"

    def test_custom_visible_chars(self):
        """Test custom visible character count."""
        assert mask_sensitive_data("1234567890", visible_chars=2) == "********90"
        assert mask_sensitive_data("secret", visible_chars=3) == "***ret"

    def test_custom_mask_char(self):
        """Test custom mask character."""
        assert mask_sensitive_data("1234567890", mask_char="X") == "XXXXXX7890"
        # "secret" = 6 chars, visible=4 -> 2 masked + "cret"
        assert mask_sensitive_data("secret", mask_char="#") == "##cret"

    def test_short_string(self):
        """Test string shorter than visible_chars."""
        assert mask_sensitive_data("123", visible_chars=4) == "***"
        assert mask_sensitive_data("ab", visible_chars=4) == "**"

    def test_empty_string(self):
        """Test empty string."""
        assert mask_sensitive_data("") == ""

    def test_exact_length(self):
        """Test string exactly visible_chars length."""
        assert mask_sensitive_data("1234", visible_chars=4) == "****"


# ==================== generate_idempotency_key Tests ====================

class TestGenerateIdempotencyKey:
    """Tests for generate_idempotency_key function."""

    def test_basic_generation(self):
        """Test basic key generation."""
        key = generate_idempotency_key()
        assert len(key) == 16
        assert all(c in "0123456789abcdef" for c in key)

    def test_with_prefix(self):
        """Test key with prefix."""
        key = generate_idempotency_key("order_")
        assert key.startswith("order_")
        assert len(key) == len("order_") + 16

    def test_custom_length(self):
        """Test custom length."""
        key = generate_idempotency_key(length=32)
        assert len(key) == 32

    def test_uniqueness(self):
        """Test keys are unique."""
        keys = [generate_idempotency_key() for _ in range(10)]
        assert len(set(keys)) == 10

    def test_deterministic_not_crypto(self):
        """Test that it's deterministic in nature (not crypto-secure)."""
        # This is expected behavior - function is for testing determinism
        key1 = generate_idempotency_key()
        key2 = generate_idempotency_key()
        # They should be different due to time/counter
        assert key1 != key2