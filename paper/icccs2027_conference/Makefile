# ==============================================================================
# Makefile for ICCCS 2027 IEEE Conference Paper Submission
# 12th International Conference on Computer and Communication Systems (ICCCS 2027)
# Submission URL: https://easychair.org/conferences/?conf=icccs2027
# Format: IEEE Conference double-column (IEEEtran)
# ==============================================================================

PDFLATEX ?= $(shell which pdflatex 2>/dev/null || echo /Library/TeX/texbin/pdflatex)
BIBTEX   ?= $(shell which bibtex 2>/dev/null || echo /Library/TeX/texbin/bibtex)

PAPER_NAME = icccs2027_paper

.PHONY: all paper clean help

all: paper

help:
	@echo "ICCCS 2027 Conference Paper Build Targets:"
	@echo "  make paper   - Compile the IEEE conference paper to PDF ($(PAPER_NAME).pdf)"
	@echo "  make clean   - Remove LaTeX intermediate auxiliary files"

paper:
	@echo ">>> Compiling ICCCS 2027 IEEE Paper ($(PAPER_NAME).pdf)..."
	$(PDFLATEX) -interaction=nonstopmode $(PAPER_NAME).tex > /dev/null
	$(BIBTEX) $(PAPER_NAME) > /dev/null
	$(PDFLATEX) -interaction=nonstopmode $(PAPER_NAME).tex > /dev/null
	$(PDFLATEX) -interaction=nonstopmode $(PAPER_NAME).tex > /dev/null
	@echo "✓ ICCCS 2027 paper compiled successfully: $(PAPER_NAME).pdf"

clean:
	@rm -f *.aux *.bbl *.blg *.log *.out *.toc *.synctex.gz
	@echo "✓ Cleaned LaTeX intermediate build files."
