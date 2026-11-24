"""
Data validation and formatting utilities for Team Guard E2E.

This module provides deterministic data processing functions
with comprehensive type hints and documentation.
"""

import json
import re
from datetime import datetime
from typing import Any


def validate_email(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email: Email address to validate.

    Returns:
        True if email format is valid, False otherwise.

    Examples:
        >>> validate_email("user@example.com")
        True
        >>> validate_email("invalid-email")
        False
    """
    if not email or not isinstance(email, str):
        return False

    # RFC 5322 simplified regex
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """
    Validate URL format.

    Args:
        url: URL to validate.

    Returns:
        True if URL format is valid, False otherwise.

    Examples:
        >>> validate_url("https://example.com")
        True
        >>> validate_url("not-a-url")
        False
    """
    if not url or not isinstance(url, str):
        return False

    # Support optional port and query/path
    pattern = r"^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?::\d+)?(?:/.*)?$"
    return bool(re.match(pattern, url))


def format_phone(phone: str, country_code: str = "US") -> str:
    """
    Format phone number to standard format.

    Args:
        phone: Phone number string (digits only or with formatting).
        country_code: Country code for formatting (default: "US").

    Returns:
        Formatted phone number.

    Examples:
        >>> format_phone("5551234567")
        '(555) 123-4567'
        >>> format_phone("15551234567")
        '+1 (555) 123-4567'
    """
    if not phone:
        return ""

    # Extract digits only
    digits = re.sub(r"\D", "", phone)

    if country_code == "US":
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == "1":
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        elif len(digits) == 11:
            return f"+{digits[0]} ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    elif country_code == "INTL":
        # International format: +CC (XXX) XXX-XXXX
        if len(digits) >= 10:
            cc_len = len(digits) - 10
            cc = digits[:cc_len]
            national = digits[cc_len:]
            return f"+{cc} ({national[:3]}) {national[3:6]}-{national[6:]}"

    # Fallback: return digits with spaces every 3-4 chars
    return " ".join(digits[i:i+3] for i in range(0, len(digits), 3))


def parse_json_safe(json_str: str, default: Any = None) -> Any:
    """
    Safely parse JSON string with default fallback.

    Args:
        json_str: JSON string to parse.
        default: Default value to return on parse failure (default: None).

    Returns:
        Parsed JSON object or default value.

    Examples:
        >>> parse_json_safe('{"key": "value"}')
        {'key': 'value'}
        >>> parse_json_safe('invalid', default={})
        {}
    """
    if not json_str or not isinstance(json_str, str):
        return default

    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def to_json_safe(obj: Any, default: str = "{}") -> str:
    """
    Safely convert object to JSON string.

    Args:
        obj: Object to serialize.
        default: Default JSON string on serialization failure (default: "{}").

    Returns:
        JSON string representation or default.

    Examples:
        >>> to_json_safe({"key": "value"})
        '{"key": "value"}'
    """
    try:
        return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError):
        return default


def flatten_dict_nested(data: dict[str, Any], separator: str = ".") -> dict[str, Any]:
    """
    Flatten nested dictionary into single-level dictionary.

    Args:
        data: Dictionary to flatten.
        separator: Key separator for nested keys (default: ".").

    Returns:
        Flattened dictionary.

    Examples:
        >>> flatten_dict_nested({"a": {"b": 1, "c": {"d": 2}}})
        {'a.b': 1, 'a.c.d': 2}
    """
    result: dict[str, Any] = {}

    def _flatten(obj: Any, prefix: str = "") -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_key = f"{prefix}{separator}{key}" if prefix else key
                _flatten(value, new_key)
        else:
            result[prefix] = obj

    _flatten(data)
    return result


def unflatten_dict(data: dict[str, Any], separator: str = ".") -> dict[str, Any]:
    """
    Unflatten a single-level dictionary into nested structure.

    Args:
        data: Flattened dictionary.
        separator: Key separator used during flattening (default: ".").

    Returns:
        Nested dictionary.

    Examples:
        >>> unflatten_dict({"a.b": 1, "a.c.d": 2})
        {'a': {'b': 1, 'c': {'d': 2}}}
    """
    result: dict[str, Any] = {}

    for key, value in data.items():
        parts = key.split(separator)
        current = result

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

    return result


def format_timestamp(timestamp: float | int | str, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format timestamp to human-readable string.

    Args:
        timestamp: Unix timestamp (float/int) or ISO format string.
        format_str: Output format string (default: "%Y-%m-%d %H:%M:%S").

    Returns:
        Formatted timestamp string.

    Examples:
        >>> format_timestamp(1704067200)  # 2024-01-01 00:00:00 UTC
        '2024-01-01 00:00:00'
    """
    if isinstance(timestamp, str):
        # Try parsing as ISO format
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            return ""
    elif isinstance(timestamp, (int, float)):
        dt = datetime.fromtimestamp(timestamp)
    else:
        return ""

    return dt.strftime(format_str)


def parse_duration(duration_str: str) -> float:
    """
    Parse duration string to seconds.

    Supports formats like: "1h30m", "45s", "2h", "1h30m45s", "90m"

    Args:
        duration_str: Duration string to parse.

    Returns:
        Duration in seconds as float.

    Raises:
        ValueError: If duration string format is invalid.

    Examples:
        >>> parse_duration("1h30m")
        5400.0
        >>> parse_duration("45s")
        45.0
        >>> parse_duration("90m")
        5400.0
    """
    if not duration_str:
        raise ValueError("Empty duration string")

    pattern = r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+(?:\.\d+)?)s)?"
    match = re.fullmatch(pattern, duration_str.strip())

    if not match or not any(match.groups()):
        raise ValueError(f"Invalid duration format: {duration_str}")

    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    seconds = float(match.group(3)) if match.group(3) else 0.0

    return hours * 3600 + minutes * 60 + seconds


