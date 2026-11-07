"""
Exact 3D Analytical Phase-Compensated Bresenham Ray Clipper (3D AP-Bresenham)

Extends the exact Diophantine clipping framework to 3D voxel lattices Z^3 for:
- CT / MRI / PET volume ray casting
- Chunked / Tiled 3D voxel grids (MPI / GPU distributed sub-volumes)
- Discrete 3D ray marching and Radon transform backprojection

Mathematical Guarantee:
    Clip(3D_Bresenham(Ray), Voxel_Box) === AP_Bresenham_3D(Ray, Voxel_Box)
    [100% Bit-Identical across all 26-connected discrete rays]
"""

from typing import List, Tuple, Optional


def ceil_div(a: int, b: int) -> int:
    """Exact integer ceiling division: ceil(a / b) for positive integer b."""
    return -(-a // b)


class ExactBresenham3DClipper:
    """
    O(1) Analytical Phase-Compensated 3D Bresenham Ray Clipper.

    Resolves the 3D Phase-Shift Problem across dual secondary axes (y, z) simultaneously,
    achieving 100% bit-level preservation of 3D discrete rays.
    """

    @staticmethod
    def clip_bounds(
        p0: Tuple[int, int, int],
        p1: Tuple[int, int, int],
        xmin: int, ymin: int, zmin: int,
        xmax: int, ymax: int, zmax: int
    ) -> Optional[Tuple[int, int, int, int, int, int, int, int, int, int, int, int, int, int]]:
        """
        Computes 3D clipping parameters in O(1) integer operations.

        Returns:
            Tuple with canonical mapping parameters, k_start, k_end, and initial (D1, D2) accumulators.
        """
        x0, y0, z0 = p0
        x1, y1, z1 = p1

        dx_orig = x1 - x0
        dy_orig = y1 - y0
        dz_orig = z1 - z0

        sx = 1 if dx_orig >= 0 else -1
        sy = 1 if dy_orig >= 0 else -1
        sz = 1 if dz_orig >= 0 else -1

        dx = abs(dx_orig)
        dy = abs(dy_orig)
        dz = abs(dz_orig)

        # Handle degenerate point
        if dx == 0 and dy == 0 and dz == 0:
            if xmin <= x0 <= xmax and ymin <= y0 <= ymax and zmin <= z0 <= zmax:
                return (0, 0, 0, 0, 0, 0, 1, 1, 1, x0, y0, z0, 0, 0)
            return None

        # Identify primary major driving axis
        if dx >= dy and dx >= dz:
            major = 0
            d_maj, d_min1, d_min2 = dx, dy, dz
            s_maj, s_min1, s_min2 = sx, sy, sz
            p0_maj, p0_min1, p0_min2 = x0, y0, z0
            w_maj_min, w_maj_max = xmin, xmax
            w_min1_min, w_min1_max = ymin, ymax
            w_min2_min, w_min2_max = zmin, zmax
        elif dy >= dx and dy >= dz:
            major = 1
            d_maj, d_min1, d_min2 = dy, dx, dz
            s_maj, s_min1, s_min2 = sy, sx, sz
            p0_maj, p0_min1, p0_min2 = y0, x0, z0
            w_maj_min, w_maj_max = ymin, ymax
            w_min1_min, w_min1_max = xmin, xmax
            w_min2_min, w_min2_max = zmin, zmax
        else:
            major = 2
            d_maj, d_min1, d_min2 = dz, dx, dy
            s_maj, s_min1, s_min2 = sz, sx, sy
            p0_maj, p0_min1, p0_min2 = z0, x0, y0
            w_maj_min, w_maj_max = zmin, zmax
            w_min1_min, w_min1_max = xmin, xmax
            w_min2_min, w_min2_max = ymin, ymax

        # Map voxel box to relative canonical coordinates
        if s_maj == 1:
            w_maj_lo = w_maj_min - p0_maj
            w_maj_hi = w_maj_max - p0_maj
        else:
            w_maj_lo = p0_maj - w_maj_max
            w_maj_hi = p0_maj - w_maj_min

        if s_min1 == 1:
            w_min1_lo = w_min1_min - p0_min1
            w_min1_hi = w_min1_max - p0_min1
        else:
            w_min1_lo = p0_min1 - w_min1_max
            w_min1_hi = p0_min1 - w_min1_min

        if s_min2 == 1:
            w_min2_lo = w_min2_min - p0_min2
            w_min2_hi = w_min2_max - p0_min2
        else:
            w_min2_lo = p0_min2 - w_min2_max
            w_min2_hi = p0_min2 - w_min2_min

        # 1. Major axis bounds
        k_maj_min = max(0, w_maj_lo)
        k_maj_max = min(d_maj, w_maj_hi)
        if k_maj_min > k_maj_max:
            return None

        # 2. Minor axis 1 bounds via Diophantine inversion
        if d_min1 == 0:
            if not (w_min1_lo <= 0 <= w_min1_hi):
                return None
            k_min1_min, k_min1_max = 0, d_maj
        else:
            num1_min = 2 * d_maj * w_min1_lo - d_maj + 1
            k_min1_min = ceil_div(num1_min, 2 * d_min1)
            num1_max = 2 * d_maj * (w_min1_hi + 1) - d_maj
            k_min1_max = num1_max // (2 * d_min1)

        # 3. Minor axis 2 bounds via Diophantine inversion
        if d_min2 == 0:
            if not (w_min2_lo <= 0 <= w_min2_hi):
                return None
            k_min2_min, k_min2_max = 0, d_maj
        else:
            num2_min = 2 * d_maj * w_min2_lo - d_maj + 1
            k_min2_min = ceil_div(num2_min, 2 * d_min2)
            num2_max = 2 * d_maj * (w_min2_hi + 1) - d_maj
            k_min2_max = num2_max // (2 * d_min2)

        # Intersect all three 1D parameter intervals
        k_start = max(k_maj_min, k_min1_min, k_min2_min)
        k_end = min(k_maj_max, k_min1_max, k_min2_max)

        if k_start > k_end:
            return None

        # Analytical state injection at k_start in O(1)
        rel1 = (2 * d_min1 * k_start + d_maj - 1) // (2 * d_maj)
        D1 = (2 * d_min1 - d_maj) + 2 * d_min1 * k_start - 2 * d_maj * rel1

        rel2 = (2 * d_min2 * k_start + d_maj - 1) // (2 * d_maj)
        D2 = (2 * d_min2 - d_maj) + 2 * d_min2 * k_start - 2 * d_maj * rel2

        return (
            major, k_start, k_end,
            d_maj, d_min1, d_min2,
            s_maj, s_min1, s_min2,
            p0_maj, p0_min1, p0_min2,
            D1, D2
        )

    @classmethod
    def clip_and_rasterize(
        cls,
        p0: Tuple[int, int, int],
        p1: Tuple[int, int, int],
        xmin: int, ymin: int, zmin: int,
        xmax: int, ymax: int, zmax: int
    ) -> List[Tuple[int, int, int]]:
        """
        Clips the 3D ray to the voxel grid bounding box and generates only the visible voxels.
        Guaranteed to match unclipped 3D Bresenham masked by the box 100% bit-for-bit.
        """
        bounds = cls.clip_bounds(p0, p1, xmin, ymin, zmin, xmax, ymax, zmax)
        if bounds is None:
            return []

        (
            major, k_start, k_end,
            d_maj, d_min1, d_min2,
            s_maj, s_min1, s_min2,
            p0_maj, p0_min1, p0_min2,
            D1, D2
        ) = bounds

        if d_maj == 0:
            return [p0]

        rel1 = (2 * d_min1 * k_start + d_maj - 1) // (2 * d_maj)
        rel2 = (2 * d_min2 * k_start + d_maj - 1) // (2 * d_maj)

        curr_rel1 = rel1
        curr_rel2 = rel2
        curr_D1 = D1
        curr_D2 = D2

        two_d_maj = 2 * d_maj
        two_d_min1 = 2 * d_min1
        two_d_min2 = 2 * d_min2

        voxels: List[Tuple[int, int, int]] = []

        for k in range(k_start, k_end + 1):
            val_maj = p0_maj + k if s_maj == 1 else p0_maj - k
            val_min1 = p0_min1 + curr_rel1 if s_min1 == 1 else p0_min1 - curr_rel1
            val_min2 = p0_min2 + curr_rel2 if s_min2 == 1 else p0_min2 - curr_rel2

            if major == 0:
                voxels.append((val_maj, val_min1, val_min2))
            elif major == 1:
                voxels.append((val_min1, val_maj, val_min2))
            else:
                voxels.append((val_min1, val_min2, val_maj))

            if curr_D1 > 0:
                curr_rel1 += 1
                curr_D1 -= two_d_maj
            curr_D1 += two_d_min1

            if curr_D2 > 0:
                curr_rel2 += 1
                curr_D2 -= two_d_maj
            curr_D2 += two_d_min2

        return voxels
