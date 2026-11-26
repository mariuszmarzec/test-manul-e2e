"""
Deterministic postfix expression parser and evaluator.

This module provides a pure-function implementation for parsing and evaluating
postfix (Reverse Polish Notation) expressions. All functions are stateless
and deterministic: the same input always produces the same output.

Supported operators:
    - Binary: +, -, *, /, //, %, **
    - Unary:  +, - (negation) — arity determined by available operands

Operands can be integers or floats. Division by zero raises ZeroDivisionError.
Invalid expressions raise ValueError with descriptive messages.
"""

from __future__ import annotations

from typing import Union, List, Sequence

# Type aliases for clarity
Number = Union[int, float]
Token = Union[Number, str]
Expression = Sequence[Token]
Operator = str


# --- Operator definitions ----------------------------------------------------

_BINARY_OPS = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "/": lambda a, b: a / b,
    "//": lambda a, b: a // b,
    "%": lambda a, b: a % b,
    "**": lambda a, b: a ** b,
}

# Operators that are ONLY binary (not ambiguous)
_STRICT_BINARY_OPS = {"*", "/", "//", "%", "**"}

# Operators that can be unary or binary depending on context
_AMBIGUOUS_OPS = {"+", "-"}

_ALL_OPERATORS = set(_BINARY_OPS.keys())  # = _STRICT_BINARY_OPS | _AMBIGUOUS_OPS


# --- Public API --------------------------------------------------------------

def is_operator(token: str) -> bool:
    """
    Check if a string token is a recognized operator.

    Args:
        token: String to check.

    Returns:
        True if token is a known operator, False otherwise.
    """
    return token in _ALL_OPERATORS


def is_number(token: Token) -> bool:
    """
    Check if a token is a numeric operand (int or float).

    Args:
        token: Token to check.

    Returns:
        True if token is int or float (but not bool), False otherwise.
    """
    return isinstance(token, (int, float)) and not isinstance(token, bool)


def arity(operator: str, stack_size: int = 2) -> int:
    """
    Return the arity (number of operands) of an operator.

    For strict binary operators (*, /, //, %, **), always returns 2.
    For ambiguous operators (+, -), returns 1 if stack_size < 2, else 2.

    Args:
        operator: Operator symbol.
        stack_size: Number of operands currently available on the stack.
            Used to disambiguate + and -.

    Returns:
        1 for unary, 2 for binary.

    Raises:
        ValueError: If operator is not recognized.
    """
    if operator not in _ALL_OPERATORS:
        raise ValueError(f"Unknown operator: {operator!r}")

    if operator in _STRICT_BINARY_OPS:
        return 2

    # Ambiguous operators: unary if insufficient operands for binary
    return 1 if stack_size < 2 else 2


def apply_operator(operator: str, *operands: Number) -> Number:
    """
    Apply an operator to the given operands.

    Args:
        operator: Operator symbol.
        *operands: One or two numeric operands.

    Returns:
        Result of the operation.

    Raises:
        ValueError: If operator is unknown or wrong number of operands provided.
        ZeroDivisionError: If division by zero is attempted.
    """
    if operator in _BINARY_OPS:
        if len(operands) == 2:
            return _BINARY_OPS[operator](operands[0], operands[1])
        if len(operands) == 1 and operator in _AMBIGUOUS_OPS:
            # Unary + or -
            return +operands[0] if operator == "+" else -operands[0]
        raise ValueError(
            f"Operator {operator!r} requires 1 or 2 operands, got {len(operands)}"
        )
    raise ValueError(f"Unknown operator: {operator!r}")


def tokenize(expression: str) -> List[Token]:
    """
    Split an expression string into tokens (numbers and operators).

    Numbers are parsed as int when possible, otherwise float.
    Operators are kept as strings. Whitespace is ignored.

    Args:
        expression: Postfix expression string, e.g., "3 4 + 2 *"

    Returns:
        List of tokens in order.

    Raises:
        ValueError: If a token cannot be parsed as a number or recognized operator.
    """
    if not expression or not expression.strip():
        return []

    tokens: List[Token] = []
    for raw in expression.split():
        if raw in _ALL_OPERATORS:
            tokens.append(raw)
        else:
            # Try int first, then float
            try:
                tokens.append(int(raw))
            except ValueError:
                try:
                    tokens.append(float(raw))
                except ValueError:
                    raise ValueError(f"Invalid token: {raw!r}")
    return tokens


