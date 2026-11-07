PDFLATEX ?= pdflatex
BIBTEX   ?= bibtex

.PHONY: all paper clean

all: paper

paper:
	@echo ">>> Compiling BMC Medical Imaging Manuscript..."
	$(PDFLATEX) -interaction=nonstopmode bmc_medical_imaging.tex > /dev/null
	$(BIBTEX) bmc_medical_imaging > /dev/null
	$(PDFLATEX) -interaction=nonstopmode bmc_medical_imaging.tex > /dev/null
	$(PDFLATEX) -interaction=nonstopmode bmc_medical_imaging.tex > /dev/null
	@echo "✓ BMC Medical Imaging manuscript compiled: bmc_medical_imaging.pdf"

clean:
	@rm -f *.aux *.bbl *.blg *.log *.out *.toc *.synctex.gz
	@echo "✓ Cleaned temporary build artifacts."

