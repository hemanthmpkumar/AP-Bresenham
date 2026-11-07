PDFLATEX ?= pdflatex
BIBTEX   ?= bibtex

.PHONY: all paper docx clean

all: paper docx

paper:
	@echo ">>> Compiling BMC Medical Imaging Manuscript..."
	$(PDFLATEX) -interaction=nonstopmode bmc_medical_imaging.tex > /dev/null
	$(BIBTEX) bmc_medical_imaging > /dev/null
	$(PDFLATEX) -interaction=nonstopmode bmc_medical_imaging.tex > /dev/null
	$(PDFLATEX) -interaction=nonstopmode bmc_medical_imaging.tex > /dev/null
	@echo "✓ BMC Medical Imaging manuscript compiled: bmc_medical_imaging.pdf"

docx:
	@echo ">>> Generating BMC Medical Imaging Word (.docx) Manuscript..."
	@python3 ../../src/generate_docx_manuscripts.py
	@echo "✓ BMC Medical Imaging Word manuscript generated: bmc_medical_imaging.docx"

clean:
	@rm -f *.aux *.bbl *.blg *.log *.out *.toc *.synctex.gz
	@echo "✓ Cleaned temporary build artifacts."

