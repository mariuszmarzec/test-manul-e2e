"""
Tests for team_parser_postfix_e2e_20261126.child_c deterministic integer
number theory utilities.

Covers normal operations, edge cases, and error conditions for all functions.
"""

import pytest
from team_parser_postfix_e2e_20261126.child_c import (
    prime_factors,
    is_prime,
    gcd,
    lcm,
    mod_pow,
    mod_inv,
    euler_totient,
    sum_of_divisors,
    aliquot_sum,
    is_perfect,
    are_amicable,
    integer_sqrt,
    sieve_of_eratosthenes,
)


# =============================================================================
# prime_factors tests
# =============================================================================

class TestPrimeFactors:
    """Tests for prime_factors function."""

    # Normal cases
    @pytest.mark.parametrize("n,expected", [
        (1, []),
        (2, [2]),
        (3, [3]),
        (4, [2, 2]),
        (6, [2, 3]),
        (12, [2, 2, 3]),
        (13, [13]),
        (15, [3, 5]),
        (27, [3, 3, 3]),
        (30, [2, 3, 5]),
        (60, [2, 2, 3, 5]),
        (100, [2, 2, 5, 5]),
        (97, [97]),
        (13195, [5, 7, 13, 29]),
        (600851475143, [71, 839, 1471, 6857]),  # Project Euler #3
    ])
    def test_normal(self, n: int, expected: list[int]) -> None:
        assert prime_factors(n) == expected

    # Edge cases
    def test_large_prime(self) -> None:
        # 2147483647 is a Mersenne prime (2^31 - 1)
        assert prime_factors(2147483647) == [2147483647]

    def test_large_composite(self) -> None:
        # 2^20 * 3^10
        n = (2 ** 20) * (3 ** 10)
        factors = prime_factors(n)
        assert factors.count(2) == 20
        assert factors.count(3) == 10
        assert len(factors) == 30

    def test_product_equals_original(self) -> None:
        import math
        for n in [2, 6, 12, 30, 100, 13195, 99991]:
            factors = prime_factors(n)
            assert math.prod(factors) == n

    # Error cases
    @pytest.mark.parametrize("invalid_input", [
        0,
        -1,
        -100,
    ])
    def test_non_positive_raises_value_error(self, invalid_input: int) -> None:
        with pytest.raises(ValueError, match="positive integer"):
            prime_factors(invalid_input)

    @pytest.mark.parametrize("invalid_input", [
        1.5,
        "12",
        None,
        [12],
        True,
        False,
    ])
    def test_non_int_raises_type_error(self, invalid_input) -> None:
        with pytest.raises(TypeError, match="integer"):
            prime_factors(invalid_input)


# =============================================================================
# is_prime tests
# =============================================================================

class TestIsPrime:
    """Tests for is_prime function."""

    # Normal cases
    @pytest.mark.parametrize("n,expected", [
        (0, False),
        (1, False),
        (2, True),
        (3, True),
        (4, False),
        (5, True),
        (6, False),
        (7, True),
        (9, False),
        (11, True),
        (13, True),
        (15, False),
        (17, True),
        (19, True),
        (21, False),
        (23, True),
        (25, False),
        (29, True),
        (97, True),
        (100, False),
        (9973, True),   # large prime
        (99991, True),  # large prime
        (100000, False),
    ])
    def test_normal(self, n: int, expected: bool) -> None:
        assert is_prime(n) == expected

    # Edge cases
    def test_large_mersenne_prime(self) -> None:
        # 2^31 - 1 = 2147483647 is prime
        assert is_prime(2147483647) is True

    def test_large_composite(self) -> None:
        assert is_prime(2147483646) is False  # 2 * 1073741823

    def test_even_numbers(self) -> None:
        for n in range(4, 100, 2):
            assert is_prime(n) is False

    # Error cases
    @pytest.mark.parametrize("invalid_input", [
        -1,
        -100,
    ])
    def test_negative_raises_value_error(self, invalid_input: int) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            is_prime(invalid_input)

    @pytest.mark.parametrize("invalid_input", [
        1.5,
        "13",
        None,
        [13],
        True,
        False,
    ])
    def test_non_int_raises_type_error(self, invalid_input) -> None:
        with pytest.raises(TypeError, match="integer"):
            is_prime(invalid_input)


