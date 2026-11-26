"""
Deterministic Integer Number Theory Utilities.

This module provides a collection of pure, deterministic mathematical functions
for integer arithmetic and number theory. All functions are fully reproducible
with no external dependencies, global state, or side effects.

Functions cover:
- Prime factorization and primality testing
- Greatest common divisor (GCD) and least common multiple (LCM)
- Modular arithmetic (modular exponentiation, modular inverse)
- Euler's totient function
- Divisor sums (sigma function, aliquot sum)
- Perfect and amicable numbers
- Integer square root
- Sieve of Eratosthenes for prime generation

All functions include comprehensive type hints and docstrings with examples.
"""

from __future__ import annotations

from math import isqrt
from typing import List


# =============================================================================
# Input validation helpers
# =============================================================================

def _require_positive_int(value: int, name: str) -> None:
    """Raise ValueError if value is not a positive integer (> 0)."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be an integer, got {type(value).__name__}")
    if value <= 0:
        raise ValueError(f"{name} must be a positive integer, got {value}")


def _require_non_negative_int(value: int, name: str) -> None:
    """Raise ValueError if value is not a non-negative integer (>= 0)."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be an integer, got {type(value).__name__}")
    if value < 0:
        raise ValueError(f"{name} must be a non-negative integer, got {value}")


def _require_ints(*pairs: tuple[int, str]) -> None:
    """Validate that all values are integers (not bool)."""
    for value, name in pairs:
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError(f"{name} must be an integer, got {type(value).__name__}")


# =============================================================================
# Core number theory functions
# =============================================================================

def prime_factors(n: int) -> List[int]:
    """
    Return the prime factorization of a positive integer as a sorted list.

    The result contains prime factors with multiplicity, sorted in
    non-decreasing order. For example, 12 = 2 * 2 * 3 returns [2, 2, 3].

    Args:
        n: A positive integer to factorize (n > 0).

    Returns:
        List of prime factors in non-decreasing order.

    Raises:
        TypeError: If n is not an integer or is a boolean.
        ValueError: If n <= 0.

    Examples:
        >>> prime_factors(1)
        []
        >>> prime_factors(12)
        [2, 2, 3]
        >>> prime_factors(13)
        [13]
        >>> prime_factors(100)
        [2, 2, 5, 5]
    """
    _require_positive_int(n, "n")

    if n == 1:
        return []

    factors: List[int] = []
    d = 2
    m = n
    while d * d <= m:
        while m % d == 0:
            factors.append(d)
            m //= d
        d += 1 if d == 2 else 2  # After 2, test only odd numbers
    if m > 1:
        factors.append(m)
    return factors


def is_prime(n: int) -> bool:
    """
    Deterministic primality test for non-negative integers.

    Returns True if n is a prime number (n > 1 and has no divisors
    other than 1 and itself), False otherwise.

    Args:
        n: Integer to test for primality (n >= 0).

    Returns:
        True if n is prime, False otherwise.

    Raises:
        TypeError: If n is not an integer or is a boolean.
        ValueError: If n < 0.

    Examples:
        >>> is_prime(0)
        False
        >>> is_prime(1)
        False
        >>> is_prime(2)
        True
        >>> is_prime(13)
        True
        >>> is_prime(100)
        False
    """
    _require_non_negative_int(n, "n")

    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False

    limit = isqrt(n)
    d = 3
    while d <= limit:
        if n % d == 0:
            return False
        d += 2
    return True


