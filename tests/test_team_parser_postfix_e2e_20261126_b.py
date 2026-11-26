"""
Tests for the deterministic postfix parser/evaluator in
team_parser_postfix_e2e_20261126.child_b.

Covers normal evaluation, edge cases, and error conditions.
"""

import pytest
from team_parser_postfix_e2e_20261126.child_b import (
    is_operator,
    is_number,
    arity,
    apply_operator,
    tokenize,
    evaluate_postfix,
    parse_and_evaluate,
    to_infix,
    infix_from_postfix,
)


# ==================== Helper & Fixture Tests ====================

class TestIsOperator:
    """Tests for is_operator()."""

    def test_binary_operators(self):
        for op in ("+", "-", "*", "/", "//", "%", "**"):
            assert is_operator(op) is True

    def test_unary_operators(self):
        for op in ("+", "-"):
            assert is_operator(op) is True

    def test_non_operators(self):
        for s in ("3", "foo", "=", "++", "--", "//*", ""):
            assert is_operator(s) is False


class TestIsNumber:
    """Tests for is_number()."""

    def test_integers(self):
        assert is_number(0) is True
        assert is_number(42) is True
        assert is_number(-7) is True

    def test_floats(self):
        assert is_number(0.0) is True
        assert is_number(3.14) is True
        assert is_number(-2.5) is True

    def test_booleans_are_not_numbers(self):
        assert is_number(True) is False
        assert is_number(False) is False

    def test_non_numbers(self):
        assert is_number("3") is False
        assert is_number(None) is False
        assert is_number([1, 2]) is False


class TestArity:
    """Tests for arity()."""

    def test_binary_operators_have_arity_2_with_sufficient_stack(self):
        # With default stack_size=2, ambiguous ops are binary
        for op in ("+", "-", "*", "/", "//", "%", "**"):
            assert arity(op) == 2

    def test_binary_operators_have_arity_2_with_explicit_stack(self):
        # Explicit stack_size >= 2 makes ambiguous ops binary
        for op in ("+", "-"):
            assert arity(op, stack_size=2) == 2
            assert arity(op, stack_size=5) == 2

    def test_ambiguous_operators_unary_with_insufficient_stack(self):
        # stack_size < 2 makes + and - unary
        for op in ("+", "-"):
            assert arity(op, stack_size=0) == 1
            assert arity(op, stack_size=1) == 1

    def test_strict_binary_operators_always_arity_2(self):
        # *, /, //, %, ** are always binary regardless of stack
        for op in ("*", "/", "//", "%", "**"):
            assert arity(op, stack_size=0) == 2
            assert arity(op, stack_size=1) == 2
            assert arity(op, stack_size=2) == 2

    def test_unknown_operator_raises(self):
        with pytest.raises(ValueError, match="Unknown operator"):
            arity("^")
        with pytest.raises(ValueError, match="Unknown operator"):
            arity("??")


class TestApplyOperator:
    """Tests for apply_operator()."""

    # Binary
    def test_add(self):
        assert apply_operator("+", 2, 3) == 5

    def test_subtract(self):
        assert apply_operator("-", 10, 4) == 6

    def test_multiply(self):
        assert apply_operator("*", 3, 7) == 21

    def test_divide(self):
        assert apply_operator("/", 10, 4) == 2.5

    def test_floor_divide(self):
        assert apply_operator("//", 10, 4) == 2
        assert apply_operator("//", -3, 2) == -2  # floor division semantics

    def test_modulo(self):
        assert apply_operator("%", 10, 4) == 2
        assert apply_operator("%", -3, 2) == 1   # Python modulo semantics

    def test_power(self):
        assert apply_operator("**", 2, 10) == 1024
        assert apply_operator("**", 4, 0.5) == 2.0

    # Unary (ambiguous operators with 1 operand)
    def test_unary_plus(self):
        assert apply_operator("+", 5) == 5
        assert apply_operator("+", -3) == -3

    def test_unary_minus(self):
        assert apply_operator("-", 5) == -5
        assert apply_operator("-", -3) == 3

    # Errors
    def test_unknown_operator_raises(self):
        with pytest.raises(ValueError, match="Unknown operator"):
            apply_operator("^", 1, 2)

    def test_wrong_arity_binary_too_many(self):
        # 3 operands for binary operator should fail
        with pytest.raises(ValueError, match="requires 1 or 2 operands"):
            apply_operator("+", 1, 2, 3)
        with pytest.raises(ValueError, match="requires 1 or 2 operands"):
            apply_operator("*", 1, 2, 3)

    def test_wrong_arity_zero_operands(self):
        # 0 operands should fail for any operator
        with pytest.raises(ValueError, match="requires 1 or 2 operands"):
            apply_operator("-")
        with pytest.raises(ValueError, match="requires 1 or 2 operands"):
            apply_operator("+")
        with pytest.raises(ValueError, match="requires 1 or 2 operands"):
            apply_operator("*")

    def test_division_by_zero_raises(self):
        with pytest.raises(ZeroDivisionError):
            apply_operator("/", 1, 0)
        with pytest.raises(ZeroDivisionError):
            apply_operator("//", 1, 0)
        with pytest.raises(ZeroDivisionError):
            apply_operator("%", 1, 0)


