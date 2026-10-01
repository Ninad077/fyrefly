# Each category maps unit aliases to a factor relative to that category's base unit.
_LENGTH = {  # base: meters
    "m": 1, "meter": 1, "meters": 1, "metre": 1, "metres": 1,
    "km": 1000, "kilometer": 1000, "kilometers": 1000, "kilometre": 1000, "kilometres": 1000,
    "cm": 0.01, "centimeter": 0.01, "centimeters": 0.01,
    "mm": 0.001, "millimeter": 0.001, "millimeters": 0.001,
    "mile": 1609.344, "miles": 1609.344, "mi": 1609.344,
    "yard": 0.9144, "yards": 0.9144, "yd": 0.9144,
    "foot": 0.3048, "feet": 0.3048, "ft": 0.3048,
    "inch": 0.0254, "inches": 0.0254, "in": 0.0254,
    "nm": 1852, "nautical_mile": 1852, "nautical_miles": 1852,
}

_MASS = {  # base: grams
    "g": 1, "gram": 1, "grams": 1,
    "kg": 1000, "kilogram": 1000, "kilograms": 1000,
    "mg": 0.001, "milligram": 0.001, "milligrams": 0.001,
    "lb": 453.59237, "lbs": 453.59237, "pound": 453.59237, "pounds": 453.59237,
    "oz": 28.349523125, "ounce": 28.349523125, "ounces": 28.349523125,
    "ton": 1_000_000, "tonne": 1_000_000, "metric_ton": 1_000_000,
    "stone": 6350.29318, "st": 6350.29318,
}

_VOLUME = {  # base: liters
    "l": 1, "liter": 1, "liters": 1, "litre": 1, "litres": 1,
    "ml": 0.001, "milliliter": 0.001, "milliliters": 0.001,
    "gallon": 3.785411784, "gallons": 3.785411784, "gal": 3.785411784,
    "quart": 0.946352946, "quarts": 0.946352946, "qt": 0.946352946,
    "pint": 0.473176473, "pints": 0.473176473, "pt": 0.473176473,
    "cup": 0.2365882365, "cups": 0.2365882365,
    "fl_oz": 0.0295735296, "fluid_ounce": 0.0295735296, "fluid_ounces": 0.0295735296,
}

_AREA = {  # base: square meters
    "sqm": 1, "m2": 1, "square_meter": 1, "square_meters": 1,
    "sqkm": 1_000_000, "km2": 1_000_000, "square_kilometer": 1_000_000, "square_kilometers": 1_000_000,
    "sqft": 0.09290304, "ft2": 0.09290304, "square_foot": 0.09290304, "square_feet": 0.09290304,
    "acre": 4046.8564224, "acres": 4046.8564224,
    "hectare": 10_000, "hectares": 10_000, "ha": 10_000,
    "sqmi": 2_589_988.110336, "mi2": 2_589_988.110336, "square_mile": 2_589_988.110336, "square_miles": 2_589_988.110336,
}

_TIME = {  # base: seconds
    "s": 1, "sec": 1, "secs": 1, "second": 1, "seconds": 1,
    "min": 60, "mins": 60, "minute": 60, "minutes": 60,
    "hr": 3600, "hrs": 3600, "hour": 3600, "hours": 3600, "h": 3600,
    "day": 86400, "days": 86400,
    "week": 604800, "weeks": 604800,
    "month": 2_628_000, "months": 2_628_000,
    "year": 31_536_000, "years": 31_536_000, "yr": 31_536_000,
}

_SPEED = {  # base: meters per second
    "mps": 1, "m/s": 1,
    "kmh": 0.2777777778, "km/h": 0.2777777778, "kph": 0.2777777778,
    "mph": 0.44704,
    "knot": 0.5144444444, "knots": 0.5144444444,
}

_DATA = {  # base: bytes
    "byte": 1, "bytes": 1, "b": 1,
    "kb": 1024, "kilobyte": 1024, "kilobytes": 1024,
    "mb": 1024 ** 2, "megabyte": 1024 ** 2, "megabytes": 1024 ** 2,
    "gb": 1024 ** 3, "gigabyte": 1024 ** 3, "gigabytes": 1024 ** 3,
    "tb": 1024 ** 4, "terabyte": 1024 ** 4, "terabytes": 1024 ** 4,
}

