"""
Tests for Child C: Deterministic Numeric/Statistics Utility.

This test suite covers normal operations, edge cases, and error conditions
for all functions in team_branch_recovery_e2e_20261126.child_c.
"""

import math
import pytest
from team_branch_recovery_e2e_20261126.child_c import (
    DeterministicRNG,
    mean,
    median,
    mode,
    variance,
    std_dev,
    range_,
    iqr,
    percentile,
    quantiles,
    skewness,
    kurtosis,
    covariance,
    correlation,
    rolling_mean,
    rolling_std,
    autocorrelation,
    z_score,
    min_max_normalize,
    geometric_mean,
    harmonic_mean,
    rms,
    sum_of_squares,
    describe,
)


# ==================== DeterministicRNG Tests ====================

class TestDeterministicRNG:
    """Tests for the Linear Congruential Generator."""

    def test_reproducibility(self):
        """Same seed produces identical sequences."""
        rng1 = DeterministicRNG(seed=12345)
        rng2 = DeterministicRNG(seed=12345)
        seq1 = [rng1.random() for _ in range(100)]
        seq2 = [rng2.random() for _ in range(100)]
        assert seq1 == seq2

    def test_different_seeds_different_sequences(self):
        """Different seeds produce different sequences."""
        rng1 = DeterministicRNG(seed=1)
        rng2 = DeterministicRNG(seed=2)
        seq1 = [rng1.random() for _ in range(10)]
        seq2 = [rng2.random() for _ in range(10)]
        assert seq1 != seq2

    def test_random_range(self):
        """random() returns values in [0.0, 1.0)."""
        rng = DeterministicRNG(seed=42)
        for _ in range(1000):
            val = rng.random()
            assert 0.0 <= val < 1.0

    def test_next_int_range(self):
        """next_int() returns 32-bit unsigned integers."""
        rng = DeterministicRNG(seed=42)
        for _ in range(100):
            val = rng.next_int()
            assert 0 <= val < 2**32

    def test_randint_inclusive_bounds(self):
        """randint(low, high) includes both bounds."""
        rng = DeterministicRNG(seed=42)
        for _ in range(100):
            val = rng.randint(5, 10)
            assert 5 <= val <= 10

    def test_randint_single_value(self):
        """randint(x, x) always returns x."""
        rng = DeterministicRNG(seed=42)
        for _ in range(10):
            assert rng.randint(7, 7) == 7

    def test_randint_invalid_bounds(self):
        """randint raises ValueError when low > high."""
        rng = DeterministicRNG(seed=42)
        with pytest.raises(ValueError):
            rng.randint(10, 5)

    def test_choice_selects_from_sequence(self):
        """choice returns an element from the sequence."""
        rng = DeterministicRNG(seed=42)
        seq = ['a', 'b', 'c', 'd', 'e']
        for _ in range(20):
            chosen = rng.choice(seq)
            assert chosen in seq

    def test_choice_empty_sequence_raises(self):
        """choice raises ValueError on empty sequence."""
        rng = DeterministicRNG(seed=42)
        with pytest.raises(ValueError):
            rng.choice([])

    def test_shuffle_permutations(self):
        """shuffle produces a permutation of the original list."""
        rng = DeterministicRNG(seed=42)
        original = list(range(10))
        shuffled = original.copy()
        rng.shuffle(shuffled)
        assert sorted(shuffled) == original
        assert shuffled != original  # Very unlikely to be same

    def test_shuffle_deterministic(self):
        """shuffle is deterministic with same seed."""
        rng1 = DeterministicRNG(seed=42)
        rng2 = DeterministicRNG(seed=42)
        seq1 = list(range(20))
        seq2 = list(range(20))
        rng1.shuffle(seq1)
        rng2.shuffle(seq2)
        assert seq1 == seq2

    def test_seed_resets_state(self):
        """seed() method resets generator state."""
        rng = DeterministicRNG(seed=42)
        first = [rng.random() for _ in range(5)]
        rng.seed(42)
        second = [rng.random() for _ in range(5)]
        assert first == second


