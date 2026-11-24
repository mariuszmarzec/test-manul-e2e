"""Numeric sequence utilities for Team Flow E2E Child C.

This module provides deterministic numeric sequence functions with
comprehensive type hints and documentation.
"""

from typing import List, Tuple, Optional


def fibonacci(n: int) -> int:
    """Return the nth Fibonacci number (0-indexed).

    Args:
        n: The index of the Fibonacci number to return (must be non-negative).

    Returns:
        The nth Fibonacci number.

    Raises:
        ValueError: If n is negative.

    Examples:
        >>> fibonacci(0)
        0
        >>> fibonacci(1)
        1
        >>> fibonacci(5)
        5
        >>> fibonacci(10)
        55
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        return 0
    if n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def fibonacci_sequence(n: int) -> List[int]:
    """Return the first n Fibonacci numbers as a list.

    Args:
        n: The number of Fibonacci numbers to generate (must be non-negative).

    Returns:
        A list containing the first n Fibonacci numbers.

    Raises:
        ValueError: If n is negative.

    Examples:
        >>> fibonacci_sequence(0)
        []
        >>> fibonacci_sequence(1)
        [0]
        >>> fibonacci_sequence(5)
        [0, 1, 1, 2, 3]
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        return []
    if n == 1:
        return [0]
    result = [0, 1]
    for _ in range(2, n):
        result.append(result[-1] + result[-2])
    return result


def is_prime(n: int) -> bool:
    """Check if a number is prime.

    Args:
        n: The number to check (must be >= 2 for prime check).

    Returns:
        True if n is prime, False otherwise.

    Examples:
        >>> is_prime(2)
        True
        >>> is_prime(7)
        True
        >>> is_prime(10)
        False
        >>> is_prime(1)
        False
    """
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n ** 0.5) + 1, 2):
        if n % i == 0:
            return False
    return True


def prime_factors(n: int) -> List[int]:
    """Return the prime factorization of a number.

    Args:
        n: The number to factorize (must be >= 2).

    Returns:
        A list of prime factors in ascending order.

    Raises:
        ValueError: If n < 2.

    Examples:
        >>> prime_factors(12)
        [2, 2, 3]
        >>> prime_factors(7)
        [7]
        >>> prime_factors(100)
        [2, 2, 5, 5]
    """
    if n < 2:
        raise ValueError("n must be >= 2")
    factors = []
    # Handle factor 2
    while n % 2 == 0:
        factors.append(2)
        n //= 2
    # Handle odd factors
    i = 3
    while i * i <= n:
        while n % i == 0:
            factors.append(i)
            n //= i
        i += 2
    if n > 1:
        factors.append(n)
    return factors


def gcd(a: int, b: int) -> int:
    """Compute the greatest common divisor of two integers.

    Args:
        a: First integer.
        b: Second integer.

    Returns:
        The greatest common divisor of a and b.

    Examples:
        >>> gcd(48, 18)
        6
        >>> gcd(7, 13)
        1
        >>> gcd(0, 5)
        5
    """
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def lcm(a: int, b: int) -> int:
    """Compute the least common multiple of two integers.

    Args:
        a: First integer.
        b: Second integer.

    Returns:
        The least common multiple of a and b.

    Examples:
        >>> lcm(4, 6)
        12
        >>> lcm(7, 13)
        91
        >>> lcm(0, 5)
        0
    """
    if a == 0 or b == 0:
        return 0
    return abs(a * b) // gcd(a, b)