# =============================================================================
# gcd tests
# =============================================================================

class TestGcd:
    """Tests for gcd function."""

    # Normal cases
    @pytest.mark.parametrize("a,b,expected", [
        (48, 18, 6),
        (18, 48, 6),
        (17, 13, 1),
        (100, 25, 25),
        (0, 5, 5),
        (5, 0, 5),
        (0, 0, 0),
        (-48, 18, 6),
        (48, -18, 6),
        (-48, -18, 6),
        (1, 1, 1),
        (1, 100, 1),
        (7, 7, 7),
        (2**20, 2**10, 2**10),
        (123456, 7890, 6),
    ])
    def test_normal(self, a: int, b: int, expected: int) -> None:
        assert gcd(a, b) == expected

    # Edge cases
    def test_gcd_properties(self) -> None:
        # gcd(a, b) == gcd(b, a)
        assert gcd(48, 18) == gcd(18, 48)
        # gcd(a, 0) == |a|
        assert gcd(42, 0) == 42
        assert gcd(-42, 0) == 42
        # gcd(0, 0) == 0
        assert gcd(0, 0) == 0
        # gcd(a, b) divides both a and b
        import random
        for _ in range(100):
            a = random.randint(-1000, 1000)
            b = random.randint(-1000, 1000)
            g = gcd(a, b)
            if g != 0:
                assert a % g == 0
                assert b % g == 0

    # Error cases
    @pytest.mark.parametrize("a,b", [
        (1.5, 2),
        (2, 1.5),
        ("48", 18),
        (48, "18"),
        (None, 5),
        (5, None),
        ([48], 18),
        (True, 5),
        (5, False),
    ])
    def test_non_int_raises_type_error(self, a, b) -> None:
        with pytest.raises(TypeError, match="integer"):
            gcd(a, b)


# =============================================================================
# lcm tests
# =============================================================================

class TestLcm:
    """Tests for lcm function."""

    # Normal cases
    @pytest.mark.parametrize("a,b,expected", [
        (4, 6, 12),
        (6, 4, 12),
        (5, 7, 35),
        (100, 25, 100),
        (0, 5, 0),
        (5, 0, 0),
        (0, 0, 0),
        (-4, 6, 12),
        (4, -6, 12),
        (-4, -6, 12),
        (1, 1, 1),
        (1, 100, 100),
        (7, 7, 7),
        (2**10, 2**5, 2**10),
    ])
    def test_normal(self, a: int, b: int, expected: int) -> None:
        assert lcm(a, b) == expected

    # Edge cases
    def test_lcm_gcd_relationship(self) -> None:
        # lcm(a, b) * gcd(a, b) == |a * b| for non-zero a, b
        import random
        for _ in range(100):
            a = random.randint(1, 1000)
            b = random.randint(1, 1000)
            assert lcm(a, b) * gcd(a, b) == a * b

    def test_lcm_properties(self) -> None:
        # lcm(a, b) == lcm(b, a)
        assert lcm(12, 18) == lcm(18, 12)
        # lcm(a, 0) == 0
        assert lcm(42, 0) == 0
        assert lcm(0, 42) == 0

    # Error cases
    @pytest.mark.parametrize("a,b", [
        (1.5, 2),
        (2, 1.5),
        ("4", 6),
        (4, "6"),
        (None, 5),
        (5, None),
        (True, 5),
        (5, False),
    ])
    def test_non_int_raises_type_error(self, a, b) -> None:
        with pytest.raises(TypeError, match="integer"):
            lcm(a, b)


