"""
Test suite for WebFrame core modules.

This module contains comprehensive tests for DataProcessor, Filter,
Transformer, and utility functions.
"""

import pytest
from mylib.core import DataProcessor, Filter, Transformer
from mylib.utils import (
    validate_input,
    sanitize_string,
    format_response,
    parse_query_string,
    generate_id,
    deep_merge,
    flatten_dict,
    chunk_list,
    safe_get,
    truncate_text,
    to_snake_case,
    to_camel_case,
)


# Sample data for tests
SAMPLE_DATA = [
    {"id": 1, "name": "Alice", "age": 30, "score": 85, "tags": ["admin", "user"]},
    {"id": 2, "name": "Bob", "age": 25, "score": 92, "tags": ["user"]},
    {"id": 3, "name": "Charlie", "age": 35, "score": 78, "tags": ["user", "moderator"]},
    {"id": 4, "name": "Diana", "age": 28, "score": 95, "tags": ["admin"]},
    {"id": 5, "name": "Eve", "age": 32, "score": 88, "tags": ["user"]},
]


@pytest.fixture
def sample_data():
    """Provide a fresh deep copy of sample data for each test."""
    import copy
    return copy.deepcopy(SAMPLE_DATA)


# ==================== DataProcessor Tests ====================

class TestDataProcessor:
    """Tests for the DataProcessor class."""
    
    def test_init_empty(self):
        """Test initialization with no data."""
        processor = DataProcessor()
        assert processor.data == []
        assert processor.first() is None
        assert processor.last() is None
    
    def test_init_with_data(self, sample_data):
        """Test initialization with data."""
        processor = DataProcessor(sample_data)
        assert len(processor.data) == 5
        assert processor.first()["name"] == "Alice"
        assert processor.last()["name"] == "Eve"
    
    def test_process_filters_none(self, sample_data):
        """Test process with function returning None."""
        processor = DataProcessor(sample_data)
        processor.process(lambda x: x if x["age"] > 25 else None)
        assert len(processor.data) == 4
    
    def test_map_updates_field(self, sample_data):
        """Test map applies function to specific field."""
        processor = DataProcessor(sample_data)
        processor.map("score", lambda s: s * 2)
        assert processor.first()["score"] == 170
    
    def test_aggregate_sum(self, sample_data):
        """Test sum aggregation."""
        processor = DataProcessor(sample_data)
        total = processor.aggregate("score", "sum")
        assert total == 438
    
    def test_aggregate_avg(self, sample_data):
        """Test average aggregation."""
        processor = DataProcessor(sample_data)
        avg = processor.aggregate("score", "avg")
        assert abs(avg - 87.6) < 0.01
    
    def test_aggregate_min(self, sample_data):
        """Test min aggregation."""
        processor = DataProcessor(sample_data)
        min_score = processor.aggregate("score", "min")
        assert min_score == 78
    
    def test_aggregate_max(self, sample_data):
        """Test max aggregation."""
        processor = DataProcessor(sample_data)
        max_score = processor.aggregate("score", "max")
        assert max_score == 95
    
    def test_aggregate_count(self, sample_data):
        """Test count aggregation."""
        processor = DataProcessor(sample_data)
        count = processor.aggregate("name", "count")
        assert count == 5
    
    def test_aggregate_empty(self):
        """Test aggregation on empty data."""
        processor = DataProcessor()
        assert processor.aggregate("score", "sum") == 0
        assert processor.aggregate("score", "avg") == 0

    def test_limit(self, sample_data):
        """Test limiting results."""
        processor = DataProcessor(sample_data)
        limited = processor.limit(2)
        assert len(limited.data) == 2
    
    def test_paginate(self, sample_data):
        """Test pagination."""
        processor = DataProcessor(sample_data)
        result = processor.paginate(1, 2)
        assert result["page"] == 1
        assert result["per_page"] == 2
        assert result["total"] == 5
        assert result["pages"] == 3
        assert len(result["items"]) == 2
    
    def test_history_tracking(self, sample_data):
        """Test that operations are tracked in history."""
        processor = DataProcessor(sample_data)
        processor.map("score", lambda s: s + 1)
        assert len(processor.history) > 0
    
    def test_to_dict(self, sample_data):
        """Test conversion to dictionary."""
        processor = DataProcessor(sample_data)
        state = processor.to_dict()
        assert state["count"] == 5
        assert state["first"] == SAMPLE_DATA[0]
        assert state["last"] == SAMPLE_DATA[4]