# ==================== Central Tendency Tests ====================

class TestMean:
    """Tests for arithmetic mean."""

    def test_basic_integers(self):
        assert mean([1, 2, 3, 4, 5]) == 3.0

    def test_basic_floats(self):
        assert abs(mean([1.5, 2.5, 3.0]) - 2.333333333333333) < 1e-10

    def test_negative_numbers(self):
        assert mean([-5, -3, 0, 3, 5]) == 0.0

    def test_single_element(self):
        assert mean([42]) == 42.0

    def test_two_elements(self):
        assert mean([10, 20]) == 15.0

    def test_large_numbers(self):
        assert mean([1e10, 2e10, 3e10]) == 2e10

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            mean([])


class TestMedian:
    """Tests for median."""

    def test_odd_length(self):
        assert median([1, 3, 5]) == 3.0
        assert median([5, 1, 3]) == 3.0  # Unsorted input

    def test_even_length(self):
        assert median([1, 2, 3, 4]) == 2.5
        assert median([4, 1, 3, 2]) == 2.5  # Unsorted input

    def test_negative_numbers(self):
        assert median([-5, -3, -1]) == -3.0

    def test_floats(self):
        assert median([1.5, 2.5, 3.5]) == 2.5

    def test_single_element(self):
        assert median([42]) == 42.0

    def test_two_elements(self):
        assert median([10, 20]) == 15.0

    def test_duplicates(self):
        assert median([1, 2, 2, 3]) == 2.0

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            median([])


class TestMode:
    """Tests for mode."""

    def test_single_mode(self):
        assert mode([1, 2, 2, 3, 4]) == [2]

    def test_multiple_modes(self):
        result = mode([1, 1, 2, 2, 3])
        assert sorted(result) == [1, 2]

    def test_all_unique(self):
        result = mode([1, 2, 3, 4, 5])
        assert sorted(result) == [1, 2, 3, 4, 5]

    def test_all_same(self):
        assert mode([7, 7, 7, 7]) == [7]

    def test_negative_numbers(self):
        assert mode([-2, -1, -1, 0]) == [-1]

    def test_floats(self):
        assert mode([1.5, 2.5, 2.5, 3.5]) == [2.5]

    def test_single_element(self):
        assert mode([42]) == [42]

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            mode([])


# ==================== Dispersion Tests ====================

class TestVariance:
    """Tests for variance."""

    def test_population_variance(self):
        # Variance of [1,2,3,4,5] with ddof=0: mean=3, sq_diffs=[4,1,0,1,4], sum=10, var=2.0
        assert abs(variance([1, 2, 3, 4, 5], ddof=0) - 2.0) < 1e-10

    def test_sample_variance(self):
        # Sample variance with ddof=1: 10/4 = 2.5
        assert abs(variance([1, 2, 3, 4, 5], ddof=1) - 2.5) < 1e-10

    def test_constant_values(self):
        assert variance([5, 5, 5, 5], ddof=0) == 0.0
        assert variance([5, 5, 5, 5], ddof=1) == 0.0

    def test_two_elements_population(self):
        assert variance([10, 20], ddof=0) == 25.0

    def test_two_elements_sample(self):
        assert variance([10, 20], ddof=1) == 50.0

    def test_negative_numbers(self):
        # mean=0, sq_diffs=[25,9,1,1,9,25], sum=70, var=70/6=11.666...
        assert abs(variance([-5, -3, -1, 1, 3, 5], ddof=0) - 11.666666666666666) < 1e-10

    def test_insufficient_data_population(self):
        # ddof=0 needs at least 1 element
        with pytest.raises(ValueError):
            variance([], ddof=0)

    def test_insufficient_data_sample(self):
        # ddof=1 needs at least 2 elements
        with pytest.raises(ValueError):
            variance([1], ddof=1)
        with pytest.raises(ValueError):
            variance([], ddof=1)


