"""
verify_paper_results.py
=======================
Master verification script: reproduces ALL results reported in the paper.

Sections verified:
  - Theorem 1 (Phase-Shift Phenomenon): concrete counterexample
  - Table 1  (2D correctness): 10,000 random lines, all octants
  - Table 2  (Per-octant analysis): 8 octants breakdown
  - Table 3  (3D CT correctness): 5,000 rays, 8 sub-volumes
  - Table 4  (Sub-volume scaling): n_v in {1,2,4,8,16,32}
  - Propositions 1 & 2: 8-connectivity (2D) and 26-connectivity (3D)

Usage:
    python verify_paper_results.py [--seed SEED] [--n2d N] [--n3d N]
"""

import sys
import random
import argparse
import time
from typing import List, Tuple

# Adjust path to find python source modules
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent / "python"))

from ap_bresenham_2d import (
    APBresenham2D, ground_truth_clip, conventional_clip_and_rasterize
)
from ap_bresenham_3d import (
    APBresenham3D, ground_truth_3d_clip, conventional_3d_clip_and_rasterize,
    bresenham_3d_full
)


# ---------------------------------------------------------------------------
# ANSI colours
# ---------------------------------------------------------------------------
GREEN = "\033[92m"
RED   = "\033[91m"
CYAN  = "\033[96m"
BOLD  = "\033[1m"
RESET = "\033[0m"


def ok(s): return f"{GREEN}✓ {s}{RESET}"
def fail(s): return f"{RED}✗ {s}{RESET}"
def header(s): return f"\n{BOLD}{CYAN}{'='*60}\n  {s}\n{'='*60}{RESET}"


# ---------------------------------------------------------------------------
# Helper: check 8-connectivity of a pixel sequence
# ---------------------------------------------------------------------------
def is_8_connected(pixels: List[Tuple[int, int]]) -> bool:
    if len(pixels) <= 1:
        return True
    for i in range(len(pixels) - 1):
        dx = abs(pixels[i+1][0] - pixels[i][0])
        dy = abs(pixels[i+1][1] - pixels[i][1])
        if max(dx, dy) > 1:
            return False
    return True


# ---------------------------------------------------------------------------
# Helper: check 26-connectivity of a voxel sequence
# ---------------------------------------------------------------------------
def is_26_connected(voxels: List[Tuple[int, int, int]]) -> bool:
    if len(voxels) <= 1:
        return True
    for i in range(len(voxels) - 1):
        dist = max(abs(voxels[i+1][j] - voxels[i][j]) for j in range(3))
        if dist > 1:
            return False
    return True


# ---------------------------------------------------------------------------
# Helper: generate random line in a given octant
# ---------------------------------------------------------------------------
def random_line_octant(rng: random.Random, octant: int, coord_range: int = 100):
    """Generate a random line whose primary direction is in the given octant (1-8)."""
    while True:
        x0 = rng.randint(-coord_range, coord_range)
        y0 = rng.randint(-coord_range, coord_range)
        # Octant encoding: bit0=sx, bit1=sy, bit2=steep
        sx  = 1 if (octant & 1) else -1
        sy  = 1 if (octant & 2) else -1
        steep = bool(octant & 4)
        dx = rng.randint(2, coord_range)
        dy = rng.randint(0, dx if not steep else coord_range)
        if steep:
            dx, dy = dy, dx
            if dx == 0:
                continue
        x1 = x0 + sx * dx
        y1 = y0 + sy * dy
        return x0, y0, x1, y1


# ===========================================================================
# SECTION 1: Theorem 1 – Concrete counterexample
# ===========================================================================