# ==================== Filter Tests ====================

class TestFilter:
    """Tests for the Filter class."""
    
    def test_where_equal(self, sample_data):
        """Test equality filter."""
        result = Filter(sample_data).where("name", "Alice").apply()
        assert len(result) == 1
        assert result[0]["name"] == "Alice"
    
    def test_where_not_equal(self, sample_data):
        """Test inequality filter."""
        result = Filter(sample_data).where_not("name", "Alice").apply()
        assert len(result) == 4
    
    def test_where_greater_than(self, sample_data):
        """Test greater-than filter."""
        result = Filter(sample_data).where_gt("age", 30).apply()
        assert len(result) == 2
    
    def test_where_less_than(self, sample_data):
        """Test less-than filter."""
        result = Filter(sample_data).where_lt("score", 90).apply()
        assert len(result) == 3
    
    def test_where_gte(self, sample_data):
        """Test greater-than-or-equal filter."""
        result = Filter(sample_data).where_gte("age", 30).apply()
        assert len(result) == 3
    
    def test_where_lte(self, sample_data):
        """Test less-than-or-equal filter."""
        result = Filter(sample_data).where_lte("score", 85).apply()
        assert len(result) == 2
    
    def test_where_contains(self, sample_data):
        """Test contains filter."""
        result = Filter(sample_data).where_contains("tags", "admin").apply()
        assert len(result) == 2
    
    def test_where_in(self, sample_data):
        """Test in filter."""
        result = Filter(sample_data).where_in("id", [1, 3, 5]).apply()
        assert len(result) == 3
    
    def test_chained_conditions(self, sample_data):
        """Test chaining multiple conditions."""
        result = (
            Filter(sample_data)
            .where_contains("tags", "user")
            .where_gt("score", 80)
            .apply()
        )
        assert len(result) >= 1
    
    def test_no_match(self, sample_data):
        """Test filter with no matches."""
        result = Filter(sample_data).where("age", 999).apply()
        assert len(result) == 0


# ==================== Transformer Tests ====================

class TestTransformer:
    """Tests for the Transformer class."""
    
    def test_rename_field(self, sample_data):
        """Test renaming a field."""
        transformer = Transformer().rename("name", "full_name")
        result = transformer.apply_single(sample_data[0])
        assert "full_name" in result
        assert "name" not in result
        assert result["full_name"] == "Alice"
    
    def test_add_constant_field(self, sample_data):
        """Test adding a constant field."""
        transformer = Transformer().add_field("created", "2024-01-01")
        result = transformer.apply_single(sample_data[0])
        assert result["created"] == "2024-01-01"
    
    def test_compute_field(self, sample_data):
        """Test computing a field from existing data."""
        transformer = Transformer().compute_field("high_scorer", lambda x: x["score"] > 90)
        result = transformer.apply_single(sample_data[0])
        assert result["high_scorer"] == False
    
    def test_remove_field(self, sample_data):
        """Test removing a field."""
        transformer = Transformer().remove_field("score")
        result = transformer.apply_single(sample_data[0])
        assert "score" not in result
    
    def test_multiple_transformations(self, sample_data):
        """Test applying multiple transformations in sequence."""
        transformer = (
            Transformer()
            .rename("name", "full_name")
            .add_field("processed", True)
            .remove_field("tags")
        )
        result = transformer.apply_single(sample_data[0])
        assert "full_name" in result
        assert result["processed"] == True
        assert "tags" not in result
    
    def test_apply_to_list(self, sample_data):
        """Test applying transformations to a list."""
        transformer = Transformer().add_field("transformed", True)
        result = transformer.apply(sample_data[:2])
        assert len(result) == 2
        assert all(item["transformed"] for item in result)


