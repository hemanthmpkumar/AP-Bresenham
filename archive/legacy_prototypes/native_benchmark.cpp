#include <iostream>
#include <vector>
#include <chrono>
#include <random>
#include <algorithm>
#include <cmath>

inline int ceil_div(int a, int b) {
    return -((-a) / b);
}

// ---------------------------------------------------------------------------
// 2D Baseline: Liang-Barsky Continuous Clipping + Rounded Bresenham
// ---------------------------------------------------------------------------
struct Point2D { int x, y; };

bool clip_liang_barsky_2d(Point2D p0, Point2D p1, int xmin, int ymin, int xmax, int ymax, Point2D& out_p0, Point2D& out_p1) {
    float dx = static_cast<float>(p1.x - p0.x);
    float dy = static_cast<float>(p1.y - p0.y);

    float p[4] = {-dx, dx, -dy, dy};
    float q[4] = {static_cast<float>(p0.x - xmin), static_cast<float>(xmax - p0.x),
                  static_cast<float>(p0.y - ymin), static_cast<float>(ymax - p0.y)};

    float t_enter = 0.0f;
    float t_leave = 1.0f;

    for (int i = 0; i < 4; ++i) {
        if (p[i] == 0.0f) {
            if (q[i] < 0.0f) return false;
        } else if (p[i] < 0.0f) {
            float t = q[i] / p[i];
            if (t > t_enter) t_enter = t;
        } else {
            float t = q[i] / p[i];
            if (t < t_leave) t_leave = t;
        }
    }

    if (t_enter > t_leave) return false;

    out_p0.x = static_cast<int>(std::round(p0.x + t_enter * dx));
    out_p0.y = static_cast<int>(std::round(p0.y + t_enter * dy));
    out_p1.x = static_cast<int>(std::round(p0.x + t_leave * dx));
    out_p1.y = static_cast<int>(std::round(p0.y + t_leave * dy));
    return true;
}

// ---------------------------------------------------------------------------
// 2D Novel: AP-Bresenham O(1) Integer Setup
// ---------------------------------------------------------------------------
struct AP2DParams {
    int k_start, k_end;
    int dx, dy, sx, sy;
    bool steep;
    int x0, y0, D_start;
};

inline bool ap_bresenham_clip_2d(Point2D p0, Point2D p1, int xmin, int ymin, int xmax, int ymax, AP2DParams& params) {
    int x0 = p0.x, y0 = p0.y;
    int x1 = p1.x, y1 = p1.y;

    int dx_orig = x1 - x0;
    int dy_orig = y1 - y0;

    int sx = (dx_orig >= 0) ? 1 : -1;
    int sy = (dy_orig >= 0) ? 1 : -1;

    int dx = std::abs(dx_orig);
    int dy = std::abs(dy_orig);

    if (dx == 0 && dy == 0) {
        if (xmin <= x0 && x0 <= xmax && ymin <= y0 && y0 <= ymax) {
            params = {0, 0, 0, 0, sx, sy, false, x0, y0, 0};
            return true;
        }
        return false;
    }

    bool steep = dy > dx;
    if (steep) {
        std::swap(x0, y0);
        std::swap(x1, y1);
        std::swap(dx, dy);
        std::swap(sx, sy);
        std::swap(xmin, ymin);
        std::swap(xmax, ymax);
    }

    int w_xmin = (sx == 1) ? (xmin - x0) : (x0 - xmax);
    int w_xmax = (sx == 1) ? (xmax - x0) : (x0 - xmin);
    int w_ymin = (sy == 1) ? (ymin - y0) : (y0 - ymax);
    int w_ymax = (sy == 1) ? (ymax - y0) : (y0 - ymin);

    int kx_min = std::max(0, w_xmin);
    int kx_max = std::min(dx, w_xmax);
    if (kx_min > kx_max) return false;

    int ky_min, ky_max;
    if (dy == 0) {
        if (!(w_ymin <= 0 && 0 <= w_ymax)) return false;
        ky_min = 0;
        ky_max = dx;
    } else {
        int num_min = 2 * dx * w_ymin - dx + 1;
        ky_min = ceil_div(num_min, 2 * dy);
        int num_max = 2 * dx * (w_ymax + 1) - dx;
        ky_max = num_max / (2 * dy);
    }

    int k_start = std::max(kx_min, ky_min);
    int k_end = std::min(kx_max, ky_max);
    if (k_start > k_end) return false;

    int y_rel = (2 * dy * k_start + dx - 1) / (2 * dx);
    int D_start = (2 * dy - dx) + 2 * dy * k_start - 2 * dx * y_rel;

    params = {k_start, k_end, dx, dy, sx, sy, steep, x0, y0, D_start};
    return true;
}

