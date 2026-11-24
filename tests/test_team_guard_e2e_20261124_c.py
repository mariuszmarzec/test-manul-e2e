"""
Tests for team_guard_e2e_20261124.child_c module.

Covers normal inputs and edge cases for all deterministic math/statistics functions.
"""

import pytest
from team_guard_e2e_20261124.child_c import (
    clamp,
    lerp,
    mean,
    median,
    std_dev,
    percentile,
    is_close,
    round_to,
)


# ==================== clamp Tests ====================

class TestClamp:
    """Tests for the clamp function."""

    def test_normal_within_range(self):
        """Test normal case: value within bounds."""
        assert clamp(5, 0, 10) == 5
        assert clamp(0, 0, 10) == 0
        assert clamp(10, 0, 10) == 10

    def test_normal_below_range(self):
        """Test normal case: value below lower bound."""
        assert clamp(-5, 0, 10) == 0
        assert clamp(-100, -10, 10) == -10

    def test_normal_above_range(self):
        """Test normal case: value above upper bound."""
        assert clamp(15, 0, 10) == 10
        assert clamp(100, -10, 10) == 10

    def test_edge_case_equal_bounds(self):
        """Edge case: minimum equals maximum."""
        assert clamp(5, 10, 10) == 10
        assert clamp(10, 10, 10) == 10
        assert clamp(15, 10, 10) == 10

    def test_edge_case_negative_bounds(self):
        """Edge case: negative bounds."""
        assert clamp(-5, -10, -1) == -5
        assert clamp(-15, -10, -1) == -10
        assert clamp(0, -10, -1) == -1

    def test_edge_case_float_bounds(self):
        """Edge case: float bounds and value."""
        assert clamp(3.14, 0.0, 5.0) == 3.14
        assert clamp(-1.5, 0.0, 5.0) == 0.0
        assert clamp(6.28, 0.0, 5.0) == 5.0

    def test_invalid_bounds_raises(self):
        """Edge case: minimum > maximum raises ValueError."""
        with pytest.raises(ValueError, match="minimum.*must not exceed maximum"):
            clamp(5, 10, 0)
        with pytest.raises(ValueError, match="minimum.*must not exceed maximum"):
            clamp(5, 5.1, 5.0)


# ==================== lerp Tests ====================

class TestLerp:
    """Tests for the lerp (linear interpolation) function."""

    def test_normal_midpoint(self):
        """Test normal case: interpolation at midpoint."""
        assert lerp(0, 10, 0.5) == 5.0
        assert lerp(10, 20, 0.5) == 15.0

    def test_normal_start_end(self):
        """Test normal case: t at boundaries."""
        assert lerp(10, 20, 0.0) == 10.0
        assert lerp(10, 20, 1.0) == 20.0

    def test_normal_fractional(self):
        """Test normal case: various fractional t values."""
        assert lerp(0, 100, 0.25) == 25.0
        assert lerp(0, 100, 0.75) == 75.0

    def test_edge_case_extrapolation_below(self):
        """Edge case: t < 0 extrapolates below start."""
        assert lerp(10, 20, -0.5) == 5.0
        assert lerp(10, 20, -1.0) == 0.0

    def test_edge_case_extrapolation_above(self):
        """Edge case: t > 1 extrapolates above end."""
        assert lerp(10, 20, 1.5) == 25.0
        assert lerp(10, 20, 2.0) == 30.0

    def test_edge_case_negative_values(self):
        """Edge case: negative start/end values."""
        assert lerp(-10, 10, 0.5) == 0.0
        assert lerp(-20, -10, 0.5) == -15.0

    def test_edge_case_zero_range(self):
        """Edge case: start equals end (zero range)."""
        assert lerp(5, 5, 0.0) == 5.0
        assert lerp(5, 5, 0.5) == 5.0
        assert lerp(5, 5, 1.0) == 5.0


# ==================== mean Tests ====================

class TestMean:
    """Tests for the mean function."""

    def test_normal_integer_list(self):
        """Test normal case: list of integers."""
        assert mean([1, 2, 3, 4, 5]) == 3.0
        assert mean([10, 20, 30]) == 20.0

    def test_normal_float_list(self):
        """Test normal case: list of floats."""
        assert mean([1.5, 2.5, 3.0]) == pytest.approx(2.3333333333)

    def test_normal_single_element(self):
        """Test normal case: single element."""
        assert mean([42]) == 42.0
        assert mean([3.14]) == 3.14

    def test_edge_case_negative_numbers(self):
        """Edge case: negative numbers."""
        assert mean([-5, -3, -1, 1, 3, 5]) == 0.0
        assert mean([-10, -20, -30]) == -20.0

    def test_edge_case_large_numbers(self):
        """Edge case: large numbers."""
        assert mean([1e10, 2e10, 3e10]) == 2e10

    def test_edge_case_small_numbers(self):
        """Edge case: very small numbers."""
        assert mean([1e-10, 2e-10, 3e-10]) == 2e-10

    def test_empty_raises(self):
        """Edge case: empty sequence raises ValueError."""
        with pytest.raises(ValueError, match="mean\\(\\) requires at least one value"):
            mean([])


