#pragma once

/**
 * ap_bresenham_2d.hpp
 * ===================
 * Production-grade, zero-allocation, header-only C++17 implementation
 * of 2D Analytical Phase-Compensated Bresenham (AP-Bresenham) line clipping.
 *
 * Guarantees:
 *   - Pure integer arithmetic (no FPU instructions, no cross-register stalls)
 *   - O(1) setup time: exactly <= 6 multiplies, <= 4 integer divisions
 *   - 100% bit-level equivalence with Clip(Dig(L), Omega)
 *   - Strictly preserves 8-connectivity across arbitrary clipping window boundaries
 */

#include <cstdint>
#include <cstdlib>
#include <algorithm>
#include <vector>
#include <utility>

namespace ap_bresenham {

using i64 = int64_t;

struct Point2D {
    i64 x, y;
};

struct Rect2D {
    i64 xmin, xmax;
    i64 ymin, ymax;
};

struct ClipState2D {
    i64 k_start, k_end;
    i64 dx, dy;
    i64 sx, sy;
    i64 x0c, y0c;
    i64 D_start;
    i64 y_rel;
    bool steep;
    bool valid;
};

// Exact integer floor division for b > 0
inline constexpr i64 floor_div(i64 a, i64 b) noexcept {
    return a / b - ((a % b < 0) ? 1 : 0);
}

// Exact integer ceiling division for b > 0
inline constexpr i64 ceil_div(i64 a, i64 b) noexcept {
    return a / b + ((a % b > 0) ? 1 : 0);
}

/**
 * O(1) Diophantine Boundary Inversion and Phase Calculation for 2D.
 */
inline ClipState2D clip_bounds_2d(
    i64 x0, i64 y0, i64 x1, i64 y1,
    i64 xmin, i64 xmax, i64 ymin, i64 ymax
) noexcept {
    i64 sx = (x1 >= x0) ? 1 : -1;
    i64 sy = (y1 >= y0) ? 1 : -1;
    i64 dx = std::abs(x1 - x0);
    i64 dy = std::abs(y1 - y0);
    bool steep = dy > dx;
    i64 x0c = x0, y0c = y0;

    if (steep) {
        std::swap(dx, dy);
        std::swap(sx, sy);
        std::swap(x0c, y0c);
        std::swap(xmin, ymin);
        std::swap(xmax, ymax);
    }

    if (dx == 0) {
        if (xmin <= x0 && x0 <= xmax && ymin <= y0 && y0 <= ymax) {
            return {0, 0, 0, 0, sx, sy, x0c, y0c, 0, 0, steep, true};
        }
        return {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, false, false};
    }

    i64 wx_min = (sx > 0) ? (xmin - x0c) : (x0c - xmax);
    i64 wx_max = (sx > 0) ? (xmax - x0c) : (x0c - xmin);
    i64 wy_min = (sy > 0) ? (ymin - y0c) : (y0c - ymax);
    i64 wy_max = (sy > 0) ? (ymax - y0c) : (y0c - ymin);

    i64 kx_min = std::max((i64)0, wx_min);
    i64 kx_max = std::min(dx, wx_max);
    if (kx_min > kx_max) {
        return {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, false, false};
    }

    i64 ky_min, ky_max;
    if (dy == 0) {
        if (wy_min <= 0 && 0 <= wy_max) {
            ky_min = 0;
            ky_max = dx;
        } else {
            return {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, false, false};
        }
    } else {
        ky_min = ceil_div(2 * dx * wy_min - dx + 1, 2 * dy);
        ky_max = floor_div(2 * dx * (wy_max + 1) - dx, 2 * dy);
    }

    i64 k_start = std::max(kx_min, ky_min);
    i64 k_end   = std::min(kx_max, ky_max);
    if (k_start > k_end) {
        return {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, false, false};
    }

    i64 y_rel   = floor_div(2 * dy * k_start + dx - 1, 2 * dx);
    i64 D_start = (2 * dy - dx) + 2 * dy * k_start - 2 * dx * y_rel;

    return {k_start, k_end, dx, dy, sx, sy, x0c, y0c, D_start, y_rel, steep, true};
}

/**
 * Direct rasterization of the clipped segment via lambda or callback.
 * Zero dynamic heap memory allocations.
 */
template <typename PixelCallback>
inline void rasterize_clipped_2d(
    i64 x0, i64 y0, i64 x1, i64 y1,
    i64 xmin, i64 xmax, i64 ymin, i64 ymax,
    PixelCallback&& emit_pixel
) {
    ClipState2D st = clip_bounds_2d(x0, y0, x1, y1, xmin, xmax, ymin, ymax);
    if (!st.valid) return;

    i64 D = st.D_start;
    i64 y_rel = st.y_rel;
    i64 dx2 = 2 * st.dx;
    i64 dy2 = 2 * st.dy;

    for (i64 k = st.k_start; k <= st.k_end; ++k) {
        i64 wx = st.x0c + st.sx * k;
        i64 wy = st.y0c + st.sy * y_rel;
        if (st.steep) {
            emit_pixel(wy, wx);
        } else {
            emit_pixel(wx, wy);
        }

        if (D > 0) {
            y_rel += 1;
            D -= dx2;
        }
        D += dy2;
    }
}

/**
 * Standard vector returning version.
 */
inline std::vector<Point2D> clip_and_rasterize_2d(
    i64 x0, i64 y0, i64 x1, i64 y1,
    i64 xmin, i64 xmax, i64 ymin, i64 ymax
) {
    std::vector<Point2D> pixels;
    ClipState2D st = clip_bounds_2d(x0, y0, x1, y1, xmin, xmax, ymin, ymax);
    if (!st.valid) return pixels;

    pixels.reserve(st.k_end - st.k_start + 1);
    i64 D = st.D_start;
    i64 y_rel = st.y_rel;
    i64 dx2 = 2 * st.dx;
    i64 dy2 = 2 * st.dy;

    for (i64 k = st.k_start; k <= st.k_end; ++k) {
        i64 wx = st.x0c + st.sx * k;
        i64 wy = st.y0c + st.sy * y_rel;
        if (st.steep) {
            pixels.push_back({wy, wx});
        } else {
            pixels.push_back({wx, wy});
        }
        if (D > 0) {
            y_rel += 1;
            D -= dx2;
        }
        D += dy2;
    }
    return pixels;
}

} // namespace ap_bresenham