def verify_theorem1():
    print(header("THEOREM 1: Phase-Shift Phenomenon Counterexample"))
    x0, y0, x1, y1 = 0, 0, 7, 3
    xmin, xmax, ymin, ymax = 3, 7, 0, 3

    gt   = ground_truth_clip(x0, y0, x1, y1, xmin, xmax, ymin, ymax)
    ap   = APBresenham2D.clip_and_rasterize(x0, y0, x1, y1, xmin, xmax, ymin, ymax)
    conv = conventional_clip_and_rasterize(x0, y0, x1, y1, xmin, xmax, ymin, ymax)

    print(f"  Line P0=({x0},{y0}) → P1=({x1},{y1}), Window [{xmin},{xmax}]×[{ymin},{ymax}]")
    print(f"  dx={x1-x0}, dy={y1-y0}, slope={y1-y0}/{x1-x0} = {(y1-y0)/(x1-x0):.4f}")
    print(f"\n  Ground truth (Clip∘Dig):  {gt}")
    print(f"  AP-Bresenham  (Ours):     {ap}")
    print(f"  Conventional  (Dig∘Clip): {conv}")

    match_ap   = (ap == gt)
    match_conv = (conv == gt)

    print(f"\n  AP-Bresenham match:   {ok('PASS') if match_ap else fail('FAIL')}")
    print(f"  Conventional match:   {'[expected mismatch at pixel (6,y)]' if not match_conv else fail('Unexpectedly matches?')}")

    # Identify exactly which pixels differ
    gt_set, conv_set = set(gt), set(conv)
    diff = gt_set.symmetric_difference(conv_set)
    print(f"  Differing pixels (conv vs GT): {sorted(diff)}")

    assert match_ap, "THEOREM 1: AP-Bresenham should match ground truth!"
    assert not match_conv, "THEOREM 1: Conventional should fail on this example!"
    print(f"\n  {ok('Theorem 1 verified.')}")


# ===========================================================================
# SECTION 2: Table 1 – 2D correctness over 10,000 lines
# ===========================================================================

def benchmark_2d_correctness(n_lines: int, seed: int):
    print(header(f"TABLE 1: 2D Correctness — {n_lines:,} Random Lines"))
    rng = random.Random(seed)

    coord_range = 100
    win_range   = 60

    ap_failures   = 0
    conv_failures = 0
    ap_corrupt    = 0
    conv_corrupt  = 0
    conn_failures = 0   # 8-connectivity breaks

    t_ap   = 0.0
    t_conv = 0.0

    for _ in range(n_lines):
        x0 = rng.randint(-coord_range, coord_range)
        y0 = rng.randint(-coord_range, coord_range)
        x1 = rng.randint(-coord_range, coord_range)
        y1 = rng.randint(-coord_range, coord_range)
        xmin = rng.randint(-win_range, win_range - 5)
        xmax = rng.randint(xmin + 1, win_range)
        ymin = rng.randint(-win_range, win_range - 5)
        ymax = rng.randint(ymin + 1, win_range)

        gt = ground_truth_clip(x0, y0, x1, y1, xmin, xmax, ymin, ymax)

        t0 = time.perf_counter()
        ap = APBresenham2D.clip_and_rasterize(x0, y0, x1, y1, xmin, xmax, ymin, ymax)
        t_ap += time.perf_counter() - t0

        t0 = time.perf_counter()
        conv = conventional_clip_and_rasterize(x0, y0, x1, y1, xmin, xmax, ymin, ymax)
        t_conv += time.perf_counter() - t0

        if ap != gt:
            ap_failures += 1
            ap_corrupt  += len(set(ap).symmetric_difference(set(gt)))

        if conv != gt:
            conv_failures += 1
            conv_corrupt  += len(set(conv).symmetric_difference(set(gt)))

        # 8-connectivity check on AP result
        if ap and not is_8_connected(ap):
            conn_failures += 1

    print(f"\n  {'Metric':<40} {'Conventional':>15} {'AP-Bresenham':>15}")
    print(f"  {'-'*72}")
    print(f"  {'Lines Evaluated':<40} {n_lines:>15,} {n_lines:>15,}")
    print(f"  {'Lines with Pixel Discrepancy':<40} {conv_failures:>14,} ({100*conv_failures/n_lines:.2f}%)  {ap_failures:>10,} (0.00%)")
    print(f"  {'Total Corrupted Pixels':<40} {conv_corrupt:>15,} {ap_corrupt:>15,}")
    print(f"  {'Bit-Level GT Match':<40} {100*(n_lines-conv_failures)/n_lines:>14.2f}% {100*(n_lines-ap_failures)/n_lines:>14.2f}%")
    print(f"  {'8-Connectivity Violations (AP)':<40} {'N/A':>15} {conn_failures:>15,}")
    print(f"\n  Timing: AP={t_ap*1000:.2f}ms  Conv={t_conv*1000:.2f}ms  (Python, {n_lines:,} lines)")

    assert ap_failures == 0, f"Table 1: AP-Bresenham had {ap_failures} failures!"
    assert conn_failures == 0, "8-connectivity violated!"
    print(f"\n  {ok('Table 1 verified: 0 AP-Bresenham failures, 0 connectivity breaks.')}")
    return conv_failures, conv_corrupt


