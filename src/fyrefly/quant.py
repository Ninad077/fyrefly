import statistics
import math
import numpy as np


# ---------------------------------------------------------------------------
# Interest
# ---------------------------------------------------------------------------

def si(p, n, r):
    """Simple Interest: (p * n * r) / 100

    Example:
        si(1000, 2, 5) -> 100.0
    """
    return (p * n * r) / 100


def ci(p, n, r, freq="annual"):
    """Compound Interest earned (not the total amount) — principal excluded.

    freq="annual" (default): compounded once per year.
    freq="semi-annual": compounded twice per year (half the rate, double the periods).

    Example:
        ci(1000, 2, 10) -> 210.00000000000023            (annual)
        ci(1000, 2, 10, "semi-annual") -> 215.506...       (semi-annual)
    """
    if freq == "annual":
        amount = p * ((1 + r / 100) ** n)
    elif freq == "semi-annual":
        amount = p * ((1 + (r / 2) / 100) ** (2 * n))
    else:
        raise ValueError("freq must be 'annual' or 'semi-annual'")
    return amount - p


def si_ci_diff(p, r, n):
    """Difference between Compound Interest and Simple Interest, for n = 2 or 3 years.

    Example:
        si_ci_diff(1000, 10, 2) -> 10.000000000000455
        si_ci_diff(1000, 10, 3) -> 31.000000000000227
    """
    if n not in (2, 3):
        raise ValueError("si_ci_diff() only supports n = 2 or 3 years")
    return ci(p, n, r) - si(p, n, r)


# ---------------------------------------------------------------------------
# Profit / Loss
# ---------------------------------------------------------------------------

def profit(sp, cp, pct=None):
    """Profit = sp - cp. If sp < cp, this is actually a loss — raises a
    clear error telling you to use loss() instead.

    Pass "%" as the third argument to also get the profit percentage:
    returns (profit, profit_pct) instead of just the value.

    Example:
        profit(120, 100) -> 20
        profit(120, 100, "%") -> (20, 20.0)
    """
    if sp < cp:
        raise ValueError(
            f"sp ({sp}) is less than cp ({cp}) — this is a LOSS, not a profit. "
            f"Use loss({sp}, {cp}) instead."
        )
    value = sp - cp
    if pct == "%":
        pct_value = (value / cp) * 100 if cp != 0 else float("inf")
        return value, pct_value
    return value


def loss(sp, cp, pct=None):
    """Loss = cp - sp. If sp > cp, this is actually a profit — raises a
    clear error telling you to use profit() instead.

    Pass "%" as the third argument to also get the loss percentage:
    returns (loss, loss_pct) instead of just the value.

    Example:
        loss(80, 100) -> 20
        loss(80, 100, "%") -> (20, 20.0)
    """
    if sp > cp:
        raise ValueError(
            f"sp ({sp}) is greater than cp ({cp}) — this is a PROFIT, not a loss. "
            f"Use profit({sp}, {cp}) instead."
        )
    value = cp - sp
    if pct == "%":
        pct_value = (value / cp) * 100 if cp != 0 else float("inf")
        return value, pct_value
    return value


# ---------------------------------------------------------------------------
# Sequences: AP, GP, HP — callable for the full sequence, .tn() for one term
# ---------------------------------------------------------------------------

class _AP:
    """
    Arithmetic Progression.

    Call directly for the full sequence: ap(a, d, n) -> list of n terms.
    Use .tn() for just the nth term: ap.tn(a, d, n) -> single value.

    Example:
        ap(2, 3, 4)      -> [2, 5, 8, 11]
        ap.tn(2, 3, 4)   -> 11
    """

    def __call__(self, a, d, n):
        return [a + i * d for i in range(n)]

    def tn(self, a, d, n):
        """The nth term: a + (n - 1) * d"""
        return a + (n - 1) * d

    def sn(self, a, d, n):
        """Sum of the first n terms: n/2 * (2a + (n - 1) * d)

        Example:
            ap.sn(2, 3, 4) -> 26   (2 + 5 + 8 + 11)
        """
        return (n / 2) * (2 * a + (n - 1) * d)


class _GP:
    """
    Geometric Progression.

    Call directly for the full sequence: gp(a, r, n) -> list of n terms.
    Use .tn() for just the nth term: gp.tn(a, r, n) -> single value.

    Example:
        gp(2, 3, 4)      -> [2, 6, 18, 54]
        gp.tn(2, 3, 4)   -> 54
    """

    def __call__(self, a, r, n):
        return [a * (r ** i) for i in range(n)]

    def tn(self, a, r, n):
        """The nth term: a * r ** (n - 1)"""
        return a * (r ** (n - 1))

    def sn(self, a, r, n):
        """Sum of the first n terms: a * (r**n - 1) / (r - 1), or a * n if r == 1.

        Example:
            gp.sn(2, 3, 4) -> 80   (2 + 6 + 18 + 54)
        """
        if r == 1:
            return a * n
        return a * (r ** n - 1) / (r - 1)


