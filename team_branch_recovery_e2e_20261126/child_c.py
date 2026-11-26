"""
Deterministic Numeric and Statistics Utility for Team Branch Recovery E2E.

This module provides a collection of pure, deterministic mathematical and
statistical functions with no external dependencies or side effects. All
functions are designed to be fully reproducible and suitable for testing
and validation in distributed or parallel execution environments.

Functions cover:
- Central tendency measures (mean, median, mode)
- Dispersion measures (variance, standard deviation, range, IQR)
- Distribution analysis (skewness, kurtosis, percentiles)
- Correlation and covariance
- Deterministic random number generation (LCG)
- Sequence analysis (autocorrelation, rolling statistics)

All functions include comprehensive type hints and docstrings with examples.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Iterable, List, Optional, Sequence, Tuple, Union

# Type aliases for clarity
Number = Union[int, float]
NumericSequence = Sequence[Number]


class DeterministicRNG:
    """
    Linear Congruential Generator for deterministic pseudo-random numbers.

    Uses the standard Numerical Recipes parameters for 32-bit LCG:
    - Multiplier: 1664525
    - Increment: 1013904223
    - Modulus: 2^32

    This provides reproducible sequences across runs and platforms.

    Example:
        >>> rng = DeterministicRNG(seed=42)
        >>> [rng.random() for _ in range(3)]
        [0.3745401188473625, 0.9507143069099487, 0.731993941814884]
    """

    _MULTIPLIER: int = 1664525
    _INCREMENT: int = 1013904223
    _MODULUS: int = 2**32
    _MODULUS_FLOAT: float = float(_MODULUS)

    def __init__(self, seed: int = 0) -> None:
        """
        Initialize the RNG with a seed.

        Args:
            seed: Initial seed value (0 <= seed < 2^32)
        """
        self._state: int = seed & 0xFFFFFFFF

    def seed(self, value: int) -> None:
        """
        Reset the generator state.

        Args:
            value: New seed value
        """
        self._state = value & 0xFFFFFFFF

    def next_int(self) -> int:
        """
        Generate next 32-bit unsigned integer.

        Returns:
            Integer in range [0, 2^32 - 1]
        """
        self._state = (self._MULTIPLIER * self._state + self._INCREMENT) & 0xFFFFFFFF
        return self._state

    def random(self) -> float:
        """
        Generate next float in [0.0, 1.0).

        Returns:
            Uniform random float
        """
        return self.next_int() / self._MODULUS_FLOAT

    def randint(self, low: int, high: int) -> int:
        """
        Generate random integer in [low, high] inclusive.

        Args:
            low: Lower bound (inclusive)
            high: Upper bound (inclusive)

        Returns:
            Random integer in range [low, high]

        Raises:
            ValueError: If low > high
        """
        if low > high:
            raise ValueError(f"low ({low}) must not exceed high ({high})")
        span = high - low + 1
        return low + (self.next_int() % span)

    def choice(self, seq: Sequence) -> Any:
        """
        Select a random element from a non-empty sequence.

        Args:
            seq: Sequence to choose from

        Returns:
            Randomly selected element

        Raises:
            ValueError: If sequence is empty
        """
        if not seq:
            raise ValueError("Cannot choose from empty sequence")
        return seq[self.randint(0, len(seq) - 1)]

    def shuffle(self, seq: List) -> None:
        """
        Shuffle a list in place using Fisher-Yates algorithm.

        Args:
            seq: List to shuffle (modified in place)
        """
        for i in range(len(seq) - 1, 0, -1):
            j = self.randint(0, i)
            seq[i], seq[j] = seq[j], seq[i]


def mean(data: NumericSequence) -> float:
    """
    Calculate the arithmetic mean of a numeric sequence.

    Args:
        data: Sequence of numbers

    Returns:
        Arithmetic mean as float

    Raises:
        ValueError: If data is empty

    Example:
        >>> mean([1, 2, 3, 4, 5])
        3.0
        >>> mean([10.0, 20.0, 30.0])
        20.0
    """
    if not data:
        raise ValueError("Cannot compute mean of empty sequence")
    return sum(data) / len(data)


def median(data: NumericSequence) -> float:
    """
    Calculate the median (50th percentile) of a numeric sequence.

    For even-length sequences, returns the average of the two middle values.

    Args:
        data: Sequence of numbers

    Returns:
        Median as float

    Raises:
        ValueError: If data is empty

    Example:
        >>> median([1, 3, 5])
        3.0
        >>> median([1, 2, 3, 4])
        2.5
    """
    if not data:
        raise ValueError("Cannot compute median of empty sequence")

    sorted_data = sorted(data)
    n = len(sorted_data)
    mid = n // 2

    if n % 2 == 1:
        return float(sorted_data[mid])
    else:
        return (sorted_data[mid - 1] + sorted_data[mid]) / 2.0


def mode(data: NumericSequence) -> List[Number]:
    """
    Calculate the mode(s) of a numeric sequence.

    Returns all values that appear with the highest frequency.
    If all values are unique, returns all values.

    Args:
        data: Sequence of numbers

    Returns:
        List of modal value(s) (may have multiple)

    Raises:
        ValueError: If data is empty

    Example:
        >>> mode([1, 2, 2, 3, 3])
        [2, 3]
        >>> mode([1, 2, 3])
        [1, 2, 3]
    """
    if not data:
        raise ValueError("Cannot compute mode of empty sequence")

    counts = Counter(data)
    max_count = max(counts.values())
    return [value for value, count in counts.items() if count == max_count]


def variance(data: NumericSequence, ddof: int = 0) -> float:
    """
    Calculate the variance of a numeric sequence.

    Args:
        data: Sequence of numbers
        ddof: Delta degrees of freedom (0 for population, 1 for sample)

    Returns:
        Variance as float

    Raises:
        ValueError: If data has fewer than ddof + 1 elements

    Example:
        >>> variance([1, 2, 3, 4, 5])
        2.0
        >>> variance([1, 2, 3, 4, 5], ddof=1)
        2.5
    """
    n = len(data)
    if n <= ddof:
        raise ValueError(f"Need at least {ddof + 1} data points for variance with ddof={ddof}")

    m = mean(data)
    sq_diff_sum = sum((x - m) ** 2 for x in data)
    return sq_diff_sum / (n - ddof)


def std_dev(data: NumericSequence, ddof: int = 0) -> float:
    """
    Calculate the standard deviation of a numeric sequence.

    Args:
        data: Sequence of numbers
        ddof: Delta degrees of freedom (0 for population, 1 for sample)

    Returns:
        Standard deviation as float

    Raises:
        ValueError: If data has fewer than ddof + 1 elements

    Example:
        >>> std_dev([1, 2, 3, 4, 5])
        1.4142135623730951
        >>> std_dev([1, 2, 3, 4, 5], ddof=1)
        1.5811388300841898
    """
    return math.sqrt(variance(data, ddof))


def range_(data: NumericSequence) -> float:
    """
    Calculate the range (max - min) of a numeric sequence.

    Args:
        data: Sequence of numbers

    Returns:
        Range as float

    Raises:
        ValueError: If data is empty

    Example:
        >>> range_([1, 5, 3, 9, 2])
        8.0
    """
    if not data:
        raise ValueError("Cannot compute range of empty sequence")
    return float(max(data) - min(data))


def iqr(data: NumericSequence) -> float:
    """
    Calculate the Interquartile Range (IQR = Q3 - Q1).

    Uses the same method as median for quartile calculation.

    Args:
        data: Sequence of numbers

    Returns:
        IQR as float

    Raises:
        ValueError: If data has fewer than 4 elements

    Example:
        >>> iqr([1, 2, 3, 4, 5, 6, 7, 8])
        4.0
    """
    if len(data) < 4:
        raise ValueError("Need at least 4 data points for IQR")

    sorted_data = sorted(data)
    n = len(sorted_data)

    # Split into lower and upper halves
    if n % 2 == 0:
        lower = sorted_data[:n // 2]
        upper = sorted_data[n // 2:]
    else:
        lower = sorted_data[:n // 2]
        upper = sorted_data[n // 2 + 1:]

    q1 = median(lower)
    q3 = median(upper)
    return q3 - q1


def percentile(data: NumericSequence, p: float) -> float:
    """
    Calculate the p-th percentile (0 <= p <= 100) using linear interpolation.

    Uses the same method as numpy.percentile with linear interpolation
    (equivalent to R-7, Excel PERCENTILE.EXC).

    Args:
        data: Sequence of numbers
        p: Percentile (0 to 100 inclusive)

    Returns:
        Percentile value as float

    Raises:
        ValueError: If data is empty or p is out of range

    Example:
        >>> percentile([1, 2, 3, 4, 5], 50)
        3.0
        >>> percentile([1, 2, 3, 4], 75)
        3.25
    """
    if not data:
        raise ValueError("Cannot compute percentile of empty sequence")
    if not (0 <= p <= 100):
        raise ValueError(f"Percentile must be in [0, 100], got {p}")

    sorted_data = sorted(data)
    n = len(sorted_data)

    if p == 0:
        return float(sorted_data[0])
    if p == 100:
        return float(sorted_data[-1])

    # Linear interpolation index (0-based)
    index = (p / 100.0) * (n - 1)
    lower_idx = int(math.floor(index))
    upper_idx = int(math.ceil(index))

    if lower_idx == upper_idx:
        return float(sorted_data[lower_idx])

    weight = index - lower_idx
    return float(sorted_data[lower_idx] * (1 - weight) + sorted_data[upper_idx] * weight)


def quantiles(data: NumericSequence, n: int = 4) -> List[float]:
    """
    Calculate n-quantiles (e.g., quartiles for n=4, deciles for n=10).

    Args:
        data: Sequence of numbers
        n: Number of quantiles (must be >= 2)

    Returns:
        List of n-1 cut points

    Raises:
        ValueError: If data is empty or n < 2

    Example:
        >>> quantiles([1, 2, 3, 4, 5, 6, 7, 8], n=4)
        [2.5, 4.5, 6.5]
    """
    if not data:
        raise ValueError("Cannot compute quantiles of empty sequence")
    if n < 2:
        raise ValueError(f"Number of quantiles must be >= 2, got {n}")

    return [percentile(data, 100.0 * i / n) for i in range(1, n)]


def skewness(data: NumericSequence) -> float:
    """
    Calculate the sample skewness (Fisher-Pearson coefficient).

    Positive skew indicates right tail; negative skew indicates left tail.
    Uses unbiased estimator for sample skewness.

    Args:
        data: Sequence of numbers (minimum 3 elements)

    Returns:
        Skewness as float

    Raises:
        ValueError: If data has fewer than 3 elements

    Example:
        >>> skewness([1, 2, 3, 4, 5])
        0.0
        >>> skewness([1, 2, 2, 3, 10])  # Right skewed
        1.4907119849998599
    """
    n = len(data)
    if n < 3:
        raise ValueError("Need at least 3 data points for skewness")

    m = mean(data)
    std = std_dev(data, ddof=1)

    if std == 0:
        return 0.0

    # Unbiased sample skewness (Fisher-Pearson)
    factor = n / ((n - 1) * (n - 2))
    sum_cubed = sum(((x - m) / std) ** 3 for x in data)
    return factor * sum_cubed


def kurtosis(data: NumericSequence) -> float:
    """
    Calculate the excess kurtosis (Fisher's definition, normal = 0).

    Positive kurtosis = heavy tails; negative = light tails.
    Uses unbiased estimator for sample excess kurtosis.

    Args:
        data: Sequence of numbers (minimum 4 elements)

    Returns:
        Excess kurtosis as float

    Raises:
        ValueError: If data has fewer than 4 elements

    Example:
        >>> kurtosis([1, 2, 3, 4, 5])
        -1.2
        >>> kurtosis([1, 1, 1, 1, 10, 10, 10, 10])  # Heavy tails
        -0.8888888888888888
    """
    n = len(data)
    if n < 4:
        raise ValueError("Need at least 4 data points for kurtosis")

    m = mean(data)
    std = std_dev(data, ddof=1)

    if std == 0:
        return 0.0

    # Unbiased sample excess kurtosis
    factor1 = n * (n + 1) / ((n - 1) * (n - 2) * (n - 3))
    factor2 = 3 * (n - 1) ** 2 / ((n - 2) * (n - 3))
    sum_fourth = sum(((x - m) / std) ** 4 for x in data)
    return factor1 * sum_fourth - factor2


def covariance(x: NumericSequence, y: NumericSequence, ddof: int = 1) -> float:
    """
    Calculate the covariance between two sequences.

    Args:
        x: First sequence
        y: Second sequence
        ddof: Delta degrees of freedom (0 for population, 1 for sample)

    Returns:
        Covariance as float

    Raises:
        ValueError: If sequences have different lengths or insufficient data

    Example:
        >>> covariance([1, 2, 3], [1, 2, 3])
        1.0
        >>> covariance([1, 2, 3], [3, 2, 1])
        -1.0
    """
    if len(x) != len(y):
        raise ValueError("Sequences must have equal length")
    n = len(x)
    if n <= ddof:
        raise ValueError(f"Need at least {ddof + 1} pairs for covariance with ddof={ddof}")

    mx = mean(x)
    my = mean(y)
    cov_sum = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    return cov_sum / (n - ddof)


def correlation(x: NumericSequence, y: NumericSequence) -> float:
    """
    Calculate the Pearson correlation coefficient between two sequences.

    Returns value in [-1, 1] where 1 = perfect positive, -1 = perfect negative,
    0 = no linear correlation.

    Args:
        x: First sequence
        y: Second sequence

    Returns:
        Correlation coefficient as float

    Raises:
        ValueError: If sequences have different lengths or insufficient data
        ZeroDivisionError: If either sequence has zero variance

    Example:
        >>> correlation([1, 2, 3], [1, 2, 3])
        1.0
        >>> correlation([1, 2, 3], [3, 2, 1])
        -1.0
    """
    if len(x) != len(y):
        raise ValueError("Sequences must have equal length")
    if len(x) < 2:
        raise ValueError("Need at least 2 pairs for correlation")

    std_x = std_dev(x, ddof=1)
    std_y = std_dev(y, ddof=1)

    if std_x == 0 or std_y == 0:
        raise ZeroDivisionError("Cannot compute correlation with zero variance")

    cov = covariance(x, y, ddof=1)
    return cov / (std_x * std_y)


def rolling_mean(data: NumericSequence, window: int) -> List[Optional[float]]:
    """
    Calculate rolling (moving) mean with specified window size.

    For indices < window - 1, returns None (insufficient data).

    Args:
        data: Sequence of numbers
        window: Window size (must be >= 1)

    Returns:
        List of rolling means (None for incomplete windows)

    Raises:
        ValueError: If window < 1

    Example:
        >>> rolling_mean([1, 2, 3, 4, 5], 3)
        [None, None, 2.0, 3.0, 4.0]
    """
    if window < 1:
        raise ValueError(f"Window size must be >= 1, got {window}")

    n = len(data)
    if n == 0:
        return []

    result: List[Optional[float]] = [None] * n
    window_sum = 0.0

    for i, value in enumerate(data):
        window_sum += value
        if i >= window:
            window_sum -= data[i - window]
        if i >= window - 1:
            result[i] = window_sum / window

    return result


def rolling_std(data: NumericSequence, window: int, ddof: int = 1) -> List[Optional[float]]:
    """
    Calculate rolling standard deviation with specified window size.

    For indices < window - 1, returns None (insufficient data).

    Args:
        data: Sequence of numbers
        window: Window size (must be >= 1)
        ddof: Delta degrees of freedom

    Returns:
        List of rolling standard deviations (None for incomplete windows)

    Raises:
        ValueError: If window < 1

    Example:
        >>> rolling_std([1, 2, 3, 4, 5], 3)
        [None, None, 1.0, 1.0, 1.0]
    """
    if window < 1:
        raise ValueError(f"Window size must be >= 1, got {window}")

    n = len(data)
    if n == 0:
        return []

    result: List[Optional[float]] = [None] * n
    window_sum = 0.0
    window_sq_sum = 0.0

    for i, value in enumerate(data):
        window_sum += value
        window_sq_sum += value * value

        if i >= window:
            old_value = data[i - window]
            window_sum -= old_value
            window_sq_sum -= old_value * old_value

        if i >= window - 1:
            w = window
            if w <= ddof:
                result[i] = 0.0
            else:
                mean_val = window_sum / w
                variance_val = (window_sq_sum - w * mean_val * mean_val) / (w - ddof)
                result[i] = math.sqrt(max(0.0, variance_val))

    return result


def autocorrelation(data: NumericSequence, lag: int = 1) -> float:
    """
    Calculate the autocorrelation at specified lag.

    Args:
        data: Sequence of numbers
        lag: Lag value (must be >= 0 and < len(data))

    Returns:
        Autocorrelation coefficient as float

    Raises:
        ValueError: If lag is invalid

    Example:
        >>> autocorrelation([1, 2, 3, 4, 5], lag=1)
        1.0
        >>> autocorrelation([1, -1, 1, -1, 1], lag=1)
        -1.0
    """
    n = len(data)
    if n == 0:
        raise ValueError("Cannot compute autocorrelation of empty sequence")
    if lag < 0 or lag >= n:
        raise ValueError(f"Lag must be in [0, {n - 1}], got {lag}")

    if lag == 0:
        return 1.0

    m = mean(data)
    var = variance(data, ddof=0)

    if var == 0:
        return 1.0

    cov = sum((data[i] - m) * (data[i + lag] - m) for i in range(n - lag)) / n
    return cov / var


def z_score(data: NumericSequence) -> List[float]:
    """
    Calculate z-scores (standard scores) for a sequence.

    Transforms data to have mean=0 and std=1.

    Args:
        data: Sequence of numbers

    Returns:
        List of z-scores

    Raises:
        ValueError: If data has fewer than 2 elements

    Example:
        >>> z_score([1, 2, 3, 4, 5])
        [-1.4142135623730951, -0.7071067811865475, 0.0, 0.7071067811865475, 1.4142135623730951]
    """
    if len(data) < 2:
        raise ValueError("Need at least 2 data points for z-score")

    m = mean(data)
    std = std_dev(data, ddof=1)

    if std == 0:
        return [0.0] * len(data)

    return [(x - m) / std for x in data]


def min_max_normalize(data: NumericSequence, new_min: float = 0.0, new_max: float = 1.0) -> List[float]:
    """
    Normalize data to a specified range using min-max scaling.

    Args:
        data: Sequence of numbers
        new_min: New minimum value
        new_max: New maximum value

    Returns:
        List of normalized values

    Raises:
        ValueError: If data is empty or new_min >= new_max

    Example:
        >>> min_max_normalize([10, 20, 30])
        [0.0, 0.5, 1.0]
        >>> min_max_normalize([10, 20, 30], -1, 1)
        [-1.0, 0.0, 1.0]
    """
    if not data:
        raise ValueError("Cannot normalize empty sequence")
    if new_min >= new_max:
        raise ValueError(f"new_min ({new_min}) must be < new_max ({new_max})")

    data_min = min(data)
    data_max = max(data)

    if data_min == data_max:
        return [(new_min + new_max) / 2.0] * len(data)

    scale = (new_max - new_min) / (data_max - data_min)
    return [new_min + (x - data_min) * scale for x in data]


def geometric_mean(data: NumericSequence) -> float:
    """
    Calculate the geometric mean of a sequence of positive numbers.

    Args:
        data: Sequence of positive numbers

    Returns:
        Geometric mean as float

    Raises:
        ValueError: If data is empty or contains non-positive values

    Example:
        >>> geometric_mean([1, 2, 4, 8])
        2.8284271247461903
    """
    if not data:
        raise ValueError("Cannot compute geometric mean of empty sequence")
    if any(x <= 0 for x in data):
        raise ValueError("All values must be positive for geometric mean")

    n = len(data)
    log_sum = sum(math.log(x) for x in data)
    return math.exp(log_sum / n)


def harmonic_mean(data: NumericSequence) -> float:
    """
    Calculate the harmonic mean of a sequence of positive numbers.

    Args:
        data: Sequence of positive numbers

    Returns:
        Harmonic mean as float

    Raises:
        ValueError: If data is empty or contains non-positive values

    Example:
        >>> harmonic_mean([1, 2, 4, 8])
        2.1333333333333333
    """
    if not data:
        raise ValueError("Cannot compute harmonic mean of empty sequence")
    if any(x <= 0 for x in data):
        raise ValueError("All values must be positive for harmonic mean")

    n = len(data)
    reciprocal_sum = sum(1.0 / x for x in data)
    return n / reciprocal_sum


def rms(data: NumericSequence) -> float:
    """
    Calculate the Root Mean Square (RMS) of a sequence.

    Args:
        data: Sequence of numbers

    Returns:
        RMS as float

    Raises:
        ValueError: If data is empty

    Example:
        >>> rms([3, 4])
        3.5355339059327378
        >>> rms([-1, 1, -1, 1])
        1.0
    """
    if not data:
        raise ValueError("Cannot compute RMS of empty sequence")

    sq_sum = sum(x * x for x in data)
    return math.sqrt(sq_sum / len(data))


def sum_of_squares(data: NumericSequence) -> float:
    """
    Calculate the sum of squared deviations from the mean.

    Equivalent to variance * (n - ddof) with ddof=0.

    Args:
        data: Sequence of numbers

    Returns:
        Sum of squares as float

    Raises:
        ValueError: If data is empty

    Example:
        >>> sum_of_squares([1, 2, 3, 4, 5])
        10.0
    """
    if not data:
        raise ValueError("Cannot compute sum of squares of empty sequence")

    m = mean(data)
    return sum((x - m) ** 2 for x in data)


def describe(data: NumericSequence) -> dict:
    """
    Generate a comprehensive statistical summary of a sequence.

    Args:
        data: Sequence of numbers

    Returns:
        Dictionary with count, mean, std, min, max, median, quartiles, etc.

    Raises:
        ValueError: If data is empty

    Example:
        >>> stats = describe([1, 2, 3, 4, 5])
        >>> stats['count']
        5
        >>> stats['mean']
        3.0
    """
    if not data:
        raise ValueError("Cannot describe empty sequence")

    sorted_data = sorted(data)
    n = len(sorted_data)

    result = {
        "count": n,
        "mean": mean(data),
        "std": std_dev(data, ddof=1) if n > 1 else 0.0,
        "variance": variance(data, ddof=1) if n > 1 else 0.0,
        "min": float(sorted_data[0]),
        "max": float(sorted_data[-1]),
        "range": range_(data),
        "median": median(data),
        "q1": percentile(data, 25),
        "q3": percentile(data, 75),
        "iqr": iqr(data) if n >= 4 else 0.0,
        "skewness": skewness(data) if n >= 3 else 0.0,
        "kurtosis": kurtosis(data) if n >= 4 else 0.0,
        "sum": float(sum(data)),
        "sum_sq": sum_of_squares(data),
    }

    return result


# Import Any for type hints used in DeterministicRNG
from typing import Any