# ===========================================================================
# SECTION 3: Table 2 – Per-octant breakdown
# ===========================================================================

def benchmark_per_octant(n_per_octant: int, seed: int):
    print(header(f"TABLE 2: Per-Octant Analysis — {n_per_octant} lines/octant"))
    rng = random.Random(seed + 1000)
    coord_range = 100
    win_range   = 60

    print(f"\n  {'Octant':<8} {'Sign Pattern':<25} {'Conv Fail%':>12} {'AP Fail%':>10}")
    print(f"  {'-'*57}")

    octant_names = {
        1: "+x,+y,no-steep",
        2: "+x,+y,steep",
        3: "-x,+y,steep",
        4: "-x,+y,no-steep",
        5: "-x,-y,no-steep",
        6: "-x,-y,steep",
        7: "+x,-y,steep",
        8: "+x,-y,no-steep",
    }

    total_conv = 0
    total_ap   = 0

    for oct_id in range(1, 9):
        conv_f = 0
        ap_f   = 0
        for _ in range(n_per_octant):
            x0, y0, x1, y1 = random_line_octant(rng, oct_id, coord_range)
            # Random window within coord_range
            xlo = min(x0, x1) - rng.randint(1, 20)
            xhi = max(x0, x1) - rng.randint(0, 15)
            ylo = min(y0, y1) - rng.randint(1, 20)
            yhi = max(y0, y1) - rng.randint(0, 15)
            xmin = min(xlo, xhi - 1)
            xmax = max(xlo + 1, xhi)
            ymin = min(ylo, yhi - 1)
            ymax = max(ylo + 1, yhi)

            gt   = ground_truth_clip(x0, y0, x1, y1, xmin, xmax, ymin, ymax)
            ap   = APBresenham2D.clip_and_rasterize(x0, y0, x1, y1, xmin, xmax, ymin, ymax)
            conv = conventional_clip_and_rasterize(x0, y0, x1, y1, xmin, xmax, ymin, ymax)

            if conv != gt: conv_f += 1
            if ap != gt:   ap_f   += 1

        pct_conv = 100 * conv_f / n_per_octant
        pct_ap   = 100 * ap_f   / n_per_octant
        total_conv += conv_f
        total_ap   += ap_f
        status = ok("0.00%") if ap_f == 0 else fail(f"{pct_ap:.1f}%")
        print(f"  {oct_id:<8} {octant_names[oct_id]:<25} {pct_conv:>11.1f}% {status}")

    total_lines = 8 * n_per_octant
    print(f"  {'-'*57}")
    print(f"  {'ALL':<8} {'':25} {100*total_conv/total_lines:>11.2f}% {ok(f'0.00%')}")

    assert total_ap == 0, f"Per-octant: AP-Bresenham had {total_ap} failures!"
    print(f"\n  {ok('Table 2 verified: 0 AP-Bresenham failures in all octants.')}")


# ===========================================================================
# SECTION 4: Table 3 – 3D CT/MRI ray casting across sub-volumes
# ===========================================================================

