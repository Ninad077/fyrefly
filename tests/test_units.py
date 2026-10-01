import pytest
from fyrefly import convert


def test_length():
    assert abs(convert(10, "km", "miles") - 6.213711922373339) < 1e-6
    assert abs(convert(1, "mile", "km") - 1.609344) < 1e-6
    assert convert(100, "cm", "m") == 1.0


def test_mass():
    assert abs(convert(5, "kg", "lb") - 11.023113109243878) < 1e-6
    assert convert(16, "oz", "lb") == pytest.approx(1.0)


def test_volume():
    assert convert(1, "gallon", "liters") == pytest.approx(3.785411784)


def test_area():
    assert convert(1, "hectare", "sqm") == 10000


def test_time():
    assert convert(2, "hr", "min") == 120.0
    assert convert(1, "day", "hours") == 24.0
    assert convert(1, "week", "days") == 7.0


def test_speed():
    assert abs(convert(100, "kmh", "mph") - 62.137119) < 1e-3


def test_data():
    assert convert(1, "gb", "mb") == 1024.0
    assert convert(1024, "kb", "mb") == 1.0


def test_energy():
    assert convert(1, "kcal", "cal") == 1000.0


def test_pressure():
    assert abs(convert(1, "atm", "psi") - 14.6959) < 0.01


def test_temperature():
    assert convert(98.6, "F", "C") == pytest.approx(37.0, abs=1e-6)
    assert convert(0, "C", "F") == 32.0
    assert convert(100, "C", "K") == 373.15
    assert convert(0, "K", "C") == -273.15


def test_incompatible_units_raises():
    with pytest.raises(ValueError):
        convert(10, "km", "kg")


def test_temperature_vs_other_raises():
    with pytest.raises(ValueError):
        convert(10, "km", "celsius")


def test_unrecognized_unit_raises():
    with pytest.raises(ValueError):
        convert(10, "banana", "km")


def test_case_insensitive_and_aliases():
    assert convert(10, "KM", "Miles") == convert(10, "kilometer", "mile")