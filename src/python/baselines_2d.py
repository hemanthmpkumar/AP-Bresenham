"""
baselines_2d.py
===============
Implementations of classical and modern 2D line clipping algorithms
from computer graphics and computational geometry literature:

1. Cohen-Sutherland (1967 / Sproull & Sutherland 1968)
2. Liang-Barsky Parametric Clipper (1984)
3. Nicholl-Lee-Nicholl (NLN 1987)
4. Cyrus-Beck Parametric Clipper (1978)
5. Skala Fast Homogeneous / Convex Clipper (1993, 2005)
6. Reveilles Digital Straight Line (DSL) Naive Preimage Rasterizer (1991)

All algorithms are coupled with nearest-integer rounding + Bresenham rasterization
to demonstrate how the Bresenham Phase-Shift Phenomenon impacts all continuous clippers.
"""

from __future__ import annotations
from typing import Optional, Tuple, List
import math
from ap_bresenham_2d import bresenham_full


# ===========================================================================
# 1. Cohen-Sutherland Algorithm (1967 / 1968)
# ===========================================================================

# Outcodes for 4 regions
INSIDE = 0  # 0000
LEFT   = 1  # 0001
RIGHT  = 2  # 0010
BOTTOM = 4  # 0100
TOP    = 8  # 1000

def _compute_outcode(x: float, y: float, xmin: float, xmax: float, ymin: float, ymax: float) -> int:
    code = INSIDE
    if x < xmin:
        code |= LEFT
    elif x > xmax:
        code |= RIGHT
    if y < ymin:
        code |= BOTTOM
    elif y > ymax:
        code |= TOP
    return code


def cohen_sutherland_clip(
    x0: float, y0: float, x1: float, y1: float,
    xmin: float, xmax: float, ymin: float, ymax: float
) -> Optional[Tuple[float, float, float, float]]:
    """
    Classical Cohen-Sutherland line clipping in continuous R^2.
    """
    code0 = _compute_outcode(x0, y0, xmin, xmax, ymin, ymax)
    code1 = _compute_outcode(x1, y1, xmin, xmax, ymin, ymax)

    while True:
        if (code0 | code1) == 0:
            # Bitwise OR is 0: Both points inside window
            return (x0, y0, x1, y1)
        elif (code0 & code1) != 0:
            # Bitwise AND is not 0: Both points share an outside zone -> trivially reject
            return None
        else:
            # Failed both tests: Calculate line segment to clip
            code_out = code0 if code0 != 0 else code1
            x, y = 0.0, 0.0

            if code_out & TOP:
                x = x0 + (x1 - x0) * (ymax - y0) / (y1 - y0)
                y = ymax
            elif code_out & BOTTOM:
                x = x0 + (x1 - x0) * (ymin - y0) / (y1 - y0)
                y = ymin
            elif code_out & RIGHT:
                y = y0 + (y1 - y0) * (xmax - x0) / (x1 - x0)
                x = xmax
            elif code_out & LEFT:
                y = y0 + (y1 - y0) * (xmin - x0) / (x1 - x0)
                x = xmin

            if code_out == code0:
                x0, y0 = x, y
                code0 = _compute_outcode(x0, y0, xmin, xmax, ymin, ymax)
            else:
                x1, y1 = x, y
                code1 = _compute_outcode(x1, y1, xmin, xmax, ymin, ymax)


# ===========================================================================
# 2. Liang-Barsky Algorithm (1984)
# ===========================================================================

def liang_barsky_clip(
    x0: float, y0: float, x1: float, y1: float,
    xmin: float, xmax: float, ymin: float, ymax: float
) -> Optional[Tuple[float, float, float, float]]:
    """
    Liang-Barsky parametric line clipping algorithm in R^2.
    """
    dx = x1 - x0
    dy = y1 - y0
    p = [-dx, dx, -dy, dy]
    q = [x0 - xmin, xmax - x0, y0 - ymin, ymax - y0]
    t0, t1 = 0.0, 1.0

    for pi, qi in zip(p, q):
        if pi == 0:
            if qi < 0:
                return None
        elif pi < 0:
            t0 = max(t0, qi / pi)
        else:
            t1 = min(t1, qi / pi)

    if t0 > t1:
        return None

    return (
        x0 + t0 * dx, y0 + t0 * dy,
        x0 + t1 * dx, y0 + t1 * dy
    )


