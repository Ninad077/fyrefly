def add(*nos):
    """Adds any count of numbers passed as separate arguments.

    Example:
        add(5, 4, 6, 10) -> 25
    """
    return sum(nos)


def mul(*nos):
    """Multiplies any count of numbers passed as separate arguments.

    Example:
        mul(5, 4, 6, 10) -> 1200
    """
    result = 1
    for n in nos:
        result *= n
    return result


def div(*nos):
    """Divides numbers in sequence: first / second / third ...

    Example:
        div(100, 5, 2) -> 10.0

    Raises:
        ValueError: if no numbers are passed.
        ZeroDivisionError: if any number after the first is zero.
    """
    if not nos:
        raise ValueError("div() requires at least one number")
    res = nos[0]
    for n in nos[1:]:
        res = res / n
    return res