# =============================================================================
# mod_pow tests
# =============================================================================

class TestModPow:
    """Tests for mod_pow function."""

    # Normal cases
    @pytest.mark.parametrize("base,exp,mod,expected", [
        (2, 10, 1000, 24),
        (3, 0, 7, 1),
        (5, 3, 13, 8),
        (2, 5, 31, 1),
        (10, 3, 7, 6),
        (0, 5, 7, 0),
        (0, 0, 7, 1),  # 0^0 convention in Python
        (5, 1, 100, 5),
        (-2, 3, 7, 6),  # (-8) % 7 = 6
        (-2, 4, 7, 2),  # 16 % 7 = 2
        (12345, 6789, 10007, pow(12345, 6789, 10007)),
    ])
    def test_normal(self, base: int, exp: int, mod: int, expected: int) -> None:
        assert mod_pow(base, exp, mod) == expected

    # Edge cases
    def test_matches_builtin_pow(self) -> None:
        import random
        for _ in range(100):
            base = random.randint(-1000, 1000)
            exp = random.randint(0, 100)
            mod = random.randint(1, 1000)
            assert mod_pow(base, exp, mod) == pow(base, exp, mod)

    def test_large_exponent(self) -> None:
        # 2^1000 mod 10007
        result = mod_pow(2, 1000, 10007)
        assert result == pow(2, 1000, 10007)

    def test_mod_one(self) -> None:
        # Anything mod 1 is 0, except 0^0 % 1 == 1 % 1 == 0
        assert mod_pow(5, 100, 1) == 0
        assert mod_pow(0, 0, 1) == 0

    # Error cases
    @pytest.mark.parametrize("base,exp,mod", [
        (2, -1, 7),  # negative exp
        (2, 5, 0),  # mod <= 0
        (2, 5, -3),
        (1.5, 5, 7),  # non-int base
        (2, 1.5, 7),  # non-int exp
        (2, 5, 1.5),  # non-int mod
        ("2", 5, 7),
        (2, "5", 7),
        (2, 5, "7"),
        (None, 5, 7),
        (2, None, 7),
        (True, 5, 7),
        (2, True, 7),
    ])
    def test_invalid_inputs_raise(self, base, exp, mod) -> None:
        with pytest.raises((TypeError, ValueError)):
            mod_pow(base, exp, mod)


# =============================================================================
# mod_inv tests
# =============================================================================

class TestModInv:
    """Tests for mod_inv function."""

    # Normal cases
    @pytest.mark.parametrize("a,mod,expected", [
        (3, 11, 4),
        (10, 17, 12),
        (7, 26, 15),
        (1, 100, 1),
        (2, 5, 3),
        (5, 2, 1),
        (17, 3120, 2753),  # RSA example
    ])
    def test_normal(self, a: int, mod: int, expected: int) -> None:
        inv = mod_inv(a, mod)
        assert inv == expected
        assert (a * inv) % mod == 1

    # Edge cases
    def test_inverse_is_unique_mod_mod(self) -> None:
        import random
        for _ in range(100):
            mod = random.randint(2, 1000)
            # find a coprime
            a = random.randint(1, mod - 1)
            try:
                inv = mod_inv(a, mod)
                # verify
                assert (a * inv) % mod == 1
                # verify it's in range [0, mod-1]
                assert 0 <= inv < mod
            except ValueError:
                # not coprime, skip
                pass

    def test_negative_a(self) -> None:
        # -3 mod 11 = 8, inverse of 8 mod 11 is 7
        assert mod_inv(-3, 11) == 7
        assert (-3 * 7) % 11 == 1

    # Error cases
    def test_non_coprime_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="does not exist"):
            mod_inv(4, 8)  # gcd(4, 8) = 4 != 1

    @pytest.mark.parametrize("a,mod", [
        (3, 0),
        (3, -5),
        (1.5, 7),
        (3, 1.5),
        ("3", 7),
        (3, "7"),
        (None, 7),
        (True, 7),
    ])
    def test_invalid_inputs_raise(self, a, mod) -> None:
        with pytest.raises((TypeError, ValueError)):
            mod_inv(a, mod)