# ==================== Utility Tests ====================

class TestValidateInput:
    """Tests for validate_input function."""
    
    def test_valid_input(self):
        """Test with valid input."""
        result = validate_input({"name": "test", "value": 123}, ["name", "value"])
        assert result["valid"] == True
        assert len(result["errors"]) == 0
    
    def test_missing_required(self):
        """Test with missing required fields."""
        result = validate_input({"name": "test"}, ["name", "value"])
        assert result["valid"] == False
        assert len(result["errors"]) == 1
    
    def test_invalid_type(self):
        """Test with incorrect types."""
        result = validate_input({"name": 123}, ["name"], types={"name": str})
        assert result["valid"] == False
        assert len(result["errors"]) == 1
    
    def test_non_dict_input(self):
        """Test with non-dictionary input."""
        result = validate_input("not a dict", ["name"])
        assert result["valid"] == False
        assert len(result["errors"]) == 1


class TestSanitizeString:
    """Tests for sanitize_string function."""
    
    def test_remove_html_tags(self):
        """Test removal of HTML tags."""
        result = sanitize_string("<b>Bold</b> text")
        assert "<b>" not in result
        assert result.strip() == "Bold text"
    
    def test_remove_scripts(self):
        """Test removal of script tags."""
        result = sanitize_string('<script>alert("xss")</script>Hello')
        assert "script" not in result.lower()
    
    def test_length_limit(self):
        """Test length limiting."""
        long_string = "x" * 1000
        result = sanitize_string(long_string, max_length=100)
        assert len(result) <= 100
    
    def test_non_string_input(self):
        """Test with non-string input."""
        result = sanitize_string(123)
        assert result == ""


class TestFormatResponse:
    """Tests for format_response function."""
    
    def test_basic_response(self):
        """Test basic response format."""
        result = format_response(data={"key": "value"})
        assert result["status"] == "success"
        assert result["data"] == {"key": "value"}
    
    def test_error_response(self):
        """Test error response format."""
        result = format_response(status="error", message="Failed")
        assert result["status"] == "error"
        assert result["message"] == "Failed"
    
    def test_response_with_meta(self):
        """Test response with metadata."""
        result = format_response(data=[1, 2, 3], meta={"page": 1})
        assert result["meta"] == {"page": 1}
    
    def test_empty_response(self):
        """Test empty response."""
        result = format_response()
        assert result["status"] == "success"
        assert "data" not in result


class TestParseQueryString:
    """Tests for parse_query_string function."""
    
    def test_basic_parsing(self):
        """Test basic query string parsing."""
        result = parse_query_string("key=value&foo=bar")
        assert result["key"] == "value"
        assert result["foo"] == "bar"
    
    def test_empty_string(self):
        """Test with empty query string."""
        result = parse_query_string("")
        assert result == {}
    
    def test_no_value(self):
        """Test query string without value."""
        result = parse_query_string("flag")
        assert result["flag"] == ""
    
    def test_special_characters(self):
        """Test with special characters."""
        result = parse_query_string("search=hello%20world")
        assert result["search"] == "hello%20world"


class TestGenerateId:
    """Tests for generate_id function."""
    
    def test_returns_string(self):
        """Test that it returns a string."""
        result = generate_id()
        assert isinstance(result, str)
    
    def test_unique_ids(self):
        """Test that generated IDs are unique."""
        ids = [generate_id() for _ in range(10)]
        assert len(set(ids)) == 10
    
    def test_uuid_format(self):
        """Test that ID follows UUID format."""
        result = generate_id()
        assert len(result) == 36  # UUID length with hyphens


