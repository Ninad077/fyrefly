import math
import pytest
from fyrefly import (
    circle, semicircle, square, rectangle, triangle, equilateral_triangle,
    parallelogram, rhombus, kite, trapezoid, ellipse, polygon, sector, annulus,
    cube, cuboid, sphere, hemisphere, cylinder, cone, frustum, pyramid, prism, torus,
)


def test_circle():
    assert circle.area(7) == pytest.approx(math.pi * 49)
    assert circle.perimeter(7) == pytest.approx(2 * math.pi * 7)


def test_semicircle():
    assert semicircle.area(7) == pytest.approx((math.pi * 49) / 2)
    assert semicircle.perimeter(7) == pytest.approx(math.pi * 7 + 14)


def test_square():
    assert square.area(5) == 25
    assert square.perimeter(5) == 20


def test_rectangle():
    assert rectangle.area(4, 6) == 24
    assert rectangle.perimeter(4, 6) == 20


def test_triangle():
    assert triangle.area(10, 5) == 25.0
    assert triangle.area_sides(3, 4, 5) == pytest.approx(6.0)
    assert triangle.perimeter(3, 4, 5) == 12


def test_triangle_invalid_sides_raises():
    with pytest.raises(ValueError):
        triangle.area_sides(1, 1, 10)


def test_equilateral_triangle():
    assert equilateral_triangle.area(4) == pytest.approx((math.sqrt(3) / 4) * 16)
    assert equilateral_triangle.perimeter(4) == 12


def test_parallelogram():
    assert parallelogram.area(10, 5) == 50
    assert parallelogram.perimeter(10, 5) == 30


def test_rhombus():
    assert rhombus.area(6, 8) == 24.0
    assert rhombus.perimeter(5) == 20


def test_kite():
    assert kite.area(6, 8) == 24.0
    assert kite.perimeter(5, 7) == 24


def test_trapezoid():
    assert trapezoid.area(8, 5, 4) == 26.0
    assert trapezoid.perimeter(8, 5, 3, 4) == 20


def test_ellipse():
    assert ellipse.area(5, 3) == pytest.approx(math.pi * 15)
    assert ellipse.perimeter(7, 7) == pytest.approx(circle.perimeter(7))


def test_polygon():
    assert polygon.area(4, 5) == pytest.approx(square.area(5))
    assert polygon.perimeter(6, 4) == 24


def test_sector():
    assert sector.area(7, 90) == pytest.approx((90 / 360) * math.pi * 49)
    assert sector.arc_length(7, 90) == pytest.approx((90 / 360) * 2 * math.pi * 7)


def test_annulus():
    assert annulus.area(10, 6) == pytest.approx(math.pi * (100 - 36))


def test_cube():
    assert cube.volume(3) == 27
    assert cube.lsa(3) == 36
    assert cube.tsa(3) == 54


def test_cuboid():
    assert cuboid.volume(2, 3, 4) == 24
    assert cuboid.lsa(2, 3, 4) == 40
    assert cuboid.tsa(2, 3, 4) == 52


def test_sphere():
    assert sphere.volume(3) == pytest.approx((4 / 3) * math.pi * 27)
    assert sphere.surface_area(3) == pytest.approx(4 * math.pi * 9)


def test_hemisphere():
    assert hemisphere.volume(3) == pytest.approx((2 / 3) * math.pi * 27)
    assert hemisphere.csa(3) == pytest.approx(2 * math.pi * 9)
    assert hemisphere.tsa(3) == pytest.approx(3 * math.pi * 9)


def test_cylinder():
    assert cylinder.volume(3, 7) == pytest.approx(math.pi * 9 * 7)
    assert cylinder.csa(3, 7) == pytest.approx(2 * math.pi * 3 * 7)
    assert cylinder.tsa(3, 7) == pytest.approx(2 * math.pi * 3 * (7 + 3))


def test_cone():
    assert cone.volume(3, 4) == pytest.approx((1 / 3) * math.pi * 9 * 4)
    assert cone.csa(3, 4) == pytest.approx(math.pi * 3 * 5)
    assert cone.tsa(3, 4) == pytest.approx(math.pi * 3 * (5 + 3))


def test_frustum():
    assert frustum.volume(3, 5, 6) == pytest.approx((1 / 3) * math.pi * 6 * (9 + 25 + 15))
    slant = math.sqrt(6 ** 2 + (3 - 5) ** 2)
    assert frustum.csa(3, 5, 6) == pytest.approx(math.pi * (3 + 5) * slant)
    assert frustum.tsa(3, 5, 6) == pytest.approx(frustum.csa(3, 5, 6) + math.pi * 9 + math.pi * 25)


def test_pyramid():
    assert pyramid.volume(6, 8) == pytest.approx(96.0)
    slant = math.sqrt(8 ** 2 + 3 ** 2)
    assert pyramid.lsa(6, 8) == pytest.approx(2 * 6 * slant)
    assert pyramid.tsa(6, 8) == pytest.approx(2 * 6 * slant + 36)


def test_prism():
    assert prism.volume(20, 10) == 200
    assert prism.lsa(18, 10) == 180
    assert prism.tsa(20, 18, 10) == 220


def test_torus():
    assert torus.volume(5, 2) == pytest.approx(2 * (math.pi ** 2) * 5 * 4)
    assert torus.surface_area(5, 2) == pytest.approx(4 * (math.pi ** 2) * 5 * 2)