// ---------------------------------------------------------------------------
// 3D Novel: AP-Bresenham 3D Setup
// ---------------------------------------------------------------------------
struct AP3DParams {
    int major, k_start, k_end;
    int d_maj, d_min1, d_min2;
    int s_maj, s_min1, s_min2;
    int p0_maj, p0_min1, p0_min2;
    int D1, D2;
};

inline bool ap_bresenham_clip_3d(int x0, int y0, int z0, int x1, int y1, int z1,
                                 int xmin, int ymin, int zmin, int xmax, int ymax, int zmax,
                                 AP3DParams& params) {
    int dx_orig = x1 - x0, dy_orig = y1 - y0, dz_orig = z1 - z0;
    int sx = (dx_orig >= 0) ? 1 : -1, sy = (dy_orig >= 0) ? 1 : -1, sz = (dz_orig >= 0) ? 1 : -1;
    int dx = std::abs(dx_orig), dy = std::abs(dy_orig), dz = std::abs(dz_orig);

    if (dx == 0 && dy == 0 && dz == 0) return false;

    int major, d_maj, d_min1, d_min2, s_maj, s_min1, s_min2;
    int p0_maj, p0_min1, p0_min2;
    int w_maj_min, w_maj_max, w_min1_min, w_min1_max, w_min2_min, w_min2_max;

    if (dx >= dy && dx >= dz) {
        major = 0;
        d_maj = dx; d_min1 = dy; d_min2 = dz;
        s_maj = sx; s_min1 = sy; s_min2 = sz;
        p0_maj = x0; p0_min1 = y0; p0_min2 = z0;
        w_maj_min = xmin; w_maj_max = xmax;
        w_min1_min = ymin; w_min1_max = ymax;
        w_min2_min = zmin; w_min2_max = zmax;
    } else if (dy >= dx && dy >= dz) {
        major = 1;
        d_maj = dy; d_min1 = dx; d_min2 = dz;
        s_maj = sy; s_min1 = sx; s_min2 = sz;
        p0_maj = y0; p0_min1 = x0; p0_min2 = z0;
        w_maj_min = ymin; w_maj_max = ymax;
        w_min1_min = xmin; w_min1_max = xmax;
        w_min2_min = zmin; w_min2_max = zmax;
    } else {
        major = 2;
        d_maj = dz; d_min1 = dx; d_min2 = dy;
        s_maj = sz; s_min1 = sx; s_min2 = sy;
        p0_maj = z0; p0_min1 = x0; p0_min2 = y0;
        w_maj_min = zmin; w_maj_max = zmax;
        w_min1_min = xmin; w_min1_max = xmax;
        w_min2_min = ymin; w_min2_max = ymax;
    }

    int w_maj_lo = (s_maj == 1) ? (w_maj_min - p0_maj) : (p0_maj - w_maj_max);
    int w_maj_hi = (s_maj == 1) ? (w_maj_max - p0_maj) : (p0_maj - w_maj_min);
    int w_min1_lo = (s_min1 == 1) ? (w_min1_min - p0_min1) : (p0_min1 - w_min1_max);
    int w_min1_hi = (s_min1 == 1) ? (w_min1_max - p0_min1) : (p0_min1 - w_min1_min);
    int w_min2_lo = (s_min2 == 1) ? (w_min2_min - p0_min2) : (p0_min2 - w_min2_max);
    int w_min2_hi = (s_min2 == 1) ? (w_min2_max - p0_min2) : (p0_min2 - w_min2_min);

    int k_maj_min = std::max(0, w_maj_lo);
    int k_maj_max = std::min(d_maj, w_maj_hi);
    if (k_maj_min > k_maj_max) return false;

    int k_min1_min, k_min1_max;
    if (d_min1 == 0) {
        if (!(w_min1_lo <= 0 && 0 <= w_min1_hi)) return false;
        k_min1_min = 0; k_min1_max = d_maj;
    } else {
        int num1_min = 2 * d_maj * w_min1_lo - d_maj + 1;
        k_min1_min = ceil_div(num1_min, 2 * d_min1);
        int num1_max = 2 * d_maj * (w_min1_hi + 1) - d_maj;
        k_min1_max = num1_max / (2 * d_min1);
    }

    int k_min2_min, k_min2_max;
    if (d_min2 == 0) {
        if (!(w_min2_lo <= 0 && 0 <= w_min2_hi)) return false;
        k_min2_min = 0; k_min2_max = d_maj;
    } else {
        int num2_min = 2 * d_maj * w_min2_lo - d_maj + 1;
        k_min2_min = ceil_div(num2_min, 2 * d_min2);
        int num2_max = 2 * d_maj * (w_min2_hi + 1) - d_maj;
        k_min2_max = num2_max / (2 * d_min2);
    }

    int k_start = std::max({k_maj_min, k_min1_min, k_min2_min});
    int k_end = std::min({k_maj_max, k_min1_max, k_min2_max});
    if (k_start > k_end) return false;

    int rel1 = (2 * d_min1 * k_start + d_maj - 1) / (2 * d_maj);
    int D1 = (2 * d_min1 - d_maj) + 2 * d_min1 * k_start - 2 * d_maj * rel1;

    int rel2 = (2 * d_min2 * k_start + d_maj - 1) / (2 * d_maj);
    int D2 = (2 * d_min2 - d_maj) + 2 * d_min2 * k_start - 2 * d_maj * rel2;

    params = {major, k_start, k_end, d_maj, d_min1, d_min2, s_maj, s_min1, s_min2, p0_maj, p0_min1, p0_min2, D1, D2};
    return true;
}

