"""A quant-based library to compute mathematical operations and run SQL queries on your data."""

from .core import add, mul, div, mod
from .dataops import load, loadh, loadc, loads, sql, xtract

__all__ = ["add", "mul", "div", "mod", "load", "loadh", "loadc", "loads", "sql", "xtract"]
__version__ = "0.3.0"