class _HP:
    """
    Harmonic Progression — reciprocals of an Arithmetic Progression with
    first term 1/a and common difference d.

    Call directly for the full sequence: hp(a, d, n) -> list of n terms.
    Use .tn() for just the nth term: hp.tn(a, d, n) -> single value.

    Example:
        hp(2, 3, 4)      -> [2.0, 0.2857142857142857, 0.15384615384615385, 0.10526315789473684]
        hp.tn(2, 3, 4)   -> 0.10526315789473684
    """

    def __call__(self, a, d, n):
        return [1 / ((1 / a) + i * d) for i in range(n)]

    def tn(self, a, d, n):
        """The nth term: reciprocal of the nth term of the underlying AP"""
        return 1 / ((1 / a) + (n - 1) * d)

    def sn(self, a, d, n):
        """Sum of the first n terms. HP has no simple closed-form sum, so
        this adds up the actual n terms directly.

        Example:
            hp.sn(2, 3, 4) -> 2.5448235974551765
        """
        return sum(1 / ((1 / a) + i * d) for i in range(n))


ap = _AP()
gp = _GP()
hp = _HP()


# ---------------------------------------------------------------------------
# Averages
# ---------------------------------------------------------------------------

def avg(*nos):
    """Average of any count of individual numbers.

    Example:
        avg(10, 12, 13) -> 11.666666666666666
    """
    if not nos:
        raise ValueError("avg() requires at least one number")
    return sum(nos) / len(nos)


def avgc(*args):
    """Weighted average from (value, count) pairs — e.g. 'this value occurred
    this many times'. Pass as many pairs as you like.

    Example:
        avgc(5, 3) -> 5.0                  (three 5's: (5+5+5)/3)
        avgc(5, 3, 10, 2) -> 7.0           (three 5's and two 10's: (15+20)/5)
    """
    if len(args) % 2 != 0:
        raise ValueError("avgc() requires (value, count) pairs — an even number of arguments")
    total_sum = 0
    total_count = 0
    for i in range(0, len(args), 2):
        value, count = args[i], args[i + 1]
        total_sum += value * count
        total_count += count
    if total_count == 0:
        raise ValueError("avgc() total count is zero — cannot compute an average")
    return total_sum / total_count


# ---------------------------------------------------------------------------
# Mode / Median
# ---------------------------------------------------------------------------

def mode(*nos):
    """Most frequently occurring value(s). Returns a list — may contain
    more than one value if there's a tie (multimodal).

    Example:
        mode(1, 2, 2, 3) -> [2]
        mode(1, 1, 2, 2) -> [1, 2]
    """
    if not nos:
        raise ValueError("mode() requires at least one number")
    return statistics.multimode(nos)


def median(*nos):
    """Median of any count of numbers.

    Example:
        median(1, 3, 2) -> 2
        median(1, 2, 3, 4) -> 2.5
    """
    if not nos:
        raise ValueError("median() requires at least one number")
    return statistics.median(nos)


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------

def hyp(a, b):
    """Hypotenuse of a right triangle given the other two sides.

    Example:
        hyp(3, 4) -> 5.0
    """
    return math.sqrt(a ** 2 + b ** 2)


def slope(point1, point2):
    """Slope between two (x, y) coordinate tuples: (y2 - y1) / (x2 - x1).

    Example:
        slope((1, 2), (3, 4)) -> 1.0
    """
    x1, y1 = point1
    x2, y2 = point2
    if x2 == x1:
        raise ValueError("Slope is undefined for a vertical line (x1 == x2)")
    return (y2 - y1) / (x2 - x1)


def centroid(point1, point2, point3):
    """Centroid of a triangle given three (x, y) coordinate tuples.

    Example:
        centroid((1, 2), (3, 2), (4, 5)) -> (2.6666666666666665, 3.0)
    """
    x1, y1 = point1
    x2, y2 = point2
    x3, y3 = point3
    return ((x1 + x2 + x3) / 3, (y1 + y2 + y3) / 3)


def dist(point1, point2):
    """Distance between two (x, y) coordinate tuples:
    sqrt((x2 - x1)**2 + (y2 - y1)**2)

    Example:
        dist((6, 2), (10, 5)) -> 5.0
    """
    x1, y1 = point1
    x2, y2 = point2
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


# ---------------------------------------------------------------------------
# Equations: linear systems and polynomial roots
# ---------------------------------------------------------------------------

class _EqnQ:
    """
    Quadratic/polynomial equation solver — callable for the roots of any
    degree polynomial, with .sum() and .mul() for the sum and product of
    all roots (Vieta's formulas), also valid for any degree.

    Coefficients are given from the highest degree down to the constant.

    Example:
        eqn.q(1, 3, 4)          -> roots of x^2 + 3x + 4 = 0
        eqn.q(3, 4, 6, 9, 10)   -> roots of 3x^4 + 4x^3 + 6x^2 + 9x + 10 = 0
        eqn.q.sum(5, 2, 3)      -> -0.4   (sum of roots of 5x^2 + 2x + 3 = 0)
        eqn.q.mul(5, 2, 3)      -> 0.6    (product of roots)
    """

    def __call__(self, *coeffs):
        if len(coeffs) < 2:
            raise ValueError("eqn.q() needs at least 2 coefficients (e.g. a, b for ax + b = 0)")
        roots = np.roots(coeffs)
        return tuple(roots)

    def sum(self, *coeffs):
        """Sum of all roots (Vieta's formula): -coeffs[1] / coeffs[0]"""
        if len(coeffs) < 2:
            raise ValueError("eqn.q.sum() needs at least 2 coefficients")
        return -coeffs[1] / coeffs[0]

    def mul(self, *coeffs):
        """Product of all roots (Vieta's formula): (-1)^degree * constant / leading coefficient"""
        if len(coeffs) < 2:
            raise ValueError("eqn.q.mul() needs at least 2 coefficients")
        degree = len(coeffs) - 1
        return ((-1) ** degree) * coeffs[-1] / coeffs[0]