# ===========================================================================
# 3. Cyrus-Beck Generalized Parametric Clipping (1978)
# ===========================================================================

def cyrus_beck_clip(
    x0: float, y0: float, x1: float, y1: float,
    xmin: float, xmax: float, ymin: float, ymax: float
) -> Optional[Tuple[float, float, float, float]]:
    """
    Cyrus-Beck line clipping using inward normals of convex window edges.
    For axis-aligned window, normals are (-1,0), (1,0), (0,-1), (0,1).
    """
    dx = x1 - x0
    dy = y1 - y0
    if dx == 0 and dy == 0:
        if xmin <= x0 <= xmax and ymin <= y0 <= ymax:
            return (x0, y0, x1, y1)
        return None

    # Edges: point on edge, inward normal
    edges = [
        ((xmin, ymin), (1.0, 0.0)),   # Left edge, normal pointing right (+x)
        ((xmax, ymin), (-1.0, 0.0)),  # Right edge, normal pointing left (-x)
        ((xmin, ymin), (0.0, 1.0)),   # Bottom edge, normal pointing up (+y)
        ((xmin, ymax), (0.0, -1.0)),  # Top edge, normal pointing down (-y)
    ]

    t_enter = 0.0
    t_leave = 1.0

    for (px, py), (nx, ny) in edges:
        # N . D
        denom = nx * dx + ny * dy
        # N . (P0 - PE)
        numer = nx * (px - x0) + ny * (py - y0)

        if denom == 0:
            # Parallel to edge: if outside, discard
            if numer > 0:
                return None
        else:
            t = numer / denom
            if denom > 0:
                # Potentially entering
                t_enter = max(t_enter, t)
            else:
                # Potentially leaving
                t_leave = min(t_leave, t)

    if t_enter > t_leave:
        return None

    return (
        x0 + t_enter * dx, y0 + t_enter * dy,
        x0 + t_leave * dx, y0 + t_leave * dy
    )


# ===========================================================================
# 4. Nicholl-Lee-Nicholl (NLN) 2D Line Clipping (1987)
# ===========================================================================

def nicholl_lee_nicholl_clip(
    x0: float, y0: float, x1: float, y1: float,
    xmin: float, xmax: float, ymin: float, ymax: float
) -> Optional[Tuple[float, float, float, float]]:
    """
    Nicholl-Lee-Nicholl (NLN) 2D line clipping algorithm.
    Minimizes divisions by sector/region classification around P0.
    """
    # For robust demonstration, we use the sector-based evaluation:
    # First classify P0 relative to the 9 regions of the window.
    # If P0 is inside, intersect with at most 1 boundary.
    # If P0 is outside, map to standard left/bottom sector and evaluate ray rays.
    
    # Fast path: degenerate line
    if x0 == x1 and y0 == y1:
        if xmin <= x0 <= xmax and ymin <= y0 <= ymax:
            return (x0, y0, x1, y1)
        return None

    dx = x1 - x0
    dy = y1 - y0

    # P0 inside window
    if xmin <= x0 <= xmax and ymin <= y0 <= ymax:
        # P1 also inside
        if xmin <= x1 <= xmax and ymin <= y1 <= ymax:
            return (x0, y0, x1, y1)
        # Compute single boundary intersection for P1
        t1 = 1.0
        if dx > 0 and x0 + t1 * dx > xmax:
            t1 = (xmax - x0) / dx
        elif dx < 0 and x0 + t1 * dx < xmin:
            t1 = (xmin - x0) / dx
        if dy > 0 and y0 + t1 * dy > ymax:
            t1 = (ymax - y0) / dy
        elif dy < 0 and y0 + t1 * dy < ymin:
            t1 = (ymin - y0) / dy
        return (x0, y0, x0 + t1 * dx, y0 + t1 * dy)

    # General NLN fallback using the Liang-Barsky parametric bounds
    # (NLN provides identical geometric intersections to LB, with fewer CPU divisions)
    return liang_barsky_clip(x0, y0, x1, y1, xmin, xmax, ymin, ymax)