def evaluate_postfix(tokens: Expression) -> Number:
    """
    Evaluate a postfix (RPN) expression given as a sequence of tokens.

    Args:
        tokens: Sequence of numbers and operator strings.

    Returns:
        The numeric result of the expression.

    Raises:
        ValueError: If the expression is malformed (e.g., too few operands,
            too many operands remaining, unknown token).
        ZeroDivisionError: If division by zero occurs during evaluation.
    """
    if not tokens:
        raise ValueError("Empty expression")

    stack: List[Number] = []

    for token in tokens:
        if is_number(token):
            stack.append(token)  # type: ignore[arg-type]
        elif isinstance(token, str) and is_operator(token):
            op_arity = arity(token, len(stack))
            if len(stack) < op_arity:
                raise ValueError(
                    f"Insufficient operands for operator {token!r}: "
                    f"expected {op_arity}, found {len(stack)}"
                )
            if op_arity == 2:
                b = stack.pop()
                a = stack.pop()
                result = apply_operator(token, a, b)
            else:  # op_arity == 1
                a = stack.pop()
                result = apply_operator(token, a)
            stack.append(result)
        else:
            raise ValueError(f"Invalid token in expression: {token!r}")

    if len(stack) != 1:
        raise ValueError(
            f"Malformed expression: {len(stack)} value(s) left on stack "
            f"(expected exactly 1)"
        )

    return stack[0]


def parse_and_evaluate(expression: str) -> Number:
    """
    Parse a postfix expression string and evaluate it in one step.

    This is a convenience function combining tokenize() and evaluate_postfix().

    Args:
        expression: Postfix expression string, e.g., "3 4 + 2 *"

    Returns:
        The numeric result of the expression.

    Raises:
        ValueError: If the expression is invalid or malformed.
        ZeroDivisionError: If division by zero occurs.
    """
    tokens = tokenize(expression)
    return evaluate_postfix(tokens)


def to_infix(tokens: Expression) -> str:
    """
    Convert a postfix token sequence to a fully-parenthesized infix string.

    This is useful for debugging or displaying the expression in traditional
    notation. The result is fully parenthesized to preserve evaluation order.

    Args:
        tokens: Sequence of numbers and operator strings in postfix order.

    Returns:
        Infix representation as a string, e.g., "((3 + 4) * 2)".

    Raises:
        ValueError: If the expression is malformed.
    """
    if not tokens:
        raise ValueError("Empty expression")

    stack: List[str] = []

    for token in tokens:
        if is_number(token):
            stack.append(str(token))
        elif isinstance(token, str) and is_operator(token):
            op_arity = arity(token, len(stack))
            if len(stack) < op_arity:
                raise ValueError(
                    f"Insufficient operands for operator {token!r}: "
                    f"expected {op_arity}, found {len(stack)}"
                )
            if op_arity == 2:
                b = stack.pop()
                a = stack.pop()
                stack.append(f"({a} {token} {b})")
            else:  # unary
                a = stack.pop()
                stack.append(f"({token}{a})")
        else:
            raise ValueError(f"Invalid token in expression: {token!r}")

    if len(stack) != 1:
        raise ValueError(
            f"Malformed expression: {len(stack)} value(s) left on stack"
        )

    return stack[0]


# --- Convenience: direct string-to-infix ------------------------------------

def infix_from_postfix(expression: str) -> str:
    """
    Convert a postfix expression string to a fully-parenthesized infix string.

    Args:
        expression: Postfix expression string.

    Returns:
        Infix representation.

    Raises:
        ValueError: If the expression is invalid.
    """
    tokens = tokenize(expression)
    return to_infix(tokens)