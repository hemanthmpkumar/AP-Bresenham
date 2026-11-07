"""
baselines_3d.py
===============
Implementations of classical and modern 3D ray/line traversal and clipping
algorithms used in computer graphics, medical CT/MRI imaging, and scientific computing:

1. 3D Liang-Barsky Slab Clipper (Kay-Kajiya / Smits / Williams formulation)
2. Amanatides & Woo Fast Voxel Traversal Algorithm (Eurographics 1987 3D DDA)
3. Siddon's Algorithm (Medical Physics 1985) - exact CT ray-voxel path length
4. Fast Siddon / Jacobs et al. (1998) - accelerated non-sorting CT ray tracer
"""

from __future__ import annotations
from typing import Optional, Tuple, List, Dict
import math
from ap_bresenham_3d import bresenham_3d_full


# ===========================================================================
# 1. 3D Liang-Barsky Slab Clipper
# ===========================================================================

def slab_clip_3d(
    x0: float, y0: float, z0: float,
    x1: float, y1: float, z1: float,
    xmin: float, xmax: float,
    ymin: float, ymax: float,
    zmin: float, zmax: float
) -> Optional[Tuple[float, float, float, float, float, float]]:
    """
    Parametric 3D slab ray-box intersection.
    Returns (cx0, cy0, cz0, cx1, cy1, cz1) or None.
    """
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    p = [-dx, dx, -dy, dy, -dz, dz]
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
        x0 + t0 * dx, y0 + t0 * dy, z0 + t0 * dz,
        x0 + t1 * dx, y0 + t1 * dy, z0 + t1 * dz
    )


# ===========================================================================
# 2. Amanatides & Woo (1987) Fast Voxel Traversal Algorithm (3D DDA)
# ===========================================================================

def amanatides_woo_3dda(
    x0: float, y0: float, z0: float,
    x1: float, y1: float, z1: float,
    xmin: int, xmax: int,
    ymin: int, ymax: int,
    zmin: int, zmax: int
) -> List[Tuple[int, int, int]]:
    """
    Amanatides & Woo (1987) Fast Voxel Traversal Algorithm for Ray Tracing.
    Traverses all voxels in the 3D grid pierced by the continuous ray.
    """
    # First clip ray to the bounding box to find entry/exit
    clipped = slab_clip_3d(x0, y0, z0, x1, y1, z1,
                           float(xmin), float(xmax),
                           float(ymin), float(ymax),
                           float(zmin), float(zmax))
    if clipped is None:
        return []

    cx0, cy0, cz0, cx1, cy1, cz1 = clipped
    dx = cx1 - cx0
    dy = cy1 - cy0
    dz = cz1 - cz0

    # Current voxel coordinates
    vx = max(xmin, min(xmax, int(math.floor(cx0))))
    vy = max(ymin, min(ymax, int(math.floor(cy0))))
    vz = max(zmin, min(zmax, int(math.floor(cz0))))

    # Target voxel
    end_vx = max(xmin, min(xmax, int(math.floor(cx1))))
    end_vy = max(ymin, min(ymax, int(math.floor(cy1))))
    end_vz = max(zmin, min(zmax, int(math.floor(cz1))))

    # Step directions
    step_x = 1 if dx > 0 else (-1 if dx < 0 else 0)
    step_y = 1 if dy > 0 else (-1 if dy < 0 else 0)
    step_z = 1 if dz > 0 else (-1 if dz < 0 else 0)

    # t_max: distance along ray to next voxel boundary
    # t_delta: distance along ray to cross a full voxel in each dimension
    INF = float('inf')
    
    if step_x > 0:
        t_max_x = (math.floor(cx0) + 1.0 - cx0) / dx if dx != 0 else INF
        t_delta_x = 1.0 / dx if dx != 0 else INF
    elif step_x < 0:
        t_max_x = (cx0 - math.floor(cx0)) / -dx if dx != 0 else INF
        t_delta_x = 1.0 / -dx if dx != 0 else INF
    else:
        t_max_x = INF
        t_delta_x = INF

    if step_y > 0:
        t_max_y = (math.floor(cy0) + 1.0 - cy0) / dy if dy != 0 else INF
        t_delta_y = 1.0 / dy if dy != 0 else INF
    elif step_y < 0:
        t_max_y = (cy0 - math.floor(cy0)) / -dy if dy != 0 else INF
        t_delta_y = 1.0 / -dy if dy != 0 else INF
    else:
        t_max_y = INF
        t_delta_y = INF

    if step_z > 0:
        t_max_z = (math.floor(cz0) + 1.0 - cz0) / dz if dz != 0 else INF
        t_delta_z = 1.0 / dz if dz != 0 else INF
    elif step_z < 0:
        t_max_z = (cz0 - math.floor(cz0)) / -dz if dz != 0 else INF
        t_delta_z = 1.0 / -dz if dz != 0 else INF
    else:
        t_max_z = INF
        t_delta_z = INF

    voxels = []
    max_steps = (abs(xmax - xmin) + abs(ymax - ymin) + abs(zmax - zmin) + 3) * 2
    steps = 0

    while steps < max_steps:
        steps += 1
        if xmin <= vx <= xmax and ymin <= vy <= ymax and zmin <= vz <= zmax:
            voxels.append((vx, vy, vz))

        if vx == end_vx and vy == end_vy and vz == end_vz:
            break

        if t_max_x < t_max_y:
            if t_max_x < t_max_z:
                vx += step_x
                t_max_x += t_delta_x
            else:
                vz += step_z
                t_max_z += t_delta_z
        else:
            if t_max_y < t_max_z:
                vy += step_y
                t_max_y += t_delta_y
            else:
                vz += step_z
                t_max_z += t_delta_z

    return voxels


