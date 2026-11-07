#!/usr/bin/env python3
"""
3D CT / MRI Ray-Casting Benchmark:
Distributed Sub-Volume Ray Traversal & Phase-Shift Analysis

Simulates ray casting for 3D computed tomography (CT) and MRI across
partitioned sub-volumes (e.g. multi-GPU or distributed MPI blocks).

Compares:
1. Ground Truth (Full Volume 3D Bresenham)
2. Standard Continuous Slab-Clipping + Rounding + 3D Bresenham
3. 3D Analytical Phase-Compensated Bresenham (3D AP-Bresenham)
"""

import random
import time
import math
from exact_bresenham_3d_clipper import ExactBresenham3DClipper


def full_3d_bresenham(p0, p1):
    """Ground truth unclipped 3D Bresenham."""
    x0, y0, z0 = p0
    x1, y1, z1 = p1
    dx_orig = x1 - x0
    dy_orig = y1 - y0
    dz_orig = z1 - z0
    sx = 1 if dx_orig >= 0 else -1
    sy = 1 if dy_orig >= 0 else -1
    sz = 1 if dz_orig >= 0 else -1
    dx, dy, dz = abs(dx_orig), abs(dy_orig), abs(dz_orig)

    if dx >= dy and dx >= dz:
        major = 0
    elif dy >= dx and dy >= dz:
        major = 1
    else:
        major = 2

    pts = []
    if major == 0:
        Dy, Dz = 2 * dy - dx, 2 * dz - dx
        curr_y, curr_z = y0, z0
        for x in range(x0, x1 + sx, sx):
            pts.append((x, curr_y, curr_z))
            if Dy > 0:
                curr_y += sy
                Dy -= 2 * dx
            Dy += 2 * dy
            if Dz > 0:
                curr_z += sz
                Dz -= 2 * dx
            Dz += 2 * dz
    elif major == 1:
        Dx, Dz = 2 * dx - dy, 2 * dz - dy
        curr_x, curr_z = x0, z0
        for y in range(y0, y1 + sy, sy):
            pts.append((curr_x, y, curr_z))
            if Dx > 0:
                curr_x += sx
                Dx -= 2 * dy
            Dx += 2 * dx
            if Dz > 0:
                curr_z += sz
                Dz -= 2 * dy
            Dz += 2 * dz
    else:
        Dx, Dy = 2 * dx - dz, 2 * dy - dz
        curr_x, curr_y = x0, y0
        for z in range(z0, z1 + sz, sz):
            pts.append((curr_x, curr_y, z))
            if Dx > 0:
                curr_x += sx
                Dx -= 2 * dz
            Dx += 2 * dx
            if Dy > 0:
                curr_y += sy
                Dy -= 2 * dz
            Dy += 2 * dy
    return pts


def standard_continuous_3d_clip(p0, p1, xmin, ymin, zmin, xmax, ymax, zmax):
    """
    Standard slab/Liang-Barsky 3D clipping + nearest-integer endpoint rounding.
    """
    x0, y0, z0 = p0
    x1, y1, z1 = p1
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0

    p = [-dx, dx, -dy, dy, -dz, dz]
    q = [x0 - xmin, xmax - x0, y0 - ymin, ymax - y0, z0 - zmin, zmax - z0]

    t_enter = 0.0
    t_leave = 1.0
    for pi, qi in zip(p, q):
        if pi == 0:
            if qi < 0:
                return []
        elif pi < 0:
            t = qi / pi
            if t > t_enter:
                t_enter = t
        else:
            t = qi / pi
            if t < t_leave:
                t_leave = t

    if t_enter > t_leave:
        return []

    cx0 = x0 + t_enter * dx
    cy0 = y0 + t_enter * dy
    cz0 = z0 + t_enter * dz

    cx1 = x0 + t_leave * dx
    cy1 = y0 + t_leave * dy
    cz1 = z0 + t_leave * dz

    rx0, ry0, rz0 = round(cx0), round(cy0), round(cz0)
    rx1, ry1, rz1 = round(cx1), round(cy1), round(cz1)

    return full_3d_bresenham((rx0, ry0, rz0), (rx1, ry1, rz1))


