"""Tests for the calculator.divide function."""

import pytest
from calculator import divide


class TestDivide:
    """Tests for the divide function."""

    def test_integer_like_inputs(self):
        """Integer-like inputs produce a float result."""
        assert divide(8, 2) == 4.0

    def test_fractional_result(self):
        """Fractional division returns the expected float."""
        assert divide(5, 2) == 2.5

    def test_negative_operands(self):
        """Negative operands are handled correctly."""
        assert divide(-10, 2) == -5.0
        assert divide(10, -2) == -5.0
        assert divide(-10, -2) == 5.0

    def test_division_by_zero_raises(self):
        """Division by zero raises ZeroDivisionError."""
        with pytest.raises(ZeroDivisionError):
            divide(5, 0)