def gcd(a: int, b: int) -> int:
    """
    Compute the greatest common divisor of two integers using Euclid's algorithm.

    The GCD is always non-negative. gcd(0, 0) returns 0 by convention.

    Args:
        a: First integer.
        b: Second integer.

    Returns:
        The greatest common divisor of a and b (>= 0).

    Raises:
        TypeError: If either argument is not an integer or is a boolean.

    Examples:
        >>> gcd(48, 18)
        6
        >>> gcd(-48, 18)
        6
        >>> gcd(0, 5)
        5
        >>> gcd(0, 0)
        0
    """
    _require_ints((a, "a"), (b, "b"))

    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def lcm(a: int, b: int) -> int:
    """
    Compute the least common multiple of two integers.

    The LCM is always non-negative. lcm(0, b) = 0 for any b.
    lcm(0, 0) = 0 by convention.

    Args:
        a: First integer.
        b: Second integer.

    Returns:
        The least common multiple of a and b (>= 0).

    Raises:
        TypeError: If either argument is not an integer or is a boolean.

    Examples:
        >>> lcm(4, 6)
        12
        >>> lcm(-4, 6)
        12
        >>> lcm(0, 5)
        0
        >>> lcm(0, 0)
        0
    """
    _require_ints((a, "a"), (b, "b"))

    if a == 0 or b == 0:
        return 0
    return abs(a // gcd(a, b) * b)


def mod_pow(base: int, exp: int, mod: int) -> int:
    """
    Compute (base ** exp) % mod efficiently using binary exponentiation.

    Works for non-negative exponent and positive modulus.

    Args:
        base: Base integer.
        exp: Non-negative exponent.
        mod: Positive modulus.

    Returns:
        (base ** exp) % mod as an integer in [0, mod - 1].

    Raises:
        TypeError: If any argument is not an integer or is a boolean.
        ValueError: If exp < 0 or mod <= 0.

    Examples:
        >>> mod_pow(2, 10, 1000)
        24
        >>> mod_pow(3, 0, 7)
        1
        >>> mod_pow(5, 3, 13)
        8
    """
    _require_ints((base, "base"), (exp, "exp"), (mod, "mod"))
    if exp < 0:
        raise ValueError(f"exp must be non-negative, got {exp}")
    if mod <= 0:
        raise ValueError(f"mod must be positive, got {mod}")

    result = 1 % mod
    base = base % mod
    while exp > 0:
        if exp & 1:
            result = (result * base) % mod
        base = (base * base) % mod
        exp >>= 1
    return result


def mod_inv(a: int, mod: int) -> int:
    """
    Compute the modular multiplicative inverse of a modulo mod.

    Returns x such that (a * x) % mod == 1. Requires gcd(a, mod) == 1.

    Args:
        a: Integer whose inverse is sought.
        mod: Positive modulus.

    Returns:
        Integer x in [0, mod - 1] such that (a * x) % mod == 1.

    Raises:
        TypeError: If either argument is not an integer or is a boolean.
        ValueError: If mod <= 0 or gcd(a, mod) != 1 (inverse does not exist).

    Examples:
        >>> mod_inv(3, 11)
        4
        >>> mod_inv(10, 17)
        12
    """
    _require_ints((a, "a"), (mod, "mod"))
    if mod <= 0:
        raise ValueError(f"mod must be positive, got {mod}")

    # Extended Euclidean Algorithm
    def egcd(x: int, y: int) -> tuple[int, int, int]:
        if y == 0:
            return (x, 1, 0)
        g, x1, y1 = egcd(y, x % y)
        return (g, y1, x1 - (x // y) * y1)

    g, x, _ = egcd(a, mod)
    if g != 1:
        raise ValueError(f"modular inverse does not exist: gcd({a}, {mod}) = {g}")
    return x % mod


def euler_totient(n: int) -> int:
    """
    Compute Euler's totient function φ(n): the count of integers in [1, n]
    that are coprime to n.

    For n > 0, φ(n) = n * ∏(1 - 1/p) over distinct prime factors p of n.

    Args:
        n: Positive integer.

    Returns:
        φ(n) as a non-negative integer.

    Raises:
        TypeError: If n is not an integer or is a boolean.
        ValueError: If n <= 0.

    Examples:
        >>> euler_totient(1)
        1
        >>> euler_totient(9)
        6
        >>> euler_totient(10)
        4
        >>> euler_totient(13)
        12
    """
    _require_positive_int(n, "n")

    if n == 1:
        return 1

    result = n
    factors = prime_factors(n)
    # Use set to get distinct primes
    for p in set(factors):
        result -= result // p
    return result


def sum_of_divisors(n: int) -> int:
    """
    Compute the sum of all positive divisors of n (sigma function σ(n)).

    For n = ∏ p_i^e_i, σ(n) = ∏ (p_i^(e_i+1) - 1) / (p_i - 1).

    Args:
        n: Positive integer.

    Returns:
        Sum of all positive divisors of n.

    Raises:
        TypeError: If n is not an integer or is a boolean.
        ValueError: If n <= 0.

    Examples:
        >>> sum_of_divisors(1)
        1
        >>> sum_of_divisors(6)
        12  # 1 + 2 + 3 + 6
        >>> sum_of_divisors(28)
        56  # 1 + 2 + 4 + 7 + 14 + 28
    """
    _require_positive_int(n, "n")

    if n == 1:
        return 1

    factors = prime_factors(n)
    # Count exponents of each prime
    from collections import Counter
    exp_counts = Counter(factors)

    total = 1
    for p, e in exp_counts.items():
        total *= (p ** (e + 1) - 1) // (p - 1)
    return total


def aliquot_sum(n: int) -> int:
    """
    Compute the aliquot sum of n: sum of proper divisors (excluding n itself).

    aliquot_sum(n) = sum_of_divisors(n) - n.

    Args:
        n: Positive integer.

    Returns:
        Sum of proper divisors of n.

    Raises:
        TypeError: If n is not an integer or is a boolean.
        ValueError: If n <= 0.

    Examples:
        >>> aliquot_sum(1)
        0
        >>> aliquot_sum(6)
        6   # 1 + 2 + 3 (perfect number)
        >>> aliquot_sum(28)
        28  # perfect number
        >>> aliquot_sum(12)
        16  # 1 + 2 + 3 + 4 + 6 (abundant)
    """
    _require_positive_int(n, "n")
    return sum_of_divisors(n) - n


def is_perfect(n: int) -> bool:
    """
    Check if n is a perfect number: aliquot_sum(n) == n.

    A perfect number equals the sum of its proper divisors.

    Args:
        n: Positive integer.

    Returns:
        True if n is perfect, False otherwise.

    Raises:
        TypeError: If n is not an integer or is a boolean.
        ValueError: If n <= 0.

    Examples:
        >>> is_perfect(6)
        True
        >>> is_perfect(28)
        True
        >>> is_perfect(12)
        False
        >>> is_perfect(496)
        True
    """
    _require_positive_int(n, "n")
    return aliquot_sum(n) == n


def are_amicable(a: int, b: int) -> bool:
    """
    Check if a and b form an amicable pair.

    Two distinct numbers are amicable if the sum of proper divisors of
    each equals the other: aliquot_sum(a) == b and aliquot_sum(b) == a.

    Args:
        a: First positive integer.
        b: Second positive integer.

    Returns:
        True if a and b are an amicable pair, False otherwise.

    Raises:
        TypeError: If either argument is not an integer or is a boolean.
        ValueError: If either argument <= 0.

    Examples:
        >>> are_amicable(220, 284)
        True
        >>> are_amicable(284, 220)
        True
        >>> are_amicable(220, 220)
        False  # must be distinct
        >>> are_amicable(6, 28)
        False
    """
    _require_positive_int(a, "a")
    _require_positive_int(b, "b")

    if a == b:
        return False
    return aliquot_sum(a) == b and aliquot_sum(b) == a


def integer_sqrt(n: int) -> int:
    """
    Compute the integer square root: floor(sqrt(n)).

    Uses math.isqrt (Python 3.8+) which returns the floor of the exact
    square root for non-negative integers.

    Args:
        n: Non-negative integer.

    Returns:
        floor(sqrt(n)).

    Raises:
        TypeError: If n is not an integer or is a boolean.
        ValueError: If n < 0.

    Examples:
        >>> integer_sqrt(0)
        0
        >>> integer_sqrt(1)
        1
        >>> integer_sqrt(15)
        3
        >>> integer_sqrt(16)
        4
        >>> integer_sqrt(17)
        4
    """
    _require_non_negative_int(n, "n")
    return isqrt(n)


def sieve_of_eratosthenes(limit: int) -> List[int]:
    """
    Generate all prime numbers up to and including limit using the
    Sieve of Eratosthenes.

    Args:
        limit: Upper bound (inclusive) for prime generation. Must be >= 2
               for non-empty result; limit < 2 returns an empty list.

    Returns:
        Sorted list of all primes <= limit.

    Raises:
        TypeError: If limit is not an integer or is a boolean.
        ValueError: If limit < 0.

    Examples:
        >>> sieve_of_eratosthenes(1)
        []
        >>> sieve_of_eratosthenes(10)
        [2, 3, 5, 7]
        >>> sieve_of_eratosthenes(20)
        [2, 3, 5, 7, 11, 13, 17, 19]
    """
    _require_non_negative_int(limit, "limit")

    if limit < 2:
        return []

    sieve = bytearray(b"\x01") * (limit + 1)
    sieve[0:2] = b"\x00\x00"
    for p in range(2, isqrt(limit) + 1):
        if sieve[p]:
            step = p
            start = p * p
            sieve[start:limit + 1:step] = b"\x00" * ((limit - start) // step + 1)

    return [i for i, is_prime in enumerate(sieve) if is_prime]