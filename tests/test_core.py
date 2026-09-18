from fyrefly import add, mul, div, mod


def test_add():
    assert add(5, 4, 6, 10) == 25
    assert add() == 0
    assert add(7) == 7


def test_mul():
    assert mul(5, 4, 6, 10) == 1200
    assert mul() == 1
    assert mul(7) == 7


def test_div():
    assert div(100, 5, 2) == 10.0
    assert div(9) == 9


def test_mod():
    assert mod(17, 5) == 2
    assert mod(100, 9) == 1
    assert mod(9) == 9
