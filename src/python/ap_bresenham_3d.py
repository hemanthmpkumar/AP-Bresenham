"""
ap_bresenham_3d.py
==================
Core 3D Analytical Phase-Compensated Bresenham (AP-Bresenham) algorithm.
Extends the 2D framework to voxel lattices Z^3 with dual error accumulators D1, D2.

Implements:
  Corollary 1: 3D Bit-Level Equivalence
  Algorithms:  AP-Bresenham 3D Voxel Clipping (Algorithm 2 in the paper)

Applications:
  - CT/MRI/PET volume ray casting
  - Multi-GPU distributed voxel processing
  - Exact 26-connected discrete ray traversal
"""

from __future__ import annotations
from typing import Iterator, Optional, Tuple, List


# ---------------------------------------------------------------------------
# Integer helpers (identical to 2D, repeated for module independence)
# ---------------------------------------------------------------------------

def _floor_div(a: int, b: int) -> int:
    return a // b


def _ceil_div(a: int, b: int) -> int:
    return -(-a // b)


# ---------------------------------------------------------------------------
# Ground truth: full 3D Bresenham, then mask
# ---------------------------------------------------------------------------

def bresenham_3d_full(
    x0: int, y0: int, z0: int,
    x1: int, y1: int, z1: int
) -> List[Tuple[int, int, int]]:
    """
    Full 3D Bresenham voxel traversal (ground truth).
    Produces a 26-connected sequence of voxels from P0 to P1.
    """
    voxels = []
    dx, dy, dz = abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)
    sx = 1 if x1 >= x0 else -1
    sy = 1 if y1 >= y0 else -1
    sz = 1 if z1 >= z0 else -1

    if dx >= dy and dx >= dz:
        # x is major axis
        d_maj, d_min1, d_min2 = dx, dy, dz
        s_maj, s_min1, s_min2 = sx, sy, sz
        emit = lambda k, m1, m2: (x0 + s_maj * k, y0 + s_min1 * m1, z0 + s_min2 * m2)
    elif dy >= dx and dy >= dz:
        # y is major axis
        d_maj, d_min1, d_min2 = dy, dx, dz
        s_maj, s_min1, s_min2 = sy, sx, sz
        emit = lambda k, m1, m2: (x0 + s_min1 * m1, y0 + s_maj * k, z0 + s_min2 * m2)
    else:
        # z is major axis
        d_maj, d_min1, d_min2 = dz, dx, dy
        s_maj, s_min1, s_min2 = sz, sx, sy
        emit = lambda k, m1, m2: (x0 + s_min1 * m1, y0 + s_min2 * m2, z0 + s_maj * k)

    D1 = 2 * d_min1 - d_maj
    D2 = 2 * d_min2 - d_maj
    m1, m2 = 0, 0

    for k in range(d_maj + 1):
        voxels.append(emit(k, m1, m2))
        if D1 > 0:
            m1 += 1
            D1 -= 2 * d_maj
        D1 += 2 * d_min1
        if D2 > 0:
            m2 += 1
            D2 -= 2 * d_maj
        D2 += 2 * d_min2

    return voxels


def ground_truth_3d_clip(
    x0: int, y0: int, z0: int,
    x1: int, y1: int, z1: int,
    xmin: int, xmax: int,
    ymin: int, ymax: int,
    zmin: int, zmax: int
) -> List[Tuple[int, int, int]]:
    """Ground truth: full 3D Bresenham then mask to voxel box."""
    return [
        v for v in bresenham_3d_full(x0, y0, z0, x1, y1, z1)
        if xmin <= v[0] <= xmax and ymin <= v[1] <= ymax and zmin <= v[2] <= zmax
    ]


# ---------------------------------------------------------------------------
# Conventional 3D pipeline (the broken reference)
# ---------------------------------------------------------------------------