class TestStdDev:
    """Tests for standard deviation."""

    def test_population_std(self):
        assert abs(std_dev([1, 2, 3, 4, 5], ddof=0) - math.sqrt(2.0)) < 1e-10

    def test_sample_std(self):
        assert abs(std_dev([1, 2, 3, 4, 5], ddof=1) - math.sqrt(2.5)) < 1e-10

    def test_constant_values(self):
        assert std_dev([5, 5, 5, 5], ddof=0) == 0.0

    def test_negative_numbers(self):
        data = [-5, -3, -1, 1, 3, 5]
        expected = math.sqrt(variance(data, ddof=0))
        assert abs(std_dev(data, ddof=0) - expected) < 1e-10

    def test_insufficient_data(self):
        with pytest.raises(ValueError):
            std_dev([1], ddof=1)


class TestRange:
    """Tests for range."""

    def test_basic(self):
        assert range_([1, 5, 3, 9, 2]) == 8.0

    def test_negative(self):
        assert range_([-10, -5, 0, 5]) == 15.0

    def test_single_element(self):
        assert range_([42]) == 0.0

    def test_floats(self):
        assert range_([1.5, 3.5, 2.0]) == 2.0

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            range_([])


class TestIQR:
    """Tests for Interquartile Range."""

    def test_basic_eight_elements(self):
        # [1,2,3,4,5,6,7,8] -> lower=[1,2,3,4], upper=[5,6,7,8]
        # Q1=median([1,2,3,4])=2.5, Q3=median([5,6,7,8])=6.5, IQR=4.0
        assert iqr([1, 2, 3, 4, 5, 6, 7, 8]) == 4.0

    def test_seven_elements(self):
        # [1,2,3,4,5,6,7] -> lower=[1,2,3], upper=[5,6,7]
        # Q1=2, Q3=6, IQR=4.0
        assert iqr([1, 2, 3, 4, 5, 6, 7]) == 4.0

    def test_unsorted_input(self):
        assert iqr([8, 1, 7, 2, 6, 3, 5, 4]) == 4.0

    def test_floats(self):
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
        assert iqr(data) == 4.0

    def test_insufficient_data(self):
        with pytest.raises(ValueError, match="at least 4"):
            iqr([1, 2, 3])
        with pytest.raises(ValueError):
            iqr([1])
        with pytest.raises(ValueError):
            iqr([])


# ==================== Percentile/Quantile Tests ====================

class TestPercentile:
    """Tests for percentile."""

    def test_median_50th(self):
        assert percentile([1, 2, 3, 4, 5], 50) == 3.0

    def test_min_0th(self):
        assert percentile([1, 2, 3, 4, 5], 0) == 1.0

    def test_max_100th(self):
        assert percentile([1, 2, 3, 4, 5], 100) == 5.0

    def test_25th_percentile(self):
        assert percentile([1, 2, 3, 4], 25) == 1.75

    def test_75th_percentile(self):
        assert percentile([1, 2, 3, 4], 75) == 3.25

    def test_interpolation(self):
        # [1,2,3,4,5,6], 40th percentile
        # index = 0.4 * 5 = 2.0 -> exact element at index 2 = 3
        assert percentile([1, 2, 3, 4, 5, 6], 40) == 3.0

    def test_single_element(self):
        assert percentile([42], 0) == 42.0
        assert percentile([42], 50) == 42.0
        assert percentile([42], 100) == 42.0

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            percentile([], 50)

    def test_out_of_range_low(self):
        with pytest.raises(ValueError, match="0, 100"):
            percentile([1, 2, 3], -1)

    def test_out_of_range_high(self):
        with pytest.raises(ValueError, match="0, 100"):
            percentile([1, 2, 3], 101)