class TestTokenize:
    """Tests for tokenize()."""

    def test_empty_string(self):
        assert tokenize("") == []
        assert tokenize("   ") == []

    def test_single_number_int(self):
        assert tokenize("42") == [42]

    def test_single_number_float(self):
        assert tokenize("3.14") == [3.14]

    def test_negative_number(self):
        assert tokenize("-7") == [-7]

    def test_mixed_numbers_and_operators(self):
        assert tokenize("3 4 +") == [3, 4, "+"]
        assert tokenize("10 2 / 3 *") == [10, 2, "/", 3, "*"]

    def test_float_and_int_mix(self):
        assert tokenize("2.5 3 +") == [2.5, 3, "+"]

    def test_unary_operators_tokenized(self):
        # Unary minus/plus appear as operators; context determines arity at eval time
        assert tokenize("5 -") == [5, "-"]
        assert tokenize("5 +") == [5, "+"]

    def test_invalid_token_raises(self):
        with pytest.raises(ValueError, match="Invalid token"):
            tokenize("3 4 ^")
        with pytest.raises(ValueError, match="Invalid token"):
            tokenize("foo bar +")


# ==================== Normal Evaluation Tests ====================

class TestEvaluatePostfixNormal:
    """Normal (happy-path) evaluation tests."""

    def test_single_operand(self):
        assert evaluate_postfix([42]) == 42
        assert evaluate_postfix([3.14]) == 3.14

    def test_binary_addition(self):
        assert evaluate_postfix([2, 3, "+"]) == 5

    def test_binary_subtraction(self):
        assert evaluate_postfix([10, 4, "-"]) == 6

    def test_binary_multiplication(self):
        assert evaluate_postfix([3, 7, "*"]) == 21

    def test_binary_division(self):
        assert evaluate_postfix([10, 4, "/"]) == 2.5

    def test_floor_division(self):
        assert evaluate_postfix([10, 4, "//"]) == 2

    def test_modulo(self):
        assert evaluate_postfix([10, 4, "%"]) == 2

    def test_power(self):
        assert evaluate_postfix([2, 10, "**"]) == 1024

    def test_chained_operations(self):
        # (3 + 4) * 2 = 14
        assert evaluate_postfix([3, 4, "+", 2, "*"]) == 14
        # 10 - (2 * 3) = 4
        assert evaluate_postfix([10, 2, 3, "*", "-"]) == 4
        # (100 / 5) + 3 = 23
        assert evaluate_postfix([100, 5, "/", 3, "+"]) == 23.0

    def test_unary_negation(self):
        # Unary minus: 5 - -> -5
        assert evaluate_postfix([5, "-"]) == -5

    def test_unary_plus(self):
        # Unary plus: 5 + -> 5
        assert evaluate_postfix([5, "+"]) == 5

    def test_unary_in_chain(self):
        # 3 4 + - -> -(3 + 4) = -7
        assert evaluate_postfix([3, 4, "+", "-"]) == -7
        # 10 2 / - -> -(10 / 2) = -5
        assert evaluate_postfix([10, 2, "/", "-"]) == -5.0

    def test_mixed_int_float_operands(self):
        # int + float -> float
        assert evaluate_postfix([2, 3.5, "+"]) == 5.5
        assert evaluate_postfix([10, 2.5, "/"]) == 4.0


