# Analytical Phase-Compensated Bresenham (AP-Bresenham)

**Official Source Code & Experimental Benchmark Suite** for the research paper:
> *"Analytical Phase-Compensated Bresenham: Topologically Exact Integer Clipping on Pixel and Voxel Lattices"*

---

## 📁 Repository Structure

```text
src/
├── cpp/
│   ├── ap_bresenham_2d.hpp      # Header-only C++17 2D AP-Bresenham (Zero allocation)
│   ├── ap_bresenham_3d.hpp      # Header-only C++17 3D AP-Bresenham (Dual accumulators)
│   ├── baselines_2d.hpp         # C++ baselines (Cohen-Sutherland, Liang-Barsky, Cyrus-Beck)
│   ├── baselines_3d.hpp         # C++ 3D baselines (3D Slab, Amanatides-Woo 3D DDA, Siddon)
│   ├── test_cpp_invariants.cpp  # Exhaustive C++ property & invariant test runner (70k items)
│   └── main_benchmark.cpp       # Nanosecond-level latency & throughput micro-benchmarks
├── python/
│   ├── ap_bresenham_2d.py       # Core 2D AP-Bresenham & ground-truth rasterizer
│   ├── ap_bresenham_3d.py       # Core 3D AP-Bresenham & 3D ground truth
│   ├── baselines_2d.py          # Python 2D baselines (CS, LB, Cyrus-Beck, NLN, Skala)
│   ├── baselines_3d.py          # Python 3D baselines (3D Slab, Amanatides-Woo, Siddon, Jacobs)
│   └── radon_transform_sim.py   # CT forward projection / Radon transform simulation
├── tests/
│   ├── test_2d_mathematical_invariants.py # 2D Lemmas 1-2, Theorem 1-3, 8-connectivity
│   └── test_3d_invariants.py              # 3D Corollary 1, 26-connectivity, 27-chunk partition
├── benchmarks/
│   ├── verify_paper_results.py            # Reproduces Tables 1-4 from paper
│   ├── comprehensive_benchmark_suite.py   # Multi-algorithm comparison
│   └── plot_results.py                    # Generates publication Figures 1-4
├── results/
│   ├── benchmark_results.json             # Raw C++ micro-benchmark measurements
│   ├── benchmark_results.csv              # Tabular latency/throughput dataset
│   └── figures/                           # Generated publication figures (PNG & PDF)
├── Makefile                     # Build & test automation
└── run_all.sh                   # Master single-command verification script
```

---

## 🚀 Quick Start (Single Command)

To build all C++ binaries, run all unit/property tests, execute the benchmarks, verify the paper tables, and generate publication figures:

```bash
chmod +x src/run_all.sh
./src/run_all.sh
```

Or using `make`:

```bash
make -f src/Makefile run-all
```

---

## 🔬 Key Mathematical Invariants Implemented

### 1. Lemma 1: Exact Discrete 2D Coordinate Formula
$$\forall k \in [0, \Delta x]: \quad y(k) = y_0 + \left\lfloor \frac{2\Delta y \cdot k + \Delta x - 1}{2\Delta x} \right\rfloor$$

### 2. Lemma 2: Exact Analytical Decision Variable
$$D(k) = (2\Delta y - \Delta x) + 2\Delta y \cdot k - 2\Delta x \cdot (y(k) - y_0)$$

### 3. Theorem 2: $O(1)$ Diophantine Boundary Inversion
$$k_{y,\min} = \left\lceil \frac{2\Delta x (Y_{\min} - y_0) - \Delta x + 1}{2\Delta y} \right\rceil, \quad k_{y,\max} = \left\lfloor \frac{2\Delta x (Y_{\max} - y_0 + 1) - \Delta x}{2\Delta y} \right\rfloor$$
$$k_{\mathrm{start}} = \max(k_{x,\min}, k_{y,\min}), \quad k_{\mathrm{end}} = \min(k_{x,\max}, k_{y,\max})$$

### 4. Corollary 1: 3D Dual-Accumulator Phase Injection
$$D_1(k_{\mathrm{start}}) = (2\Delta_{\mathrm{min1}} - \Delta_{\mathrm{maj}}) + 2\Delta_{\mathrm{min1}} k_{\mathrm{start}} - 2\Delta_{\mathrm{maj}} \cdot m_{1,\mathrm{rel}}$$
$$D_2(k_{\mathrm{start}}) = (2\Delta_{\mathrm{min2}} - \Delta_{\mathrm{maj}}) + 2\Delta_{\mathrm{min2}} k_{\mathrm{start}} - 2\Delta_{\mathrm{maj}} \cdot m_{2,\mathrm{rel}}$$

---

## 📊 Summary of Verified Results

| Metric | Conventional Pipeline (Liang-Barsky / Slab + Bresenham) | AP-Bresenham (Ours) |
| :--- | :---: | :---: |
| **2D Pixel Inconsistency Rate** | **20.74%** (2,074 / 10,000 lines) | **0.00%** (0 / 10,000 lines) |
| **2D Setup Latency (C++ ARM64)** | 10.32 ns / op | **6.79 ns / op (1.52$\times$ faster)** |
| **2D Setup Throughput** | 96.9 M ops / sec | **147.2 M ops / sec** |
| **2D 8-Connectivity at Boundary** | ❌ Broken (Jumps & Gaps) | **Strictly Preserved** |
| **3D CT Ray Seam Artifacts (8 chunks)** | **99.93%** (4,208 / 4,211 rays) | **0.00%** (0 / 4,211 rays) |
| **3D Discrepant/Missing Voxels** | **140,331 voxels** | **0 voxels** |
| **CT Radon Attenuation Line Integral** | ❌ Corrupted (71.43% error) | **100% Conserved** |
| **3D 26-Connectivity at Boundary** | ❌ Broken | **Strictly Preserved** |
| **Arithmetic Requirements** | FP32 / FP64 FPU + Rounding | **Pure Integer ALU (Zero Float)** |

---

## 🧪 Individual Component Execution

### Run C++ Tests
```bash
make -f src/Makefile test
```

### Run C++ Micro-benchmarks
```bash
make -f src/Makefile benchmark
```

### Run Python Mathematical Invariant Tests
```bash
make -f src/Makefile python-test
```

### Verify Paper Tables (Tables 1-4)
```bash
python3 src/benchmarks/verify_paper_results.py
```

### Run CT Radon Transform Forward Projection Simulation
```bash
python3 src/python/radon_transform_sim.py
```

### Generate Publication Figures
```bash
python3 src/benchmarks/plot_results.py
```
Outputs are written to `src/results/figures/` in both `.png` and `.pdf` formats.
