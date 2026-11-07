"""
Test suite for query string parsing in mylib.utils.
"""

import pytest
from mylib.utils import parse_query_string


class TestParseQueryStringDetailed:
    """Detailed tests for parse_query_string function."""

    def test_encoded_keys(self):
        """Test URL-encoded keys."""
        result = parse_query_string("first%20name=John&last%20name=Doe")
        assert result["first name"] == "John"
        assert result["last name"] == "Doe"

    def test_encoded_values(self):
        """Test URL-encoded values."""
        result = parse_query_string("greeting=hello%20world&code=%231")
        assert result["greeting"] == "hello world"
        assert result["code"] == "#1"

    def test_plus_signs(self):
        """Test decoding '+' as space in keys and values."""
        result = parse_query_string("user+name=john+doe&city+name=new+york")
        assert result["user name"] == "john doe"
        assert result["city name"] == "new york"

    def test_values_containing_additional_equals_signs(self):
        """Test values containing additional equals signs."""
        result = parse_query_string("expr=a=b&equation=1%2B1=2")
        assert result["expr"] == "a=b"
        assert result["equation"] == "1+1=2"

    def test_missing_values(self):
        """Test query parameters with missing values (no equals sign)."""
        result = parse_query_string("flag&debug")
        assert result == {"flag": "", "debug": ""}

    def test_duplicate_keys(self):
        """Test duplicate keys where the last occurrence wins."""
        result = parse_query_string("key=first&key=second&key=last")
        assert result["key"] == "last"

    def test_empty_input(self):
        """Test empty query string input."""
        assert parse_query_string("") == {}

    def test_combined_complex_query(self):
        """Test combined scenario with encoded keys/values, plus signs, duplicates, and missing values."""
        result = parse_query_string("q=search%20term&tag+name=py%2Btest&flag&q=final+term")
        assert result == {
            "q": "final term",
            "tag name": "py+test",
            "flag": "",
        }
