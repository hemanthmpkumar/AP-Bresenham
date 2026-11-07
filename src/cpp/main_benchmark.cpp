/**
 * main_benchmark.cpp
 * ==================
 * High-performance native C++ benchmark suite measuring nanosecond-level setup latency,
 * throughput across trajectory lengths, and end-to-end pixel/voxel generation.
 *
 * Algorithms evaluated:
 *   2D:
 *     - Cohen-Sutherland (1967)
 *     - Liang-Barsky (1984)
 *     - Cyrus-Beck (1978)
 *     - Kuzmin Built-In (1995)
 *     - AP-Bresenham 2D (Ours)
 *   3D:
 *     - 3D Slab Clipper (Liang-Barsky 3D)
 *     - AP-Bresenham 3D (Ours)
 */

#include <iostream>
#include <vector>
#include <chrono>
#include <random>
#include <fstream>
#include <iomanip>
#include <numeric>
#include <cmath>
#include "ap_bresenham_2d.hpp"
#include "ap_bresenham_3d.hpp"
#include "baselines_2d.hpp"
#include "baselines_3d.hpp"

using namespace ap_bresenham;
using namespace baselines_2d;
using namespace baselines_3d;

template <typename T>
static void escape(T* p) {
    asm volatile("" : : "g"(p) : "memory");
}