# ==================== median Tests ====================

class TestMedian:
    """Tests for the median function."""

    def test_normal_odd_count(self):
        """Test normal case: odd number of elements."""
        assert median([1, 3, 5]) == 3.0
        assert median([5, 1, 3]) == 3.0  # unsorted input

    def test_normal_even_count(self):
        """Test normal case: even number of elements."""
        assert median([1, 2, 3, 4]) == 2.5
        assert median([4, 1, 3, 2]) == 2.5  # unsorted input

    def test_normal_single_element(self):
        """Test normal case: single element."""
        assert median([42]) == 42.0
        assert median([3.14]) == 3.14

    def test_edge_case_negative_numbers(self):
        """Edge case: negative numbers."""
        assert median([-5, -1, 1, 5]) == 0.0
        assert median([-10, -5, -1]) == -5.0

    def test_edge_case_duplicate_values(self):
        """Edge case: duplicate values."""
        assert median([1, 2, 2, 3]) == 2.0
        assert median([5, 5, 5, 5, 5]) == 5.0

    def test_edge_case_float_values(self):
        """Edge case: float values."""
        assert median([1.1, 2.2, 3.3]) == 2.2
        assert median([1.0, 2.0, 3.0, 4.0]) == 2.5

    def test_empty_raises(self):
        """Edge case: empty sequence raises ValueError."""
        with pytest.raises(ValueError, match="median\\(\\) requires at least one value"):
            median([])


# ==================== std_dev Tests ====================

class TestStdDev:
    """Tests for the std_dev (population standard deviation) function."""

    def test_normal_constant_values(self):
        """Test normal case: all values equal (std dev = 0)."""
        assert std_dev([10, 10, 10, 10]) == 0.0
        assert std_dev([5.0]) == 0.0

    def test_normal_uniform_spread(self):
        """Test normal case: uniform spread."""
        # For [1, 2, 3, 4, 5], mean=3, variance=2, std_dev=sqrt(2)
        assert std_dev([1, 2, 3, 4, 5]) == pytest.approx(1.41421356237)

    def test_normal_two_values(self):
        """Test normal case: two values."""
        # For [0, 10], mean=5, variance=25, std_dev=5
        assert std_dev([0, 10]) == 5.0

    def test_edge_case_negative_values(self):
        """Edge case: negative values."""
        assert std_dev([-5, -3, -1, 1, 3, 5]) == pytest.approx(3.415650255)

    def test_edge_case_single_value(self):
        """Edge case: single value (std dev = 0)."""
        assert std_dev([42]) == 0.0
        assert std_dev([-100]) == 0.0

    def test_empty_raises(self):
        """Edge case: empty sequence raises ValueError."""
        with pytest.raises(ValueError, match="std_dev\\(\\) requires at least one value"):
            std_dev([])


# ==================== percentile Tests ====================

class TestPercentile:
    """Tests for the percentile function."""

    def test_normal_median(self):
        """Test normal case: 50th percentile (median)."""
        assert percentile([1, 2, 3, 4, 5], 50) == 3.0
        assert percentile([1, 2, 3, 4], 50) == 2.5

    def test_normal_quartiles(self):
        """Test normal case: 25th and 75th percentiles."""
        # For [1,2,3,4,5], 25th percentile: pos=1.0, value=2.0
        assert percentile([1, 2, 3, 4, 5], 25) == 2.0
        # 75th percentile: pos=3.0, value=4.0
        assert percentile([1, 2, 3, 4, 5], 75) == 4.0

    def test_normal_bounds(self):
        """Test normal case: 0th and 100th percentiles."""
        assert percentile([1, 2, 3, 4, 5], 0) == 1.0
        assert percentile([1, 2, 3, 4, 5], 100) == 5.0

    def test_edge_case_single_element(self):
        """Edge case: single element sequence."""
        assert percentile([42], 0) == 42.0
        assert percentile([42], 50) == 42.0
        assert percentile([42], 100) == 42.0

    def test_edge_case_interpolation(self):
        """Edge case: interpolation between values."""
        # For [1, 2, 3, 4], 50th percentile = (2+3)/2 = 2.5
        assert percentile([1, 2, 3, 4], 50) == 2.5
        # 33rd percentile: pos = 0.33 * 3 = 0.99, between 1 and 2
        result = percentile([1, 2, 3, 4], 33)
        assert 1.0 < result < 2.0

    def test_edge_case_negative_values(self):
        """Edge case: negative values."""
        assert percentile([-10, -5, 0, 5, 10], 50) == 0.0
        assert percentile([-10, -5, 0, 5, 10], 0) == -10.0
        assert percentile([-10, -5, 0, 5, 10], 100) == 10.0

    def test_invalid_p_below_zero_raises(self):
        """Edge case: p < 0 raises ValueError."""
        with pytest.raises(ValueError, match="percentile p must be in \\[0, 100\\]"):
            percentile([1, 2, 3], -1)
        with pytest.raises(ValueError, match="percentile p must be in \\[0, 100\\]"):
            percentile([1, 2, 3], -0.1)

    def test_invalid_p_above_hundred_raises(self):
        """Edge case: p > 100 raises ValueError."""
        with pytest.raises(ValueError, match="percentile p must be in \\[0, 100\\]"):
            percentile([1, 2, 3], 101)
        with pytest.raises(ValueError, match="percentile p must be in \\[0, 100\\]"):
            percentile([1, 2, 3], 150)

    def test_empty_raises(self):
        """Edge case: empty sequence raises ValueError."""
        with pytest.raises(ValueError, match="percentile\\(\\) requires at least one value"):
            percentile([], 50)