# ==================== Edge Case Tests ====================

class TestEvaluatePostfixEdgeCases:
    """Edge case tests."""

    def test_large_numbers(self):
        assert evaluate_postfix([10**10, 10**10, "+"]) == 2 * 10**10

    def test_very_small_floats(self):
        result = evaluate_postfix([1e-10, 1e-10, "+"])
        assert abs(result - 2e-10) < 1e-20

    def test_zero_operands(self):
        assert evaluate_postfix([0, 5, "+"]) == 5
        assert evaluate_postfix([5, 0, "+"]) == 5
        assert evaluate_postfix([0, 5, "*"]) == 0
        assert evaluate_postfix([5, 0, "*"]) == 0

    def test_negative_numbers(self):
        assert evaluate_postfix([-3, -4, "+"]) == -7
        assert evaluate_postfix([-3, 4, "*"]) == -12
        assert evaluate_postfix([-3, -4, "*"]) == 12

    def test_deeply_nested_expression(self):
        # ((((1 + 2) + 3) + 4) + 5) = 15
        tokens = [1, 2, "+", 3, "+", 4, "+", 5, "+"]
        assert evaluate_postfix(tokens) == 15

    def test_many_operands_before_operators(self):
        # 1 2 3 4 + * + 5 + = 1 + (2 * (3 + 4)) + 5 = 1 + 14 + 5 = 20
        assert evaluate_postfix([1, 2, 3, 4, "+", "*", "+", 5, "+"]) == 20

    def test_all_binary_operators_in_one_expression(self):
        # 10 2 / 3 * 4 + 5 - 6 % 2 ** = (((((10/2)*3)+4)-5)%6)**2
        # = (((5*3)+4)-5)%6)**2 = ((15+4)-5)%6)**2 = (19-5)%6)**2 = 14%6)**2 = 2**2 = 4
        tokens = [10, 2, "/", 3, "*", 4, "+", 5, "-", 6, "%", 2, "**"]
        assert evaluate_postfix(tokens) == 4


# ==================== Error Condition Tests ====================

class TestEvaluatePostfixErrors:
    """Error condition tests."""

    def test_empty_expression_raises(self):
        with pytest.raises(ValueError, match="Empty expression"):
            evaluate_postfix([])

    def test_insufficient_operands_for_strict_binary(self):
        # Strict binary operators (*, /, //, %, **) need 2 operands
        with pytest.raises(ValueError, match="Insufficient operands"):
            evaluate_postfix([1, "*"])
        with pytest.raises(ValueError, match="Insufficient operands"):
            evaluate_postfix(["*"])

    def test_insufficient_operands_for_ambiguous_with_zero_stack(self):
        # Ambiguous operators with 0 operands on stack
        with pytest.raises(ValueError, match="Insufficient operands"):
            evaluate_postfix(["+"])
        with pytest.raises(ValueError, match="Insufficient operands"):
            evaluate_postfix(["-"])

    def test_too_many_operands_remaining(self):
        # 1 2 3 + -> two values left on stack
        with pytest.raises(ValueError, match="Malformed expression"):
            evaluate_postfix([1, 2, 3, "+"])

    def test_division_by_zero(self):
        with pytest.raises(ZeroDivisionError):
            evaluate_postfix([1, 0, "/"])
        with pytest.raises(ZeroDivisionError):
            evaluate_postfix([1, 0, "//"])
        with pytest.raises(ZeroDivisionError):
            evaluate_postfix([1, 0, "%"])

    def test_invalid_token_type_in_expression(self):
        with pytest.raises(ValueError, match="Invalid token"):
            evaluate_postfix([1, 2, "foo"])
        with pytest.raises(ValueError, match="Invalid token"):
            evaluate_postfix([1, 2, None])  # type: ignore[list-item]

    def test_unknown_operator_in_expression(self):
        with pytest.raises(ValueError, match="Invalid token in expression"):
            evaluate_postfix([1, 2, "^"])


# ==================== Parse and Evaluate Integration Tests ====================