class TestQuantiles:
    """Tests for quantiles."""

    def test_quartiles(self):
        # [1,2,3,4,5,6,7,8] -> quartiles at 25%, 50%, 75%
        # Using linear interpolation on (n-1) scale (R-7 / numpy default)
        # 25th: index=0.25*7=1.75 -> 2 + 0.75*(3-2) = 2.75
        # 50th: index=0.50*7=3.5 -> 4 + 0.5*(5-4) = 4.5
        # 75th: index=0.75*7=5.25 -> 6 + 0.25*(7-6) = 6.25
        q = quantiles([1, 2, 3, 4, 5, 6, 7, 8], n=4)
        assert len(q) == 3
        assert abs(q[0] - 2.75) < 1e-10
        assert abs(q[1] - 4.5) < 1e-10
        assert abs(q[2] - 6.25) < 1e-10

    def test_quintiles(self):
        q = quantiles([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], n=5)
        assert len(q) == 4

    def test_deciles(self):
        q = quantiles(range(1, 101), n=10)
        assert len(q) == 9

    def test_n_less_than_2_raises(self):
        with pytest.raises(ValueError, match=">= 2"):
            quantiles([1, 2, 3], n=1)

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            quantiles([], n=4)


# ==================== Distribution Shape Tests ====================

class TestSkewness:
    """Tests for skewness."""

    def test_symmetric_zero_skew(self):
        # Perfectly symmetric distribution
        assert abs(skewness([1, 2, 3, 4, 5]) - 0.0) < 1e-10

    def test_right_skewed_positive(self):
        # Long right tail
        data = [1, 2, 2, 3, 10]
        s = skewness(data)
        assert s > 0

    def test_left_skewed_negative(self):
        # Long left tail
        data = [1, 8, 9, 9, 10]
        s = skewness(data)
        assert s < 0

    def test_constant_values(self):
        assert skewness([5, 5, 5, 5, 5]) == 0.0

    def test_three_elements(self):
        # Minimum for skewness
        s = skewness([1, 2, 10])
        assert s > 0  # Right skewed

    def test_insufficient_data(self):
        with pytest.raises(ValueError, match="at least 3"):
            skewness([1, 2])
        with pytest.raises(ValueError):
            skewness([1])
        with pytest.raises(ValueError):
            skewness([])


class TestKurtosis:
    """Tests for kurtosis."""

    def test_normal_like_negative_excess(self):
        # Uniform-ish distribution has negative excess kurtosis
        k = kurtosis([1, 2, 3, 4, 5])
        assert k < 0

    def test_constant_values(self):
        assert kurtosis([5, 5, 5, 5, 5]) == 0.0

    def test_four_elements_minimum(self):
        k = kurtosis([1, 2, 3, 10])
        assert isinstance(k, float)

    def test_insufficient_data(self):
        with pytest.raises(ValueError, match="at least 4"):
            kurtosis([1, 2, 3])
        with pytest.raises(ValueError):
            kurtosis([1])
        with pytest.raises(ValueError):
            kurtosis([])


# ==================== Correlation/Covariance Tests ====================

class TestCovariance:
    """Tests for covariance."""

    def test_positive_covariance(self):
        x = [1, 2, 3, 4, 5]
        y = [1, 2, 3, 4, 5]
        assert abs(covariance(x, y, ddof=1) - 2.5) < 1e-10

    def test_negative_covariance(self):
        x = [1, 2, 3, 4, 5]
        y = [5, 4, 3, 2, 1]
        assert abs(covariance(x, y, ddof=1) - (-2.5)) < 1e-10

    def test_zero_covariance(self):
        x = [1, 2, 3, 4, 5]
        y = [3, 3, 3, 3, 3]
        assert covariance(x, y, ddof=1) == 0.0

    def test_population_covariance(self):
        x = [1, 2, 3]
        y = [1, 2, 3]
        assert abs(covariance(x, y, ddof=0) - 2.0/3.0) < 1e-10

    def test_different_lengths_raises(self):
        with pytest.raises(ValueError, match="equal length"):
            covariance([1, 2], [1, 2, 3])

    def test_insufficient_data(self):
        with pytest.raises(ValueError):
            covariance([1], [1], ddof=1)


