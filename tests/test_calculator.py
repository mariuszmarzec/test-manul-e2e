"""
Test suite for calculator module.
"""

import pytest
from calculator import add

class TestCalculator:
    """Tests for calculator functions."""

    def test_add(self):
        """Test addition."""
        assert add(2, 3) == 5.0