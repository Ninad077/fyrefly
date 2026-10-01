import pytest
import pandas as pd
from datetime import date, datetime
from fyrefly import cast, round as fround


def test_basic_numeric_and_string_casts():
    assert cast("123", "int") == 123
    assert cast("3.14", float) == 3.14
    assert cast(42, "str") == "42"
    assert cast(3.99, "int") == 3


def test_bool_gotcha_fix():
    assert bool("False") is True  # documenting the gotcha we're avoiding
    assert cast("False", "bool") is False
    assert cast("True", "bool") is True
    assert cast("yes", "bool") is True
    assert cast("no", "bool") is False
    assert cast("0", "bool") is False
    assert cast("1", "bool") is True
    assert cast(0, "bool") is False
    assert cast(1, "bool") is True


def test_string_to_container_types():
    assert cast("[1, 2, 3]", "list") == [1, 2, 3]
    assert cast("(1, 2, 3)", "tuple") == (1, 2, 3)
    assert cast("{1, 2, 3}", "set") == {1, 2, 3}
    assert cast("{'a': 1, 'b': 2}", "dict") == {"a": 1, "b": 2}


def test_container_to_container_conversions():
    assert cast([1, 2, 3], "tuple") == (1, 2, 3)
    assert cast((1, 2, 3), "list") == [1, 2, 3]
    assert cast([1, 2, 2, 3], "set") == {1, 2, 3}


def test_date_and_datetime():
    assert cast("2024-01-15", "date") == date(2024, 1, 15)
    assert cast("2024-01-15 10:30:00", "datetime") == datetime(2024, 1, 15, 10, 30, 0)


def test_accepts_real_type_objects():
    assert cast("5", int) == 5
    assert cast(5, str) == "5"


def test_bad_int_cast_raises():
    with pytest.raises(ValueError):
        cast("not a number", "int")


def test_bad_bool_cast_raises():
    with pytest.raises(ValueError):
        cast("maybe", "bool")


def test_unknown_target_type_raises():
    with pytest.raises(ValueError):
        cast(5, "unknown_type")


def test_round_fixes_bankers_rounding_gotcha():
    assert round(2.5) == 2  # documenting the gotcha we're avoiding
    assert fround(2.5) == 3
    assert fround(0.5) == 1
    assert fround(1.5) == 2
    assert fround(3.5) == 4


def test_round_decimal_places():
    assert fround(3.14159, 2) == 3.14
    assert fround(3.14159, 4) == 3.1416
    assert fround(2.345, 2) == 2.35


def test_round_negative_places():
    assert fround(1250, -2) == 1300  # Python's own round(1250, -2) gives 1200
    assert fround(1249, -2) == 1200
    assert fround(1234, -3) == 1000


def test_round_return_types():
    assert isinstance(fround(3.14159, 2), float)
    assert isinstance(fround(1250, -2), int)


def test_cast_entire_column_to_int():
    col = pd.Series(["25", "30", "45"])
    result = cast(col, "int")
    assert result.tolist() == [25, 30, 45]
    assert result.dtype == "int64"


def test_cast_entire_column_to_bool_fixes_gotcha():
    col = pd.Series(["True", "False", "yes", "no"])
    result = cast(col, "bool")
    assert result.tolist() == [True, False, True, False]


def test_cast_entire_column_to_float():
    col = pd.Series(["19.99", "25.50", "10.00"])
    result = cast(col, "float")
    assert result.tolist() == [19.99, 25.50, 10.00]


def test_cast_column_does_not_mutate_original():
    col = pd.Series(["25", "30"])
    cast(col, "int")
    assert col.tolist() == ["25", "30"]


def test_cast_column_bad_value_raises():
    col = pd.Series(["123", "not a number", "456"])
    with pytest.raises(ValueError):
        cast(col, "int")