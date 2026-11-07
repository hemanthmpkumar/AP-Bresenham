#pragma once

/**
 * ap_bresenham_3d.hpp
 * ===================
 * Production-grade, zero-allocation, header-only C++17 implementation
 * of 3D Analytical Phase-Compensated Bresenham (AP-Bresenham) voxel ray clipping.
 *
 * Guarantees:
 *   - Pure integer arithmetic (no FPU instructions, no cross-register stalls)
 *   - Dual accumulator D1, D2 exact analytical phase injection
 *   - 100% bit-level equivalence with Bresen_Z3(P0, P1) ∩ Omega
 *   - Strictly preserves 26-connectivity across distributed 3D sub-volume boundaries
 */

#include <cstdint>
#include <cstdlib>
#include <algorithm>
#include <vector>
#include "ap_bresenham_2d.hpp"

namespace ap_bresenham {

struct Point3D {
    i64 x, y, z;
};

struct Box3D {
    i64 xmin, xmax;
    i64 ymin, ymax;
    i64 zmin, zmax;
};

struct ClipState3D {
    i64 k_start, k_end;
    i64 d_maj, d_min1, d_min2;
    i64 s_maj, s_min1, s_min2;
    int major; // 0=x, 1=y, 2=z
    i64 p0_maj, p0_min1, p0_min2;
    i64 m1_rel, m2_rel;
    i64 D1_start, D2_start;
    bool valid;
};

/**
 * O(1) Diophantine Boundary Inversion and Phase Calculation for 3D Voxel Lattices.
 */
inline ClipState3D clip_bounds_3d(
    i64 x0, i64 y0, i64 z0,
    i64 x1, i64 y1, i64 z1,
    i64 xmin, i64 xmax,
    i64 ymin, i64 ymax,
    i64 zmin, i64 zmax
) noexcept {
    i64 dx = std::abs(x1 - x0);
    i64 dy = std::abs(y1 - y0);
    i64 dz = std::abs(z1 - z0);

    i64 sx = (x1 >= x0) ? 1 : -1;
    i64 sy = (y1 >= y0) ? 1 : -1;
    i64 sz = (z1 >= z0) ? 1 : -1;

    int major = 0;
    i64 d_maj, d_min1, d_min2;
    i64 s_maj, s_min1, s_min2;
    i64 p0_maj, p0_min1, p0_min2;
    i64 w_maj_min, w_maj_max;
    i64 w_min1_min, w_min1_max;
    i64 w_min2_min, w_min2_max;

    if (dx >= dy && dx >= dz) {
        major = 0; // x-major
        d_maj = dx; d_min1 = dy; d_min2 = dz;
        s_maj = sx; s_min1 = sy; s_min2 = sz;
        p0_maj = x0; p0_min1 = y0; p0_min2 = z0;
        w_maj_min = xmin; w_maj_max = xmax;
        w_min1_min = ymin; w_min1_max = ymax;
        w_min2_min = zmin; w_min2_max = zmax;
    } else if (dy >= dx && dy >= dz) {
        major = 1; // y-major
        d_maj = dy; d_min1 = dx; d_min2 = dz;
        s_maj = sy; s_min1 = sx; s_min2 = sz;
        p0_maj = y0; p0_min1 = x0; p0_min2 = z0;
        w_maj_min = ymin; w_maj_max = ymax;
        w_min1_min = xmin; w_min1_max = xmax;
        w_min2_min = zmin; w_min2_max = zmax;
    } else {
        major = 2; // z-major
        d_maj = dz; d_min1 = dx; d_min2 = dy;
        s_maj = sz; s_min1 = sx; s_min2 = sy;
        p0_maj = z0; p0_min1 = x0; p0_min2 = y0;
        w_maj_min = zmin; w_maj_max = zmax;
        w_min1_min = xmin; w_min1_max = xmax;
        w_min2_min = ymin; w_min2_max = ymax;
    }

    if (d_maj == 0) {
        if (xmin <= x0 && x0 <= xmax && ymin <= y0 && y0 <= ymax && zmin <= z0 && z0 <= zmax) {
            return {0, 0, 0, 0, 0, sx, sy, sz, major, p0_maj, p0_min1, p0_min2, 0, 0, 0, 0, true};
        }
        return {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, false};
    }

    i64 wm_min = (s_maj > 0)  ? (w_maj_min - p0_maj)   : (p0_maj - w_maj_max);
    i64 wm_max = (s_maj > 0)  ? (w_maj_max - p0_maj)   : (p0_maj - w_maj_min);
    i64 w1_min = (s_min1 > 0) ? (w_min1_min - p0_min1) : (p0_min1 - w_min1_max);
    i64 w1_max = (s_min1 > 0) ? (w_min1_max - p0_min1) : (p0_min1 - w_min1_min);
    i64 w2_min = (s_min2 > 0) ? (w_min2_min - p0_min2) : (p0_min2 - w_min2_max);
    i64 w2_max = (s_min2 > 0) ? (w_min2_max - p0_min2) : (p0_min2 - w_min2_min);

    i64 km_min = std::max((i64)0, wm_min);
    i64 km_max = std::min(d_maj, wm_max);
    if (km_min > km_max) {
        return {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, false};
    }

    i64 k1_min, k1_max;
    if (d_min1 == 0) {
        if (w1_min <= 0 && 0 <= w1_max) {
            k1_min = 0; k1_max = d_maj;
        } else {
            return {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, false};
        }
    } else {
        k1_min = ceil_div(2 * d_maj * w1_min - d_maj + 1, 2 * d_min1);
        k1_max = floor_div(2 * d_maj * (w1_max + 1) - d_maj, 2 * d_min1);
    }

    i64 k2_min, k2_max;
    if (d_min2 == 0) {
        if (w2_min <= 0 && 0 <= w2_max) {
            k2_min = 0; k2_max = d_maj;
        } else {
            return {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, false};
        }
    } else {
        k2_min = ceil_div(2 * d_maj * w2_min - d_maj + 1, 2 * d_min2);
        k2_max = floor_div(2 * d_maj * (w2_max + 1) - d_maj, 2 * d_min2);
    }

    i64 k_start = std::max({km_min, k1_min, k2_min});
    i64 k_end   = std::min({km_max, k1_max, k2_max});
    if (k_start > k_end) {
        return {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, false};
    }

    i64 m1_rel = floor_div(2 * d_min1 * k_start + d_maj - 1, 2 * d_maj);
    i64 m2_rel = floor_div(2 * d_min2 * k_start + d_maj - 1, 2 * d_maj);
    i64 D1_start = (2 * d_min1 - d_maj) + 2 * d_min1 * k_start - 2 * d_maj * m1_rel;
    i64 D2_start = (2 * d_min2 - d_maj) + 2 * d_min2 * k_start - 2 * d_maj * m2_rel;

    return {k_start, k_end, d_maj, d_min1, d_min2, s_maj, s_min1, s_min2,
            major, p0_maj, p0_min1, p0_min2, m1_rel, m2_rel, D1_start, D2_start, true};
}

/**
 * Direct 3D rasterization callback version.
 */
template <typename VoxelCallback>
inline void rasterize_clipped_3d(
    i64 x0, i64 y0, i64 z0,
    i64 x1, i64 y1, i64 z1,
    i64 xmin, i64 xmax,
    i64 ymin, i64 ymax,
    i64 zmin, i64 zmax,
    VoxelCallback&& emit_voxel
) {
    ClipState3D st = clip_bounds_3d(x0, y0, z0, x1, y1, z1, xmin, xmax, ymin, ymax, zmin, zmax);
    if (!st.valid) return;

    i64 D1 = st.D1_start;
    i64 D2 = st.D2_start;
    i64 m1 = st.m1_rel;
    i64 m2 = st.m2_rel;
    i64 d_maj2 = 2 * st.d_maj;
    i64 d_min1_2 = 2 * st.d_min1;
    i64 d_min2_2 = 2 * st.d_min2;

    for (i64 k = st.k_start; k <= st.k_end; ++k) {
        i64 val_maj  = st.p0_maj  + st.s_maj  * k;
        i64 val_min1 = st.p0_min1 + st.s_min1 * m1;
        i64 val_min2 = st.p0_min2 + st.s_min2 * m2;

        if (st.major == 0) {
            emit_voxel(val_maj, val_min1, val_min2);
        } else if (st.major == 1) {
            emit_voxel(val_min1, val_maj, val_min2);
        } else {
            emit_voxel(val_min1, val_min2, val_maj);
        }

        if (D1 > 0) {
            m1 += 1;
            D1 -= d_maj2;
        }
        D1 += d_min1_2;

        if (D2 > 0) {
            m2 += 1;
            D2 -= d_maj2;
        }
        D2 += d_min2_2;
    }
}

/**
 * Vector returning version for 3D.
 */
inline std::vector<Point3D> clip_and_rasterize_3d(
    i64 x0, i64 y0, i64 z0,
    i64 x1, i64 y1, i64 z1,
    i64 xmin, i64 xmax,
    i64 ymin, i64 ymax,
    i64 zmin, i64 zmax
) {
    std::vector<Point3D> voxels;
    rasterize_clipped_3d(
        x0, y0, z0, x1, y1, z1, xmin, xmax, ymin, ymax, zmin, zmax,
        [&voxels](i64 vx, i64 vy, i64 vz) {
            voxels.push_back({vx, vy, vz});
        }
    );
    return voxels;
}

} // namespace ap_bresenham
