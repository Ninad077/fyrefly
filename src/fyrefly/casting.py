import ast
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd

_TYPE_ALIASES = {
    "int": int, "integer": int,
    "float": float, "double": float,
    "str": str, "string": str,
    "bool": bool, "boolean": bool,
    "list": list,
    "tuple": tuple,
    "set": set,
    "dict": dict, "dictionary": dict,
    "bytes": bytes,
    "complex": complex,
}

_SPECIAL_TARGETS = {"date", "datetime"}


def _resolve_target_type(target):
    if isinstance(target, type):
        return target
    if isinstance(target, str):
        key = target.strip().lower()
        if key in _SPECIAL_TARGETS:
            return key
        if key in _TYPE_ALIASES:
            return _TYPE_ALIASES[key]
    raise ValueError(
        f"Unrecognized target type: {target!r}. Supported: "
        f"int, float, str, bool, list, tuple, set, dict, bytes, complex, date, datetime"
    )


def _parse_literal_string(value):
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        raise ValueError(f"Could not parse '{value}' as a Python literal")


def _cast_to_bool(value):
    if isinstance(value, str):
        key = value.strip().lower()
        if key in ("true", "yes", "y", "1"):
            return True
        if key in ("false", "no", "n", "0", ""):
            return False
        raise ValueError(f"Cannot interpret '{value}' as a boolean")
    return bool(value)


def _cast_scalar(value, resolved):
    if resolved in _SPECIAL_TARGETS:
        try:
            parsed = pd.to_datetime(value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Could not cast {value!r} to {resolved}: {e}")
        return parsed.date() if resolved == "date" else parsed.to_pydatetime()

    if resolved is bool:
        return _cast_to_bool(value)

    if resolved in (list, tuple, set, dict) and isinstance(value, str):
        parsed = _parse_literal_string(value)
        return resolved(parsed)

    try:
        return resolved(value)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Could not cast {value!r} to {resolved.__name__}: {e}")


def cast(value, target):
    """
    Casts `value` to `target` type. target can be a real Python type
    (int, float, str, list, ...) or its name as a string ("int", "float",
    "bool", "date", "datetime", ...).

    Works on a single value, OR on an entire DataFrame column (a pandas
    Series) — pass df["column_name"] as value and every element gets cast,
    returning a new Series.

    Example:
        cast("123", "int")           -> 123
        cast("False", "bool")        -> False
        cast("[1, 2, 3]", "list")    -> [1, 2, 3]
        cast("2024-01-15", "date")   -> date(2024, 1, 15)
    """
    resolved = _resolve_target_type(target)

    if isinstance(value, pd.Series):
        return value.apply(lambda v: _cast_scalar(v, resolved))

    return _cast_scalar(value, resolved)


def round(value, places=0):
    """
    Rounds `value` to the given number of decimal places, using standard
    round-half-up rounding (like Excel), not Python's banker's rounding.

    Example:
        round(2.5)          -> 3   (Python's own round(2.5) gives 2)
        round(1250, -2)     -> 1300
    """
    d = Decimal(str(value))
    exponent = Decimal(1).scaleb(-places)
    rounded = d.quantize(exponent, rounding=ROUND_HALF_UP)
    result = float(rounded)
    if places <= 0:
        return int(result)
    return result