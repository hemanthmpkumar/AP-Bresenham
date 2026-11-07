# ==============================================================================
# Master Makefile for AP-Bresenham Research Project
# ==============================================================================

PDFLATEX ?= /Library/TeX/texbin/pdflatex
BIBTEX   ?= /Library/TeX/texbin/bibtex

PAPER_DIR = paper/extended_journal
PAPER_NAME = ap_bresenham_extended

.PHONY: all paper dgmm icccs test bench figures clean help

all: test bench figures paper

help:
	@echo "AP-Bresenham Build and Verification Targets:"
	@echo "  make paper    - Compile the extended journal LaTeX paper to PDF"
	@echo "  make dgmm     - Compile the DGMM 2027 conference LaTeX paper to PDF"
	@echo "  make icccs    - Compile the ICCCS 2027 IEEE conference paper to PDF"
	@echo "  make test     - Run C++ and Python unit and property invariant tests"
	@echo "  make bench    - Run C++ nanosecond micro-benchmarks & Python comparison"
	@echo "  make figures  - Generate high-resolution publication figures"
	@echo "  make all      - Execute test, bench, figures, and paper compilation"
	@echo "  make clean    - Remove build artifacts and temporary files"

paper:
	@echo ">>> Compiling LaTeX Journal Paper ($(PAPER_NAME).pdf)..."
	@cd $(PAPER_DIR) && $(PDFLATEX) -interaction=nonstopmode $(PAPER_NAME).tex > /dev/null
	@cd $(PAPER_DIR) && $(BIBTEX) $(PAPER_NAME) > /dev/null
	@cd $(PAPER_DIR) && $(PDFLATEX) -interaction=nonstopmode $(PAPER_NAME).tex > /dev/null
	@cd $(PAPER_DIR) && $(PDFLATEX) -interaction=nonstopmode $(PAPER_NAME).tex > /dev/null
	@echo "✓ Paper compiled successfully: $(PAPER_DIR)/$(PAPER_NAME).pdf"

dgmm:
	@echo ">>> Compiling DGMM 2027 Conference Paper..."
	@cd paper/dgmm2027_conference && $(PDFLATEX) -interaction=nonstopmode dgmm2027_paper.tex > /dev/null
	@cd paper/dgmm2027_conference && $(BIBTEX) dgmm2027_paper > /dev/null
	@cd paper/dgmm2027_conference && $(PDFLATEX) -interaction=nonstopmode dgmm2027_paper.tex > /dev/null
	@cd paper/dgmm2027_conference && $(PDFLATEX) -interaction=nonstopmode dgmm2027_paper.tex > /dev/null
	@echo "✓ DGMM 2027 paper compiled successfully: paper/dgmm2027_conference/dgmm2027_paper.pdf"

icccs:
	@echo ">>> Compiling ICCCS 2027 IEEE Conference Paper..."
	@cd paper/icccs2027_conference && $(PDFLATEX) -interaction=nonstopmode icccs2027_paper.tex > /dev/null
	@cd paper/icccs2027_conference && $(BIBTEX) icccs2027_paper > /dev/null
	@cd paper/icccs2027_conference && $(PDFLATEX) -interaction=nonstopmode icccs2027_paper.tex > /dev/null
	@cd paper/icccs2027_conference && $(PDFLATEX) -interaction=nonstopmode icccs2027_paper.tex > /dev/null
	@echo "✓ ICCCS 2027 paper compiled successfully: paper/icccs2027_conference/icccs2027_paper.pdf"

test:
	@echo ">>> Running C++ & Python Test Suites..."
	@make -f src/Makefile test
	@make -f src/Makefile python-test

bench:
	@echo ">>> Running Micro-benchmarks & CT Simulations..."
	@make -f src/Makefile benchmark
	@python3 src/python/radon_transform_sim.py
	@python3 src/benchmarks/comprehensive_benchmark_suite.py

figures:
	@echo ">>> Generating Publication Figures..."
	@python3 src/benchmarks/plot_results.py

clean:
	@rm -rf build/
	@rm -f $(PAPER_DIR)/*.aux $(PAPER_DIR)/*.bbl $(PAPER_DIR)/*.blg $(PAPER_DIR)/*.log $(PAPER_DIR)/*.out $(PAPER_DIR)/*.toc
	@rm -f paper/dgmm2027_conference/*.aux paper/dgmm2027_conference/*.bbl paper/dgmm2027_conference/*.blg paper/dgmm2027_conference/*.log paper/dgmm2027_conference/*.out paper/dgmm2027_conference/*.toc
	@rm -f paper/icccs2027_conference/*.aux paper/icccs2027_conference/*.bbl paper/icccs2027_conference/*.blg paper/icccs2027_conference/*.log paper/icccs2027_conference/*.out paper/icccs2027_conference/*.toc
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleaned build artifacts."
