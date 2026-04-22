# doc2md

Convert PDFs, Word docs, PowerPoints, HTML, and images to Markdown. Thin wrapper around [Docling](https://github.com/docling-project/docling).

## Prerequisites

- **Python 3.10+** on Windows, installed from [python.org](https://www.python.org/downloads/). The standard installer bundles the `py` launcher that the commands below use.
- **Git** — for cloning the repo.
- **Tesseract OCR** — *only* required if you pass `ocr_langs` to force OCR on scanned PDFs. Skip this if your documents are text PDFs (most modern Word/LaTeX exports are).
  - Windows installer: https://github.com/UB-Mannheim/tesseract/wiki
  - During install, tick the language packs you need (e.g. `English`, `Tamil`).
  - After install, make sure `tesseract.exe` is on your PATH (the installer offers this option).
- **~5 GB free disk space** for Docling's ML model downloads on first run (PyTorch, transformers, layout models).

## Get the code

```powershell
cd C:\Users\<you>\Dev
git clone https://github.com/bala-actuary/doc2md.git
cd doc2md
```

## Install (Windows + PowerShell)

One-time setup from PowerShell:

```powershell
cd C:\Users\<you>\Dev\doc2md

# Create venv pinned to Python 3.13 (any 3.10+ works)
py -3.13 -m venv .venv

# Allow venv activation in this PowerShell session (one-time per session)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Activate — note the leading .\ — required by PowerShell for relative script paths
.\.venv\Scripts\Activate.ps1

# Install doc2md + Docling + Jupyter into the venv (slow: 2–5 GB of ML deps)
pip install -e ".[dev]"

# Register the venv as a Jupyter kernel (permanent — only needed once)
python -m ipykernel install --user --name doc2md --display-name "Python (doc2md)"
```

## Daily use

Each new PowerShell session that wants the `doc2md` CLI or library needs the venv activated first:

```powershell
cd C:\Users\<you>\Dev\doc2md
.\.venv\Scripts\Activate.ps1
```

Then `doc2md input.pdf output.md` works, and any Python invoked in the session can `from doc2md import convert`.

For the notebook: open `notebooks/explore.ipynb` and pick **Kernel → Change Kernel → "Python (doc2md)"**. The kernel path is hardcoded to the venv, so no activation needed for notebook use.

## Using doc2md from another project

In the other project's own venv:

```powershell
pip install -e C:\Users\<you>\Dev\doc2md
```

Then `from doc2md import convert` works inside that project.

## CLI

```bash
doc2md input.pdf output.md
doc2md scan.pdf output.md --ocr eng            # force OCR, English
doc2md ballot.pdf ballot.md --ocr eng,tam      # English + Tamil
```

## Library

```python
from doc2md import convert

convert("input.pdf", "output.md")
convert("ballot.pdf", "ballot.md", ocr_langs=["eng", "tam"])
```

## OCR behaviour

- Omit `ocr_langs` / `--ocr` → Docling auto-detects scanned pages and OCRs only those (default engine).
- Pass `ocr_langs` → forces Tesseract with the listed language packs. Needs Tesseract and the matching language packs installed on the system (see Prerequisites).

## Exploration

`notebooks/explore.ipynb` imports `convert()` and runs it on sample documents. Replace the placeholder paths with your own files and use it to tune OCR settings and inspect output before relying on the CLI.