class TestCorrelation:
    """Tests for Pearson correlation."""

    def test_perfect_positive(self):
        x = [1, 2, 3, 4, 5]
        y = [1, 2, 3, 4, 5]
        assert abs(correlation(x, y) - 1.0) < 1e-10

    def test_perfect_negative(self):
        x = [1, 2, 3, 4, 5]
        y = [5, 4, 3, 2, 1]
        assert abs(correlation(x, y) - (-1.0)) < 1e-10

    def test_no_correlation(self):
        x = [1, 2, 3, 4, 5]
        y = [3, 3, 3, 3, 3]
        with pytest.raises(ZeroDivisionError):
            correlation(x, y)

    def test_partial_correlation(self):
        x = [1, 2, 3, 4, 5]
        y = [2, 3, 1, 5, 4]
        r = correlation(x, y)
        assert -1 < r < 1

    def test_different_lengths_raises(self):
        with pytest.raises(ValueError, match="equal length"):
            correlation([1, 2], [1, 2, 3])

    def test_insufficient_data(self):
        with pytest.raises(ValueError, match="at least 2"):
            correlation([1], [1])


# ==================== Rolling Statistics Tests ====================

class TestRollingMean:
    """Tests for rolling mean."""

    def test_window_3(self):
        result = rolling_mean([1, 2, 3, 4, 5], 3)
        assert result == [None, None, 2.0, 3.0, 4.0]

    def test_window_1(self):
        result = rolling_mean([1, 2, 3], 1)
        assert result == [1.0, 2.0, 3.0]

    def test_window_equals_length(self):
        result = rolling_mean([1, 2, 3], 3)
        assert result == [None, None, 2.0]

    def test_window_larger_than_length(self):
        result = rolling_mean([1, 2], 5)
        assert result == [None, None]

    def test_empty_input(self):
        assert rolling_mean([], 3) == []

    def test_invalid_window_raises(self):
        with pytest.raises(ValueError, match=">= 1"):
            rolling_mean([1, 2, 3], 0)
        with pytest.raises(ValueError):
            rolling_mean([1, 2, 3], -1)


class TestRollingStd:
    """Tests for rolling standard deviation."""

    def test_window_3(self):
        result = rolling_std([1, 2, 3, 4, 5], 3, ddof=1)
        # Window [1,2,3]: mean=2, var=1, std=1
        # Window [2,3,4]: mean=3, var=1, std=1
        # Window [3,4,5]: mean=4, var=1, std=1
        assert result[:2] == [None, None]
        assert all(abs(v - 1.0) < 1e-10 for v in result[2:])

    def test_window_1_sample(self):
        # Sample std with window=1 and ddof=1 is undefined (0/0), returns 0
        result = rolling_std([1, 2, 3], 1, ddof=1)
        assert result == [0.0, 0.0, 0.0]

    def test_constant_values(self):
        result = rolling_std([5, 5, 5, 5], 2, ddof=1)
        assert result[:1] == [None]
        assert all(v == 0.0 for v in result[1:])

    def test_empty_input(self):
        assert rolling_std([], 3) == []

    def test_invalid_window_raises(self):
        with pytest.raises(ValueError):
            rolling_std([1, 2, 3], 0)


# ==================== Autocorrelation Tests ====================

