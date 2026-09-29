"""A quant-based library for math, SQL-powered data analysis, AI, and visualization."""

from .core import add, mul, div, mod, diff
from .dataops import load, loadh, loadc, loads, sql, xtract, clean
from .ai import ask, insights
from .viz import viz
from .quant import (
    si, ci, si_ci_diff,
    profit, loss,
    ap, gp, hp,
    avg, avgc, mode, median,
    hyp, slope, centroid, dist,
    eqn, log, exp, nroot, sqrt, curt,
    sin, cos, tan, cosec, sec, cot,
)

__all__ = [
    "add", "mul", "div", "mod", "diff",
    "load", "loadh", "loadc", "loads", "sql", "xtract", "clean",
    "ask", "insights",
    "viz",
    "si", "ci", "si_ci_diff",
    "profit", "loss",
    "ap", "gp", "hp",
    "avg", "avgc", "mode", "median",
    "hyp", "slope", "centroid", "dist",
    "eqn", "log", "exp", "nroot", "sqrt", "curt",
    "sin", "cos", "tan", "cosec", "sec", "cot",
]
__version__ = "0.5.0"