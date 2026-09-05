"""
Utility functions for WebFrame.

This module provides helper functions for input validation, sanitization,
response formatting, and common operations.
"""

import re
import uuid
from typing import Any, Dict, List, Optional, Union


def validate_input(data: Any, required_fields: List[str], types: Optional[Dict[str, type]] = None) -> Dict[str, Any]:
    """
    Validate input data against required fields and types.
    
    Args:
        data: Input dictionary to validate
        required_fields: List of required field names
        types: Optional dict mapping field names to expected types
    
    Returns:
        Dict with 'valid' boolean and 'errors' list
    """
    errors = []
    
    if not isinstance(data, dict):
        return {"valid": False, "errors": ["Input must be a dictionary"]}
    
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    if types:
        for field, expected_type in types.items():
            if field in data and not isinstance(data[field], expected_type):
                errors.append(f"Field '{field}' must be of type {expected_type.__name__}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "data": data,
    }


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize a string by removing potentially dangerous characters.
    
    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return ""
    
    # Remove HTML tags
    sanitized = re.sub(r"<[^>]*>", "", value)
    
    # Remove script tags and content
    sanitized = re.sub(r"<script[^>]*>.*?</script>", "", sanitized, flags=re.DOTALL | re.IGNORECASE)
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()


def format_response(
    data: Any = None,
    status: str = "success",
    message: str = "",
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Format a standardized API response.
    
    Args:
        data: Response data payload
        status: Status string (success, error, etc.)
        message: Optional message
        meta: Optional metadata dictionary
    
    Returns:
        Formatted response dictionary
    """
    response = {
        "status": status,
        "message": message,
    }
    
    if data is not None:
        response["data"] = data
    
    if meta is not None:
        response["meta"] = meta
    
    return response


def parse_query_string(query_string: str) -> Dict[str, str]:
    """
    Parse a URL query string into a dictionary.
    
    Args:
        query_string: Raw query string (e.g., "key=value&foo=bar")
    
    Returns:
        Dictionary of query parameters
    """
    if not query_string:
        return {}
    
    params: Dict[str, str] = {}
    for part in query_string.split("&"):
        if "=" in part:
            key, value = part.split("=", 1)
            params[key] = value
        else:
            params[part] = ""
    
    return params


def generate_id() -> str:
    """
    Generate a unique identifier.
    
    Returns:
        UUID4 string
    """
    return str(uuid.uuid4())


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.
    
    Override values take precedence over base values.
    Nested dictionaries are merged recursively.
    
    Args:
        base: Base dictionary
        override: Override dictionary
    
    Returns:
        Merged dictionary
    """
    result = dict(base)
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def flatten_dict(d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """
    Flatten a nested dictionary.
    
    Args:
        d: Dictionary to flatten
        parent_key: Prefix for keys
        sep: Separator between nested keys
    
    Returns:
        Flattened dictionary
    """
    items: List = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def chunk_list(lst: List[Any], size: int) -> List[List[Any]]:
    """
    Split a list into chunks of specified size.
    
    Args:
        lst: List to chunk
        size: Maximum chunk size
    
    Returns:
        List of chunks
    """
    return [lst[i:i + size] for i in range(0, len(lst), size)]


def safe_get(d: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Safely get a nested value from a dictionary using dot notation.
    
    Args:
        d: Dictionary to access
        key_path: Dot-separated key path (e.g., "user.name")
        default: Default value if key not found
    
    Returns:
        Value at key path or default
    """
    keys = key_path.split(".")
    current = d
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to append when truncated
    
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def to_snake_case(text: str) -> str:
    """
    Convert a string to snake_case.
    
    Args:
        text: Input string (e.g., "camelCase" or "PascalCase")
    
    Returns:
        snake_case string
    """
    # Insert underscore before uppercase letters
    s1 = re.sub(r'([A-Z])', r'_\1', text)
    # Replace hyphens and spaces with underscores
    s2 = re.sub(r'[-\s]', '_', s1)
    # Convert to lowercase and strip leading underscores
    return s2.lower().lstrip('_')


def to_camel_case(text: str) -> str:
    """
    Convert a string to camelCase.
    
    Args:
        text: Input string (e.g., "snake_case")
    
    Returns:
        camelCase string
    """
    components = text.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])