# =============================================================================
# euler_totient tests
# =============================================================================

class TestEulerTotient:
    """Tests for euler_totient function."""

    # Normal cases
    @pytest.mark.parametrize("n,expected", [
        (1, 1),
        (2, 1),
        (3, 2),
        (4, 2),
        (5, 4),
        (6, 2),
        (7, 6),
        (8, 4),
        (9, 6),
        (10, 4),
        (11, 10),
        (12, 4),
        (13, 12),
        (30, 8),
        (36, 12),
        (100, 40),
        (97, 96),  # prime: φ(p) = p-1
    ])
    def test_normal(self, n: int, expected: int) -> None:
        assert euler_totient(n) == expected

    # Edge cases
    def test_prime_totient(self) -> None:
        # φ(p) = p - 1 for prime p
        for p in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 97, 9973]:
            assert euler_totient(p) == p - 1

    def test_prime_power_totient(self) -> None:
        # φ(p^k) = p^k - p^(k-1) = p^(k-1)(p-1)
        assert euler_totient(4) == 2    # 2^2: 4 - 2 = 2
        assert euler_totient(8) == 4    # 2^3: 8 - 4 = 4
        assert euler_totient(9) == 6    # 3^2: 9 - 3 = 6
        assert euler_totient(27) == 18  # 3^3: 27 - 9 = 18

    def test_multiplicative_property(self) -> None:
        # φ is multiplicative for coprime: φ(ab) = φ(a)φ(b) if gcd(a,b)=1
        import random
        for _ in range(100):
            a = random.randint(1, 100)
            b = random.randint(1, 100)
            if gcd(a, b) == 1:
                assert euler_totient(a * b) == euler_totient(a) * euler_totient(b)

    # Error cases
    @pytest.mark.parametrize("invalid_input", [
        0,
        -1,
        -100,
    ])
    def test_non_positive_raises_value_error(self, invalid_input: int) -> None:
        with pytest.raises(ValueError, match="positive integer"):
            euler_totient(invalid_input)

    @pytest.mark.parametrize("invalid_input", [
        1.5,
        "10",
        None,
        [10],
        True,
        False,
    ])
    def test_non_int_raises_type_error(self, invalid_input) -> None:
        with pytest.raises(TypeError, match="integer"):
            euler_totient(invalid_input)


# =============================================================================
# sum_of_divisors tests
# =============================================================================

class TestSumOfDivisors:
    """Tests for sum_of_divisors function."""

    # Normal cases
    @pytest.mark.parametrize("n,expected", [
        (1, 1),
        (2, 3),     # 1 + 2
        (3, 4),     # 1 + 3
        (4, 7),     # 1 + 2 + 4
        (5, 6),     # 1 + 5
        (6, 12),    # 1 + 2 + 3 + 6
        (7, 8),     # 1 + 7
        (8, 15),    # 1 + 2 + 4 + 8
        (9, 13),    # 1 + 3 + 9
        (10, 18),   # 1 + 2 + 5 + 10
        (12, 28),   # 1 + 2 + 3 + 4 + 6 + 12
        (28, 56),   # 1 + 2 + 4 + 7 + 14 + 28
        (100, 217),
    ])
    def test_normal(self, n: int, expected: int) -> None:
        assert sum_of_divisors(n) == expected

    # Edge cases
    def test_prime_sum(self) -> None:
        # σ(p) = p + 1 for prime p
        for p in [2, 3, 5, 7, 11, 13, 97]:
            assert sum_of_divisors(p) == p + 1

    def test_prime_power(self) -> None:
        # σ(p^k) = (p^(k+1) - 1) / (p - 1)
        assert sum_of_divisors(4) == 7   # 1 + 2 + 4
        assert sum_of_divisors(8) == 15  # 1 + 2 + 4 + 8
        assert sum_of_divisors(9) == 13  # 1 + 3 + 9
        assert sum_of_divisors(16) == 31 # 1 + 2 + 4 + 8 + 16

    def test_multiplicative_property(self) -> None:
        # σ is multiplicative for coprime
        import random
        for _ in range(100):
            a = random.randint(1, 100)
            b = random.randint(1, 100)
            if gcd(a, b) == 1:
                assert sum_of_divisors(a * b) == sum_of_divisors(a) * sum_of_divisors(b)

    # Error cases
    @pytest.mark.parametrize("invalid_input", [
        0,
        -1,
        -100,
    ])
    def test_non_positive_raises_value_error(self, invalid_input: int) -> None:
        with pytest.raises(ValueError, match="positive integer"):
            sum_of_divisors(invalid_input)

    @pytest.mark.parametrize("invalid_input", [
        1.5,
        "6",
        None,
        [6],
        True,
        False,
    ])
    def test_non_int_raises_type_error(self, invalid_input) -> None:
        with pytest.raises(TypeError, match="integer"):
            sum_of_divisors(invalid_input)


