import math
import pytest
from fyrefly import (
    si, ci, si_ci_diff,
    profit, loss,
    ap, gp, hp,
    avg, avgc, mode, median,
    hyp, slope, centroid, dist,
    eqn, log, exp, nroot, sqrt, curt,
    sin, cos, tan, cosec, sec, cot,
)


# ---------------------------------------------------------------------------
# Interest
# ---------------------------------------------------------------------------

def test_si():
    assert si(1000, 2, 5) == 100.0


def test_ci_annual():
    assert abs(ci(1000, 2, 10) - 210.0) < 1e-6
    assert abs(ci(1000, 2, 10, "annual") - 210.0) < 1e-6


def test_ci_semi_annual():
    expected = 1000 * (1.05 ** 4) - 1000
    assert abs(ci(1000, 2, 10, "semi-annual") - expected) < 1e-6


def test_ci_invalid_freq_raises():
    with pytest.raises(ValueError):
        ci(1000, 2, 10, "monthly")


def test_si_ci_diff_two_years():
    assert abs(si_ci_diff(1000, 10, 2) - 10.0) < 1e-6


def test_si_ci_diff_three_years():
    assert abs(si_ci_diff(1000, 10, 3) - 31.0) < 1e-6


def test_si_ci_diff_rejects_other_years():
    with pytest.raises(ValueError):
        si_ci_diff(1000, 10, 4)


# ---------------------------------------------------------------------------
# Profit / Loss
# ---------------------------------------------------------------------------

def test_profit_value_only():
    assert profit(120, 100) == 20


def test_profit_with_percentage():
    value, pct = profit(120, 100, "%")
    assert value == 20
    assert pct == 20.0


def test_profit_smart_detects_loss():
    with pytest.raises(ValueError):
        profit(80, 100)


def test_loss_value_only():
    assert loss(80, 100) == 20


def test_loss_with_percentage():
    value, pct = loss(80, 100, "%")
    assert value == 20
    assert pct == 20.0


def test_loss_smart_detects_profit():
    with pytest.raises(ValueError):
        loss(120, 100)


def test_profit_loss_equal_sp_cp():
    assert profit(100, 100) == 0
    assert loss(100, 100) == 0


# ---------------------------------------------------------------------------
# Sequences: AP, GP, HP
# ---------------------------------------------------------------------------

def test_ap_sequence():
    assert ap(2, 3, 4) == [2, 5, 8, 11]


def test_ap_tn():
    assert ap.tn(2, 3, 4) == 11
    assert ap.tn(2, 3, 4) == ap(2, 3, 4)[-1]


def test_ap_sn():
    assert ap.sn(2, 3, 4) == 26
    assert ap.sn(2, 3, 4) == sum(ap(2, 3, 4))


def test_gp_sequence():
    assert gp(2, 3, 4) == [2, 6, 18, 54]


def test_gp_tn():
    assert gp.tn(2, 3, 4) == 54
    assert gp.tn(2, 3, 4) == gp(2, 3, 4)[-1]


def test_gp_sn():
    assert gp.sn(2, 3, 4) == 80
    assert gp.sn(2, 3, 4) == sum(gp(2, 3, 4))


def test_gp_sn_with_ratio_one():
    assert gp.sn(5, 1, 4) == 20


def test_hp_sequence():
    result = hp(2, 3, 4)
    assert result[0] == 2.0
    assert len(result) == 4


def test_hp_tn():
    assert abs(hp.tn(2, 3, 4) - hp(2, 3, 4)[-1]) < 1e-9


def test_hp_sn():
    assert abs(hp.sn(2, 3, 4) - sum(hp(2, 3, 4))) < 1e-9


def test_sequences_consistency_across_n():
    for i in range(1, 6):
        assert ap.tn(5, 2, i) == ap(5, 2, i)[-1]
        assert ap.sn(5, 2, i) == sum(ap(5, 2, i))
        assert gp.tn(1, 2, i) == gp(1, 2, i)[-1]
        assert gp.sn(1, 2, i) == sum(gp(1, 2, i))
        assert abs(hp.tn(4, 1, i) - hp(4, 1, i)[-1]) < 1e-9
        assert abs(hp.sn(4, 1, i) - sum(hp(4, 1, i))) < 1e-9


# ---------------------------------------------------------------------------
# Averages, Mode, Median
# ---------------------------------------------------------------------------