class TestDeepMerge:
    """Tests for deep_merge function."""
    
    def test_merge_simple(self):
        """Test simple merge."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}
    
    def test_nested_merge(self):
        """Test nested dictionary merge."""
        base = {"a": {"b": 1, "c": 2}}
        override = {"a": {"c": 3, "d": 4}}
        result = deep_merge(base, override)
        assert result == {"a": {"b": 1, "c": 3, "d": 4}}
    
    def test_override_takes_precedence(self):
        """Test that override values take precedence."""
        base = {"x": 10}
        override = {"x": 20}
        result = deep_merge(base, override)
        assert result["x"] == 20


class TestFlattenDict:
    """Tests for flatten_dict function."""
    
    def test_flatten_nested(self):
        """Test flattening nested dictionary."""
        nested = {"a": {"b": {"c": 1}}}
        result = flatten_dict(nested)
        assert result == {"a.b.c": 1}
    
    def test_flatten_multiple_levels(self):
        """Test with multiple nesting levels."""
        nested = {"a": 1, "b": {"c": 2, "d": {"e": 3}}}
        result = flatten_dict(nested)
        assert result["a"] == 1
        assert result["b.c"] == 2
        assert result["b.d.e"] == 3


class TestChunkList:
    """Tests for chunk_list function."""
    
    def test_chunk_even(self):
        """Test chunking evenly sized list."""
        result = chunk_list([1, 2, 3, 4, 5, 6], 2)
        assert len(result) == 3
        assert result[0] == [1, 2]
    
    def test_chunk_odd(self):
        """Test chunking list with remainder."""
        result = chunk_list([1, 2, 3, 4, 5], 2)
        assert len(result) == 3
        assert result[-1] == [5]
    
    def test_chunk_single(self):
        """Test chunking with size 1."""
        result = chunk_list([1, 2, 3], 1)
        assert len(result) == 3
        assert result[0] == [1]


class TestSafeGet:
    """Tests for safe_get function."""
    
    def test_existing_key(self):
        """Test getting existing nested key."""
        data = {"a": {"b": {"c": 42}}}
        assert safe_get(data, "a.b.c") == 42
    
    def test_missing_key(self):
        """Test with missing key."""
        data = {"a": 1}
        result = safe_get(data, "b.c", default=0)
        assert result == 0
    
    def test_invalid_path(self):
        """Test with invalid path through non-dict."""
        data = {"a": {"b": 1}}
        result = safe_get(data, "a.b.c", default="fallback")
        assert result == "fallback"


class TestTruncateText:
    """Tests for truncate_text function."""
    
    def test_no_truncation(self):
        """Test when text is within limit."""
        result = truncate_text("Hello", max_length=10)
        assert result == "Hello"
    
    def test_truncation(self):
        """Test truncation with suffix."""
        result = truncate_text("Hello World", max_length=8)
        assert result.endswith("...")
        assert len(result) == 8
    
    def test_exact_length(self):
        """Test with exact max length."""
        result = truncate_text("Hello", max_length=5)
        assert result == "Hello"


class TestToSnakeCase:
    """Tests for to_snake_case function."""
    
    def test_camel_case(self):
        """Test converting camelCase."""
        result = to_snake_case("camelCase")
        assert result == "camel_case"
    
    def test_pascal_case(self):
        """Test converting PascalCase."""
        result = to_snake_case("PascalCase")
        assert result == "pascal_case"
    
    def test_already_snake(self):
        """Test with already snake_case."""
        result = to_snake_case("already_snake")
        assert result == "already_snake"


class TestToCamelCase:
    """Tests for to_camel_case function."""
    
    def test_snake_to_camel(self):
        """Test converting snake_case to camelCase."""
        result = to_camel_case("snake_case")
        assert result == "snakeCase"
    
    def test_multi_word(self):
        """Test with multiple words."""
        result = to_camel_case("hello_world_test")
        assert result == "helloWorldTest"
