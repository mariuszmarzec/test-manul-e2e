"""Pytest tests for Team Flow E2E Child C numeric sequence utilities."""

import pytest

from team_flow_e2e.child_c import (
    fibonacci,
    fibonacci_sequence,
    is_prime,
    prime_factors,
    gcd,
    lcm,
)


class TestFibonacci:
    """Tests for fibonacci function."""

    def test_base_cases(self) -> None:
        """Test base cases."""
        assert fibonacci(0) == 0
        assert fibonacci(1) == 1

    def test_normal_input(self) -> None:
        """Test normal Fibonacci numbers."""
        assert fibonacci(2) == 1
        assert fibonacci(3) == 2
        assert fibonacci(5) == 5
        assert fibonacci(10) == 55
        assert fibonacci(15) == 610

    def test_negative_input(self) -> None:
        """Test negative input raises ValueError (edge case)."""
        with pytest.raises(ValueError, match="n must be non-negative"):
            fibonacci(-1)
        with pytest.raises(ValueError, match="n must be non-negative"):
            fibonacci(-10)


class TestFibonacciSequence:
    """Tests for fibonacci_sequence function."""

    def test_zero_length(self) -> None:
        """Test zero length sequence (edge case)."""
        assert fibonacci_sequence(0) == []

    def test_single_element(self) -> None:
        """Test single element sequence (edge case)."""
        assert fibonacci_sequence(1) == [0]

    def test_normal_sequences(self) -> None:
        """Test normal sequences."""
        assert fibonacci_sequence(2) == [0, 1]
        assert fibonacci_sequence(5) == [0, 1, 1, 2, 3]
        assert fibonacci_sequence(10) == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]

    def test_negative_input(self) -> None:
        """Test negative input raises ValueError (edge case)."""
        with pytest.raises(ValueError, match="n must be non-negative"):
            fibonacci_sequence(-1)


class TestIsPrime:
    """Tests for is_prime function."""

    def test_small_primes(self) -> None:
        """Test small prime numbers."""
        assert is_prime(2) is True
        assert is_prime(3) is True
        assert is_prime(5) is True
        assert is_prime(7) is True
        assert is_prime(11) is True

    def test_small_composites(self) -> None:
        """Test small composite numbers."""
        assert is_prime(4) is False
        assert is_prime(6) is False
        assert is_prime(8) is False
        assert is_prime(9) is False
        assert is_prime(10) is False

    def test_edge_cases(self) -> None:
        """Test edge cases: 0, 1, negative."""
        assert is_prime(0) is False
        assert is_prime(1) is False
        assert is_prime(-1) is False
        assert is_prime(-7) is False

    def test_larger_primes(self) -> None:
        """Test larger prime numbers."""
        assert is_prime(13) is True
        assert is_prime(17) is True
        assert is_prime(19) is True
        assert is_prime(23) is True
        assert is_prime(97) is True

    def test_larger_composites(self) -> None:
        """Test larger composite numbers."""
        assert is_prime(100) is False
        assert is_prime(121) is False
        assert is_prime(143) is False


class TestPrimeFactors:
    """Tests for prime_factors function."""

    def test_prime_numbers(self) -> None:
        """Test prime factorization of prime numbers."""
        assert prime_factors(2) == [2]
        assert prime_factors(7) == [7]
        assert prime_factors(13) == [13]

    def test_composite_numbers(self) -> None:
        """Test prime factorization of composite numbers."""
        assert prime_factors(12) == [2, 2, 3]
        assert prime_factors(100) == [2, 2, 5, 5]
        assert prime_factors(60) == [2, 2, 3, 5]
        assert prime_factors(84) == [2, 2, 3, 7]

    def test_edge_case_two(self) -> None:
        """Test edge case n=2."""
        assert prime_factors(2) == [2]

    def test_invalid_input(self) -> None:
        """Test invalid input raises ValueError (edge case)."""
        with pytest.raises(ValueError, match="n must be >= 2"):
            prime_factors(1)
        with pytest.raises(ValueError, match="n must be >= 2"):
            prime_factors(0)
        with pytest.raises(ValueError, match="n must be >= 2"):
            prime_factors(-5)


class TestGCD:
    """Tests for gcd function."""

    def test_normal_cases(self) -> None:
        """Test normal GCD cases."""
        assert gcd(48, 18) == 6
        assert gcd(18, 48) == 6
        assert gcd(7, 13) == 1
        assert gcd(100, 25) == 25

    def test_with_zero(self) -> None:
        """Test GCD with zero (edge case)."""
        assert gcd(0, 5) == 5
        assert gcd(5, 0) == 5
        assert gcd(0, 0) == 0

    def test_negative_numbers(self) -> None:
        """Test GCD with negative numbers."""
        assert gcd(-48, 18) == 6
        assert gcd(48, -18) == 6
        assert gcd(-48, -18) == 6

    def test_coprime(self) -> None:
        """Test coprime numbers."""
        assert gcd(7, 13) == 1
        assert gcd(17, 19) == 1


class TestLCM:
    """Tests for lcm function."""

    def test_normal_cases(self) -> None:
        """Test normal LCM cases."""
        assert lcm(4, 6) == 12
        assert lcm(6, 4) == 12
        assert lcm(7, 13) == 91
        assert lcm(100, 25) == 100

    def test_with_zero(self) -> None:
        """Test LCM with zero (edge case)."""
        assert lcm(0, 5) == 0
        assert lcm(5, 0) == 0
        assert lcm(0, 0) == 0

    def test_negative_numbers(self) -> None:
        """Test LCM with negative numbers."""
        assert lcm(-4, 6) == 12
        assert lcm(4, -6) == 12
        assert lcm(-4, -6) == 12