"""
Exact Analytical Phase-Compensated Bresenham Clipper (AP-Bresenham)

A novel algorithm for discrete geometry, digital topology, and pixel grids that solves
the 'Digitization Inconsistency Problem' (Bresenham Phase Shift) in 2D line clipping.

Mathematical Guarantee:
    Clip(Bresenham(L), W) === AP_Bresenham(L, W)  [100% Bit-Identical]

Authors: Research prototype for 2D Line Clipping in Discrete Geometry
"""

from typing import List, Tuple, Optional


def ceil_div(a: int, b: int) -> int:
    """Exact integer ceiling division: ceil(a / b) for positive integer b."""
    return -(-a // b)


class ExactBresenhamClipper:
    """
    Novel O(1) Analytical Phase-Compensated Bresenham Line Clipper.

    Solves the exact boundary intersection interval [k_start, k_end] in O(1) integer
    arithmetic and analytically evaluates the exact Bresenham error accumulator state
    D_start, eliminating the digitization inconsistency (phase-shift) of traditional clipping.
    """

    @staticmethod
    def clip_bounds(
        p0: Tuple[int, int],
        p1: Tuple[int, int],
        xmin: int,
        ymin: int,
        xmax: int,
        ymax: int
    ) -> Optional[Tuple[int, int, int, int, int, int, int, bool, int, int]]:
        """
        Computes the exact clipping parameters in O(1) pure integer operations.

        Returns:
            Tuple containing:
            (k_start, k_end, dx, dy, sx, sy, steep, x0_t, y0_t, D_start)
            or None if the line does not intersect the window.
        """
        x0, y0 = p0
        x1, y1 = p1

        dx_orig = x1 - x0
        dy_orig = y1 - y0

        sx = 1 if dx_orig >= 0 else -1
        sy = 1 if dy_orig >= 0 else -1

        dx = abs(dx_orig)
        dy = abs(dy_orig)

        # Handle degenerate point
        if dx == 0 and dy == 0:
            if xmin <= x0 <= xmax and ymin <= y0 <= ymax:
                # Point is inside
                return (0, 0, 0, 0, sx, sy, False, x0, y0, 0)
            return None

        steep = dy > dx
        if steep:
            # Major axis is y: swap coordinates
            x0, y0 = y0, x0
            x1, y1 = y1, x1
            dx, dy = dy, dx
            sx, sy = sy, sx
            xmin, ymin, xmax, ymax = ymin, xmin, ymax, xmax

        # Map window bounds into the canonical local coordinate space:
        # where the line runs from (0, 0) to (dx, dy) with 0 <= dy <= dx
        if sx == 1:
            w_xmin = xmin - x0
            w_xmax = xmax - x0
        else:
            w_xmin = x0 - xmax
            w_xmax = x0 - xmin

        if sy == 1:
            w_ymin = ymin - y0
            w_ymax = ymax - y0
        else:
            w_ymin = y0 - ymax
            w_ymax = y0 - ymin

        # 1. Primary axis (major axis) bounds: k in [0, dx]
        kx_min = max(0, w_xmin)
        kx_max = min(dx, w_xmax)
        if kx_min > kx_max:
            return None

        # 2. Secondary axis (minor axis) bounds in O(1) via Diophantine inversion:
        # y(k) = floor((2 * dy * k + dx - 1) / (2 * dx)) in [w_ymin, w_ymax]
        if dy == 0:
            if not (w_ymin <= 0 <= w_ymax):
                return None
            ky_min = 0
            ky_max = dx
        else:
            # Exact integer bounds
            num_min = 2 * dx * w_ymin - dx + 1
            ky_min = ceil_div(num_min, 2 * dy)

            num_max = 2 * dx * (w_ymax + 1) - dx
            ky_max = num_max // (2 * dy)

        # 3. Intersect parameter intervals
        k_start = max(kx_min, ky_min)
        k_end = min(kx_max, ky_max)

        if k_start > k_end:
            return None

        # 4. Analytical state injection at k_start in O(1)
        y_rel = (2 * dy * k_start + dx - 1) // (2 * dx)
        D_start = (2 * dy - dx) + 2 * dy * k_start - 2 * dx * y_rel

        return (k_start, k_end, dx, dy, sx, sy, steep, x0, y0, D_start)

    @classmethod
    def clip_and_rasterize(
        cls,
        p0: Tuple[int, int],
        p1: Tuple[int, int],
        xmin: int,
        ymin: int,
        xmax: int,
        ymax: int
    ) -> List[Tuple[int, int]]:
        """
        Clips the 2D line and rasterizes only the visible pixels.
        Guaranteed to be bit-identical to rasterizing the full line and masking with the window.
        """
        bounds = cls.clip_bounds(p0, p1, xmin, ymin, xmax, ymax)
        if bounds is None:
            return []

        k_start, k_end, dx, dy, sx, sy, steep, x0, y0, D_start = bounds

        if dx == 0 and dy == 0:
            return [p0]

        # Analytical start coordinates
        y_rel = (2 * dy * k_start + dx - 1) // (2 * dx)
        curr_y_rel = y_rel
        curr_D = D_start

        pts: List[Tuple[int, int]] = []
        two_dx = 2 * dx
        two_dy = 2 * dy

        for k in range(k_start, k_end + 1):
            # Transform back to original coordinate system
            orig_x = x0 + k if sx == 1 else x0 - k
            orig_y = y0 + curr_y_rel if sy == 1 else y0 - curr_y_rel

            pts.append((orig_y, orig_x) if steep else (orig_x, orig_y))

            # Exact Bresenham error step
            if curr_D > 0:
                curr_y_rel += 1
                curr_D -= two_dx
            curr_D += two_dy

        return pts

    @classmethod
    def clip_endpoints(
        cls,
        p0: Tuple[int, int],
        p1: Tuple[int, int],
        xmin: int,
        ymin: int,
        xmax: int,
        ymax: int
    ) -> Optional[Tuple[Tuple[int, int], Tuple[int, int], int]]:
        """
        Returns the exact first pixel, exact last pixel, and exact pixel count inside the window,
        computed in O(1) operations without any rasterization loop.
        """
        bounds = cls.clip_bounds(p0, p1, xmin, ymin, xmax, ymax)
        if bounds is None:
            return None

        k_start, k_end, dx, dy, sx, sy, steep, x0, y0, _ = bounds

        if dx == 0 and dy == 0:
            return (p0, p0, 1)

        # First pixel
        y_start = (2 * dy * k_start + dx - 1) // (2 * dx)
        x_first = x0 + k_start if sx == 1 else x0 - k_start
        y_first = y0 + y_start if sy == 1 else y0 - y_start
        first_pt = (y_first, x_first) if steep else (x_first, y_first)

        # Last pixel
        y_end = (2 * dy * k_end + dx - 1) // (2 * dx)
        x_last = x0 + k_end if sx == 1 else x0 - k_end
        y_last = y0 + y_end if sy == 1 else y0 - y_end
        last_pt = (y_last, x_last) if steep else (x_last, y_last)

        count = k_end - k_start + 1
        return (first_pt, last_pt, count)
