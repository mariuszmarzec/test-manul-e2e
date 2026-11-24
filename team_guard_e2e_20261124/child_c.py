"""
Deterministic mathematical and statistical utility module.

This module provides pure, deterministic functions for common numerical
operations and statistical calculations. All functions are side-effect free
and have no external dependencies.

Functions:
    - clamp: Constrain a value within a range
    - lerp: Linear interpolation between two values
    - mean: Arithmetic mean of a sequence
    - median: Median value of a sequence
    - std_dev: Population standard deviation
    - percentile: Percentile value using linear interpolation
    - is_close: Compare floats with relative and absolute tolerance
    - round_to: Round to specified decimal places
"""

from __future__ import annotations

from typing import Sequence, Union

Number = Union[int, float]


def clamp(value: Number, minimum: Number, maximum: Number) -> Number:
    """
    Constrain a value to lie within the inclusive range [minimum, maximum].

    Args:
        value: The value to clamp.
        minimum: Lower bound (inclusive).
        maximum: Upper bound (inclusive).

    Returns:
        The value constrained to the range.

    Raises:
        ValueError: If minimum > maximum.

    Examples:
        >>> clamp(5, 0, 10)
        5
        >>> clamp(-5, 0, 10)
        0
        >>> clamp(15, 0, 10)
        10
    """
    if minimum > maximum:
        raise ValueError(f"minimum ({minimum}) must not exceed maximum ({maximum})")
    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value


def lerp(start: Number, end: Number, t: float) -> float:
    """
    Linear interpolation between start and end using parameter t.

    Computes: start + t * (end - start)

    Args:
        start: Starting value (t=0).
        end: Ending value (t=1).
        t: Interpolation parameter. Values outside [0, 1] extrapolate.

    Returns:
        Interpolated value as float.

    Examples:
        >>> lerp(0, 10, 0.5)
        5.0
        >>> lerp(10, 20, 0.0)
        10.0
        >>> lerp(10, 20, 1.0)
        20.0
    """
    return start + t * (end - start)


def mean(values: Sequence[Number]) -> float:
    """
    Calculate the arithmetic mean of a sequence of numbers.

    Args:
        values: Non-empty sequence of numbers.

    Returns:
        Arithmetic mean as float.

    Raises:
        ValueError: If values is empty.

    Examples:
        >>> mean([1, 2, 3, 4, 5])
        3.0
        >>> mean([10])
        10.0
    """
    if not values:
        raise ValueError("mean() requires at least one value")
    return sum(values) / len(values)


def median(values: Sequence[Number]) -> float:
    """
    Calculate the median (middle value) of a sequence of numbers.

    For an even number of elements, returns the average of the two middle values.

    Args:
        values: Non-empty sequence of numbers.

    Returns:
        Median as float.

    Raises:
        ValueError: If values is empty.

    Examples:
        >>> median([1, 3, 5])
        3.0
        >>> median([1, 2, 3, 4])
        2.5
    """
    if not values:
        raise ValueError("median() requires at least one value")
    sorted_values = sorted(values)
    n = len(sorted_values)
    mid = n // 2
    if n % 2 == 1:
        return float(sorted_values[mid])
    return (sorted_values[mid - 1] + sorted_values[mid]) / 2.0


def std_dev(values: Sequence[Number]) -> float:
    """
    Calculate the population standard deviation of a sequence of numbers.

    Uses the population formula (divides by N, not N-1).

    Args:
        values: Non-empty sequence of numbers.

    Returns:
        Population standard deviation as float.

    Raises:
        ValueError: If values is empty.

    Examples:
        >>> std_dev([10, 10, 10, 10])
        0.0
        >>> round(std_dev([1, 2, 3, 4, 5]), 10)
        1.4142135624
    """
    if not values:
        raise ValueError("std_dev() requires at least one value")
    m = mean(values)
    variance = sum((x - m) ** 2 for x in values) / len(values)
    return variance ** 0.5


def percentile(values: Sequence[Number], p: float) -> float:
    """
    Calculate the p-th percentile (0 <= p <= 100) using linear interpolation.

    Uses the same method as numpy.percentile with interpolation='linear'.

    Args:
        values: Non-empty sequence of numbers.
        p: Percentile to compute, in range [0, 100].

    Returns:
        Percentile value as float.

    Raises:
        ValueError: If values is empty or p is outside [0, 100].

    Examples:
        >>> percentile([1, 2, 3, 4, 5], 50)
        3.0
        >>> percentile([1, 2, 3, 4, 5], 0)
        1.0
        >>> percentile([1, 2, 3, 4, 5], 100)
        5.0
    """
    if not values:
        raise ValueError("percentile() requires at least one value")
    if p < 0 or p > 100:
        raise ValueError(f"percentile p must be in [0, 100], got {p}")

    sorted_values = sorted(values)
    n = len(sorted_values)

    if n == 1:
        return float(sorted_values[0])

    # Compute the position using linear interpolation
    # Position = (p / 100) * (n - 1)
    pos = (p / 100.0) * (n - 1)
    idx = int(pos)
    frac = pos - idx

    if idx >= n - 1:
        return float(sorted_values[-1])

    lower = sorted_values[idx]
    upper = sorted_values[idx + 1]
    return float(lower + frac * (upper - lower))


def is_close(a: Number, b: Number, rel_tol: float = 1e-9, abs_tol: float = 0.0) -> bool:
    """
    Determine whether two numbers are close to each other.

    Implements the same logic as math.isclose (PEP 485).

    Args:
        a: First number.
        b: Second number.
        rel_tol: Relative tolerance (default 1e-9).
        abs_tol: Absolute tolerance (default 0.0).

    Returns:
        True if |a - b| <= max(rel_tol * max(|a|, |b|), abs_tol)

    Examples:
        >>> is_close(1.0, 1.0 + 1e-10)
        True
        >>> is_close(1.0, 1.0 + 1e-8)
        False
        >>> is_close(1e-10, 2e-10, abs_tol=1e-9)
        True
    """
    if rel_tol < 0 or abs_tol < 0:
        raise ValueError("tolerances must be non-negative")
    diff = abs(a - b)
    return diff <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


def round_to(value: Number, decimals: int = 0) -> float:
    """
    Round a number to a specified number of decimal places.

    Unlike built-in round(), this always returns a float and handles
    negative decimals correctly.

    Args:
        value: Number to round.
        decimals: Number of decimal places (can be negative).

    Returns:
        Rounded value as float.

    Examples:
        >>> round_to(3.14159, 2)
        3.14
        >>> round_to(1234, -2)
        1200.0
        >>> round_to(2.5, 0)
        2.0
    """
    factor = 10 ** decimals
    return round(value * factor) / factor


__all__ = [
    "clamp",
    "lerp",
    "mean",
    "median",
    "std_dev",
    "percentile",
    "is_close",
    "round_to",
]