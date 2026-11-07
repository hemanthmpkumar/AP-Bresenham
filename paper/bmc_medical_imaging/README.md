# BMC Medical Imaging (Springer Nature) Submission Package

This directory contains the submission-ready manuscript formatted according to **BMC Medical Imaging** (Springer Nature) author guidelines.

## Journal Profile
- **Journal**: *BMC Medical Imaging*
- **Publisher**: BioMed Central / Springer Nature
- **Indexed In**: Web of Science (SCIE), PubMed, Scopus, DOAJ
- **Impact Factor**: 2.7 (Q2/Q1 Imaging Science & Photographic Technology / Radiology, Nuclear Medicine & Medical Imaging)
- **Scope**: Open-access journal publishing research on medical imaging techniques, reconstruction algorithms, computational radiology, and tomographic pipelines.

---

## Manuscript Files
| File | Description |
| :--- | :--- |
| `bmc_medical_imaging.docx` | **Editable source manuscript** (Microsoft Word format) with embedded high-resolution figures, structured abstract, styled tables, and formatted declarations. |
| `bmc_medical_imaging.tex` | Full manuscript formatted with BMC structured abstract, double-spaced review format, continuous line numbering (`lineno`), and mandatory BMC declaration sections. |
| `bmc_medical_imaging.pdf` | Compiled 16-page review-ready PDF. |
| `references.bib` | Complete BibTeX bibliography with DOIs. |
| `IEEEtran.bst` | Standard bibliography style file. |
| `figures/` | High-resolution publication figures (`figure1_phase_shift_phenomenon.pdf`, `figure4_ct_radon_attenuation_error.pdf`, `figure6_clinical_before_after_col.pdf`). |
| `Makefile` | Automated build script. |

---

## Compliance Checklist for BMC Medical Imaging
- [x] **Title**: Concise and descriptive (*Exact Ray-Voxel Traversal for Distributed Medical Image Reconstruction: Analytical Phase-Preserving Bresenham Algorithm*).
- [x] **Author & Affiliation**: Single author (Hemanth Manchabale Papachappa, Independent Researcher, Seattle, WA, USA, ORCID: 0009-0007-1398-9451).
- [x] **Structured Abstract**: Explicitly split into:
  - **Background**: Computational bottleneck in 3D CT/PET ray tracing and multi-subvolume boundary seam artifacts.
  - **Methods**: Mathematical formulation of the AP-Bresenham closed-form accumulator injection and bounding box clipping.
  - **Results**: PSNR $=\infty$, RMSE $=0.0000$, $1.20\times$--$1.60\times$ speedup, eliminated peak attenuation error of $15.94\text{ cm}^{-1}$.
  - **Conclusions**: Practical impact for real-time and distributed clinical tomographic reconstruction.
- [x] **Keywords**: 4--8 relevant MeSH/imaging keywords.
- [x] **Required BMC Sections**:
  - Background
  - Methods
  - Results
  - Discussion
  - Conclusions
  - List of abbreviations
- [x] **Mandatory Declarations**:
  - Ethics approval and consent to participate (Not applicable; public de-identified datasets).
  - Consent for publication (Not applicable).
  - Availability of data and materials (Public GitHub repository linked).
  - Competing interests (None declared).
  - Funding (No external funding received).
  - Authors' contributions (Sole author responsibility statement).
  - Acknowledgements (Acknowledging public imaging repositories).
  - Authors' information (Independent researcher credentials).

---

## Building the Package

To compile the manuscript:
```bash
make paper
# or
make all
```

To clean temporary auxiliary files:
```bash
make clean
```

