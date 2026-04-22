# doc2md

Convert PDFs, Word docs, PowerPoints, HTML, and images to Markdown. Thin wrapper around [Docling](https://github.com/docling-project/docling).

## Install

One-time, from this directory:

```bash
pipx install -e .
```

This puts a `doc2md` command on your PATH, usable from any project directory.

For library use inside another project's venv:

```bash
pip install -e C:/Users/balaa/Dev/doc2md
```

For the notebook:

```bash
pip install -e ".[dev]"
```

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
- Pass `ocr_langs` → forces Tesseract with the listed language packs. Needs Tesseract installed on the system (already the case on your machine from ER_OCR work).

## Exploration

`notebooks/explore.ipynb` imports `convert()` and runs it on sample documents (BMA spec, ER_OCR ballot). Use this for tuning OCR settings and inspecting output before relying on the CLI.