# ==================== is_close Tests ====================

class TestIsClose:
    """Tests for the is_close function."""

    def test_normal_exact_equal(self):
        """Test normal case: exactly equal values."""
        assert is_close(1.0, 1.0) is True
        assert is_close(0.0, 0.0) is True
        assert is_close(-5.0, -5.0) is True

    def test_normal_within_rel_tol(self):
        """Test normal case: within relative tolerance."""
        assert is_close(1.0, 1.0 + 1e-10) is True
        assert is_close(1000.0, 1000.0 + 1e-6) is True

    def test_normal_outside_rel_tol(self):
        """Test normal case: outside relative tolerance."""
        assert is_close(1.0, 1.0 + 1e-8) is False
        assert is_close(1000.0, 1000.0 + 1e-3) is False

    def test_edge_case_abs_tol(self):
        """Edge case: absolute tolerance for very small numbers."""
        assert is_close(1e-10, 2e-10, abs_tol=1e-9) is True
        assert is_close(0.0, 1e-10, abs_tol=1e-9) is True
        assert is_close(1e-10, 2e-10, abs_tol=1e-11) is False

    def test_edge_case_zero_comparison(self):
        """Edge case: comparison with zero."""
        assert is_close(0.0, 1e-10, rel_tol=1e-9) is False  # rel_tol doesn't help near zero
        assert is_close(0.0, 1e-10, abs_tol=1e-9) is True

    def test_edge_case_negative_numbers(self):
        """Edge case: negative numbers."""
        assert is_close(-1.0, -1.0 + 1e-10) is True
        assert is_close(-1.0, -1.0 + 1e-8) is False

    def test_edge_case_large_numbers(self):
        """Edge case: large numbers."""
        assert is_close(1e10, 1e10 + 1.0) is True  # within rel_tol
        assert is_close(1e10, 1e10 + 1e5) is False  # outside rel_tol

    def test_invalid_negative_rel_tol_raises(self):
        """Edge case: negative rel_tol raises ValueError."""
        with pytest.raises(ValueError, match="tolerances must be non-negative"):
            is_close(1.0, 1.0, rel_tol=-1e-9)

    def test_invalid_negative_abs_tol_raises(self):
        """Edge case: negative abs_tol raises ValueError."""
        with pytest.raises(ValueError, match="tolerances must be non-negative"):
            is_close(1.0, 1.0, abs_tol=-1e-9)


# ==================== round_to Tests ====================

class TestRoundTo:
    """Tests for the round_to function."""

    def test_normal_positive_decimals(self):
        """Test normal case: positive decimal places."""
        assert round_to(3.14159, 2) == 3.14
        assert round_to(2.71828, 3) == 2.718
        assert round_to(1.5, 0) == 2.0

    def test_normal_zero_decimals(self):
        """Test normal case: zero decimal places."""
        assert round_to(3.7, 0) == 4.0
        assert round_to(3.2, 0) == 3.0
        assert round_to(-3.7, 0) == -4.0

    def test_normal_negative_decimals(self):
        """Test normal case: negative decimal places (round to tens, hundreds)."""
        assert round_to(1234, -2) == 1200.0
        assert round_to(1567, -2) == 1600.0
        assert round_to(999, -1) == 1000.0

    def test_edge_case_half_even_bankers_rounding(self):
        """Edge case: Python's banker's rounding (round half to even)."""
        assert round_to(2.5, 0) == 2.0  # 2.5 rounds to even 2
        assert round_to(3.5, 0) == 4.0  # 3.5 rounds to even 4
        assert round_to(1.25, 1) == 1.2  # 1.25 rounds to even 1.2
        assert round_to(1.35, 1) == 1.4  # 1.35 rounds to even 1.4

    def test_edge_case_negative_values(self):
        """Edge case: negative values."""
        assert round_to(-3.14159, 2) == -3.14
        assert round_to(-1234, -2) == -1200.0

    def test_edge_case_integer_input(self):
        """Edge case: integer input."""
        assert round_to(42, 2) == 42.0
        assert round_to(42, -1) == 40.0

    def test_edge_case_zero(self):
        """Edge case: zero value."""
        assert round_to(0, 2) == 0.0
        assert round_to(0, -2) == 0.0