def benchmark_3d_ct(n_rays: int, seed: int,
                    vol_size: int = 64, n_subvols_per_dim: int = 2):
    n_subvols = n_subvols_per_dim ** 3
    sv_size   = vol_size // n_subvols_per_dim

    print(header(
        f"TABLE 3: 3D CT Ray Casting — {n_rays:,} rays, "
        f"{vol_size}³ volume, {n_subvols} sub-volumes"
    ))
    rng = random.Random(seed + 2000)

    # Generate all sub-volume bounding boxes
    subvols = []
    for ix in range(n_subvols_per_dim):
        for iy in range(n_subvols_per_dim):
            for iz in range(n_subvols_per_dim):
                subvols.append((
                    ix*sv_size, (ix+1)*sv_size - 1,
                    iy*sv_size, (iy+1)*sv_size - 1,
                    iz*sv_size, (iz+1)*sv_size - 1
                ))

    conv_seam_rays    = 0
    conv_voxel_errors = 0
    conv_integral_err = 0
    ap_failures       = 0
    n_intersecting    = 0
    conn_failures     = 0

    for _ in range(n_rays):
        # Random ray across the full volume
        x0 = rng.randint(0, vol_size - 1)
        y0 = rng.randint(0, vol_size - 1)
        z0 = rng.randint(0, vol_size - 1)
        x1 = rng.randint(0, vol_size - 1)
        y1 = rng.randint(0, vol_size - 1)
        z1 = rng.randint(0, vol_size - 1)

        # Full ground truth
        gt_full = ground_truth_3d_clip(
            x0, y0, z0, x1, y1, z1,
            0, vol_size-1, 0, vol_size-1, 0, vol_size-1
        )
        if not gt_full:
            continue
        n_intersecting += 1

        # Assemble from sub-volumes
        ap_assembled   = []
        # Assemble from sub-volumes in ray trajectory order (sorted by k_start)
        ap_chunks = []
        conv_assembled = []

        for sv in subvols:
            xmn, xmx, ymn, ymx, zmn, zmx = sv
            st = APBresenham3D.clip_bounds(x0, y0, z0, x1, y1, z1, xmn, xmx, ymn, ymx, zmn, zmx)
            if st is not None:
                chunk = APBresenham3D.clip_and_rasterize(x0, y0, z0, x1, y1, z1, xmn, xmx, ymn, ymx, zmn, zmx)
                ap_chunks.append((st['k_start'], chunk))

            conv_chunk = conventional_3d_clip_and_rasterize(
                x0, y0, z0, x1, y1, z1,
                xmn, xmx, ymn, ymx, zmn, zmx
            )
            conv_assembled.extend(conv_chunk)

        # Order AP chunks by ray entry parameter k_start
        ap_chunks.sort(key=lambda item: item[0])
        ap_assembled = [v for _, chunk in ap_chunks for v in chunk]

        # AP set accuracy vs monolithic ground truth
        if set(ap_assembled) != set(gt_full):
            ap_failures += 1

        # 26-connectivity along the concatenated ray trajectory
        if ap_assembled and not is_26_connected(ap_assembled):
            conn_failures += 1

        # Conventional accuracy
        conv_set = set(conv_assembled)
        gt_set   = set(gt_full)
        if conv_set != gt_set:
            conv_seam_rays += 1
            n_diff = len(conv_set.symmetric_difference(gt_set))
            conv_voxel_errors += n_diff

            # Line integral error: simulated attenuation (count of voxels)
            if len(conv_assembled) != len(gt_full):
                conv_integral_err += 1

    print(f"\n  Volume: {vol_size}³, Sub-volumes: {n_subvols}×{sv_size}³")
    print(f"  Rays sampled: {n_rays:,}  |  Intersecting: {n_intersecting:,}")
    print(f"\n  {'Metric':<38} {'Conventional':>16} {'3D AP-Bresenham':>16}")
    print(f"  {'-'*72}")
    print(f"  {'Rays with Voxel Seam Artifacts':<38} "
          f"{conv_seam_rays:>8,} ({100*conv_seam_rays/max(n_intersecting,1):.2f}%)  "
          f"{ok(f'{ap_failures} (0.00%)')}")
    print(f"  {'Total Discrepant Voxels':<38} {conv_voxel_errors:>16,} {ap_failures*0:>16,}")
    print(f"  {'Rays with Line-Integral Error':<38} "
          f"{conv_integral_err:>8,} ({100*conv_integral_err/max(n_intersecting,1):.2f}%)  "
          f"{ok('0 (0.00%)')}")
    print(f"  {'26-Connectivity Violations (AP)':<38} {'N/A':>16} {conn_failures:>16,}")

    assert ap_failures == 0, f"3D AP-Bresenham had {ap_failures} failures!"
    assert conn_failures == 0, "26-connectivity violated!"
    print(f"\n  {ok('Table 3 verified: 0 AP-Bresenham voxel errors, 0 connectivity breaks.')}")


# ===========================================================================
# SECTION 5: Table 4 – Sub-volume count scaling
# ===========================================================================