def slab_clip_3d(
    x0: int, y0: int, z0: int,
    x1: int, y1: int, z1: int,
    xmin: int, xmax: int,
    ymin: int, ymax: int,
    zmin: int, zmax: int
) -> Optional[Tuple[float, float, float, float, float, float]]:
    """Parametric slab clipping in 3D (floating-point)."""
    ddx, ddy, ddz = x1 - x0, y1 - y0, z1 - z0
    p = [-ddx, ddx, -ddy, ddy, -ddz, ddz]
    q = [x0 - xmin, xmax - x0, y0 - ymin, ymax - y0, z0 - zmin, zmax - z0]
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
        x0 + t0 * ddx, y0 + t0 * ddy, z0 + t0 * ddz,
        x0 + t1 * ddx, y0 + t1 * ddy, z0 + t1 * ddz
    )


def conventional_3d_clip_and_rasterize(
    x0: int, y0: int, z0: int,
    x1: int, y1: int, z1: int,
    xmin: int, xmax: int,
    ymin: int, ymax: int,
    zmin: int, zmax: int
) -> List[Tuple[int, int, int]]:
    """
    Conventional 3D pipeline: slab clip → round → fresh 3D Bresenham.
    This has the Phase-Shift Phenomenon at every sub-volume boundary.
    """
    result = slab_clip_3d(x0, y0, z0, x1, y1, z1, xmin, xmax, ymin, ymax, zmin, zmax)
    if result is None:
        return []
    cx0, cy0, cz0, cx1, cy1, cz1 = result
    rx0, ry0, rz0 = round(cx0), round(cy0), round(cz0)
    rx1, ry1, rz1 = round(cx1), round(cy1), round(cz1)
    return bresenham_3d_full(rx0, ry0, rz0, rx1, ry1, rz1)


# ---------------------------------------------------------------------------
# AP-Bresenham 3D core
# ---------------------------------------------------------------------------