def test_avg():
    assert abs(avg(10, 12, 13) - 11.666666666666666) < 1e-9


def test_avg_requires_at_least_one():
    with pytest.raises(ValueError):
        avg()


def test_avgc_single_pair():
    assert avgc(5, 3) == 5.0


def test_avgc_multiple_pairs():
    assert avgc(5, 3, 10, 2) == 7.0


def test_avgc_odd_args_raises():
    with pytest.raises(ValueError):
        avgc(5, 3, 10)


def test_mode_single():
    assert mode(1, 2, 2, 3) == [2]


def test_mode_multimodal():
    assert mode(1, 1, 2, 2) == [1, 2]


def test_median_odd_count():
    assert median(1, 3, 2) == 2


def test_median_even_count():
    assert median(1, 2, 3, 4) == 2.5


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------

def test_hyp():
    assert hyp(3, 4) == 5.0


def test_slope():
    assert slope((1, 2), (3, 4)) == 1.0


def test_slope_vertical_line_raises():
    with pytest.raises(ValueError):
        slope((2, 5), (2, 9))


def test_centroid():
    result = centroid((1, 2), (3, 2), (4, 5))
    assert abs(result[0] - 2.6666666666666665) < 1e-9
    assert result[1] == 3.0


def test_dist():
    assert dist((6, 2), (10, 5)) == 5.0


# ---------------------------------------------------------------------------
# Equations
# ---------------------------------------------------------------------------

def test_eqn_l_two_unknowns():
    x, y = eqn.l((2, 3, 5), (7, 6, 10))
    assert abs(2 * x + 3 * y - 5) < 1e-9
    assert abs(7 * x + 6 * y - 10) < 1e-9


def test_eqn_l_three_unknowns():
    a, b, c = eqn.l((1, 1, 1, 6), (2, -1, 1, 3), (1, 2, -1, 2))
    assert abs(a - 1.0) < 1e-9
    assert abs(b - 2.0) < 1e-9
    assert abs(c - 3.0) < 1e-9


def test_eqn_l_mismatched_size_raises():
    with pytest.raises(ValueError):
        eqn.l((1, 2), (3, 2))


def test_eqn_q_quadratic_real_roots():
    roots = eqn.q(1, -3, 2)
    real_parts = sorted(r.real for r in roots)
    assert abs(real_parts[0] - 1.0) < 1e-9
    assert abs(real_parts[1] - 2.0) < 1e-9


def test_eqn_q_quartic_returns_four_roots():
    roots = eqn.q(3, 4, 6, 9, 10)
    assert len(roots) == 4


def test_eqn_q_sum():
    assert abs(eqn.q.sum(5, 2, 3) - (-0.4)) < 1e-9


def test_eqn_q_mul():
    assert abs(eqn.q.mul(5, 2, 3) - 0.6) < 1e-9


# ---------------------------------------------------------------------------
# Log, exponent, roots
# ---------------------------------------------------------------------------

def test_log_natural():
    assert abs(log(math.e) - 1.0) < 1e-9


def test_log_with_base():
    assert abs(log(8, 2) - 3.0) < 1e-9


def test_exp_positive():
    assert exp(2, 5) == 32


def test_exp_negative():
    assert exp(2, -1) == 0.5


def test_sqrt():
    assert sqrt(16) == 4.0


def test_curt():
    assert abs(curt(27) - 3.0) < 1e-9


def test_curt_negative():
    assert abs(curt(-27) - (-3.0)) < 1e-9


def test_sqrt_negative_raises():
    with pytest.raises(ValueError):
        sqrt(-16)


# ---------------------------------------------------------------------------
# Trigonometry
# ---------------------------------------------------------------------------

def test_sin_degrees():
    assert abs(sin(30) - 0.5) < 1e-9


def test_cos_degrees():
    assert abs(cos(60) - 0.5) < 1e-9


def test_tan_degrees():
    assert abs(tan(45) - 1.0) < 1e-9


def test_cosec():
    assert abs(cosec(30) - 2.0) < 1e-9


def test_sec():
    assert abs(sec(60) - 2.0) < 1e-9


def test_cot():
    assert abs(cot(45) - 1.0) < 1e-9


def test_sin_radians_mode():
    assert abs(sin(math.pi / 2, mode="rad") - 1.0) < 1e-9