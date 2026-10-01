import math


# ===========================================================================
# 2D Shapes — area() and perimeter()
# ===========================================================================

class _Circle:
    def area(self, r):
        """Area of a circle: pi * r^2"""
        return math.pi * r ** 2

    def perimeter(self, r):
        """Circumference of a circle: 2 * pi * r"""
        return 2 * math.pi * r


class _Semicircle:
    def area(self, r):
        """Area of a semicircle: (pi * r^2) / 2"""
        return (math.pi * r ** 2) / 2

    def perimeter(self, r):
        """Perimeter of a semicircle: curved edge + diameter = pi*r + 2*r"""
        return math.pi * r + 2 * r


class _Square:
    def area(self, s):
        """Area of a square: s^2"""
        return s ** 2

    def perimeter(self, s):
        """Perimeter of a square: 4 * s"""
        return 4 * s


class _Rectangle:
    def area(self, l, w):
        """Area of a rectangle: l * w"""
        return l * w

    def perimeter(self, l, w):
        """Perimeter of a rectangle: 2 * (l + w)"""
        return 2 * (l + w)


class _Triangle:
    def area(self, base, height):
        """Area of a triangle from base and height: 0.5 * base * height"""
        return 0.5 * base * height

    def area_sides(self, a, b, c):
        """Area of a triangle from its three sides, using Heron's formula."""
        s = (a + b + c) / 2
        value = s * (s - a) * (s - b) * (s - c)
        if value < 0:
            raise ValueError(f"Sides {a}, {b}, {c} cannot form a valid triangle")
        return math.sqrt(value)

    def perimeter(self, a, b, c):
        """Perimeter of a triangle: a + b + c"""
        return a + b + c


class _EquilateralTriangle:
    def area(self, s):
        """Area of an equilateral triangle: (sqrt(3)/4) * s^2"""
        return (math.sqrt(3) / 4) * s ** 2

    def perimeter(self, s):
        """Perimeter of an equilateral triangle: 3 * s"""
        return 3 * s


class _Parallelogram:
    def area(self, base, height):
        """Area of a parallelogram: base * height"""
        return base * height

    def perimeter(self, a, b):
        """Perimeter of a parallelogram: 2 * (a + b)"""
        return 2 * (a + b)


class _Rhombus:
    def area(self, d1, d2):
        """Area of a rhombus from its diagonals: 0.5 * d1 * d2"""
        return 0.5 * d1 * d2

    def perimeter(self, s):
        """Perimeter of a rhombus: 4 * s"""
        return 4 * s


class _Kite:
    def area(self, d1, d2):
        """Area of a kite from its diagonals: 0.5 * d1 * d2"""
        return 0.5 * d1 * d2

    def perimeter(self, a, b):
        """Perimeter of a kite from its two distinct side lengths: 2 * (a + b)"""
        return 2 * (a + b)


class _Trapezoid:
    def area(self, a, b, height):
        """Area of a trapezoid from its two parallel sides and height: 0.5 * (a + b) * height"""
        return 0.5 * (a + b) * height

    def perimeter(self, a, b, c, d):
        """Perimeter of a trapezoid: sum of all four sides"""
        return a + b + c + d


class _Ellipse:
    def area(self, a, b):
        """Area of an ellipse: pi * a * b"""
        return math.pi * a * b

    def perimeter(self, a, b):
        """
        Approximate perimeter of an ellipse using Ramanujan's formula
        (extremely accurate — no exact closed-form formula exists for
        an ellipse's perimeter).
        """
        h = ((a - b) ** 2) / ((a + b) ** 2)
        return math.pi * (a + b) * (1 + (3 * h) / (10 + math.sqrt(4 - 3 * h)))


class _Polygon:
    def area(self, n_sides, length):
        """Area of a regular polygon: (n * length^2) / (4 * tan(pi/n))"""
        return (n_sides * length ** 2) / (4 * math.tan(math.pi / n_sides))

    def perimeter(self, n_sides, length):
        """Perimeter of a regular polygon: n * length"""
        return n_sides * length


class _Sector:
    def area(self, r, angle):
        """Area of a circular sector, angle in degrees: (angle/360) * pi * r^2"""
        return (angle / 360) * math.pi * r ** 2

    def arc_length(self, r, angle):
        """Arc length of a circular sector, angle in degrees: (angle/360) * 2 * pi * r"""
        return (angle / 360) * 2 * math.pi * r


class _Annulus:
    def area(self, outer_r, inner_r):
        """Area of an annulus (ring): pi * (outer_r^2 - inner_r^2)"""
        return math.pi * (outer_r ** 2 - inner_r ** 2)


circle = _Circle()
semicircle = _Semicircle()
square = _Square()
rectangle = _Rectangle()
triangle = _Triangle()
equilateral_triangle = _EquilateralTriangle()
parallelogram = _Parallelogram()
rhombus = _Rhombus()
kite = _Kite()
trapezoid = _Trapezoid()
ellipse = _Ellipse()
polygon = _Polygon()
sector = _Sector()
annulus = _Annulus()


# ===========================================================================
# 3D Shapes — volume() and tsa()/csa()/lsa() (or surface_area() where
# there's no TSA/CSA distinction)
# ===========================================================================

class _Cube:
    def volume(self, s):
        """Volume of a cube: s^3"""
        return s ** 3

    def lsa(self, s):
        """Lateral Surface Area of a cube (4 side faces, excludes top/bottom): 4 * s^2"""
        return 4 * s ** 2

    def tsa(self, s):
        """Total Surface Area of a cube (all 6 faces): 6 * s^2"""
        return 6 * s ** 2