# =============================================================================
# aliquot_sum tests
# =============================================================================

class TestAliquotSum:
    """Tests for aliquot_sum function."""

    # Normal cases
    @pytest.mark.parametrize("n,expected", [
        (1, 0),
        (2, 1),
        (3, 1),
        (4, 3),
        (5, 1),
        (6, 6),    # perfect
        (7, 1),
        (8, 7),
        (9, 4),
        (10, 8),
        (12, 16),  # abundant
        (28, 28),  # perfect
        (220, 284),  # amicable pair member
        (284, 220),
    ])
    def test_normal(self, n: int, expected: int) -> None:
        assert aliquot_sum(n) == expected

    # Edge cases
    def test_aliquot_sum_relationship(self) -> None:
        for n in range(1, 100):
            assert aliquot_sum(n) == sum_of_divisors(n) - n

    # Error cases
    @pytest.mark.parametrize("invalid_input", [
        0,
        -1,
        -100,
    ])
    def test_non_positive_raises_value_error(self, invalid_input: int) -> None:
        with pytest.raises(ValueError, match="positive integer"):
            aliquot_sum(invalid_input)

    @pytest.mark.parametrize("invalid_input", [
        1.5,
        "6",
        None,
        True,
        False,
    ])
    def test_non_int_raises_type_error(self, invalid_input) -> None:
        with pytest.raises(TypeError, match="integer"):
            aliquot_sum(invalid_input)


# =============================================================================
# is_perfect tests
# =============================================================================

class TestIsPerfect:
    """Tests for is_perfect function."""

    # Normal cases
    @pytest.mark.parametrize("n,expected", [
        (1, False),
        (2, False),
        (3, False),
        (4, False),
        (5, False),
        (6, True),    # 1 + 2 + 3 = 6
        (28, True),   # 1 + 2 + 4 + 7 + 14 = 28
        (496, True),
        (8128, True),
        (12, False),  # abundant
        (20, False),
        (100, False),
    ])
    def test_normal(self, n: int, expected: bool) -> None:
        assert is_perfect(n) == expected

    # Edge cases
    def test_known_perfect_numbers(self) -> None:
        # First 4 perfect numbers
        perfect = [6, 28, 496, 8128]
        for n in perfect:
            assert is_perfect(n) is True

    # Error cases
    @pytest.mark.parametrize("invalid_input", [
        0,
        -1,
        -100,
    ])
    def test_non_positive_raises_value_error(self, invalid_input: int) -> None:
        with pytest.raises(ValueError, match="positive integer"):
            is_perfect(invalid_input)

    @pytest.mark.parametrize("invalid_input", [
        1.5,
        "6",
        None,
        True,
        False,
    ])
    def test_non_int_raises_type_error(self, invalid_input) -> None:
        with pytest.raises(TypeError, match="integer"):
            is_perfect(invalid_input)


