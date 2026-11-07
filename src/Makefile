# ============================================================
# Makefile for AP-Bresenham Research Codebase
# ============================================================

CXX ?= clang++
CXXFLAGS ?= -O3 -std=c++17 -march=native -Wall -Wextra -Isrc/cpp
BUILD_DIR = build
BIN_TEST = $(BUILD_DIR)/test_cpp_invariants
BIN_BENCH = $(BUILD_DIR)/main_benchmark

.PHONY: all clean test benchmark python-test figures run-all

all: $(BIN_TEST) $(BIN_BENCH)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)
	mkdir -p src/results/figures

$(BIN_TEST): src/cpp/test_cpp_invariants.cpp $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $< -o $@

$(BIN_BENCH): src/cpp/main_benchmark.cpp $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $< -o $@

test: $(BIN_TEST)
	@echo ">>> Running C++ Unit and Invariant Test Suite..."
	@./$(BIN_TEST)

benchmark: $(BIN_BENCH)
	@echo ">>> Running C++ High-Throughput Benchmarks..."
	@./$(BIN_BENCH)

python-test:
	@echo ">>> Running Python Invariant Tests..."
	@python3 src/tests/test_2d_mathematical_invariants.py
	@python3 src/tests/test_3d_invariants.py

figures:
	@echo ">>> Generating Publication Figures..."
	@python3 src/benchmarks/plot_results.py

paper-results:
	@echo ">>> Verifying Paper Results (Tables 1-4)..."
	@python3 src/benchmarks/verify_paper_results.py

run-all: all test python-test benchmark paper-results figures
	@echo "\n========================================================"
	@echo "  ALL TESTS, BENCHMARKS, AND FIGURES COMPLETED SUCCESSFULLY!"
	@echo "========================================================\n"

clean:
	rm -rf $(BUILD_DIR)
