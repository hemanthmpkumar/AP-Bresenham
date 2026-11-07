"""
ap_bresenham_2d.py
==================
Core 2D Analytical Phase-Compensated Bresenham (AP-Bresenham) algorithm.
Implements exact integer-only clipping that satisfies:

    Dig(Clip(L, Omega)) == Clip(Dig(L), Omega)

Key invariants proved in the paper:
  - Lemma 1: y(k) = y0 + floor((2*dy*k + dx - 1) / (2*dx))
  - Lemma 2: D(k) = (2*dy - dx) + 2*dy*k - 2*dx*(y(k) - y0)
  - Theorem 2: O(1) Diophantine boundary inversion
  - Theorem 3: Bit-level equivalence with Clip(Dig(L), Omega)
"""

from __future__ import annotations
from typing import Iterator, Optional, Tuple, List
import math


# ---------------------------------------------------------------------------
# Integer arithmetic helpers (exact, no floating point)
# ---------------------------------------------------------------------------

def _floor_div(a: int, b: int) -> int:
    """Floor division for any signed integers (b > 0)."""
    return a // b  # Python's // already does floor division


def _ceil_div(a: int, b: int) -> int:
    """Ceiling division for any signed integers (b > 0)."""
    return -(-a // b)  # Python's // rounds toward -inf, so negate trick works


# ---------------------------------------------------------------------------
# Ground-truth reference: full Bresenham, then mask (for verification)
# ---------------------------------------------------------------------------

def bresenham_full(x0: int, y0: int, x1: int, y1: int) -> List[Tuple[int, int]]:
    """
    Standard Bresenham's line algorithm — ALL pixels from P0 to P1.
    Used as ground truth. No clipping applied.
    """
    pixels = []
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x1 >= x0 else -1
    sy = 1 if y1 >= y0 else -1
    steep = dy > dx
    if steep:
        x0, y0 = y0, x0
        x1, y1 = y1, x1
        dx, dy = dy, dx
        sx, sy = sy, sx

    D = 2 * dy - dx
    y = y0
    for x in range(x0, x1 + sx, sx):
        pixels.append((y, x) if steep else (x, y))
        if D > 0:
            y += sy
            D += 2 * dy - 2 * dx
        else:
            D += 2 * dy
    return pixels


def ground_truth_clip(
    x0: int, y0: int, x1: int, y1: int,
    xmin: int, xmax: int, ymin: int, ymax: int
) -> List[Tuple[int, int]]:
    """
    Ground truth: rasterize full Bresenham then mask to window.
    This is Clip(Dig(L), Omega) — the correct answer.
    """
    return [
        (px, py) for px, py in bresenham_full(x0, y0, x1, y1)
        if xmin <= px <= xmax and ymin <= py <= ymax
    ]


# ---------------------------------------------------------------------------
# Conventional pipeline (the broken approach for comparison)
# ---------------------------------------------------------------------------

def liang_barsky_clip(
    x0: int, y0: int, x1: int, y1: int,
    xmin: int, xmax: int, ymin: int, ymax: int
) -> Optional[Tuple[float, float, float, float]]:
    """
    Liang-Barsky continuous clipping.
    Returns (cx0, cy0, cx1, cy1) or None if line is fully outside.
    """
    dx, dy = x1 - x0, y1 - y0
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


def conventional_clip_and_rasterize(
    x0: int, y0: int, x1: int, y1: int,
    xmin: int, xmax: int, ymin: int, ymax: int
) -> List[Tuple[int, int]]:
    """
    Conventional pipeline: Liang-Barsky clip → round → fresh Bresenham.
    This is Dig(Clip(L, Omega)) with the phase-reset bug.
    """
    result = liang_barsky_clip(x0, y0, x1, y1, xmin, xmax, ymin, ymax)
    if result is None:
        return []
    cx0, cy0, cx1, cy1 = result
    rx0, ry0 = round(cx0), round(cy0)
    rx1, ry1 = round(cx1), round(cy1)
    return bresenham_full(rx0, ry0, rx1, ry1)


# ---------------------------------------------------------------------------
# AP-Bresenham core: O(1) setup, exact integer clipping
# ---------------------------------------------------------------------------

class APBresenham2D:
    """
    Analytical Phase-Compensated Bresenham for 2D pixel grids.

    Proves and implements:
        Dig(Clip(L, Omega)) == Clip(Dig(L), Omega)

    using purely integer arithmetic — zero floating-point operations.
    """

    @staticmethod
    def clip_bounds(
        x0: int, y0: int, x1: int, y1: int,
        xmin: int, xmax: int, ymin: int, ymax: int
    ) -> Optional[dict]:
        """
        O(1) Diophantine boundary inversion.

        Returns a dict with all the state needed to rasterize the clipped
        segment, or None if the line is entirely outside the window.

        The dict contains:
          k_start, k_end  : step indices in canonical coordinates
          dx, dy          : canonical axis deltas
          sx, sy          : sign of original direction
          steep           : True if axes were swapped
          x0c, y0c        : canonical origin
          D_start         : exact initial Bresenham accumulator value
          y_rel           : canonical y at k_start
        """
        # --- Step 1: Canonical octant reduction ---
        sx = 1 if x1 >= x0 else -1
        sy = 1 if y1 >= y0 else -1
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        steep = dy > dx
        x0c, y0c = x0, y0

        if steep:
            dx, dy = dy, dx
            sx, sy = sy, sx
            x0c, y0c = y0, x0
            xmin, xmax, ymin, ymax = ymin, ymax, xmin, xmax

        if dx == 0:
            # Degenerate point — single pixel
            if xmin <= x0 <= xmax and ymin <= y0 <= ymax:
                return dict(k_start=0, k_end=0, dx=0, dy=0,
                            sx=sx, sy=sy, steep=steep,
                            x0c=x0c, y0c=y0c, D_start=0, y_rel=0)
            return None

        # --- Step 2: Map window to canonical relative coords ---
        if sx > 0:
            wx_min = xmin - x0c
            wx_max = xmax - x0c
        else:
            wx_min = x0c - xmax
            wx_max = x0c - xmin

        if sy > 0:
            wy_min = ymin - y0c
            wy_max = ymax - y0c
        else:
            wy_min = y0c - ymax
            wy_max = y0c - ymin

        # --- Step 3: x-axis parameter bounds ---
        kx_min = max(0, wx_min)
        kx_max = min(dx, wx_max)
        if kx_min > kx_max:
            return None

        # --- Step 4: y-axis parameter bounds (Diophantine inversion) ---
        if dy == 0:
            # Horizontal line (in canonical space)
            if wy_min <= 0 <= wy_max:
                ky_min, ky_max = 0, dx
            else:
                return None
        else:
            # Theorem 2: exact Diophantine inversion
            # k_y_min = ceil((2*dx*wy_min - dx + 1) / (2*dy))
            # k_y_max = floor((2*dx*(wy_max + 1) - dx) / (2*dy))
            ky_min = _ceil_div(2 * dx * wy_min - dx + 1, 2 * dy)
            ky_max = _floor_div(2 * dx * (wy_max + 1) - dx, 2 * dy)

        # --- Step 5: Intersect intervals ---
        k_start = max(kx_min, ky_min)
        k_end = min(kx_max, ky_max)
        if k_start > k_end:
            return None

        # --- Step 6: Analytical phase injection ---
        # Lemma 1: y_rel = floor((2*dy*k_start + dx - 1) / (2*dx))
        y_rel = _floor_div(2 * dy * k_start + dx - 1, 2 * dx)
        # Lemma 2: D_start = (2*dy - dx) + 2*dy*k_start - 2*dx*y_rel
        D_start = (2 * dy - dx) + 2 * dy * k_start - 2 * dx * y_rel

        return dict(
            k_start=k_start, k_end=k_end,
            dx=dx, dy=dy, sx=sx, sy=sy,
            steep=steep, x0c=x0c, y0c=y0c,
            D_start=D_start, y_rel=y_rel
        )

    @staticmethod
    def _unmap_pixel(k: int, y_rel: int, state: dict) -> Tuple[int, int]:
        """Un-map canonical (k, y_rel) back to world coordinates."""
        sx, sy = state['sx'], state['sy']
        x0c, y0c = state['x0c'], state['y0c']
        steep = state['steep']
        wx = x0c + sx * k
        wy = y0c + sy * y_rel
        return (wy, wx) if steep else (wx, wy)

    @classmethod
    def clip_and_rasterize(
        cls,
        x0: int, y0: int, x1: int, y1: int,
        xmin: int, xmax: int, ymin: int, ymax: int
    ) -> List[Tuple[int, int]]:
        """
        Main entry point: return the exact list of pixels in the clipped segment.

        Theorem 3 (Bit-Level Equivalence): the result equals
        Bresen(P0, P1) ∩ Omega exactly.
        """
        state = cls.clip_bounds(x0, y0, x1, y1, xmin, xmax, ymin, ymax)
        if state is None:
            return []

        k_start = state['k_start']
        k_end = state['k_end']
        dx = state['dx']
        dy = state['dy']
        D = state['D_start']
        y_rel = state['y_rel']

        pixels = []
        for k in range(k_start, k_end + 1):
            pixels.append(cls._unmap_pixel(k, y_rel, state))
            if D > 0:
                y_rel += 1
                D -= 2 * dx
            D += 2 * dy

        return pixels

    @classmethod
    def clip_and_rasterize_iter(
        cls,
        x0: int, y0: int, x1: int, y1: int,
        xmin: int, xmax: int, ymin: int, ymax: int
    ) -> Iterator[Tuple[int, int]]:
        """Generator version — zero memory allocation, O(1) setup."""
        state = cls.clip_bounds(x0, y0, x1, y1, xmin, xmax, ymin, ymax)
        if state is None:
            return

        k_start = state['k_start']
        k_end = state['k_end']
        dx = state['dx']
        dy = state['dy']
        D = state['D_start']
        y_rel = state['y_rel']

        for k in range(k_start, k_end + 1):
            yield cls._unmap_pixel(k, y_rel, state)
            if D > 0:
                y_rel += 1
                D -= 2 * dx
            D += 2 * dy


# ---------------------------------------------------------------------------
# Convenience function: verify a single line
# ---------------------------------------------------------------------------

def verify_line(
    x0: int, y0: int, x1: int, y1: int,
    xmin: int, xmax: int, ymin: int, ymax: int,
    verbose: bool = False
) -> Tuple[bool, int]:
    """
    Compare AP-Bresenham output against ground truth.
    Returns (match: bool, num_discrepant_pixels: int).
    """
    gt = ground_truth_clip(x0, y0, x1, y1, xmin, xmax, ymin, ymax)
    ap = APBresenham2D.clip_and_rasterize(x0, y0, x1, y1, xmin, xmax, ymin, ymax)
    conv = conventional_clip_and_rasterize(x0, y0, x1, y1, xmin, xmax, ymin, ymax)

    match_ap = (ap == gt)
    match_conv = (conv == gt)

    if verbose:
        print(f"Line ({x0},{y0})->({x1},{y1}), window [{xmin},{xmax}]x[{ymin},{ymax}]")
        print(f"  Ground truth ({len(gt)} px): {gt}")
        print(f"  AP-Bresenham ({len(ap)} px): {ap}  {'✓ MATCH' if match_ap else '✗ MISMATCH'}")
        print(f"  Conventional ({len(conv)} px): {conv}  {'✓ MATCH' if match_conv else '✗ MISMATCH'}")

    # Count discrepant pixels (symmetric difference)
    gt_set, ap_set = set(gt), set(ap)
    discrepant = len(gt_set.symmetric_difference(ap_set))
    return match_ap, discrepant


if __name__ == "__main__":
    # Quick self-test: the counterexample from Theorem 1 (Phase-Shift Phenomenon)
    print("=== Theorem 1 Counterexample ===")
    verify_line(0, 0, 7, 3, 3, 7, 0, 3, verbose=True)

    print("\n=== Horizontal line ===")
    verify_line(0, 0, 10, 0, 2, 8, 0, 5, verbose=True)

    print("\n=== Steep (dy > dx) ===")
    verify_line(0, 0, 3, 10, 0, 3, 3, 7, verbose=True)

    print("\n=== Negative direction ===")
    verify_line(10, 8, 0, 0, 1, 6, 1, 5, verbose=True)