int main() {
    constexpr size_t N_RUNS = 2000000;
    std::cout << "=================================================================" << std::endl;
    std::cout << "  AP-Bresenham Native High-Throughput C++ Benchmark (" << N_RUNS << " ops)" << std::endl;
    std::cout << "=================================================================" << std::endl;

    std::mt19937_64 rng(1337);
    std::uniform_int_distribution<i64> cdist(-200, 200);
    std::uniform_int_distribution<i64> wdist(-100, 100);

    // Generate test datasets
    struct Line2D { i64 x0, y0, x1, y1, xmin, xmax, ymin, ymax; };
    std::vector<Line2D> lines2d;
    lines2d.reserve(N_RUNS);
    for (size_t i = 0; i < N_RUNS; ++i) {
        i64 x0 = cdist(rng), y0 = cdist(rng);
        i64 x1 = cdist(rng), y1 = cdist(rng);
        i64 w1 = wdist(rng), w2 = wdist(rng);
        i64 w3 = wdist(rng), w4 = wdist(rng);
        lines2d.push_back({
            x0, y0, x1, y1,
            std::min(w1, w2), std::max(w1, w2),
            std::min(w3, w4), std::max(w3, w4)
        });
    }

    struct Ray3D { i64 x0, y0, z0, x1, y1, z1, xmin, xmax, ymin, ymax, zmin, zmax; };
    std::vector<Ray3D> rays3d;
    rays3d.reserve(N_RUNS);
    for (size_t i = 0; i < N_RUNS; ++i) {
        i64 x0 = cdist(rng), y0 = cdist(rng), z0 = cdist(rng);
        i64 x1 = cdist(rng), y1 = cdist(rng), z1 = cdist(rng);
        i64 w1 = wdist(rng), w2 = wdist(rng);
        i64 w3 = wdist(rng), w4 = wdist(rng);
        i64 w5 = wdist(rng), w6 = wdist(rng);
        rays3d.push_back({
            x0, y0, z0, x1, y1, z1,
            std::min(w1, w2), std::max(w1, w2),
            std::min(w3, w4), std::max(w3, w4),
            std::min(w5, w6), std::max(w5, w6)
        });
    }

    // -----------------------------------------------------------------------
    // Benchmark 1: 2D Setup Latencies
    // -----------------------------------------------------------------------
    std::cout << "\n>>> [2D Line Clipping Setup Benchmarks]" << std::endl;

    // 1.1 Cohen-Sutherland
    volatile double dummy_d = 0.0;
    auto t0 = std::chrono::high_resolution_clock::now();
    for (size_t i = 0; i < N_RUNS; ++i) {
        const auto& l = lines2d[i];
        double cx0, cy0, cx1, cy1;
        cohen_sutherland_clip((double)l.x0, (double)l.y0, (double)l.x1, (double)l.y1,
                              (double)l.xmin, (double)l.xmax, (double)l.ymin, (double)l.ymax,
                              cx0, cy0, cx1, cy1);
        dummy_d += cx0;
    }
    auto t1 = std::chrono::high_resolution_clock::now();
    double cs_ns = std::chrono::duration<double, std::nano>(t1 - t0).count() / N_RUNS;

    // 1.2 Liang-Barsky
    t0 = std::chrono::high_resolution_clock::now();
    for (size_t i = 0; i < N_RUNS; ++i) {
        const auto& l = lines2d[i];
        double cx0, cy0, cx1, cy1;
        liang_barsky_clip((double)l.x0, (double)l.y0, (double)l.x1, (double)l.y1,
                          (double)l.xmin, (double)l.xmax, (double)l.ymin, (double)l.ymax,
                          cx0, cy0, cx1, cy1);
        dummy_d += cx0;
    }
    t1 = std::chrono::high_resolution_clock::now();
    double lb_ns = std::chrono::duration<double, std::nano>(t1 - t0).count() / N_RUNS;

    // 1.3 Cyrus-Beck
    t0 = std::chrono::high_resolution_clock::now();
    for (size_t i = 0; i < N_RUNS; ++i) {
        const auto& l = lines2d[i];
        double cx0, cy0, cx1, cy1;
        cyrus_beck_clip((double)l.x0, (double)l.y0, (double)l.x1, (double)l.y1,
                        (double)l.xmin, (double)l.xmax, (double)l.ymin, (double)l.ymax,
                        cx0, cy0, cx1, cy1);
        dummy_d += cx0;
    }
    t1 = std::chrono::high_resolution_clock::now();
    double cb_ns = std::chrono::duration<double, std::nano>(t1 - t0).count() / N_RUNS;

    // 1.4 AP-Bresenham 2D (Ours)
    volatile i64 dummy_i = 0;
    t0 = std::chrono::high_resolution_clock::now();
    for (size_t i = 0; i < N_RUNS; ++i) {
        const auto& l = lines2d[i];
        ClipState2D st = clip_bounds_2d(l.x0, l.y0, l.x1, l.y1, l.xmin, l.xmax, l.ymin, l.ymax);
        dummy_i += st.k_start + st.D_start;
    }
    t1 = std::chrono::high_resolution_clock::now();
    double ap2d_ns = std::chrono::duration<double, std::nano>(t1 - t0).count() / N_RUNS;

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "  Cohen-Sutherland (1967): " << cs_ns   << " ns/op (" << 1000.0 / cs_ns   << " Mops/s)" << std::endl;
    std::cout << "  Liang-Barsky     (1984): " << lb_ns   << " ns/op (" << 1000.0 / lb_ns   << " Mops/s)" << std::endl;
    std::cout << "  Cyrus-Beck       (1978): " << cb_ns   << " ns/op (" << 1000.0 / cb_ns   << " Mops/s)" << std::endl;
    std::cout << "  AP-Bresenham 2D  (Ours): " << ap2d_ns << " ns/op (" << 1000.0 / ap2d_ns << " Mops/s)  --> "
              << (lb_ns / ap2d_ns) << "x speedup vs Liang-Barsky" << std::endl;

    // -----------------------------------------------------------------------
    // Benchmark 2: 3D Ray Clipping Setup Latencies
    // -----------------------------------------------------------------------
    std::cout << "\n>>> [3D Ray Clipping Setup Benchmarks]" << std::endl;

    // 2.1 3D Slab Clipper
    t0 = std::chrono::high_resolution_clock::now();
    for (size_t i = 0; i < N_RUNS; ++i) {
        const auto& r = rays3d[i];
        double cx0, cy0, cz0, cx1, cy1, cz1;
        slab_clip_3d((double)r.x0, (double)r.y0, (double)r.z0,
                     (double)r.x1, (double)r.y1, (double)r.z1,
                     (double)r.xmin, (double)r.xmax,
                     (double)r.ymin, (double)r.ymax,
                     (double)r.zmin, (double)r.zmax,
                     cx0, cy0, cz0, cx1, cy1, cz1);
        dummy_d += cx0;
    }
    t1 = std::chrono::high_resolution_clock::now();
    double slab3d_ns = std::chrono::duration<double, std::nano>(t1 - t0).count() / N_RUNS;

    // 2.2 AP-Bresenham 3D (Ours)
    t0 = std::chrono::high_resolution_clock::now();
    for (size_t i = 0; i < N_RUNS; ++i) {
        const auto& r = rays3d[i];
        ClipState3D st = clip_bounds_3d(r.x0, r.y0, r.z0, r.x1, r.y1, r.z1,
                                        r.xmin, r.xmax, r.ymin, r.ymax, r.zmin, r.zmax);
        dummy_i += st.k_start + st.D1_start + st.D2_start;
    }
    t1 = std::chrono::high_resolution_clock::now();
    double ap3d_ns = std::chrono::duration<double, std::nano>(t1 - t0).count() / N_RUNS;

    std::cout << "  3D Slab Clipper (LB3D):  " << slab3d_ns << " ns/op (" << 1000.0 / slab3d_ns << " Mops/s)" << std::endl;
    std::cout << "  AP-Bresenham 3D  (Ours): " << ap3d_ns   << " ns/op (" << 1000.0 / ap3d_ns   << " Mops/s)  --> "
              << (slab3d_ns / ap3d_ns) << "x speedup vs 3D Slab Clipper" << std::endl;

    // -----------------------------------------------------------------------
    // Benchmark 3: Performance vs Trajectory Length (Short, Medium, Long, Ultra-Long)
    // -----------------------------------------------------------------------
    std::cout << "\n>>> [Throughput vs Ray Trajectory Length (100,000 rays each)]" << std::endl;
    std::vector<i64> lengths = {16, 64, 256, 1024, 4096};
    constexpr size_t LEN_RUNS = 100000;

    for (i64 len : lengths) {
        t0 = std::chrono::high_resolution_clock::now();
        volatile i64 count = 0;
        for (size_t i = 0; i < LEN_RUNS; ++i) {
            i64 x0 = 0, y0 = 0, z0 = 0;
            i64 x1 = len, y1 = len * 3 / 4, z1 = len / 2;
            ClipState3D st = clip_bounds_3d(x0, y0, z0, x1, y1, z1, 10, len - 10, 10, len - 10, 5, len / 2 - 5);
            count += st.k_start;
        }
        t1 = std::chrono::high_resolution_clock::now();
        double lat_ns = std::chrono::duration<double, std::nano>(t1 - t0).count() / LEN_RUNS;
        std::cout << "  Length " << std::setw(5) << len << " voxels: Setup Latency = "
                  << std::setw(6) << lat_ns << " ns/op (" << (1000.0 / lat_ns) << " Mops/s)" << std::endl;
    }

    // -----------------------------------------------------------------------
    // Benchmark 4: End-to-End Voxel Generation Throughput
    // -----------------------------------------------------------------------
    std::cout << "\n>>> [End-to-End Pixel/Voxel Generation Throughput (100,000 items)]" << std::endl;
    size_t SUB_N = 100000;
    size_t total_px = 0;

    t0 = std::chrono::high_resolution_clock::now();
    for (size_t i = 0; i < SUB_N; ++i) {
        const auto& l = lines2d[i];
        rasterize_clipped_2d(l.x0, l.y0, l.x1, l.y1, l.xmin, l.xmax, l.ymin, l.ymax,
                             [&total_px](i64 x, i64 y) {
                                 total_px += (x ^ y);
                             });
    }
    t1 = std::chrono::high_resolution_clock::now();
    double ap2d_full_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    std::cout << "  AP-Bresenham 2D Raster Throughput: " << (SUB_N / ap2d_full_ms * 1000.0) / 1e6 << " M lines/sec" << std::endl;

    size_t total_vx = 0;
    t0 = std::chrono::high_resolution_clock::now();
    for (size_t i = 0; i < SUB_N; ++i) {
        const auto& r = rays3d[i];
        rasterize_clipped_3d(r.x0, r.y0, r.z0, r.x1, r.y1, r.z1,
                             r.xmin, r.xmax, r.ymin, r.ymax, r.zmin, r.zmax,
                             [&total_vx](i64 x, i64 y, i64 z) {
                                 total_vx += (x ^ y ^ z);
                             });
    }
    t1 = std::chrono::high_resolution_clock::now();
    double ap3d_full_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    std::cout << "  AP-Bresenham 3D Voxel Throughput:  " << (SUB_N / ap3d_full_ms * 1000.0) / 1e6 << " M rays/sec" << std::endl;

    // Export raw JSON results
    std::ofstream jout("src/results/benchmark_results.json");
    if (jout.is_open()) {
        jout << "{\n";
        jout << "  \"runs\": " << N_RUNS << ",\n";
        jout << "  \"2d\": {\n";
        jout << "    \"cohen_sutherland_ns\": " << cs_ns << ",\n";
        jout << "    \"liang_barsky_ns\": " << lb_ns << ",\n";
        jout << "    \"cyrus_beck_ns\": " << cb_ns << ",\n";
        jout << "    \"ap_bresenham_ns\": " << ap2d_ns << ",\n";
        jout << "    \"speedup_vs_lb\": " << (lb_ns / ap2d_ns) << "\n";
        jout << "  },\n";
        jout << "  \"3d\": {\n";
        jout << "    \"slab_3d_ns\": " << slab3d_ns << ",\n";
        jout << "    \"ap_bresenham_3d_ns\": " << ap3d_ns << ",\n";
        jout << "    \"speedup_vs_slab\": " << (slab3d_ns / ap3d_ns) << "\n";
        jout << "  }\n";
        jout << "}\n";
        jout.close();
        std::cout << "\n[Exported results to src/results/benchmark_results.json]" << std::endl;
    }

    // Export CSV results
    std::ofstream cout("src/results/benchmark_results.csv");
    if (cout.is_open()) {
        cout << "Algorithm,Dimension,Latency_ns,Throughput_Mops\n";
        cout << "Cohen-Sutherland,2D," << cs_ns << "," << (1000.0 / cs_ns) << "\n";
        cout << "Liang-Barsky,2D," << lb_ns << "," << (1000.0 / lb_ns) << "\n";
        cout << "Cyrus-Beck,2D," << cb_ns << "," << (1000.0 / cb_ns) << "\n";
        cout << "AP-Bresenham,2D," << ap2d_ns << "," << (1000.0 / ap2d_ns) << "\n";
        cout << "3D Slab Clipper,3D," << slab3d_ns << "," << (1000.0 / slab3d_ns) << "\n";
        cout << "3D AP-Bresenham,3D," << ap3d_ns << "," << (1000.0 / ap3d_ns) << "\n";
        cout.close();
        std::cout << "[Exported results to src/results/benchmark_results.csv]" << std::endl;
    }

    return 0;
}