class _Cuboid:
    def volume(self, l, w, h):
        """Volume of a cuboid: l * w * h"""
        return l * w * h

    def lsa(self, l, w, h):
        """Lateral Surface Area of a cuboid (4 side faces, excludes top/bottom): 2*h*(l+w)"""
        return 2 * h * (l + w)

    def tsa(self, l, w, h):
        """Total Surface Area of a cuboid (all 6 faces): 2*(l*w + w*h + h*l)"""
        return 2 * (l * w + w * h + h * l)


class _Sphere:
    def volume(self, r):
        """Volume of a sphere: (4/3) * pi * r^3"""
        return (4 / 3) * math.pi * r ** 3

    def surface_area(self, r):
        """Surface area of a sphere: 4 * pi * r^2 (no TSA/CSA split — the whole surface is uniform)"""
        return 4 * math.pi * r ** 2


class _Hemisphere:
    def volume(self, r):
        """Volume of a hemisphere: (2/3) * pi * r^3"""
        return (2 / 3) * math.pi * r ** 3

    def csa(self, r):
        """Curved Surface Area of a hemisphere (dome only, excludes the flat circular base): 2 * pi * r^2"""
        return 2 * math.pi * r ** 2

    def tsa(self, r):
        """Total Surface Area of a hemisphere (dome + flat base): 3 * pi * r^2"""
        return 3 * math.pi * r ** 2


class _Cylinder:
    def volume(self, r, h):
        """Volume of a cylinder: pi * r^2 * h"""
        return math.pi * r ** 2 * h

    def csa(self, r, h):
        """Curved Surface Area of a cylinder (side only, excludes the two circular ends): 2 * pi * r * h"""
        return 2 * math.pi * r * h

    def tsa(self, r, h):
        """Total Surface Area of a cylinder (side + both circular ends): 2*pi*r*(h + r)"""
        return 2 * math.pi * r * (h + r)


class _Cone:
    def volume(self, r, h):
        """Volume of a cone: (1/3) * pi * r^2 * h"""
        return (1 / 3) * math.pi * r ** 2 * h

    def _slant(self, r, h):
        return math.sqrt(r ** 2 + h ** 2)

    def csa(self, r, h):
        """Curved Surface Area of a cone (excludes the circular base): pi * r * slant_height
        (slant height is computed internally from r and h)."""
        return math.pi * r * self._slant(r, h)

    def tsa(self, r, h):
        """Total Surface Area of a cone (curved + circular base): pi*r*(slant_height + r)"""
        slant = self._slant(r, h)
        return math.pi * r * (slant + r)


class _Frustum:
    def volume(self, r1, r2, h):
        """Volume of a frustum (of a cone): (1/3) * pi * h * (r1^2 + r2^2 + r1*r2)"""
        return (1 / 3) * math.pi * h * (r1 ** 2 + r2 ** 2 + r1 * r2)

    def _slant(self, r1, r2, h):
        return math.sqrt(h ** 2 + (r1 - r2) ** 2)

    def csa(self, r1, r2, h):
        """Curved Surface Area of a frustum (excludes both circular ends): pi*(r1+r2)*slant_height
        (slant height is computed internally from r1, r2, and h)."""
        return math.pi * (r1 + r2) * self._slant(r1, r2, h)

    def tsa(self, r1, r2, h):
        """Total Surface Area of a frustum (curved + both circular ends)."""
        csa = self.csa(r1, r2, h)
        return csa + math.pi * r1 ** 2 + math.pi * r2 ** 2


class _Pyramid:
    """Square-based pyramid."""

    def volume(self, s, h):
        """Volume of a square pyramid, h = vertical height: (1/3) * s^2 * h"""
        return (1 / 3) * s ** 2 * h

    def _slant(self, s, h):
        return math.sqrt(h ** 2 + (s / 2) ** 2)

    def lsa(self, s, h):
        """Lateral Surface Area of a square pyramid (4 triangular faces, excludes the square base).
        h is the vertical height — the slant height is computed internally."""
        slant = self._slant(s, h)
        return 2 * s * slant

    def tsa(self, s, h):
        """Total Surface Area of a square pyramid (4 triangular faces + square base)."""
        return self.lsa(s, h) + s ** 2


class _Prism:
    """General prism, described by its base area and base perimeter."""

    def volume(self, base_area, h):
        """Volume of a prism: base_area * h"""
        return base_area * h

    def lsa(self, base_perimeter, h):
        """Lateral Surface Area of a prism (side faces, excludes the two bases): base_perimeter * h"""
        return base_perimeter * h

    def tsa(self, base_area, base_perimeter, h):
        """Total Surface Area of a prism (side faces + both bases)."""
        return self.lsa(base_perimeter, h) + 2 * base_area


class _Torus:
    def volume(self, R, r):
        """Volume of a torus: 2 * pi^2 * R * r^2 (R = distance from center of tube to center of torus, r = tube radius)"""
        return 2 * (math.pi ** 2) * R * r ** 2

    def surface_area(self, R, r):
        """Surface area of a torus: 4 * pi^2 * R * r (no TSA/CSA split — the whole surface is uniform)"""
        return 4 * (math.pi ** 2) * R * r


cube = _Cube()
cuboid = _Cuboid()
sphere = _Sphere()
hemisphere = _Hemisphere()
cylinder = _Cylinder()
cone = _Cone()
frustum = _Frustum()
pyramid = _Pyramid()
prism = _Prism()
torus = _Torus()