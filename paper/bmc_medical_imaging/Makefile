PDFLATEX ?= pdflatex
BIBTEX   ?= bibtex

.PHONY: all paper cover docx clean

all: paper cover docx

paper:
	@echo ">>> Compiling BMC Medical Imaging Manuscript..."
	$(PDFLATEX) -interaction=nonstopmode bmc_medical_imaging.tex > /dev/null
	$(BIBTEX) bmc_medical_imaging > /dev/null
	$(PDFLATEX) -interaction=nonstopmode bmc_medical_imaging.tex > /dev/null
	$(PDFLATEX) -interaction=nonstopmode bmc_medical_imaging.tex > /dev/null
	@echo "✓ BMC Medical Imaging manuscript compiled: bmc_medical_imaging.pdf"

cover:
	@echo ">>> Compiling BMC Medical Imaging Cover Letter..."
	$(PDFLATEX) -interaction=nonstopmode cover_letter.tex > /dev/null
	$(PDFLATEX) -interaction=nonstopmode cover_letter.tex > /dev/null
	@echo "✓ BMC Medical Imaging cover letter compiled: cover_letter.pdf"

docx:
	@echo ">>> Generating BMC Medical Imaging Word (.docx) Files..."
	@python3 ../../src/generate_docx_manuscripts.py
	@echo "✓ BMC Medical Imaging Word documents generated: bmc_medical_imaging.docx, cover_letter.docx"

clean:
	@rm -f *.aux *.bbl *.blg *.log *.out *.toc *.synctex.gz
	@echo "✓ Cleaned temporary build artifacts."

