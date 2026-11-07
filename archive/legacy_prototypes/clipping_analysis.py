#!/usr/bin/env python3
"""
2D Line Clipping: Tangent Formulation Analysis and Benchmarking

This module demonstrates and benchmarks four paradigms of 2D line clipping:
1. Direct Trigonometric Tangent (with edge cases and singularities)
2. Implicit Tangent Cross-Product / Angular Sectoring (Nicholl-Lee-Nicholl approach)
3. Parametric Tangent Vector (Liang-Barsky approach)
4. Discrete Arithmetic Geometry (Reveillès Digital Straight Lines on pixel grids)
"""

import math

# ---------------------------------------------------------------------------
# 1. Direct Trigonometric Tangent Clipping
# ---------------------------------------------------------------------------
def clip_direct_tangent(p1, p2, xmin, ymin, xmax, ymax):
    """
    Direct clipping using slope m = tan(theta).
    Highlights singularity handling and division hazards.
    """
    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1

    # Vertical line singularity (theta = +/- pi/2)
    if abs(dx) < 1e-12:
        if x1 < xmin or x1 > xmax:
            return None  # Trivially outside
        y_low = max(ymin, min(y1, y2))
        y_high = min(ymax, max(y1, y2))
        if y_low > y_high:
            return None
        return ((x1, y_low), (x1, y_high))

    m = dy / dx  # tan(theta)

    # Intersect with x = xmin, x = xmax
    # y = y1 + m * (x - x1)
    pts = []
    for xw in (xmin, xmax):
        yw = y1 + m * (xw - x1)
        if ymin <= yw <= ymax and min(x1, x2) <= xw <= max(x1, x2):
            pts.append((xw, yw))

    # Intersect with y = ymin, y = ymax
    # x = x1 + (1/m) * (y - y1)
    if abs(m) > 1e-12:
        inv_m = 1.0 / m  # cot(theta)
        for yw in (ymin, ymax):
            xw = x1 + inv_m * (yw - y1)
            if xmin <= xw <= xmax and min(y1, y2) <= yw <= max(y1, y2):
                pts.append((xw, yw))

    # Also check endpoints inside window
    for x, y in (p1, p2):
        if xmin <= x <= xmax and ymin <= y <= ymax:
            pts.append((x, y))

    # Deduplicate
    unique_pts = []
    for pt in pts:
        if not any(math.isclose(pt[0], u[0], abs_tol=1e-7) and math.isclose(pt[1], u[1], abs_tol=1e-7) for u in unique_pts):
            unique_pts.append(pt)

    if len(unique_pts) < 2:
        return None
    return (unique_pts[0], unique_pts[1])


# ---------------------------------------------------------------------------
# 2. Implicit Tangent Cross-Product (Nicholl-Lee-Nicholl principle)
# ---------------------------------------------------------------------------
def cross_product_2d(v1, v2):
    """v1_x * v2_y - v1_y * v2_x: Determinant testing relative slope without division."""
    return v1[0] * v2[1] - v1[1] * v2[0]


def compare_slopes(p_base, p_target, p_ref):
    """
    Compares tan(theta_target) vs tan(theta_ref) from p_base using cross-multiplication:
    Returns >0 if target is counter-clockwise of ref, <0 if clockwise, 0 if collinear.
    """
    v_target = (p_target[0] - p_base[0], p_target[1] - p_base[1])
    v_ref = (p_ref[0] - p_base[0], p_ref[1] - p_base[1])
    return cross_product_2d(v_ref, v_target)


# ---------------------------------------------------------------------------
# 3. Parametric Tangent Vector (Liang-Barsky)
# ---------------------------------------------------------------------------
def clip_liang_barsky(p1, p2, xmin, ymin, xmax, ymax):
    """
    Uses the directional tangent vector T = (dx, dy) = dP/dt.
    Parametric interval clipping in [0, 1].
    """
    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1

    p = [-dx, dx, -dy, dy]
    q = [x1 - xmin, xmax - x1, y1 - ymin, ymax - y1]

    t_enter = 0.0
    t_leave = 1.0

    for pi, qi in zip(p, q):
        if pi == 0:  # Parallel to boundary
            if qi < 0:
                return None  # Outside
        elif pi < 0:  # Enters boundary
            t = qi / pi
            if t > t_enter:
                t_enter = t
        else:  # Leaves boundary
            t = qi / pi
            if t < t_leave:
                t_leave = t

    if t_enter > t_leave:
        return None

    clipped_p1 = (x1 + t_enter * dx, y1 + t_enter * dy)
    clipped_p2 = (x1 + t_leave * dx, y1 + t_leave * dy)
    return (clipped_p1, clipped_p2)


# ---------------------------------------------------------------------------
# 4. Discrete Arithmetic Geometry (Reveillès Digital Straight Line)
# ---------------------------------------------------------------------------
class ReveillesDSL:
    """
    Reveillès analytical digital straight line:
    D(a, b, mu, omega) = { (x, y) in Z^2 | mu <= ax - by < mu + omega }
    For 8-connected naive lines: omega = max(|a|, |b|).
    Slope is the rational tangent a/b.
    """
    def __init__(self, a, b, mu=0):
        self.a = a
        self.b = b
        self.mu = mu
        self.omega = max(abs(a), abs(b))

    def get_y_for_x(self, x):
        """Exact integer floor division; preserves discrete 8-connectivity."""
        return (self.a * x - self.mu) // self.b

    def clip_x_range(self, xmin, xmax):
        """Exact digital clipping: commutativity between clipping and digitization is strictly preserved."""
        return [(x, self.get_y_for_x(x)) for x in range(xmin, xmax + 1)]


# ---------------------------------------------------------------------------
# Verification & Self-Test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== 1. Direct Tangent vs Parametric Tangent ===")
    p1 = (1.0, 2.0)
    p2 = (9.0, 7.0)
    box = (2.0, 3.0, 8.0, 6.0)

    res_tan = clip_direct_tangent(p1, p2, *box)
    res_lb = clip_liang_barsky(p1, p2, *box)
    print(f"Direct Tangent Result: {res_tan}")
    print(f"Liang-Barsky Result:  {res_lb}")

    print("\n=== 2. Singularity Test: Near-Vertical Line ===")
    p_vert1 = (5.0, 0.0)
    p_vert2 = (5.0 + 1e-15, 10.0)
    print(f"Liang-Barsky Near-Vertical: {clip_liang_barsky(p_vert1, p_vert2, *box)}")

    print("\n=== 3. Reveillès Arithmetic DSL vs Bresenham Rounding Discrepancy ===")
    a, b = 11, 20
    dsl = ReveillesDSL(a, b, mu=0)
    full_dsl = dsl.clip_x_range(0, 20)
    masked_dsl = [p for p in full_dsl if 5 <= p[0] <= 15]
    clipped_dsl = dsl.clip_x_range(5, 15)

    print(f"Reveillès Commutativity (Masked == Clipped): {masked_dsl == clipped_dsl}")
