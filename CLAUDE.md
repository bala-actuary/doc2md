# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A thin Python wrapper around [Docling](https://github.com/docling-project/docling) that converts PDFs, DOCX, PPTX, HTML, and images to Markdown. Exposes both a `doc2md` CLI (Typer) and a `from doc2md import convert` library API.

## Environment

- Windows + PowerShell. There is no test suite, lint config, or CI.
- Use the project `.venv` explicitly: `.venv\Scripts\python.exe` (and `.venv\Scripts\doc2md.exe`). Bare `python` on this machine resolves to Anaconda base, which does not have doc2md or Docling installed.
- Activation for an interactive PowerShell session: `.\.venv\Scripts\Activate.ps1` (note the leading `.\`).
- Install/reinstall after edits: `.venv\Scripts\python.exe -m pip install -e ".[dev]"`. The package is editable, so source edits take effect immediately without reinstall.

## Architecture

Three modules under `src/doc2md/`, all small:

- `converter.py` — the only real logic. Public `convert()`, plus internals `_convert_single`, `_convert_chunked`, `_run_chunk_in_subprocess`, `_pdf_page_count`, and `_find_tesseract`.
- `cli.py` — Typer wrapper. Parses `--ocr`, `--images`, `--pages`, `--chunk-size`; calls `convert()`.
- `_worker.py` — subprocess entry point. Invoked as `python -m doc2md._worker '<json-args>'` by `_run_chunk_in_subprocess`. Not for direct use.

### Memory-driven design decisions

The non-obvious behaviors in `converter.py` exist because Docling + PyTorch routinely OOM (`std::bad_alloc`) on large PDFs on this user's hardware. Preserve them unless explicitly told otherwise:

- **OCR is off by default** (`pipeline.do_ocr = False` when `ocr_langs is None`). Docling's own default is `do_ocr=True`, which loads the OCR engine (~300 MB) into memory even on PDFs with a text layer. We opt out unless OCR is explicitly requested.
- **Image extraction is opt-in** (`extract_images=False`). `generate_picture_images` spikes RAM and OOMs on 100+ page PDFs.
- **Chunked PDF mode runs each chunk in a fresh subprocess** (not just a fresh `DocumentConverter`). The point is that only a new OS process reclaims Docling/PyTorch memory between chunks. Don't refactor `_convert_chunked` to call `_convert_single` in-process.
- **Chunked mode keeps placeholder-only image output** even when `extract_images=True`. Per-chunk image sidecar dirs would be invalidated by the final markdown concatenation.

### Other behaviors worth knowing

- `_find_tesseract()` checks PATH then standard Windows/macOS/Linux install locations and sets `TesseractCliOcrOptions.tesseract_cmd` explicitly. PATH setup is not required for users.
- **No LibreOffice dependency by design.** Docling's DOCX backend calls `soffice` to render native Word DrawingML charts; we deliberately don't install or auto-detect LibreOffice. DOCX with native charts will silently drop those charts — workaround is "Save As PDF" from Word, then convert the PDF. Don't re-add a LibreOffice auto-detect path without checking with the user first; it was explicitly removed (commit after `fd03a71`).
- `image_artifacts_dir` is passed as a **basename only** (`f"{stem}_images"`), not a full path. `save_as_markdown` joins it with the .md's parent for disk writes and uses it verbatim in image refs; an absolute or nested path would nest twice on disk and produce broken refs.
- `page_range` is 1-indexed inclusive on both ends. CLI's `--pages 1-50` and library's `page_range=(1, 50)` are equivalent.
- `page_range` and `chunk_size` are mutually exclusive (raised at the top of `convert()`).

## Notebooks

The committed notebook is `notebooks/explore.template.ipynb`. `notebooks/explore.ipynb` is **gitignored** — it is the user's working copy with real document paths and outputs. Improvements to the workflow go in the template; never commit the local copy. The Jupyter kernel `Python (doc2md)` points at the venv directly, so notebooks don't need activation.

## Outputs

`outputs/` is gitignored except for `.gitkeep`. Generated markdown lives there during development and should not be committed.