# =============================================================================
# are_amicable tests
# =============================================================================

class TestAreAmicable:
    """Tests for are_amicable function."""

    # Normal cases
    @pytest.mark.parametrize("a,b,expected", [
        (220, 284, True),
        (284, 220, True),
        (1184, 1210, True),
        (2620, 2924, True),
        (5020, 5564, True),
        (6232, 6368, True),
        (220, 220, False),  # must be distinct
        (6, 28, False),
        (220, 285, False),
        (1, 1, False),
    ])
    def test_normal(self, a: int, b: int, expected: bool) -> None:
        assert are_amicable(a, b) == expected

    # Edge cases
    def test_known_amicable_pairs(self) -> None:
        pairs = [
            (220, 284),
            (1184, 1210),
            (2620, 2924),
            (5020, 5564),
            (6232, 6368),
        ]
        for a, b in pairs:
            assert are_amicable(a, b) is True
            assert are_amicable(b, a) is True

    def test_symmetry(self) -> None:
        assert are_amicable(220, 284) == are_amicable(284, 220)

    # Error cases
    @pytest.mark.parametrize("a,b", [
        (0, 284),
        (220, 0),
        (-1, 284),
        (220, -1),
    ])
    def test_non_positive_raises_value_error(self, a: int, b: int) -> None:
        with pytest.raises(ValueError, match="positive integer"):
            are_amicable(a, b)

    @pytest.mark.parametrize("a,b", [
        (1.5, 284),
        (220, 1.5),
        ("220", 284),
        (220, "284"),
        (None, 284),
        (True, 284),
    ])
    def test_non_int_raises_type_error(self, a, b) -> None:
        with pytest.raises(TypeError, match="integer"):
            are_amicable(a, b)


# =============================================================================
# integer_sqrt tests
# =============================================================================

class TestIntegerSqrt:
    """Tests for integer_sqrt function."""

    # Normal cases
    @pytest.mark.parametrize("n,expected", [
        (0, 0),
        (1, 1),
        (2, 1),
        (3, 1),
        (4, 2),
        (5, 2),
        (8, 2),
        (9, 3),
        (10, 3),
        (15, 3),
        (16, 4),
        (17, 4),
        (100, 10),
        (101, 10),
        (10000, 100),
        (1000000, 1000),
    ])
    def test_normal(self, n: int, expected: int) -> None:
        assert integer_sqrt(n) == expected

    # Edge cases
    def test_matches_math_isqrt(self) -> None:
        from math import isqrt
        import random
        for _ in range(1000):
            n = random.randint(0, 10**12)
            assert integer_sqrt(n) == isqrt(n)

    def test_property_sqrt_squared_le_n(self) -> None:
        import random
        for _ in range(100):
            n = random.randint(0, 10**6)
            r = integer_sqrt(n)
            assert r * r <= n
            assert (r + 1) * (r + 1) > n

    # Error cases
    @pytest.mark.parametrize("invalid_input", [
        -1,
        -100,
    ])
    def test_negative_raises_value_error(self, invalid_input: int) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            integer_sqrt(invalid_input)

    @pytest.mark.parametrize("invalid_input", [
        1.5,
        "16",
        None,
        [16],
        True,
        False,
    ])
    def test_non_int_raises_type_error(self, invalid_input) -> None:
        with pytest.raises(TypeError, match="integer"):
            integer_sqrt(invalid_input)


# =============================================================================
# sieve_of_eratosthenes tests
# =============================================================================