class TestParseAndEvaluate:
    """Tests for the parse_and_evaluate convenience function."""

    def test_simple_addition(self):
        assert parse_and_evaluate("2 3 +") == 5

    def test_complex_expression(self):
        assert parse_and_evaluate("3 4 + 2 *") == 14

    def test_with_floats(self):
        assert parse_and_evaluate("2.5 3.5 +") == 6.0

    def test_unary_operators(self):
        assert parse_and_evaluate("5 -") == -5
        assert parse_and_evaluate("3 4 + -") == -7

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="Empty expression"):
            parse_and_evaluate("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="Empty expression"):
            parse_and_evaluate("   ")

    def test_invalid_token_in_string(self):
        with pytest.raises(ValueError, match="Invalid token"):
            parse_and_evaluate("2 3 ^")

    def test_malformed_expression_in_string(self):
        with pytest.raises(ValueError, match="Malformed expression"):
            parse_and_evaluate("1 2 3 +")


# ==================== Infix Conversion Tests ====================

class TestToInfix:
    """Tests for to_infix() and infix_from_postfix()."""

    def test_single_operand(self):
        assert to_infix([42]) == "42"

    def test_binary_operation(self):
        assert to_infix([3, 4, "+"]) == "(3 + 4)"

    def test_chained_operations(self):
        # (3 + 4) * 2
        assert to_infix([3, 4, "+", 2, "*"]) == "((3 + 4) * 2)"

    def test_nested_operations(self):
        # 10 - (2 * 3)
        assert to_infix([10, 2, 3, "*", "-"]) == "(10 - (2 * 3))"

    def test_unary_negation(self):
        assert to_infix([5, "-"]) == "(-5)"

    def test_unary_in_chain(self):
        # -(3 + 4)
        assert to_infix([3, 4, "+", "-"]) == "(-(3 + 4))"

    def test_infix_from_postfix_string(self):
        assert infix_from_postfix("3 4 + 2 *") == "((3 + 4) * 2)"
        assert infix_from_postfix("5 -") == "(-5)"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="Empty expression"):
            to_infix([])

    def test_malformed_raises(self):
        with pytest.raises(ValueError, match="Malformed expression"):
            to_infix([1, 2, 3, "+"])

    def test_insufficient_operands_for_strict_binary_raises(self):
        with pytest.raises(ValueError, match="Insufficient operands"):
            to_infix([1, "*"])

    def test_insufficient_operands_for_ambiguous_with_zero_stack_raises(self):
        with pytest.raises(ValueError, match="Insufficient operands"):
            to_infix(["+"])
        with pytest.raises(ValueError, match="Insufficient operands"):
            to_infix(["-"])


# ==================== Determinism Tests ====================

class TestDeterminism:
    """Verify that the same input always produces the same output."""

    def test_evaluate_is_deterministic(self):
        tokens = [3, 4, "+", 2, "*", 5, "-", 6, "/"]
        results = [evaluate_postfix(tokens) for _ in range(100)]
        assert all(r == results[0] for r in results)
        assert results[0] == ((3 + 4) * 2 - 5) / 6

    def test_parse_and_evaluate_is_deterministic(self):
        expr = "3 4 + 2 * 5 - 6 /"
        results = [parse_and_evaluate(expr) for _ in range(100)]
        assert all(r == results[0] for r in results)

    def test_tokenize_is_deterministic(self):
        expr = "3 4.5 + 2 *"
        results = [tokenize(expr) for _ in range(100)]
        assert all(r == results[0] for r in results)

    def test_to_infix_is_deterministic(self):
        tokens = [3, 4, "+", 2, "*"]
        results = [to_infix(tokens) for _ in range(100)]
        assert all(r == results[0] for r in results)


# ==================== Type Hint Compliance (Static Check) ====================

class TestTypeHints:
    """Lightweight runtime checks that functions accept annotated types."""

    def test_functions_accept_annotated_types(self):
        # These should not raise type-related errors at runtime
        assert is_operator("+") is True
        assert is_number(1) is True
        assert is_number(1.0) is True
        assert arity("+") == 2  # default stack_size=2 -> binary
        assert apply_operator("+", 1, 2) == 3
        assert tokenize("1 2 +") == [1, 2, "+"]
        assert evaluate_postfix([1, 2, "+"]) == 3
        assert parse_and_evaluate("1 2 +") == 3
        assert to_infix([1, 2, "+"]) == "(1 + 2)"
        assert infix_from_postfix("1 2 +") == "(1 + 2)"