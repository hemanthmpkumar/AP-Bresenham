#pragma once

/**
 * baselines_3d.hpp
 * ================
 * C++17 implementations of classical 3D ray traversal and clipping algorithms:
 * 1. 3D Liang-Barsky Slab Clipper
 * 2. Full 3D Bresenham (Ground Truth Generator)
 * 3. Amanatides & Woo (1987) Fast Voxel Traversal Algorithm (3D DDA)
 * 4. Siddon's Algorithm (1985) for CT Radiological Ray Tracing
 * 5. Conventional 3D Pipeline Adapter
 */

#include <cmath>
#include <vector>
#include <algorithm>
#include <set>
#include "ap_bresenham_3d.hpp"

namespace baselines_3d {

using namespace ap_bresenham;

// ---------------------------------------------------------------------------
// Full 3D Bresenham (Ground Truth)
// ---------------------------------------------------------------------------
inline std::vector<Point3D> bresenham_full_3d(
    i64 x0, i64 y0, i64 z0,
    i64 x1, i64 y1, i64 z1
) {
    std::vector<Point3D> voxels;
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

    if (dx >= dy && dx >= dz) {
        major = 0;
        d_maj = dx; d_min1 = dy; d_min2 = dz;
        s_maj = sx; s_min1 = sy; s_min2 = sz;
        p0_maj = x0; p0_min1 = y0; p0_min2 = z0;
    } else if (dy >= dx && dy >= dz) {
        major = 1;
        d_maj = dy; d_min1 = dx; d_min2 = dz;
        s_maj = sy; s_min1 = sx; s_min2 = sz;
        p0_maj = y0; p0_min1 = x0; p0_min2 = z0;
    } else {
        major = 2;
        d_maj = dz; d_min1 = dx; d_min2 = dy;
        s_maj = sz; s_min1 = sx; s_min2 = sy;
        p0_maj = z0; p0_min1 = x0; p0_min2 = y0;
    }

    i64 D1 = 2 * d_min1 - d_maj;
    i64 D2 = 2 * d_min2 - d_maj;
    i64 m1 = 0, m2 = 0;
    i64 d_maj2 = 2 * d_maj;
    i64 d_min1_2 = 2 * d_min1;
    i64 d_min2_2 = 2 * d_min2;

    for (i64 k = 0; k <= d_maj; ++k) {
        i64 val_maj  = p0_maj  + s_maj  * k;
        i64 val_min1 = p0_min1 + s_min1 * m1;
        i64 val_min2 = p0_min2 + s_min2 * m2;

        if (major == 0) {
            voxels.push_back({val_maj, val_min1, val_min2});
        } else if (major == 1) {
            voxels.push_back({val_min1, val_maj, val_min2});
        } else {
            voxels.push_back({val_min1, val_min2, val_maj});
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
    return voxels;
}

inline std::vector<Point3D> ground_truth_clip_3d(
    i64 x0, i64 y0, i64 z0,
    i64 x1, i64 y1, i64 z1,
    i64 xmin, i64 xmax,
    i64 ymin, i64 ymax,
    i64 zmin, i64 zmax
) {
    std::vector<Point3D> full = bresenham_full_3d(x0, y0, z0, x1, y1, z1);
    std::vector<Point3D> clipped;
    for (const auto& v : full) {
        if (xmin <= v.x && v.x <= xmax &&
            ymin <= v.y && v.y <= ymax &&
            zmin <= v.z && v.z <= zmax) {
            clipped.push_back(v);
        }
    }
    return clipped;
}

// ---------------------------------------------------------------------------
// 3D Parametric Slab Clipper
// ---------------------------------------------------------------------------
inline bool slab_clip_3d(
    double x0, double y0, double z0,
    double x1, double y1, double z1,
    double xmin, double xmax,
    double ymin, double ymax,
    double zmin, double zmax,
    double& cx0, double& cy0, double& cz0,
    double& cx1, double& cy1, double& cz1
) {
    double dx = x1 - x0;
    double dy = y1 - y0;
    double dz = z1 - z0;

    double p[6] = {-dx, dx, -dy, dy, -dz, dz};
    double q[6] = {x0 - xmin, xmax - x0, y0 - ymin, ymax - y0, z0 - zmin, zmax - z0};
    double t0 = 0.0, t1 = 1.0;

    for (int i = 0; i < 6; ++i) {
        if (p[i] == 0.0) {
            if (q[i] < 0.0) return false;
        } else if (p[i] < 0.0) {
            double t = q[i] / p[i];
            if (t > t0) t0 = t;
        } else {
            double t = q[i] / p[i];
            if (t < t1) t1 = t;
        }
    }

    if (t0 > t1) return false;

    cx0 = x0 + t0 * dx;
    cy0 = y0 + t0 * dy;
    cz0 = z0 + t0 * dz;
    cx1 = x0 + t1 * dx;
    cy1 = y0 + t1 * dy;
    cz1 = z0 + t1 * dz;
    return true;
}

// ---------------------------------------------------------------------------
// Conventional 3D Pipeline (Slab Clip + Round + 3D Bresenham)
// ---------------------------------------------------------------------------
inline std::vector<Point3D> conventional_clip_and_rasterize_3d(
    i64 x0, i64 y0, i64 z0,
    i64 x1, i64 y1, i64 z1,
    i64 xmin, i64 xmax,
    i64 ymin, i64 ymax,
    i64 zmin, i64 zmax
) {
    double cx0, cy0, cz0, cx1, cy1, cz1;
    if (!slab_clip_3d((double)x0, (double)y0, (double)z0,
                      (double)x1, (double)y1, (double)z1,
                      (double)xmin, (double)xmax,
                      (double)ymin, (double)ymax,
                      (double)zmin, (double)zmax,
                      cx0, cy0, cz0, cx1, cy1, cz1)) {
        return {};
    }

    i64 rx0 = (i64)std::round(cx0);
    i64 ry0 = (i64)std::round(cy0);
    i64 rz0 = (i64)std::round(cz0);
    i64 rx1 = (i64)std::round(cx1);
    i64 ry1 = (i64)std::round(cy1);
    i64 rz1 = (i64)std::round(cz1);

    return bresenham_full_3d(rx0, ry0, rz0, rx1, ry1, rz1);
}

// ---------------------------------------------------------------------------
// Amanatides & Woo (1987) Fast Voxel Traversal (3D DDA)
// ---------------------------------------------------------------------------
inline std::vector<Point3D> amanatides_woo_3dda(
    double x0, double y0, double z0,
    double x1, double y1, double z1,
    i64 xmin, i64 xmax,
    i64 ymin, i64 ymax,
    i64 zmin, i64 zmax
) {
    double cx0, cy0, cz0, cx1, cy1, cz1;
    if (!slab_clip_3d(x0, y0, z0, x1, y1, z1,
                      (double)xmin, (double)xmax,
                      (double)ymin, (double)ymax,
                      (double)zmin, (double)zmax,
                      cx0, cy0, cz0, cx1, cy1, cz1)) {
        return {};
    }

    double dx = cx1 - cx0;
    double dy = cy1 - cy0;
    double dz = cz1 - cz0;

    i64 vx = std::max(xmin, std::min(xmax, (i64)std::floor(cx0)));
    i64 vy = std::max(ymin, std::min(ymax, (i64)std::floor(cy0)));
    i64 vz = std::max(zmin, std::min(zmax, (i64)std::floor(cz0)));

    i64 end_vx = std::max(xmin, std::min(xmax, (i64)std::floor(cx1)));
    i64 end_vy = std::max(ymin, std::min(ymax, (i64)std::floor(cy1)));
    i64 end_vz = std::max(zmin, std::min(zmax, (i64)std::floor(cz1)));

    i64 step_x = (dx > 0) ? 1 : ((dx < 0) ? -1 : 0);
    i64 step_y = (dy > 0) ? 1 : ((dy < 0) ? -1 : 0);
    i64 step_z = (dz > 0) ? 1 : ((dz < 0) ? -1 : 0);

    const double INF = 1e30;
    double t_max_x = (step_x > 0) ? (std::floor(cx0) + 1.0 - cx0) / dx :
                     ((step_x < 0) ? (cx0 - std::floor(cx0)) / -dx : INF);
    double t_delta_x = (dx != 0.0) ? std::abs(1.0 / dx) : INF;

    double t_max_y = (step_y > 0) ? (std::floor(cy0) + 1.0 - cy0) / dy :
                     ((step_y < 0) ? (cy0 - std::floor(cy0)) / -dy : INF);
    double t_delta_y = (dy != 0.0) ? std::abs(1.0 / dy) : INF;

    double t_max_z = (step_z > 0) ? (std::floor(cz0) + 1.0 - cz0) / dz :
                     ((step_z < 0) ? (cz0 - std::floor(cz0)) / -dz : INF);
    double t_delta_z = (dz != 0.0) ? std::abs(1.0 / dz) : INF;

    std::vector<Point3D> voxels;
    i64 max_steps = (std::abs(xmax - xmin) + std::abs(ymax - ymin) + std::abs(zmax - zmin) + 3) * 2;
    i64 steps = 0;

    while (steps++ < max_steps) {
        if (xmin <= vx && vx <= xmax && ymin <= vy && vy <= ymax && zmin <= vz && vz <= zmax) {
            voxels.push_back({vx, vy, vz});
        }
        if (vx == end_vx && vy == end_vy && vz == end_vz) break;

        if (t_max_x < t_max_y) {
            if (t_max_x < t_max_z) {
                vx += step_x;
                t_max_x += t_delta_x;
            } else {
                vz += step_z;
                t_max_z += t_delta_z;
            }
        } else {
            if (t_max_y < t_max_z) {
                vy += step_y;
                t_max_y += t_delta_y;
            } else {
                vz += step_z;
                t_max_z += t_delta_z;
            }
        }
    }
    return voxels;
}

// ---------------------------------------------------------------------------
// Siddon's Algorithm (1985) Exact Radiological Path Length Calculation
// ---------------------------------------------------------------------------
struct SiddonVoxelIntersection {
    Point3D voxel;
    double chord_length;
};

inline std::vector<SiddonVoxelIntersection> siddon_ray_trace(
    double x0, double y0, double z0,
    double x1, double y1, double z1,
    i64 Nx, i64 Ny, i64 Nz
) {
    double L = std::sqrt((x1 - x0) * (x1 - x0) + (y1 - y0) * (y1 - y0) + (z1 - z0) * (z1 - z0));
    if (L < 1e-9) return {};

    auto get_alphas = [](double p0, double p1, i64 N, std::vector<double>& alphas, double& a_min, double& a_max) {
        if (std::abs(p1 - p0) < 1e-9) {
            a_min = 0.0; a_max = 1.0;
            return;
        }
        double a0 = (0.0 - p0) / (p1 - p0);
        double aN = ((double)N - p0) / (p1 - p0);
        a_min = std::min(a0, aN);
        a_max = std::max(a0, aN);

        if (p1 > p0) {
            i64 i_min = std::max((i64)1, (i64)std::ceil(a_min * (p1 - p0) + p0));
            i64 i_max = std::min(N, (i64)std::floor(a_max * (p1 - p0) + p0));
            for (i64 i = i_min; i <= i_max; ++i) alphas.push_back(((double)i - p0) / (p1 - p0));
        } else {
            i64 i_min = std::max((i64)1, (i64)std::ceil(a_max * (p1 - p0) + p0));
            i64 i_max = std::min(N, (i64)std::floor(a_min * (p1 - p0) + p0));
            for (i64 i = i_max; i >= i_min; --i) alphas.push_back(((double)i - p0) / (p1 - p0));
        }
    };

    std::vector<double> ax, ay, az;
    double ax_min, ax_max, ay_min, ay_max, az_min, az_max;
    get_alphas(x0, x1, Nx, ax, ax_min, ax_max);
    get_alphas(y0, y1, Ny, ay, ay_min, ay_max);
    get_alphas(z0, z1, Nz, az, az_min, az_max);

    double alpha_min = std::max({0.0, ax_min, ay_min, az_min});
    double alpha_max = std::min({1.0, ax_max, ay_max, az_max});

    if (alpha_min >= alpha_max) return {};

    std::vector<double> all_alphas = {alpha_min, alpha_max};
    for (double a : ax) if (a > alpha_min && a < alpha_max) all_alphas.push_back(a);
    for (double a : ay) if (a > alpha_min && a < alpha_max) all_alphas.push_back(a);
    for (double a : az) if (a > alpha_min && a < alpha_max) all_alphas.push_back(a);

    std::sort(all_alphas.begin(), all_alphas.end());
    all_alphas.erase(std::unique(all_alphas.begin(), all_alphas.end()), all_alphas.end());

    std::vector<SiddonVoxelIntersection> result;
    for (size_t m = 0; m + 1 < all_alphas.size(); ++m) {
        double a_mid = (all_alphas[m] + all_alphas[m+1]) * 0.5;
        double xm = x0 + a_mid * (x1 - x0);
        double ym = y0 + a_mid * (y1 - y0);
        double zm = z0 + a_mid * (z1 - z0);

        i64 ix = (i64)std::floor(xm);
        i64 iy = (i64)std::floor(ym);
        i64 iz = (i64)std::floor(zm);

        if (ix >= 0 && ix < Nx && iy >= 0 && iy < Ny && iz >= 0 && iz < Nz) {
            double chord = (all_alphas[m+1] - all_alphas[m]) * L;
            result.push_back({{ix, iy, iz}, chord});
        }
    }
    return result;
}

} // namespace baselines_3d
