def add(a: float, b: float) -> float:
    """
    Add two numbers and return the result.
    
    Args:
        a (float): The first number to add
        b (float): The second number to add
    
    Returns:
        float: The sum of a and b
        
    Example:
        >>> add(2, 3)
        5.0
        >>> add(1.5, 2.5)
        4.0
    """
    return a + b


def divide(a: float, b: float) -> float:
    """
    Divide two numbers and return the result.

    Args:
        a (float): The dividend
        b (float): The divisor

    Returns:
        float: The result of a divided by b

    Raises:
        ZeroDivisionError: If b is zero

    Example:
        >>> divide(8, 2)
        4.0
        >>> divide(5, 2)
        2.5
    """
    return a / b