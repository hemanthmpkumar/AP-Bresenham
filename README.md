# Analytical Phase-Compensated Bresenham (AP-Bresenham)
### *Topologically Exact Integer Clipping on Pixel and Voxel Lattices*

[![Language: C++17](https://img.shields.io/badge/Language-C%2B%2B17-blue.svg)](src/cpp/)
[![Language: Python 3](https://img.shields.io/badge/Language-Python%203-green.svg)](src/python/)
[![Paper: IEEE PDF](https://img.shields.io/badge/Paper-IEEE%20PDF-red.svg)](paper/icccs2027_conference/icccs2027_paper.pdf)
[![Status: 100% Bit-Identical](https://img.shields.io/badge/Topology-100%25%20Exact-brightgreen.svg)](src/tests/)

---

## 📖 Overview

This repository contains the complete research paper, mathematical proofs, C++17 / Python source code, test suites, and empirical benchmarks for **Analytical Phase-Compensated Bresenham (AP-Bresenham)**.

### The Problem: The 60-Year Bresenham Phase-Shift Phenomenon
In computer graphics, computer vision, and medical imaging (CT/MRI ray casting), the conventional pipeline decouples line clipping from rasterization:
1. Clip line segment continuously using floating-point arithmetic (e.g. Liang-Barsky, Cohen-Sutherland).
2. Round intersection coordinates to integer endpoints.
3. Reseed Bresenham's rasterizer afresh with zero error accumulation ($D_0 = 2\Delta y - \Delta x$).

This decoupled approach fundamentally violates the **commutativity of digitization and clipping**:
$$\mathrm{Rasterize}(\mathrm{Clip}(L, \Omega)) \;\ne\; \mathrm{Clip}(\mathrm{Rasterize}(L), \Omega)$$

Rounding the continuous intersection point introduces slope distortion and resets the fractional error register, corrupting pixel selection in **over 20.7% of 2D lines** and escalating to **99.93% of 3D rays traversing partitioned sub-volumes**.

### The Solution: AP-Bresenham
AP-Bresenham resolves this challenge by deriving the closed-form Diophantine state equations governing multi-dimensional Bresenham rasterization:
* **$O(1)$ Diophantine Boundary Inversion**: Pure integer formulas replace floating-point division entirely.
* **Analytical Phase Injection**: The exact historical accumulator state ($D_{\mathrm{start}}, D_1, D_2$) is evaluated directly at the entry cell in $O(1)$ without iterative simulation.
* **100% Bit-Level Identity**: Guarantees bit-identical output with $\mathrm{Clip}(\mathrm{Rasterize}(L), \Omega)$ using **pure integer ALU operations (zero floating point)**.

---

## 📂 Repository Layout

```text
2Dlineclipping/
├── paper/                                  # Research manuscripts & LaTeX source
│   ├── acs_digital_medical_engineering/    # ACS Digital Medical Engineering (Fast Format submission package)
│   │   ├── main_manuscript.tex / .pdf      # Main research article (1.5 spaced, line numbers)
│   │   ├── supporting_information.tex/.pdf # Standalone Supporting Information (SI)
│   │   ├── cover_letter.tex / .pdf         # Formal Editor-in-Chief cover letter (5 reviewers)
│   │   ├── toc_graphic.tex / .pdf / .png   # Table of Contents graphic (strictly 3.25" x 1.75")
│   │   ├── Makefile                        # Standalone build automation
│   │   └── README.md                       # Submission guideline checklist & notes
│   ├── icccs2027_conference/
│   │   ├── icccs2027_paper.tex             # IEEE Conference format submission (ICCCS 2027)
│   │   ├── icccs2027_paper.pdf             # Compiled publication PDF
│   │   ├── references.bib                  # BibTeX references
│   │   ├── Makefile                        # Standalone LaTeX build makefile
│   │   └── README.md                       # Conference & submission details
│   ├── dgmm2027_conference/
│   │   ├── dgmm2027_paper.tex              # 12-page DGMM 2027 conference submission
│   │   └── references.bib
│   └── drafts/
│       └── AP_Bresenham_Paper_Draft.md     # Markdown working draft
│
├── src/                                    # Core algorithms, benchmarks, & tests
│   ├── cpp/                                # Production C++17 implementations
│   │   ├── ap_bresenham_2d.hpp             # 2D AP-Bresenham (Zero-allocation callback)
│   │   ├── ap_bresenham_3d.hpp             # 3D AP-Bresenham (Dual accumulators)
│   │   ├── baselines_2d.hpp                # C++ baselines (CS, LB, Cyrus-Beck)
│   │   ├── baselines_3d.hpp                # C++ 3D baselines (3D Slab, 3D DDA, Siddon)
│   │   ├── test_cpp_invariants.cpp         # 70,000 randomized invariant tests
│   │   └── main_benchmark.cpp              # High-throughput C++ micro-benchmarks
│   ├── python/                             # Python reference implementations
│   │   ├── ap_bresenham_2d.py              # 2D AP-Bresenham & ground-truth rasterizer
│   │   ├── ap_bresenham_3d.py              # 3D AP-Bresenham & 3D ground truth
│   │   ├── baselines_2d.py                 # Python 2D baselines (CS, LB, CB, NLN, Skala)
│   │   ├── baselines_3d.py                 # Python 3D baselines (Slab, DDA, Siddon, Jacobs)
│   │   └── radon_transform_sim.py          # CT forward projection Radon transform sim
│   ├── tests/                              # Mathematical invariant property test suites
│   │   ├── test_2d_mathematical_invariants.py
│   │   └── test_3d_invariants.py
│   ├── benchmarks/                         # Verification & publication figure scripts
│   │   ├── verify_paper_results.py         # Reproduces Tables 1-4
│   │   ├── comprehensive_benchmark_suite.py
│   │   └── plot_results.py                 # Renders Figures 1-4 (PNG & PDF)
│   ├── results/                            # Benchmark measurements & figures
│   │   ├── benchmark_results.json
│   │   ├── benchmark_results.csv
│   │   └── figures/                        # Generated publication figures
│   ├── Makefile                            # Source build makefile
│   ├── run_all.sh                          # Master verification script
│   └── README.md                           # Detailed source documentation
│
├── archive/                                # Legacy exploratory prototype scripts
│   └── legacy_prototypes/
│
├── Makefile                                # Root master makefile
└── .gitignore
```

---

## ⚡ Quick Start

### 1. Run Complete Verification & Benchmark Suite (One Command)
```bash
./src/run_all.sh
```

### 2. Compile Conference Paper
```bash
make paper
# Output written to: paper/icccs2027_conference/icccs2027_paper.pdf
```

### 3. Run Unit and Property Tests
```bash
make test
```

### 4. Run High-Performance Micro-benchmarks
```bash
make bench
```

### 5. Generate Publication Figures
```bash
make figures
# Outputs written to: src/results/figures/
```

---

## 📊 Summary of Experimental Results

| Metric | Conventional Pipeline (Liang-Barsky / Slab + Bresenham) | AP-Bresenham (Ours) |
| :--- | :---: | :---: |
| **2D Pixel Inconsistency Rate** | **20.74% – 22.30%** | **0.00% (100% Bit-Identical)** |
| **2D Setup Latency (C++ ARM64)** | 10.54 ns / op | **8.89 ns / op (1.19$\times$ – 1.52$\times$ faster)** |
| **2D Setup Throughput** | 94.8 M ops / sec | **112.4 M ops / sec** |
| **2D 8-Connectivity at Seams** | ❌ Broken (Jumps & Gaps) | **Strictly Preserved** |
| **3D CT Ray Seam Artifacts (8 chunks)** | **86.72% – 99.93%** | **0.00% (0 errors / 5,000 rays)** |
| **3D Discrepant/Missing Voxels** | **75,681 – 140,331 voxels** | **0 voxels** |
| **CT Radon Attenuation Line Integral** | ❌ Corrupted (34.8% – 71.4% error) | **100% Conserved** |
| **3D 26-Connectivity at Seams** | ❌ Broken | **Strictly Preserved** |
| **Arithmetic Domain** | FP32 / FP64 FPU + Rounding | **Pure Integer ALU (Zero Float)** |

---

## 📜 Citations & Venue Targets

* **Primary Conference Paper (IEEE Format)**: [`paper/icccs2027_conference/icccs2027_paper.pdf`](paper/icccs2027_conference/icccs2027_paper.pdf)
* **Discrete Geometry Conference Paper (12 Pages)**: [`paper/dgmm2027_conference/dgmm2027_paper.tex`](paper/dgmm2027_conference/dgmm2027_paper.tex) (Target: *5th IAPR International Conference on Discrete Geometry and Mathematical Morphology*, DGMM 2027).