class TestAutocorrelation:
    """Tests for autocorrelation."""

    def test_lag_0_always_1(self):
        assert autocorrelation([1, 2, 3, 4, 5], lag=0) == 1.0

    def test_perfect_positive_lag_1(self):
        # Linear sequence: autocorr at lag 1 is 0.4 for [1,2,3,4,5]
        # (correlation between [1,2,3,4] and [2,3,4,5] with mean-adjusted normalization)
        assert abs(autocorrelation([1, 2, 3, 4, 5], lag=1) - 0.4) < 1e-10

    def test_perfect_negative_lag_1(self):
        # Alternating sequence: autocorr at lag 1 is -0.8 for [1,-1,1,-1,1]
        assert abs(autocorrelation([1, -1, 1, -1, 1], lag=1) - (-0.8)) < 1e-10

    def test_constant_sequence(self):
        assert autocorrelation([5, 5, 5, 5], lag=1) == 1.0
        assert autocorrelation([5, 5, 5, 5], lag=2) == 1.0

    def test_random_like(self):
        # Some random-ish data
        data = [1, 3, 2, 5, 4, 7, 6]
        acf1 = autocorrelation(data, lag=1)
        assert -1 <= acf1 <= 1

    def test_invalid_lag_negative(self):
        with pytest.raises(ValueError):
            autocorrelation([1, 2, 3], lag=-1)

    def test_invalid_lag_too_large(self):
        with pytest.raises(ValueError):
            autocorrelation([1, 2, 3], lag=3)

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            autocorrelation([], lag=0)


# ==================== Normalization/Transformation Tests ====================

class TestZScore:
    """Tests for z-score normalization."""

    def test_basic(self):
        result = z_score([1, 2, 3, 4, 5])
        assert abs(mean(result)) < 1e-10
        assert abs(std_dev(result, ddof=1) - 1.0) < 1e-10

    def test_constant_values(self):
        result = z_score([5, 5, 5, 5])
        assert all(v == 0.0 for v in result)

    def test_negative_values(self):
        result = z_score([-5, -3, -1, 1, 3, 5])
        assert abs(mean(result)) < 1e-10
        assert abs(std_dev(result, ddof=1) - 1.0) < 1e-10

    def test_two_elements(self):
        result = z_score([10, 20])
        assert abs(mean(result)) < 1e-10
        assert abs(std_dev(result, ddof=1) - 1.0) < 1e-10

    def test_insufficient_data(self):
        with pytest.raises(ValueError, match="at least 2"):
            z_score([1])
        with pytest.raises(ValueError):
            z_score([])


class TestMinMaxNormalize:
    """Tests for min-max normalization."""

    def test_default_range(self):
        result = min_max_normalize([10, 20, 30])
        assert result == [0.0, 0.5, 1.0]

    def test_custom_range(self):
        result = min_max_normalize([10, 20, 30], -1, 1)
        assert result == [-1.0, 0.0, 1.0]

    def test_constant_values(self):
        result = min_max_normalize([5, 5, 5], 0, 1)
        assert all(v == 0.5 for v in result)

    def test_negative_values(self):
        result = min_max_normalize([-10, 0, 10])
        assert result == [0.0, 0.5, 1.0]

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            min_max_normalize([])

    def test_invalid_range_raises(self):
        with pytest.raises(ValueError, match="new_min.*must be < new_max"):
            min_max_normalize([1, 2, 3], 5, 5)
        with pytest.raises(ValueError):
            min_max_normalize([1, 2, 3], 10, 5)


# ==================== Alternative Means Tests ====================

class TestGeometricMean:
    """Tests for geometric mean."""

    def test_basic(self):
        # GM of [1,2,4,8] = (1*2*4*8)^(1/4) = 64^(1/4) = 2*sqrt(2) ≈ 2.828
        assert abs(geometric_mean([1, 2, 4, 8]) - 2.8284271247461903) < 1e-10

    def test_all_ones(self):
        assert geometric_mean([1, 1, 1, 1]) == 1.0

    def test_floats(self):
        assert abs(geometric_mean([1.5, 2.0, 3.0]) - 2.080083823051904) < 1e-10

    def test_single_element(self):
        # Floating point precision: exp(log(42)) = 42.00000000000001
        assert abs(geometric_mean([42]) - 42.0) < 1e-10

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            geometric_mean([])

    def test_zero_raises(self):
        with pytest.raises(ValueError, match="positive"):
            geometric_mean([1, 0, 3])

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="positive"):
            geometric_mean([1, -2, 3])