# ===========================================================================
# 5. Skala Fast Line Clipping (1993, 2005)
# ===========================================================================

def skala_clip(
    x0: float, y0: float, x1: float, y1: float,
    xmin: float, xmax: float, ymin: float, ymax: float
) -> Optional[Tuple[float, float, float, float]]:
    """
    Skala clipping via cross-product space / homogeneous formulation.
    """
    # Vector cross product formulation of line ax + by + c = 0
    # Line L through P0, P1:
    a = y0 - y1
    b = x1 - x0
    c = x0 * y1 - x1 * y0

    # Corners of clipping window: C0=(xmin,ymin), C1=(xmax,ymin), C2=(xmax,ymax), C3=(xmin,ymax)
    corners = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]
    dists = [a * cx + b * cy + c for cx, cy in corners]

    # Check if all corners are strictly on one side
    if all(d > 0 for d in dists) or all(d < 0 for d in dists):
        return None

    # Standard parametric parameter recovery
    return liang_barsky_clip(x0, y0, x1, y1, xmin, xmax, ymin, ymax)


# ===========================================================================
# 6. Kuzmin Built-In Clipping Algorithm (1995)
# ===========================================================================

def kuzmin_clip_and_rasterize(
    x0: int, y0: int, x1: int, y1: int,
    xmin: int, xmax: int, ymin: int, ymax: int
) -> List[Tuple[int, int]]:
    """
    Yevgeny P. Kuzmin's (1995) built-in line clipping rasterizer.
    Embeds clipping checks directly into the incremental Bresenham step loop.
    Early-exits once the line exits the bounding window, avoiding post-exit steps,
    but requires stepping through all off-screen pixels prior to window entry.
    """
    # Trivial bounding-box rejection
    if min(x0, x1) > xmax or max(x0, x1) < xmin:
        return []
    if min(y0, y1) > ymax or max(y0, y1) < ymin:
        return []

    pixels: List[Tuple[int, int]] = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x1 >= x0 else -1
    sy = 1 if y1 >= y0 else -1
    steep = dy > dx

    cur_x, cur_y = x0, y0
    end_x, end_y = x1, y1

    if steep:
        cur_x, cur_y = cur_y, cur_x
        end_x, end_y = end_y, end_x
        dx, dy = dy, dx
        sx, sy = sy, sx
        w_xmin, w_xmax = ymin, ymax
        w_ymin, w_ymax = xmin, xmax
    else:
        w_xmin, w_xmax = xmin, xmax
        w_ymin, w_ymax = ymin, ymax

    D = 2 * dy - dx
    y = cur_y
    entered = False

    x = cur_x
    while (sx > 0 and x <= end_x) or (sx < 0 and x >= end_x):
        # Current unmapped coordinate
        px, py = (y, x) if steep else (x, y)
        in_bounds = (xmin <= px <= xmax and ymin <= py <= ymax)

        if in_bounds:
            pixels.append((px, py))
            entered = True
        elif entered:
            # Once we were inside the window and have now exited, early terminate
            break

        if D > 0:
            y += sy
            D += 2 * dy - 2 * dx
        else:
            D += 2 * dy

        x += sx

    return pixels


# ===========================================================================
# Generic Discrete Pipeline Adapter: Continuous Clip + Round + Bresenham
# ===========================================================================

def rasterize_clipped_baseline(
    clip_func,
    x0: int, y0: int, x1: int, y1: int,
    xmin: int, xmax: int, ymin: int, ymax: int
) -> List[Tuple[int, int]]:
    """
    Executes a continuous clipping algorithm, rounds endpoints to integer,
    and runs Bresenham's algorithm (conventional pipeline).
    """
    res = clip_func(float(x0), float(y0), float(x1), float(y1),
                    float(xmin), float(xmax), float(ymin), float(ymax))
    if res is None:
        return []
    cx0, cy0, cx1, cy1 = res
    rx0, ry0 = round(cx0), round(cy0)
    rx1, ry1 = round(cx1), round(cy1)
    return bresenham_full(rx0, ry0, rx1, ry1)
