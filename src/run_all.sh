#!/usr/bin/env bash
# ==============================================================================
# run_all.sh
# Master Execution & Verification Script for AP-Bresenham Research Paper
# ==============================================================================
set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BASE_DIR"

echo "======================================================================"
echo "  AP-Bresenham: Complete Verification and Benchmark Pipeline"
echo "  Workspace: $BASE_DIR"
echo "======================================================================"

# 1. Compile C++ binaries
echo -e "\n[1/6] Compiling High-Performance Native C++ Binaries (Clang -O3)..."
mkdir -p build src/results/figures
clang++ -O3 -std=c++17 -march=native -Wall -Wextra -Isrc/cpp src/cpp/test_cpp_invariants.cpp -o build/test_cpp_invariants
clang++ -O3 -std=c++17 -march=native -Wall -Wextra -Isrc/cpp src/cpp/main_benchmark.cpp -o build/main_benchmark
echo "✓ Binaries compiled successfully."

# 2. Run C++ invariant tests
echo -e "\n[2/6] Executing C++ Mathematical Invariants & Property Tests (70k items)..."
./build/test_cpp_invariants

# 3. Run Python unit tests
echo -e "\n[3/6] Executing Python Invariant Tests..."
python3 src/tests/test_2d_mathematical_invariants.py
python3 src/tests/test_3d_invariants.py

# 4. Run Native C++ high-throughput benchmark
echo -e "\n[4/6] Executing C++ Micro-benchmarks (2,000,000 runs)..."
./build/main_benchmark

# 5. Run Paper results verification & comprehensive baselines
echo -e "\n[5/6] Executing Master Verification of Paper Tables 1-4 & CT Simulation..."
python3 src/benchmarks/verify_paper_results.py
python3 src/python/radon_transform_sim.py
python3 src/benchmarks/comprehensive_benchmark_suite.py

# 6. Generate Publication Figures
echo -e "\n[6/6] Generating Publication Figures (PNG & PDF)..."
python3 src/benchmarks/plot_results.py

echo -e "\n======================================================================"
echo "  ALL VERIFICATION TESTS AND BENCHMARKS EXECUTED SUCCESSFULLY!"
echo "  Results and figures stored in: src/results/"
echo "======================================================================"
