"""A quant-based library for math, SQL-powered data analysis, AI, and visualization."""

from .core import add, mul, div, mod, diff
from .dataops import load, loadh, loadc, loads, sql, xtract, clean, vlook, xlook, countif, sumif, avgif
from .ai import ask, insights
from .viz import viz
from .units import convert
from .casting import cast, round
from .quant import (
    si, ci, si_ci_diff,
    profit, loss,
    ap, gp, hp,
    avg, avgc, mode, median,
    hyp, slope, centroid, dist,
    eqn, log, exp, nroot, sqrt, curt,
    sin, cos, tan, cosec, sec, cot,
)
from .mensuration import (
    circle, semicircle, square, rectangle, triangle, equilateral_triangle,
    parallelogram, rhombus, kite, trapezoid, ellipse, polygon, sector, annulus,
    cube, cuboid, sphere, hemisphere, cylinder, cone, frustum, pyramid, prism, torus,
)

__all__ = [
    "add", "mul", "div", "mod", "diff",
    "load", "loadh", "loadc", "loads", "sql", "xtract", "clean", "vlook", "xlook", "countif", "sumif", "avgif",
    "ask", "insights",
    "viz",
    "convert", "cast", "round",
    "si", "ci", "si_ci_diff",
    "profit", "loss",
    "ap", "gp", "hp",
    "avg", "avgc", "mode", "median",
    "hyp", "slope", "centroid", "dist",
    "eqn", "log", "exp", "nroot", "sqrt", "curt",
    "sin", "cos", "tan", "cosec", "sec", "cot",
    "circle", "semicircle", "square", "rectangle", "triangle", "equilateral_triangle",
    "parallelogram", "rhombus", "kite", "trapezoid", "ellipse", "polygon", "sector", "annulus",
    "cube", "cuboid", "sphere", "hemisphere", "cylinder", "cone", "frustum", "pyramid", "prism", "torus",
]
__version__ = "0.7.0"