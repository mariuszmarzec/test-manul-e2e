"""
Test suite for calculator module.
"""

import pytest
from calculator import add, multiply


class TestCalculator:
    """Tests for calculator functions."""

    def test_add(self):
        """Test addition."""
        assert add(2, 3) == 5.0
        assert add(1.5, 2.5) == 4.0
        assert add(-1, 1) == 0.0

    def test_multiply(self):
        """Test multiplication."""
        assert multiply(3, 4) == 12.0
        assert multiply(2.5, 4) == 10.0
        assert multiply(0, 5) == 0.0
        assert multiply(-2, 3) == -6.0
