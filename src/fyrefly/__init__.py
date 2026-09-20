"""A quant-based library to compute mathematical operations, run SQL queries, get AI-powered insights, and visualize your data."""

from .core import add, mul, div, mod, diff
from .dataops import load, loadh, loadc, loads, sql, xtract, clean
from .ai import ask, insights
from .viz import viz

__all__ = [
    "add", "mul", "div", "mod", "diff",
    "load", "loadh", "loadc", "loads", "sql", "xtract", "clean",
    "ask", "insights",
    "viz",
]
__version__ = "0.3.2"