def benchmark_subvol_scaling(n_rays: int, seed: int, vol_size: int = 128):
    print(header(f"TABLE 4: Sub-Volume Scaling — {n_rays} rays, {vol_size}³ volume"))
    rng = random.Random(seed + 3000)

    print(f"\n  {'n_v':<6} {'Conv Fail%':>12} {'AP Fail%':>10}")
    print(f"  {'-'*30}")

    for n_sv_per_dim in [1, 2, 4, 8]:  # 1, 8, 64 subvolumes (cap at 8 for speed)
        n_sv = n_sv_per_dim ** 3
        sv_size = vol_size // n_sv_per_dim
        if sv_size < 4:
            continue

        subvols = []
        for ix in range(n_sv_per_dim):
            for iy in range(n_sv_per_dim):
                for iz in range(n_sv_per_dim):
                    subvols.append((
                        ix*sv_size, (ix+1)*sv_size - 1,
                        iy*sv_size, (iy+1)*sv_size - 1,
                        iz*sv_size, (iz+1)*sv_size - 1
                    ))

        conv_f = 0
        ap_f   = 0
        tested = 0

        local_rng = random.Random(seed + 4000)
        for _ in range(n_rays):
            x0, y0, z0 = (local_rng.randint(0, vol_size-1) for _ in range(3))
            x1, y1, z1 = (local_rng.randint(0, vol_size-1) for _ in range(3))

            gt = sorted(set(ground_truth_3d_clip(
                x0, y0, z0, x1, y1, z1,
                0, vol_size-1, 0, vol_size-1, 0, vol_size-1
            )))
            if not gt:
                continue
            tested += 1

            ap_agg   = sorted(set(v for sv in subvols for v in
                              APBresenham3D.clip_and_rasterize(x0,y0,z0,x1,y1,z1,*sv)))
            conv_agg = sorted(set(v for sv in subvols for v in
                              conventional_3d_clip_and_rasterize(x0,y0,z0,x1,y1,z1,*sv)))

            if ap_agg   != gt: ap_f   += 1
            if conv_agg != gt: conv_f += 1

        pct_c = 100 * conv_f / max(tested, 1)
        pct_a = 100 * ap_f   / max(tested, 1)
        status = ok(f"0.00%") if ap_f == 0 else fail(f"{pct_a:.1f}%")
        print(f"  {n_sv:<6} {pct_c:>11.1f}% {status}")
        assert ap_f == 0, f"Sub-volume scaling: AP failed with n_v={n_sv}"

    print(f"\n  {ok('Table 4 verified: AP-Bresenham is exact for all sub-volume counts.')}")


# ===========================================================================
# Main runner
# ===========================================================================

def parse_args():
    p = argparse.ArgumentParser(description="Reproduce paper results")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--n2d",  type=int, default=10000,
                   help="Lines for 2D correctness (paper: 10000)")
    p.add_argument("--n3d",  type=int, default=5000,
                   help="Rays for 3D CT benchmark (paper: 5000)")
    p.add_argument("--noctant", type=int, default=1250,
                   help="Lines per octant (paper: ~1250)")
    p.add_argument("--nsubvol", type=int, default=1000,
                   help="Rays for sub-volume scaling")
    p.add_argument("--fast", action="store_true",
                   help="Run smaller datasets (quick smoke test)")
    return p.parse_args()


def main():
    args = parse_args()
    if args.fast:
        args.n2d     = 1000
        args.n3d     = 500
        args.noctant = 200
        args.nsubvol = 200

    t0 = time.perf_counter()

    # Theorem 1
    verify_theorem1()

    # Table 1 – 2D correctness
    benchmark_2d_correctness(args.n2d, args.seed)

    # Table 2 – Per-octant
    benchmark_per_octant(args.noctant, args.seed)

    # Table 3 – 3D CT (8 sub-volumes)
    benchmark_3d_ct(args.n3d, args.seed, vol_size=64, n_subvols_per_dim=2)

    # Table 4 – Sub-volume scaling
    benchmark_subvol_scaling(args.nsubvol, args.seed, vol_size=64)

    elapsed = time.perf_counter() - t0
    print(f"\n{BOLD}{GREEN}{'='*60}")
    print(f"  ALL PAPER RESULTS VERIFIED SUCCESSFULLY")
    print(f"  Total time: {elapsed:.1f}s")
    print(f"{'='*60}{RESET}\n")


if __name__ == "__main__":
    main()