class TestHarmonicMean:
    """Tests for harmonic mean."""

    def test_basic(self):
        # HM of [1,2,4,8] = 4 / (1 + 1/2 + 1/4 + 1/8) = 4 / 1.875 = 2.1333...
        assert abs(harmonic_mean([1, 2, 4, 8]) - 2.1333333333333333) < 1e-10

    def test_all_same(self):
        assert harmonic_mean([5, 5, 5, 5]) == 5.0

    def test_single_element(self):
        assert harmonic_mean([42]) == 42.0

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            harmonic_mean([])

    def test_zero_raises(self):
        with pytest.raises(ValueError, match="positive"):
            harmonic_mean([1, 0, 3])

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="positive"):
            harmonic_mean([1, -2, 3])


class TestRMS:
    """Tests for Root Mean Square."""

    def test_basic(self):
        # RMS of [3, 4] = sqrt((9+16)/2) = sqrt(12.5) ≈ 3.536
        assert abs(rms([3, 4]) - 3.5355339059327378) < 1e-10

    def test_alternating(self):
        assert rms([-1, 1, -1, 1]) == 1.0

    def test_all_positive(self):
        assert abs(rms([1, 2, 3]) - math.sqrt(14/3)) < 1e-10

    def test_single_element(self):
        assert rms([5]) == 5.0

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            rms([])


class TestSumOfSquares:
    """Tests for sum of squares."""

    def test_basic(self):
        # [1,2,3,4,5], mean=3, deviations=[-2,-1,0,1,2], squares=[4,1,0,1,4], sum=10
        assert sum_of_squares([1, 2, 3, 4, 5]) == 10.0

    def test_constant(self):
        assert sum_of_squares([5, 5, 5]) == 0.0

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            sum_of_squares([])


# ==================== Describe Tests ====================

class TestDescribe:
    """Tests for comprehensive statistical summary."""

    def test_basic(self):
        stats = describe([1, 2, 3, 4, 5])
        assert stats['count'] == 5
        assert stats['mean'] == 3.0
        assert stats['min'] == 1.0
        assert stats['max'] == 5.0
        assert stats['median'] == 3.0
        assert stats['range'] == 4.0
        assert stats['sum'] == 15.0
        assert 'std' in stats
        assert 'variance' in stats
        assert 'q1' in stats
        assert 'q3' in stats
        assert 'iqr' in stats
        assert 'skewness' in stats
        assert 'kurtosis' in stats
        assert 'sum_sq' in stats

    def test_single_element(self):
        stats = describe([42])
        assert stats['count'] == 1
        assert stats['mean'] == 42.0
        assert stats['std'] == 0.0
        assert stats['variance'] == 0.0
        assert stats['skewness'] == 0.0
        assert stats['kurtosis'] == 0.0

    def test_two_elements(self):
        stats = describe([10, 20])
        assert stats['count'] == 2
        assert stats['mean'] == 15.0
        assert stats['std'] > 0
        assert stats['skewness'] == 0.0
        assert stats['kurtosis'] == 0.0

    def test_three_elements(self):
        stats = describe([1, 2, 10])
        assert stats['count'] == 3
        assert stats['skewness'] != 0.0
        assert stats['kurtosis'] == 0.0

    def test_four_elements(self):
        stats = describe([1, 2, 3, 10])
        assert stats['count'] == 4
        assert stats['kurtosis'] != 0.0

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            describe([])


# ==================== Edge Case Integration Tests ====================