def run_ct_benchmark():
    random.seed(42)
    N_RAYS = 5000

    print("=================================================================")
    print("3D CT / MRI RAY CASTING BENCHMARK: DISTRIBUTED VOXEL SUB-VOLUMES")
    print("=================================================================")
    print(f"Simulating {N_RAYS} tomographic X-ray trajectories across 3D voxel grid...")

    # Define a 3D volume partitioned into 8 sub-volume chunks (2x2x2)
    chunks = []
    chunk_size = 32
    for cx in (0, 1):
        for cy in (0, 1):
            for cz in (0, 1):
                xmin = cx * chunk_size
                xmax = (cx + 1) * chunk_size - 1
                ymin = cy * chunk_size
                ymax = (cy + 1) * chunk_size - 1
                zmin = cz * chunk_size
                zmax = (cz + 1) * chunk_size - 1
                chunks.append((xmin, ymin, zmin, xmax, ymax, zmax))

    vol_min = 0
    vol_max = 2 * chunk_size - 1

    rays = []
    for _ in range(N_RAYS):
        # Ray from outside emitter to outside detector
        source = (random.randint(-20, 0), random.randint(-20, 80), random.randint(-20, 80))
        target = (random.randint(64, 84), random.randint(-20, 80), random.randint(-20, 80))
        rays.append((source, target))

    std_corrupted_rays = 0
    std_total_discrepant_voxels = 0
    std_integral_errors = 0

    ap_corrupted_rays = 0
    ap_total_discrepant_voxels = 0
    ap_integral_errors = 0

    evaluated_rays = 0

    for source, target in rays:
        # Ground truth: full ray masked by each chunk and unioned
        full_voxels = full_3d_bresenham(source, target)
        vol_voxels = [p for p in full_voxels if vol_min <= p[0] <= vol_max and vol_min <= p[1] <= vol_max and vol_min <= p[2] <= vol_max]
        if not vol_voxels:
            continue

        evaluated_rays += 1

        # 1. Standard pipeline across 8 sub-volumes
        std_segments = []
        for xmin, ymin, zmin, xmax, ymax, zmax in chunks:
            # Get t_enter for sorting
            dx, dy, dz = target[0] - source[0], target[1] - source[1], target[2] - source[2]
            p = [-dx, dx, -dy, dy, -dz, dz]
            q = [source[0] - xmin, xmax - source[0], source[1] - ymin, ymax - source[1], source[2] - zmin, zmax - source[2]]
            t_enter, t_leave = 0.0, 1.0
            valid = True
            for pi, qi in zip(p, q):
                if pi == 0:
                    if qi < 0:
                        valid = False
                        break
                elif pi < 0:
                    t = qi / pi
                    if t > t_enter: t_enter = t
                else:
                    t = qi / pi
                    if t < t_leave: t_leave = t
            if valid and t_enter <= t_leave:
                chunk_voxels = standard_continuous_3d_clip(source, target, xmin, ymin, zmin, xmax, ymax, zmax)
                if chunk_voxels:
                    std_segments.append((t_enter, chunk_voxels))

        std_segments.sort(key=lambda s: s[0])
        std_assembled_voxels = []
        for _, seg in std_segments:
            std_assembled_voxels.extend(seg)

        if std_assembled_voxels != vol_voxels:
            std_corrupted_rays += 1
            diff = set(std_assembled_voxels) ^ set(vol_voxels)
            std_total_discrepant_voxels += len(diff)
            if len(std_assembled_voxels) != len(vol_voxels):
                std_integral_errors += 1

        # 2. Novel 3D AP-Bresenham across 8 sub-volumes
        ap_segments = []
        for xmin, ymin, zmin, xmax, ymax, zmax in chunks:
            bounds = ExactBresenham3DClipper.clip_bounds(source, target, xmin, ymin, zmin, xmax, ymax, zmax)
            if bounds is not None:
                k_start = bounds[1]
                chunk_voxels = ExactBresenham3DClipper.clip_and_rasterize(source, target, xmin, ymin, zmin, xmax, ymax, zmax)
                ap_segments.append((k_start, chunk_voxels))

        ap_segments.sort(key=lambda s: s[0])
        ap_assembled_voxels = []
        for _, seg in ap_segments:
            ap_assembled_voxels.extend(seg)

        if ap_assembled_voxels != vol_voxels:
            ap_corrupted_rays += 1
            diff = set(ap_assembled_voxels) ^ set(vol_voxels)
            ap_total_discrepant_voxels += len(diff)
            if len(ap_assembled_voxels) != len(vol_voxels):
                ap_integral_errors += 1

    print(f"\nEvaluated Rays intersecting volume: {evaluated_rays}")
    print("\n--- Standard Continuous Slab-Clipping + 3D Bresenham ---")
    print(f"Rays with Voxel Seam Artifacts:      {std_corrupted_rays} / {evaluated_rays} ({std_corrupted_rays / evaluated_rays * 100:.2f}%)")
    print(f"Total Discrepant / Missing Voxels:    {std_total_discrepant_voxels}")
    print(f"Rays with Attenuation Integral Error: {std_integral_errors} ({std_integral_errors / evaluated_rays * 100:.2f}%)")

    print("\n--- 3D AP-Bresenham Ray Clipper (Ours) ---")
    print(f"Rays with Voxel Seam Artifacts:      {ap_corrupted_rays} / {evaluated_rays} ({ap_corrupted_rays / evaluated_rays * 100:.2f}%)")
    print(f"Total Discrepant / Missing Voxels:    {ap_total_discrepant_voxels}")
    print(f"Rays with Attenuation Integral Error: {ap_integral_errors} ({ap_integral_errors / evaluated_rays * 100:.2f}%)")
    print("=================================================================\n")

    if ap_corrupted_rays == 0 and std_corrupted_rays > 0:
        print(">> VERDICT: 3D AP-Bresenham achieves 100% mathematical bit-identity across partitioned sub-volumes,")
        print("   eliminating seam artifacts and preserving exact Radon attenuation line integrals!")


if __name__ == "__main__":
    run_ct_benchmark()
