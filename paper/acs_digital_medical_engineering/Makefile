PDFLATEX ?= pdflatex
BIBTEX   ?= bibtex

.PHONY: all manuscript si cover toc docx clean

all: manuscript si cover toc docx

manuscript:
	@echo ">>> Compiling ACS Digital Medical Engineering Manuscript..."
	$(PDFLATEX) -interaction=nonstopmode main_manuscript.tex > /dev/null
	$(BIBTEX) main_manuscript > /dev/null
	$(PDFLATEX) -interaction=nonstopmode main_manuscript.tex > /dev/null
	$(PDFLATEX) -interaction=nonstopmode main_manuscript.tex > /dev/null
	@echo "✓ Manuscript compiled: main_manuscript.pdf"

si:
	@echo ">>> Compiling Supporting Information..."
	$(PDFLATEX) -interaction=nonstopmode supporting_information.tex > /dev/null
	$(PDFLATEX) -interaction=nonstopmode supporting_information.tex > /dev/null
	@echo "✓ Supporting Information compiled: supporting_information.pdf"

cover:
	@echo ">>> Compiling Cover Letter..."
	$(PDFLATEX) -interaction=nonstopmode cover_letter.tex > /dev/null
	@echo "✓ Cover Letter compiled: cover_letter.pdf"

toc:
	@echo ">>> Compiling Table of Contents (TOC) Graphic..."
	$(PDFLATEX) -interaction=nonstopmode toc_graphic.tex > /dev/null
	@echo "✓ TOC Graphic compiled: toc_graphic.pdf"

docx:
	@echo ">>> Generating ACS Digital Medical Engineering Word (.docx) Files..."
	@python3 ../../src/generate_docx_manuscripts.py
	@echo "✓ ACS Word manuscripts generated: main_manuscript.docx, supporting_information.docx"

clean:
	@rm -f *.aux *.bbl *.blg *.log *.out *.toc *.synctex.gz
	@echo "✓ Cleaned temporary build artifacts."