class TestEdgeCases:
    """Integration tests for edge cases and numerical stability."""

    def test_large_numbers_mean(self):
        data = [1e15, 1e15 + 1, 1e15 + 2]
        m = mean(data)
        assert abs(m - (1e15 + 1)) < 1e-3

    def test_small_numbers_mean(self):
        data = [1e-15, 2e-15, 3e-15]
        m = mean(data)
        assert abs(m - 2e-15) < 1e-20

    def test_mixed_signs_variance(self):
        data = [-1e10, 0, 1e10]
        v = variance(data, ddof=1)
        assert v > 0

    def test_high_precision_percentile(self):
        data = [i * 0.001 for i in range(1000)]
        p50 = percentile(data, 50)
        assert abs(p50 - 0.4995) < 1e-4

    def test_rng_large_sequence(self):
        rng = DeterministicRNG(seed=42)
        seq = [rng.random() for _ in range(10000)]
        assert len(seq) == 10000
        assert all(0 <= x < 1 for x in seq)

    def test_rolling_window_at_boundary(self):
        # Test rolling functions at exact boundary conditions
        assert rolling_mean([1, 2], 2) == [None, 1.5]
        assert rolling_std([1, 2], 2, ddof=1) == [None, math.sqrt(0.5)]

    def test_describe_with_extreme_values(self):
        data = [1e-100, 1e100]
        stats = describe(data)
        assert stats['count'] == 2
        assert stats['min'] == 1e-100
        assert stats['max'] == 1e100

    def test_correlation_near_perfect(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [1.0000001, 2.0000002, 3.0000003, 4.0000004, 5.0000005]
        r = correlation(x, y)
        assert r > 0.999999

    def test_autocorrelation_periodic(self):
        # Periodic signal: [1, 0, -1, 0, 1, 0, -1, 0]
        data = [1, 0, -1, 0, 1, 0, -1, 0]
        # At lag 4, autocorrelation is 0.5 (not 1.0 due to mean-adjusted normalization)
        acf4 = autocorrelation(data, lag=4)
        assert abs(acf4 - 0.5) < 1e-10


# ==================== Deterministic Regression Tests ====================

class TestDeterministicResults:
    """Regression tests with fixed expected values for deterministic verification."""

    def test_rng_known_sequence(self):
        """LCG with seed=0 produces known sequence."""
        rng = DeterministicRNG(seed=0)
        # First few values from Numerical Recipes LCG (1664525, 1013904223, 2^32)
        expected_ints = [
            1013904223,  # 1664525*0 + 1013904223
            1196435762,  # (1664525*1013904223 + 1013904223) mod 2^32
        ]
        for expected in expected_ints:
            assert rng.next_int() == expected

    def test_mean_known_values(self):
        assert mean([1, 2, 3]) == 2.0
        assert mean([0.1, 0.2, 0.3]) == pytest.approx(0.2, rel=1e-10)

    def test_variance_known_values(self):
        assert variance([2, 4, 4, 4, 5, 5, 7, 9], ddof=0) == 4.0
        assert variance([2, 4, 4, 4, 5, 5, 7, 9], ddof=1) == pytest.approx(4.571428571428571)

    def test_percentile_known_values(self):
        # From numpy reference
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        assert percentile(data, 25) == 3.25
        assert percentile(data, 50) == 5.5
        assert percentile(data, 75) == 7.75

    def test_correlation_known_values(self):
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]  # Perfect linear relationship y = 2x
        # Floating point precision gives 0.9999999999999998
        assert abs(correlation(x, y) - 1.0) < 1e-10

    def test_skewness_known_values(self):
        # Symmetric distribution
        assert skewness([1, 2, 3, 4, 5]) == 0.0

    def test_kurtosis_known_values(self):
        # Normal distribution sample (approximate)
        data = [-2, -1, 0, 1, 2]
        # Excess kurtosis for uniform is -1.2
        # For this small symmetric sample, should be computable
        k = kurtosis(data)
        assert isinstance(k, float)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])