_ENERGY = {  # base: joules
    "j": 1, "joule": 1, "joules": 1,
    "kj": 1000, "kilojoule": 1000, "kilojoules": 1000,
    "cal": 4.184, "calorie": 4.184, "calories": 4.184,
    "kcal": 4184, "kilocalorie": 4184, "kilocalories": 4184,
    "wh": 3600, "watt_hour": 3600,
    "kwh": 3_600_000, "kilowatt_hour": 3_600_000,
}

_PRESSURE = {  # base: pascals
    "pa": 1, "pascal": 1, "pascals": 1,
    "kpa": 1000, "kilopascal": 1000,
    "bar": 100_000,
    "atm": 101_325, "atmosphere": 101_325,
    "psi": 6894.757293168,
}

_CATEGORIES = {
    "length": _LENGTH,
    "mass": _MASS,
    "volume": _VOLUME,
    "area": _AREA,
    "time": _TIME,
    "speed": _SPEED,
    "data": _DATA,
    "energy": _ENERGY,
    "pressure": _PRESSURE,
}

_TEMPERATURE_UNITS = {
    "c": "celsius", "celsius": "celsius",
    "f": "fahrenheit", "fahrenheit": "fahrenheit",
    "k": "kelvin", "kelvin": "kelvin",
}


def _normalize(unit):
    return unit.strip().lower().replace(" ", "_")


def _find_unit(unit):
    """Returns (category_name, factor) for a given unit, or None if not found."""
    for category_name, table in _CATEGORIES.items():
        if unit in table:
            return category_name, table[unit]
    return None


def _convert_temperature(value, from_unit, to_unit):
    from_kind = _TEMPERATURE_UNITS[from_unit]
    to_kind = _TEMPERATURE_UNITS[to_unit]

    if from_kind == "celsius":
        celsius = value
    elif from_kind == "fahrenheit":
        celsius = (value - 32) * 5 / 9
    elif from_kind == "kelvin":
        celsius = value - 273.15

    if to_kind == "celsius":
        return celsius
    elif to_kind == "fahrenheit":
        return celsius * 9 / 5 + 32
    elif to_kind == "kelvin":
        return celsius + 273.15


def convert(value, from_unit, to_unit):
    """
    Converts a value from one unit to another. Covers length, mass, volume,
    area, time, speed, data storage, energy, pressure, and temperature.

    Example:
        convert(10, "km", "miles")   -> 6.213711922373339
        convert(98.6, "F", "C")      -> 37.0
        convert(5, "kg", "lb")       -> 11.023113109243878
        convert(1, "gb", "mb")       -> 1024.0
        convert(2, "hr", "min")      -> 120.0

    Raises a clear error if the units are incompatible (e.g. length vs. mass)
    or if a unit isn't recognized.
    """
    from_u = _normalize(from_unit)
    to_u = _normalize(to_unit)

    from_is_temp = from_u in _TEMPERATURE_UNITS
    to_is_temp = to_u in _TEMPERATURE_UNITS

    if from_is_temp or to_is_temp:
        if not (from_is_temp and to_is_temp):
            raise ValueError(
                f"Cannot convert between temperature ('{from_unit}' or '{to_unit}') "
                f"and a non-temperature unit."
            )
        return _convert_temperature(value, from_u, to_u)

    from_result = _find_unit(from_u)
    to_result = _find_unit(to_u)

    if from_result is None:
        raise ValueError(f"Unrecognized unit: '{from_unit}'")
    if to_result is None:
        raise ValueError(f"Unrecognized unit: '{to_unit}'")

    from_category, from_factor = from_result
    to_category, to_factor = to_result

    if from_category != to_category:
        raise ValueError(
            f"Cannot convert between incompatible units: '{from_unit}' ({from_category}) "
            f"and '{to_unit}' ({to_category})"
        )

    base_value = value * from_factor
    return base_value / to_factor