class _Eqn:
    """
    Namespace for solving equations.

    eqn.l(...)   — system of linear equations
    eqn.q(...)   — polynomial roots (any degree), plus .sum()/.mul()
    """

    def __init__(self):
        self.q = _EqnQ()

    def l(self, *equations):
        """
        Solves a system of n linear equations in n unknowns.

        Each equation is a tuple of (n + 1) numbers: the n coefficients
        followed by the constant on the right-hand side. You need exactly
        as many equations as unknowns.

        Example — solving 2x + 3y = 5 and 7x + 6y = 10:
            eqn.l((2, 3, 5), (7, 6, 10)) -> (x, y)

        Example — 3 equations, 3 unknowns (a, b, c):
            eqn.l((1, 1, 1, 6), (2, -1, 1, 3), (1, 2, -1, 2)) -> (a, b, c)
        """
        n = len(equations)
        for eq in equations:
            if len(eq) != n + 1:
                raise ValueError(
                    f"For {n} equations ({n} unknowns), each equation needs "
                    f"{n + 1} numbers ({n} coefficients + 1 constant). "
                    f"Got {len(eq)} in {eq}."
                )
        A = [eq[:-1] for eq in equations]
        b = [eq[-1] for eq in equations]
        solution = np.linalg.solve(A, b)
        return tuple(solution)


eqn = _Eqn()


# ---------------------------------------------------------------------------
# Logs, exponents, roots
# ---------------------------------------------------------------------------

def log(x, base=math.e):
    """Logarithm of x. Natural log (base e) by default; pass a second
    argument for a different base.

    Example:
        log(math.e) -> 1.0
        log(8, 2) -> 3.0
    """
    return math.log(x, base)


def exp(a, b):
    """a raised to the power b. Works for positive and negative exponents.

    Example:
        exp(2, 5) -> 32
        exp(2, -1) -> 0.5
    """
    return a ** b


def nroot(no, n):
    """The nth root of a number. Handles negative numbers correctly for
    odd roots (e.g. cube root of a negative number is negative); raises
    for even roots of a negative number, since that's not a real number.

    Example:
        nroot(16, 2) -> 4.0
        nroot(27, 3) -> 3.0
        nroot(-27, 3) -> -3.0
    """
    if no < 0:
        if n % 2 == 0:
            raise ValueError(f"Even root ({n}) of a negative number ({no}) is not a real number")
        return -((-no) ** (1 / n))
    return no ** (1 / n)


def sqrt(no):
    """Square root. Shortcut for nroot(no, 2).

    Example:
        sqrt(16) -> 4.0
    """
    return nroot(no, 2)


def curt(no):
    """Cube root. Shortcut for nroot(no, 3).

    Example:
        curt(27) -> 3.0
    """
    return nroot(no, 3)


# ---------------------------------------------------------------------------
# Trigonometry — angle in degrees by default; pass mode="rad" for radians
# ---------------------------------------------------------------------------

def _to_radians(angle, mode):
    if mode == "deg":
        return math.radians(angle)
    elif mode == "rad":
        return angle
    else:
        raise ValueError("mode must be 'deg' or 'rad'")


def sin(angle, mode="deg"):
    """Sine of an angle. Degrees by default; pass mode="rad" for radians."""
    return math.sin(_to_radians(angle, mode))


def cos(angle, mode="deg"):
    """Cosine of an angle. Degrees by default; pass mode="rad" for radians."""
    return math.cos(_to_radians(angle, mode))


def tan(angle, mode="deg"):
    """Tangent of an angle. Degrees by default; pass mode="rad" for radians."""
    return math.tan(_to_radians(angle, mode))


def cosec(angle, mode="deg"):
    """Cosecant (1/sin) of an angle. Degrees by default."""
    s = sin(angle, mode)
    if s == 0:
        raise ValueError("cosec() is undefined when sin(angle) is 0")
    return 1 / s


def sec(angle, mode="deg"):
    """Secant (1/cos) of an angle. Degrees by default."""
    c = cos(angle, mode)
    if c == 0:
        raise ValueError("sec() is undefined when cos(angle) is 0")
    return 1 / c


def cot(angle, mode="deg"):
    """Cotangent (1/tan, or cos/sin) of an angle. Degrees by default."""
    s = sin(angle, mode)
    if s == 0:
        raise ValueError("cot() is undefined when sin(angle) is 0")
    return cos(angle, mode) / s