class TestSieveOfEratosthenes:
    """Tests for sieve_of_eratosthenes function."""

    # Normal cases
    @pytest.mark.parametrize("limit,expected", [
        (0, []),
        (1, []),
        (2, [2]),
        (3, [2, 3]),
        (4, [2, 3]),
        (5, [2, 3, 5]),
        (10, [2, 3, 5, 7]),
        (20, [2, 3, 5, 7, 11, 13, 17, 19]),
        (30, [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]),
        (100, [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]),
    ])
    def test_normal(self, limit: int, expected: list[int]) -> None:
        assert sieve_of_eratosthenes(limit) == expected

    # Edge cases
    def test_all_primes_are_prime(self) -> None:
        primes = sieve_of_eratosthenes(1000)
        for p in primes:
            assert is_prime(p) is True

    def test_no_composites(self) -> None:
        primes = sieve_of_eratosthenes(1000)
        prime_set = set(primes)
        for n in range(2, 1001):
            if is_prime(n):
                assert n in prime_set, f"Missing prime {n}"

    def test_count_matches_pi_function(self) -> None:
        # π(100) = 25, π(1000) = 168
        assert len(sieve_of_eratosthenes(100)) == 25
        assert len(sieve_of_eratosthenes(1000)) == 168
        assert len(sieve_of_eratosthenes(10000)) == 1229

    # Error cases
    def test_negative_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            sieve_of_eratosthenes(-1)

    @pytest.mark.parametrize("invalid_input", [
        1.5,
        "10",
        None,
        [10],
        True,
        False,
    ])
    def test_non_int_raises_type_error(self, invalid_input) -> None:
        with pytest.raises(TypeError, match="integer"):
            sieve_of_eratosthenes(invalid_input)


# =============================================================================
# Determinism / reproducibility tests
# =============================================================================

class TestDeterminism:
    """Verify all functions are fully deterministic."""

    def test_prime_factors_deterministic(self) -> None:
        for n in range(2, 1000):
            f1 = prime_factors(n)
            f2 = prime_factors(n)
            assert f1 == f2

    def test_is_prime_deterministic(self) -> None:
        for n in range(0, 1000):
            assert is_prime(n) == is_prime(n)

    def test_gcd_deterministic(self) -> None:
        for a in range(-100, 101):
            for b in range(-100, 101):
                assert gcd(a, b) == gcd(a, b)

    def test_lcm_deterministic(self) -> None:
        for a in range(-50, 51):
            for b in range(-50, 51):
                assert lcm(a, b) == lcm(a, b)

    def test_mod_pow_deterministic(self) -> None:
        for base in range(-10, 11):
            for exp in range(0, 20):
                for mod in range(1, 20):
                    assert mod_pow(base, exp, mod) == mod_pow(base, exp, mod)

    def test_mod_inv_deterministic(self) -> None:
        for a in range(-20, 21):
            for mod in range(2, 50):
                try:
                    assert mod_inv(a, mod) == mod_inv(a, mod)
                except ValueError:
                    pass  # no inverse

    def test_euler_totient_deterministic(self) -> None:
        for n in range(1, 200):
            assert euler_totient(n) == euler_totient(n)

    def test_sum_of_divisors_deterministic(self) -> None:
        for n in range(1, 200):
            assert sum_of_divisors(n) == sum_of_divisors(n)

    def test_aliquot_sum_deterministic(self) -> None:
        for n in range(1, 200):
            assert aliquot_sum(n) == aliquot_sum(n)

    def test_is_perfect_deterministic(self) -> None:
        for n in range(1, 500):
            assert is_perfect(n) == is_perfect(n)

    def test_are_amicable_deterministic(self) -> None:
        for a in [220, 284, 1184, 1210]:
            for b in [220, 284, 1184, 1210]:
                assert are_amicable(a, b) == are_amicable(a, b)

    def test_integer_sqrt_deterministic(self) -> None:
        for n in range(0, 10000):
            assert integer_sqrt(n) == integer_sqrt(n)

    def test_sieve_deterministic(self) -> None:
        for limit in [10, 100, 1000]:
            assert sieve_of_eratosthenes(limit) == sieve_of_eratosthenes(limit)