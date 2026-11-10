"""
Tests for safe_get in mylib.utils.
"""

import pytest
from mylib.utils import safe_get


def test_dict_paths():
    data = {"user": {"name": "Ada", "details": {"age": 30}}}
    assert safe_get(data, "user.name") == "Ada"
    assert safe_get(data, "user.details.age") == 30
    assert safe_get(data, "user.nonexistent") is None


def test_list_objects_and_nested_lists():
    data = {
        "users": [{"name": "Ada"}, {"name": "Bob"}],
        "matrix": [[10, 20], [30, 40]],
    }
    assert safe_get(data, "users.0.name") == "Ada"
    assert safe_get(data, "users.1.name") == "Bob"
    assert safe_get(data, "matrix.1.0") == 30
    assert safe_get(data, "matrix.0.1") == 20


def test_mixed_traversals():
    data = {
        "org": {
            "teams": [
                {"members": [{"id": 1, "name": "Alice"}]},
                {"members": [{"id": 2, "name": "Bob"}]},
            ]
        }
    }
    assert safe_get(data, "org.teams.0.members.0.name") == "Alice"
    assert safe_get(data, "org.teams.1.members.0.id") == 2


def test_invalid_indices_and_out_of_bounds():
    data = {"items": ["a", "b", "c"]}
    assert safe_get(data, "items.-1") is None
    assert safe_get(data, "items.10") is None
    assert safe_get(data, "items.foo") is None
    assert safe_get(data, "items.0.extra") is None


def test_missing_key_and_custom_default():
    data = {"a": {"b": 1}}
    assert safe_get(data, "a.c", default="N/A") == "N/A"
    assert safe_get(data, "x.y.z", default=42) == 42
    assert safe_get(data, "a.b.c", default=None) is None


def test_numeric_dict_keys():
    data = {"0": "zero", "1": "one", "nested": {"0": "inner_zero"}}
    assert safe_get(data, "0") == "zero"
    assert safe_get(data, "1") == "one"
    assert safe_get(data, "nested.0") == "inner_zero"
