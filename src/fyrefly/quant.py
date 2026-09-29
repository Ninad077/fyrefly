import statistics
import math


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
# Sequences: AP, GP, HP — callable for the full sequence, .tn()/.sn() for one term / sum
# ---------------------------------------------------------------------------

class _AP:
    """
    Arithmetic Progression.

    Call directly for the full sequence: ap(a, d, n) -> list of n terms.
    Use .tn() for just the nth term: ap.tn(a, d, n) -> single value.
    Use .sn() for the sum of the first n terms: ap.sn(a, d, n) -> single value.

    Example:
        ap(2, 3, 4)      -> [2, 5, 8, 11]
        ap.tn(2, 3, 4)   -> 11
        ap.sn(2, 3, 4)   -> 26
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
    Use .sn() for the sum of the first n terms: gp.sn(a, r, n) -> single value.

    Example:
        gp(2, 3, 4)      -> [2, 6, 18, 54]
        gp.tn(2, 3, 4)   -> 54
        gp.sn(2, 3, 4)   -> 80
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
    Use .sn() for the sum of the first n terms: hp.sn(a, d, n) -> single value.

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