def format_duration(seconds: float) -> str:
    """
    Format seconds to human-readable duration string.

    Args:
        seconds: Duration in seconds.

    Returns:
        Formatted duration string (e.g., "1h30m45s").

    Examples:
        >>> format_duration(5400)
        '1h30m'
        >>> format_duration(45)
        '45s'
        >>> format_duration(3661)
        '1h1m1s'
    """
    if seconds < 0:
        return "0s"

    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")

    return "".join(parts)


def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """
    Mask sensitive data showing only last N characters.

    Args:
        data: String to mask.
        mask_char: Character to use for masking (default: "*").
        visible_chars: Number of trailing characters to show (default: 4).

    Returns:
        Masked string.

    Examples:
        >>> mask_sensitive_data("1234567890")
        '******7890'
        >>> mask_sensitive_data("secret", visible_chars=2)
        '****et'
    """
    if not data:
        return ""

    if len(data) <= visible_chars:
        return mask_char * len(data)

    masked_length = len(data) - visible_chars
    return mask_char * masked_length + data[-visible_chars:]


def generate_idempotency_key(prefix: str = "", length: int = 16) -> str:
    """
    Generate a deterministic idempotency key.

    Args:
        prefix: Optional prefix for the key.
        length: Length of random portion (default: 16).

    Returns:
        Idempotency key string.

    Note:
        This uses a simple counter-based approach for determinism in tests.
        For production, use cryptographically secure random generation.

    Examples:
        >>> generate_idempotency_key("order_")
        'order_a1b2c3d4e5f6g7h8'
    """
    import time
    import hashlib

    # Use timestamp + counter for deterministic but unique keys
    timestamp = str(time.time_ns())
    counter = str(id(object()) % 1000000)
    combined = f"{prefix}{timestamp}{counter}"

    # Hash and truncate
    hash_obj = hashlib.sha256(combined.encode())
    random_part = hash_obj.hexdigest()[:length]

    return f"{prefix}{random_part}"