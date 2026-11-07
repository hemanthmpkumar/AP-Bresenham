# ACS Digital Medical Engineering Submission Package

This folder contains the complete, review-ready submission package for **_ACS Digital Medical Engineering_** (ACS Publications), prepared in strict accordance with the official Author Guidelines (`dmead6_authguide.pdf`).

---

## 📄 Submission Files

| File | Description | Guidelines Adherence |
| :--- | :--- | :--- |
| **[`main_manuscript.docx`](main_manuscript.docx)** | Main article editable source | Formatted Microsoft Word document (.docx) with embedded figures and tables. |
| **[`supporting_information.docx`](supporting_information.docx)** | Supporting Information editable source | Formatted Microsoft Word document (.docx) with proofs, Algorithm S1, and Table S1. |
| **[`cover_letter.docx`](cover_letter.docx)** | Formal Cover Letter editable source | Formatted Microsoft Word document (.docx) addressed to Editor-in-Chief. |
| **[`main_manuscript.tex`](main_manuscript.tex)** / **[`main_manuscript.pdf`](main_manuscript.pdf)** | Main research article (Fast Format) | Review-ready single-column, 1.5-spaced with line numbering (`lineno`), standardized ACS sections (*Introduction*, *Results and Discussion*, *Methods*, *Safety Considerations*, *Data and Code Availability*, *Author Information*, *Conflict of Interest*). Conforms to title & abstract guidelines (no banned words: "novel", "new", "first"). |
| **[`supporting_information.tex`](supporting_information.tex)** / **[`supporting_information.pdf`](supporting_information.pdf)** | Supporting Information (SI) document | Standalone document containing extended Diophantine proofs, Algorithm S1 pseudocode, and multi-scale scaling tables. Numbered sequentially with S-prefixes (Figure S1, Table S1, Algorithm S1). |
| **[`cover_letter.tex`](cover_letter.tex)** / **[`cover_letter.pdf`](cover_letter.pdf)** | Formal Editor-in-Chief Cover Letter | Addressed to `eic@dme.acs.org`. Details scope alignment, key advances relative to state-of-the-art, prior publication & preprint policy disclosure, and lists **5 suggested independent international reviewers** from multiple countries (France, USA, Czech Republic). |
| **[`toc_graphic.tex`](toc_graphic.tex)** / **[`toc_graphic.pdf`](toc_graphic.pdf)** / **[`toc_graphic.png`](toc_graphic.png)** | Table of Contents (TOC) / Abstract Graphic | Strictly sized to **3.25 in. $\times$ 1.75 in. (8.25 cm $\times$ 4.45 cm)** as mandated on pages 1 and 22 of the Author Guidelines. Visually contrasts conventional decoupled phase shift with AP-Bresenham's exact continuity. |
| **[`references.bib`](references.bib)** / **[`IEEEtran.bst`](IEEEtran.bst)** | BibTeX reference database | Full citations including complete article titles. |
| **[`Makefile`](Makefile)** | Build automation makefile | Automated generation for all components via `make all`. |

---

## ⚡ Build Commands

To recompile all submission PDFs from source:
```bash
make clean
make all
```

Individual targets:
```bash
make manuscript   # Builds main_manuscript.pdf
make si           # Builds supporting_information.pdf
make cover        # Builds cover_letter.pdf
make toc          # Builds toc_graphic.pdf
```