class APBresenham3D:
    """
    Analytical Phase-Compensated Bresenham for 3D voxel lattices.

    Corollary 1 (3D Bit-Level Equivalence): the output is 100% bit-identical
    to Bresen_Z3(P0, P1) ∩ Omega for any integer voxel box Omega.

    All arithmetic is integer-only. Zero floating-point operations.
    """

    @staticmethod
    def clip_bounds(
        x0: int, y0: int, z0: int,
        x1: int, y1: int, z1: int,
        xmin: int, xmax: int,
        ymin: int, ymax: int,
        zmin: int, zmax: int
    ) -> Optional[dict]:
        """
        O(1) Diophantine boundary inversion for 3D.

        Returns state dict or None if line is entirely outside the voxel box.
        """
        dx, dy, dz = abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)
        sx = 1 if x1 >= x0 else -1
        sy = 1 if y1 >= y0 else -1
        sz = 1 if z1 >= z0 else -1

        # --- Determine major axis ---
        if dx >= dy and dx >= dz:
            major = 0  # x
            d_maj, d_min1, d_min2 = dx, dy, dz
            s_maj, s_min1, s_min2 = sx, sy, sz
            p0_maj, p0_min1, p0_min2 = x0, y0, z0
            w_maj_min, w_maj_max = xmin, xmax
            w_min1_min, w_min1_max = ymin, ymax
            w_min2_min, w_min2_max = zmin, zmax
        elif dy >= dx and dy >= dz:
            major = 1  # y
            d_maj, d_min1, d_min2 = dy, dx, dz
            s_maj, s_min1, s_min2 = sy, sx, sz
            p0_maj, p0_min1, p0_min2 = y0, x0, z0
            w_maj_min, w_maj_max = ymin, ymax
            w_min1_min, w_min1_max = xmin, xmax
            w_min2_min, w_min2_max = zmin, zmax
        else:
            major = 2  # z
            d_maj, d_min1, d_min2 = dz, dx, dy
            s_maj, s_min1, s_min2 = sz, sx, sy
            p0_maj, p0_min1, p0_min2 = z0, x0, y0
            w_maj_min, w_maj_max = zmin, zmax
            w_min1_min, w_min1_max = xmin, xmax
            w_min2_min, w_min2_max = ymin, ymax

        if d_maj == 0:
            # Degenerate: single voxel
            if (xmin <= x0 <= xmax and ymin <= y0 <= ymax and zmin <= z0 <= zmax):
                return dict(k_start=0, k_end=0, d_maj=0, d_min1=0, d_min2=0,
                            sx=sx, sy=sy, sz=sz, major=major,
                            x0=x0, y0=y0, z0=z0,
                            m1_rel=0, m2_rel=0, D1_start=0, D2_start=0)
            return None

        # --- Map window to canonical relative coords for each axis ---
        def canonical_bounds(p0, s, w_lo, w_hi):
            if s > 0:
                return w_lo - p0, w_hi - p0
            else:
                return p0 - w_hi, p0 - w_lo

        wm_min, wm_max = canonical_bounds(p0_maj, s_maj, w_maj_min, w_maj_max)
        w1_min, w1_max = canonical_bounds(p0_min1, s_min1, w_min1_min, w_min1_max)
        w2_min, w2_max = canonical_bounds(p0_min2, s_min2, w_min2_min, w_min2_max)

        # --- Major axis bounds ---
        km_min = max(0, wm_min)
        km_max = min(d_maj, wm_max)
        if km_min > km_max:
            return None

        # --- Minor axis 1 Diophantine inversion ---
        if d_min1 == 0:
            if w1_min <= 0 <= w1_max:
                k1_min, k1_max = 0, d_maj
            else:
                return None
        else:
            k1_min = _ceil_div(2 * d_maj * w1_min - d_maj + 1, 2 * d_min1)
            k1_max = _floor_div(2 * d_maj * (w1_max + 1) - d_maj, 2 * d_min1)

        # --- Minor axis 2 Diophantine inversion ---
        if d_min2 == 0:
            if w2_min <= 0 <= w2_max:
                k2_min, k2_max = 0, d_maj
            else:
                return None
        else:
            k2_min = _ceil_div(2 * d_maj * w2_min - d_maj + 1, 2 * d_min2)
            k2_max = _floor_div(2 * d_maj * (w2_max + 1) - d_maj, 2 * d_min2)

        # --- Composite entry/exit (Eqs. 19-20 in the paper) ---
        k_start = max(km_min, k1_min, k2_min)
        k_end = min(km_max, k1_max, k2_max)
        if k_start > k_end:
            return None

        # --- Analytical dual phase injection (Corollary 1) ---
        m1_rel = _floor_div(2 * d_min1 * k_start + d_maj - 1, 2 * d_maj)
        m2_rel = _floor_div(2 * d_min2 * k_start + d_maj - 1, 2 * d_maj)
        D1_start = (2 * d_min1 - d_maj) + 2 * d_min1 * k_start - 2 * d_maj * m1_rel
        D2_start = (2 * d_min2 - d_maj) + 2 * d_min2 * k_start - 2 * d_maj * m2_rel

        return dict(
            k_start=k_start, k_end=k_end,
            d_maj=d_maj, d_min1=d_min1, d_min2=d_min2,
            s_maj=s_maj, s_min1=s_min1, s_min2=s_min2,
            major=major,
            x0=x0, y0=y0, z0=z0,
            p0_maj=p0_maj, p0_min1=p0_min1, p0_min2=p0_min2,
            m1_rel=m1_rel, m2_rel=m2_rel,
            D1_start=D1_start, D2_start=D2_start
        )

    @staticmethod
    def _unmap_voxel(k: int, m1: int, m2: int, state: dict) -> Tuple[int, int, int]:
        """Un-map canonical (k, m1, m2) to world coordinates."""
        major = state['major']
        p0_maj = state['p0_maj']
        p0_min1 = state['p0_min1']
        p0_min2 = state['p0_min2']
        s_maj = state['s_maj']
        s_min1 = state['s_min1']
        s_min2 = state['s_min2']

        val_maj = p0_maj + s_maj * k
        val_min1 = p0_min1 + s_min1 * m1
        val_min2 = p0_min2 + s_min2 * m2

        if major == 0:   # x-major
            return (val_maj, val_min1, val_min2)
        elif major == 1:  # y-major
            return (val_min1, val_maj, val_min2)
        else:             # z-major
            return (val_min1, val_min2, val_maj)

    @classmethod
    def clip_and_rasterize(
        cls,
        x0: int, y0: int, z0: int,
        x1: int, y1: int, z1: int,
        xmin: int, xmax: int,
        ymin: int, ymax: int,
        zmin: int, zmax: int
    ) -> List[Tuple[int, int, int]]:
        """
        Main entry point: return exact list of voxels in clipped ray.

        Corollary 1: result == Bresen_Z3(P0, P1) ∩ Omega.
        """
        state = cls.clip_bounds(
            x0, y0, z0, x1, y1, z1,
            xmin, xmax, ymin, ymax, zmin, zmax
        )
        if state is None:
            return []

        k_start = state['k_start']
        k_end = state['k_end']
        d_maj = state['d_maj']
        d_min1 = state['d_min1']
        d_min2 = state['d_min2']
        D1 = state['D1_start']
        D2 = state['D2_start']
        m1 = state['m1_rel']
        m2 = state['m2_rel']

        voxels = []
        for k in range(k_start, k_end + 1):
            voxels.append(cls._unmap_voxel(k, m1, m2, state))
            if D1 > 0:
                m1 += 1
                D1 -= 2 * d_maj
            D1 += 2 * d_min1
            if D2 > 0:
                m2 += 1
                D2 -= 2 * d_maj
            D2 += 2 * d_min2

        return voxels

    @classmethod
    def clip_and_rasterize_iter(
        cls,
        x0: int, y0: int, z0: int,
        x1: int, y1: int, z1: int,
        xmin: int, xmax: int,
        ymin: int, ymax: int,
        zmin: int, zmax: int
    ) -> Iterator[Tuple[int, int, int]]:
        """Generator version — O(1) memory for setup, O(1) per voxel."""
        state = cls.clip_bounds(
            x0, y0, z0, x1, y1, z1,
            xmin, xmax, ymin, ymax, zmin, zmax
        )
        if state is None:
            return

        k_start = state['k_start']
        k_end = state['k_end']
        d_maj = state['d_maj']
        d_min1 = state['d_min1']
        d_min2 = state['d_min2']
        D1 = state['D1_start']
        D2 = state['D2_start']
        m1 = state['m1_rel']
        m2 = state['m2_rel']

        for k in range(k_start, k_end + 1):
            yield cls._unmap_voxel(k, m1, m2, state)
            if D1 > 0:
                m1 += 1
                D1 -= 2 * d_maj
            D1 += 2 * d_min1
            if D2 > 0:
                m2 += 1
                D2 -= 2 * d_maj
            D2 += 2 * d_min2


if __name__ == "__main__":
    # Quick self-test
    print("=== 3D AP-Bresenham Self-Test ===")
    x0, y0, z0 = 0, 0, 0
    x1, y1, z1 = 10, 7, 4
    xmin, xmax = 3, 8
    ymin, ymax = 0, 7
    zmin, zmax = 0, 4

    gt = ground_truth_3d_clip(x0, y0, z0, x1, y1, z1,
                               xmin, xmax, ymin, ymax, zmin, zmax)
    ap = APBresenham3D.clip_and_rasterize(x0, y0, z0, x1, y1, z1,
                                           xmin, xmax, ymin, ymax, zmin, zmax)
    conv = conventional_3d_clip_and_rasterize(x0, y0, z0, x1, y1, z1,
                                               xmin, xmax, ymin, ymax, zmin, zmax)

    print(f"Ground truth  ({len(gt)} voxels): {gt}")
    print(f"AP-Bresenham  ({len(ap)} voxels): {ap}")
    print(f"Conventional  ({len(conv)} voxels): {conv}")
    print(f"AP match: {'✓' if ap == gt else '✗ FAIL'}")
    print(f"Conv match: {'✓' if conv == gt else '✗ MISMATCH (expected)'}")
