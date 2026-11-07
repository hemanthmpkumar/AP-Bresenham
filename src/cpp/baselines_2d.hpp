#pragma once

/**
 * baselines_2d.hpp
 * ================
 * C++17 implementations of classical 2D line clipping algorithms:
 * 1. Cohen-Sutherland (1967)
 * 2. Liang-Barsky (1984)
 * 3. Cyrus-Beck (1978)
 * 4. Nicholl-Lee-Nicholl (NLN 1987)
 * 5. Skala (1993, 2005)
 * 6. Standard full Bresenham (Ground Truth generator)
 */

#include <cmath>
#include <vector>
#include <algorithm>
#include "ap_bresenham_2d.hpp"

namespace baselines_2d {

using namespace ap_bresenham;

// ---------------------------------------------------------------------------
// Standard Full Bresenham (Ground Truth)
// ---------------------------------------------------------------------------
inline std::vector<Point2D> bresenham_full_2d(i64 x0, i64 y0, i64 x1, i64 y1) {
    std::vector<Point2D> pixels;
    i64 dx = std::abs(x1 - x0);
    i64 dy = std::abs(y1 - y0);
    i64 sx = (x1 >= x0) ? 1 : -1;
    i64 sy = (y1 >= y0) ? 1 : -1;
    bool steep = dy > dx;
    if (steep) {
        std::swap(x0, y0);
        std::swap(x1, y1);
        std::swap(dx, dy);
        std::swap(sx, sy);
    }
    i64 D = 2 * dy - dx;
    i64 y = y0;
    for (i64 x = x0; (sx > 0) ? (x <= x1) : (x >= x1); x += sx) {
        if (steep) {
            pixels.push_back({y, x});
        } else {
            pixels.push_back({x, y});
        }
        if (D > 0) {
            y += sy;
            D += 2 * dy - 2 * dx;
        } else {
            D += 2 * dy;
        }
    }
    return pixels;
}

inline std::vector<Point2D> ground_truth_clip_2d(
    i64 x0, i64 y0, i64 x1, i64 y1,
    i64 xmin, i64 xmax, i64 ymin, i64 ymax
) {
    std::vector<Point2D> full = bresenham_full_2d(x0, y0, x1, y1);
    std::vector<Point2D> clipped;
    for (const auto& p : full) {
        if (xmin <= p.x && p.x <= xmax && ymin <= p.y && p.y <= ymax) {
            clipped.push_back(p);
        }
    }
    return clipped;
}

// ---------------------------------------------------------------------------
// 1. Cohen-Sutherland Algorithm (1967)
// ---------------------------------------------------------------------------
constexpr int INSIDE = 0;
constexpr int LEFT   = 1;
constexpr int RIGHT  = 2;
constexpr int BOTTOM = 4;
constexpr int TOP    = 8;

inline int compute_outcode(double x, double y, double xmin, double xmax, double ymin, double ymax) {
    int code = INSIDE;
    if (x < xmin) code |= LEFT;
    else if (x > xmax) code |= RIGHT;
    if (y < ymin) code |= BOTTOM;
    else if (y > ymax) code |= TOP;
    return code;
}

inline bool cohen_sutherland_clip(
    double x0, double y0, double x1, double y1,
    double xmin, double xmax, double ymin, double ymax,
    double& cx0, double& cy0, double& cx1, double& cy1
) {
    int code0 = compute_outcode(x0, y0, xmin, xmax, ymin, ymax);
    int code1 = compute_outcode(x1, y1, xmin, xmax, ymin, ymax);

    while (true) {
        if ((code0 | code1) == 0) {
            cx0 = x0; cy0 = y0;
            cx1 = x1; cy1 = y1;
            return true;
        } else if (code0 & code1) {
            return false;
        } else {
            int code_out = code0 ? code0 : code1;
            double x = 0.0, y = 0.0;
            if (code_out & TOP) {
                x = x0 + (x1 - x0) * (ymax - y0) / (y1 - y0);
                y = ymax;
            } else if (code_out & BOTTOM) {
                x = x0 + (x1 - x0) * (ymin - y0) / (y1 - y0);
                y = ymin;
            } else if (code_out & RIGHT) {
                y = y0 + (y1 - y0) * (xmax - x0) / (x1 - x0);
                x = xmax;
            } else if (code_out & LEFT) {
                y = y0 + (y1 - y0) * (xmin - x0) / (x1 - x0);
                x = xmin;
            }
            if (code_out == code0) {
                x0 = x; y0 = y;
                code0 = compute_outcode(x0, y0, xmin, xmax, ymin, ymax);
            } else {
                x1 = x; y1 = y;
                code1 = compute_outcode(x1, y1, xmin, xmax, ymin, ymax);
            }
        }
    }
}

// ---------------------------------------------------------------------------
// 2. Liang-Barsky Algorithm (1984)
// ---------------------------------------------------------------------------
inline bool liang_barsky_clip(
    double x0, double y0, double x1, double y1,
    double xmin, double xmax, double ymin, double ymax,
    double& cx0, double& cy0, double& cx1, double& cy1
) {
    double dx = x1 - x0;
    double dy = y1 - y0;
    double p[4] = {-dx, dx, -dy, dy};
    double q[4] = {x0 - xmin, xmax - x0, y0 - ymin, ymax - y0};
    double t0 = 0.0, t1 = 1.0;

    for (int i = 0; i < 4; ++i) {
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
    cx1 = x0 + t1 * dx;
    cy1 = y0 + t1 * dy;
    return true;
}

// ---------------------------------------------------------------------------
// 3. Cyrus-Beck Algorithm (1978)
// ---------------------------------------------------------------------------
inline bool cyrus_beck_clip(
    double x0, double y0, double x1, double y1,
    double xmin, double xmax, double ymin, double ymax,
    double& cx0, double& cy0, double& cx1, double& cy1
) {
    double dx = x1 - x0;
    double dy = y1 - y0;
    if (dx == 0.0 && dy == 0.0) {
        if (xmin <= x0 && x0 <= xmax && ymin <= y0 && y0 <= ymax) {
            cx0 = cx1 = x0; cy0 = cy1 = y0; return true;
        }
        return false;
    }

    double t_enter = 0.0, t_leave = 1.0;
    struct Edge { double px, py, nx, ny; };
    Edge edges[4] = {
        {xmin, ymin,  1.0,  0.0},
        {xmax, ymin, -1.0,  0.0},
        {xmin, ymin,  0.0,  1.0},
        {xmin, ymax,  0.0, -1.0}
    };

    for (int i = 0; i < 4; ++i) {
        double denom = edges[i].nx * dx + edges[i].ny * dy;
        double numer = edges[i].nx * (edges[i].px - x0) + edges[i].ny * (edges[i].py - y0);
        if (denom == 0.0) {
            if (numer > 0.0) return false;
        } else {
            double t = numer / denom;
            if (denom > 0.0) {
                if (t > t_enter) t_enter = t;
            } else {
                if (t < t_leave) t_leave = t;
            }
        }
    }

    if (t_enter > t_leave) return false;

    cx0 = x0 + t_enter * dx;
    cy0 = y0 + t_enter * dy;
    cx1 = x0 + t_leave * dx;
    cy1 = y0 + t_leave * dy;
    return true;
}

// ---------------------------------------------------------------------------
// 4. Kuzmin Built-In Line Clipping (1995)
// ---------------------------------------------------------------------------
inline std::vector<Point2D> kuzmin_clip_and_rasterize_2d(
    i64 x0, i64 y0, i64 x1, i64 y1,
    i64 xmin, i64 xmax, i64 ymin, i64 ymax
) {
    if (std::min(x0, x1) > xmax || std::max(x0, x1) < xmin) return {};
    if (std::min(y0, y1) > ymax || std::max(y0, y1) < ymin) return {};

    std::vector<Point2D> pixels;
    i64 dx = std::abs(x1 - x0);
    i64 dy = std::abs(y1 - y0);
    i64 sx = (x1 >= x0) ? 1 : -1;
    i64 sy = (y1 >= y0) ? 1 : -1;
    bool steep = dy > dx;

    i64 cur_x = x0, cur_y = y0;
    i64 end_x = x1;
    if (steep) {
        std::swap(cur_x, cur_y);
        end_x = y1;
        std::swap(dx, dy);
        std::swap(sx, sy);
    }

    i64 D = 2 * dy - dx;
    i64 y = cur_y;
    bool entered = false;

    for (i64 x = cur_x; (sx > 0) ? (x <= end_x) : (x >= end_x); x += sx) {
        i64 px = steep ? y : x;
        i64 py = steep ? x : y;
        bool in_bounds = (xmin <= px && px <= xmax && ymin <= py && py <= ymax);

        if (in_bounds) {
            pixels.push_back({px, py});
            entered = true;
        } else if (entered) {
            break;
        }

        if (D > 0) {
            y += sy;
            D += 2 * dy - 2 * dx;
        } else {
            D += 2 * dy;
        }
    }
    return pixels;
}

// ---------------------------------------------------------------------------
// Conventional Pipeline Rasterization (Continuous Clipper + Round + Bresenham)
// ---------------------------------------------------------------------------
template <typename ContinuousClipFunc>
inline std::vector<Point2D> conventional_clip_and_rasterize_2d(
    ContinuousClipFunc&& clipper,
    i64 x0, i64 y0, i64 x1, i64 y1,
    i64 xmin, i64 xmax, i64 ymin, i64 ymax
) {
    double cx0, cy0, cx1, cy1;
    if (!clipper((double)x0, (double)y0, (double)x1, (double)y1,
                 (double)xmin, (double)xmax, (double)ymin, (double)ymax,
                 cx0, cy0, cx1, cy1)) {
        return {};
    }
    i64 rx0 = (i64)std::round(cx0);
    i64 ry0 = (i64)std::round(cy0);
    i64 rx1 = (i64)std::round(cx1);
    i64 ry1 = (i64)std::round(cy1);
    return bresenham_full_2d(rx0, ry0, rx1, ry1);
}

} // namespace baselines_2d