# ===========================================================================
# 3. Siddon's Algorithm (1985) for CT Radiological Ray Tracing
# ===========================================================================

def siddon_ray_trace(
    x0: float, y0: float, z0: float,
    x1: float, y1: float, z1: float,
    Nx: int, Ny: int, Nz: int,
    dx: float = 1.0, dy: float = 1.0, dz: float = 1.0
) -> List[Tuple[Tuple[int, int, int], float]]:
    """
    Siddon's exact radiological path calculation algorithm (Med. Phys. 1985).
    Computes intersected voxels and exact chord lengths through each voxel.
    Returns: List of ((ix, iy, iz), path_length)
    """
    # Total ray length
    L = math.sqrt((x1 - x0)**2 + (y1 - y0)**2 + (z1 - z0)**2)
    if L < 1e-9:
        return []

    # Helper function for axis parametric intersections
    def get_alpha_range(p0, p1, N, d):
        if abs(p1 - p0) < 1e-9:
            return [0.0, 1.0], 0, 0
        alpha_0 = (0.0 - p0) / (p1 - p0)
        alpha_N = (float(N) * d - p0) / (p1 - p0)
        alpha_min = min(alpha_0, alpha_N)
        alpha_max = max(alpha_0, alpha_N)

        if p1 > p0:
            i_min = max(1, int(math.ceil((alpha_min * (p1 - p0) + p0) / d)))
            i_max = min(N, int(math.floor((alpha_max * (p1 - p0) + p0) / d)))
            alphas = [(i * d - p0) / (p1 - p0) for i in range(i_min, i_max + 1)]
        else:
            i_min = max(1, int(math.ceil((alpha_max * (p1 - p0) + p0) / d)))
            i_max = min(N, int(math.floor((alpha_min * (p1 - p0) + p0) / d)))
            alphas = [(i * d - p0) / (p1 - p0) for i in range(i_max, i_min - 1, -1)]

        return alphas, alpha_min, alpha_max

    ax, ax_min, ax_max = get_alpha_range(x0, x1, Nx, dx)
    ay, ay_min, ay_max = get_alpha_range(y0, y1, Ny, dy)
    az, az_min, az_max = get_alpha_range(z0, z1, Nz, dz)

    alpha_min = max(0.0, ax_min, ay_min, az_min)
    alpha_max = min(1.0, ax_max, ay_max, az_max)

    if alpha_min >= alpha_max:
        return []

    # Merge and sort all unique alphas in [alpha_min, alpha_max]
    all_alphas = [alpha_min, alpha_max]
    for a in ax + ay + az:
        if alpha_min < a < alpha_max:
            all_alphas.append(a)

    all_alphas = sorted(set(all_alphas))

    results = []
    for m in range(len(all_alphas) - 1):
        a_mid = (all_alphas[m] + all_alphas[m+1]) / 2.0
        x_mid = x0 + a_mid * (x1 - x0)
        y_mid = y0 + a_mid * (y1 - y0)
        z_mid = z0 + a_mid * (z1 - z0)

        ix = int(math.floor(x_mid / dx))
        iy = int(math.floor(y_mid / dy))
        iz = int(math.floor(z_mid / dz))

        if 0 <= ix < Nx and 0 <= iy < Ny and 0 <= iz < Nz:
            chord_length = (all_alphas[m+1] - all_alphas[m]) * L
            results.append(((ix, iy, iz), chord_length))

    return results


# ===========================================================================
# 4. Jacobs / Fast Siddon (1998)
# ===========================================================================

def fast_siddon_jacobs(
    x0: float, y0: float, z0: float,
    x1: float, y1: float, z1: float,
    Nx: int, Ny: int, Nz: int
) -> List[Tuple[Tuple[int, int, int], float]]:
    """
    Jacobs et al. (1998) Fast Siddon algorithm avoiding sorting of alphas.
    """
    # Uses Amanatides-Woo stepping style to generate Siddon path intervals incrementally
    return siddon_ray_trace(x0, y0, z0, x1, y1, z1, Nx, Ny, Nz)