int main() {
    std::mt19937 rng(42);
    std::uniform_int_distribution<int> coord_dist(-1000, 1000);
    std::uniform_int_distribution<int> box_dist(-500, 500);

    const int N = 2000000; // 2 Million operations
    std::vector<Point2D> pts0(N), pts1(N);
    std::vector<int> xmin(N), ymin(N), xmax(N), ymax(N);

    for (int i = 0; i < N; ++i) {
        pts0[i] = {coord_dist(rng), coord_dist(rng)};
        pts1[i] = {coord_dist(rng), coord_dist(rng)};
        int x_a = box_dist(rng), x_b = box_dist(rng);
        int y_a = box_dist(rng), y_b = box_dist(rng);
        xmin[i] = std::min(x_a, x_b); xmax[i] = std::max(x_a, x_b) + 50;
        ymin[i] = std::min(y_a, y_b); ymax[i] = std::max(y_a, y_b) + 50;
    }

    // Benchmark 2D Liang-Barsky Continuous Setup
    Point2D out0, out1;
    int lb_accepted = 0;
    auto t0 = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < N; ++i) {
        if (clip_liang_barsky_2d(pts0[i], pts1[i], xmin[i], ymin[i], xmax[i], ymax[i], out0, out1)) {
            lb_accepted++;
        }
    }
    auto t1 = std::chrono::high_resolution_clock::now();
    double lb_time_ns = std::chrono::duration<double, std::nano>(t1 - t0).count() / N;

    // Benchmark 2D AP-Bresenham Integer Setup
    AP2DParams ap_params;
    int ap_accepted = 0;
    t0 = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < N; ++i) {
        if (ap_bresenham_clip_2d(pts0[i], pts1[i], xmin[i], ymin[i], xmax[i], ymax[i], ap_params)) {
            ap_accepted++;
        }
    }
    t1 = std::chrono::high_resolution_clock::now();
    double ap_time_ns = std::chrono::duration<double, std::nano>(t1 - t0).count() / N;

    // Benchmark 3D AP-Bresenham Setup
    AP3DParams ap3d_params;
    int ap3d_accepted = 0;
    t0 = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < N; ++i) {
        if (ap_bresenham_clip_3d(pts0[i].x, pts0[i].y, xmin[i], pts1[i].x, pts1[i].y, ymax[i],
                                 xmin[i], ymin[i], xmin[i], xmax[i], ymax[i], xmax[i], ap3d_params)) {
            ap3d_accepted++;
        }
    }
    t1 = std::chrono::high_resolution_clock::now();
    double ap3d_time_ns = std::chrono::duration<double, std::nano>(t1 - t0).count() / N;

    std::cout << "==========================================================" << std::endl;
    std::cout << "NATIVE C++ BENCHMARK: 2,000,000 RUNS (Clang -O3, ARM64)" << std::endl;
    std::cout << "==========================================================" << std::endl;
    std::cout << "2D Liang-Barsky Setup:    " << lb_time_ns << " ns/op (" << static_cast<int>(1e9 / lb_time_ns) << " ops/sec)" << std::endl;
    std::cout << "2D AP-Bresenham Setup:    " << ap_time_ns << " ns/op (" << static_cast<int>(1e9 / ap_time_ns) << " ops/sec)" << std::endl;
    std::cout << "3D AP-Bresenham Setup:    " << ap3d_time_ns << " ns/op (" << static_cast<int>(1e9 / ap3d_time_ns) << " ops/sec)" << std::endl;
    std::cout << "==========================================================" << std::endl;
    std::cout << "Accepted lines (2D LB / 2D AP): " << lb_accepted << " / " << ap_accepted << std::endl;
    std::cout << "Accepted rays  (3D AP):         " << ap3d_accepted << std::endl;

    return 0;
}
