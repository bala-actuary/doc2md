import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable, Optional, Tuple

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractCliOcrOptions
from docling.document_converter import DocumentConverter, PdfFormatOption


_TESSERACT_COMMON_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    "/usr/bin/tesseract",
    "/usr/local/bin/tesseract",
    "/opt/homebrew/bin/tesseract",
]


def _find_tesseract() -> Optional[str]:
    """Locate the tesseract executable. PATH first, then common install paths."""
    found = shutil.which("tesseract")
    if found:
        return found
    for candidate in _TESSERACT_COMMON_PATHS:
        if Path(candidate).exists():
            return candidate
    return None


def _pdf_page_count(source: str) -> int:
    """Return the number of pages in a PDF (using pypdfium2 — ships with Docling)."""
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(source)
    try:
        return len(pdf)
    finally:
        pdf.close()


def _convert_single(
    source: str,
    output: str,
    ocr_langs: Optional[Iterable[str]],
    extract_images: bool,
    page_range: Optional[Tuple[int, int]],
) -> Path:
    """Run Docling once on the given source. Used for small docs directly and
    invoked via `_worker.py` in a subprocess for individual chunks."""
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pipeline = PdfPipelineOptions()
    if extract_images:
        pipeline.generate_picture_images = True

    if ocr_langs is not None:
        pipeline.do_ocr = True
        ocr_options = TesseractCliOcrOptions(lang=list(ocr_langs))
        tesseract_cmd = _find_tesseract()
        if tesseract_cmd:
            ocr_options.tesseract_cmd = tesseract_cmd
        pipeline.ocr_options = ocr_options

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline),
        }
    )

    convert_kwargs = {}
    if page_range is not None:
        convert_kwargs["page_range"] = page_range

    result = converter.convert(str(source), **convert_kwargs)
    markdown = result.document.export_to_markdown()
    output_path.write_text(markdown, encoding="utf-8")
    return output_path


def _run_chunk_in_subprocess(
    source: str,
    chunk_output: str,
    ocr_langs: Optional[Iterable[str]],
    extract_images: bool,
    page_range: Tuple[int, int],
) -> None:
    """Spawn a fresh Python process to convert one page range. When the process
    exits, all Docling/PyTorch memory is released to the OS — preventing the
    cross-chunk memory accumulation that causes std::bad_alloc on large docs."""
    args = {
        "source": source,
        "output": chunk_output,
        "ocr_langs": list(ocr_langs) if ocr_langs else None,
        "extract_images": extract_images,
        "page_range": list(page_range),
    }
    subprocess.run(
        [sys.executable, "-m", "doc2md._worker", json.dumps(args)],
        check=True,
    )


def _convert_chunked(
    source: str,
    output: str,
    ocr_langs: Optional[Iterable[str]],
    extract_images: bool,
    chunk_size: int,
    n_pages: int,
) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ranges = [
        (i + 1, min(i + chunk_size, n_pages)) for i in range(0, n_pages, chunk_size)
    ]
    print(
        f"Chunking {n_pages}-page document into {len(ranges)} chunk(s) "
        f"of up to {chunk_size} pages.",
        file=sys.stderr,
    )

    with tempfile.TemporaryDirectory(prefix="doc2md_chunks_") as tmpdir:
        chunk_paths = []
        for i, (start, end) in enumerate(ranges, start=1):
            chunk_md = Path(tmpdir) / f"chunk_{i:03d}.md"
            print(
                f"  Chunk {i}/{len(ranges)}: pages {start}-{end} ...",
                file=sys.stderr,
            )
            _run_chunk_in_subprocess(
                source, str(chunk_md), ocr_langs, extract_images, (start, end)
            )
            chunk_paths.append(chunk_md)

        with output_path.open("w", encoding="utf-8") as out_f:
            for i, chunk_md in enumerate(chunk_paths):
                if i > 0:
                    out_f.write("\n\n---\n\n")
                out_f.write(chunk_md.read_text(encoding="utf-8"))

    return output_path


def convert(
    source: str,
    output: str,
    ocr_langs: Optional[Iterable[str]] = None,
    extract_images: bool = False,
    page_range: Optional[Tuple[int, int]] = None,
    chunk_size: Optional[int] = None,
) -> Path:
    """Convert a document to Markdown.

    source:         path or URL to input (PDF, DOCX, PPTX, HTML, image).
    output:         path for the .md file. Parent dirs are created.
    ocr_langs:      e.g. ["eng"] or ["eng", "tam"]. Forces Tesseract OCR with
                    those languages. Leave as None for Docling auto-detection
                    (OCR fires only on pages that need it).
    extract_images: if True, render embedded pictures as PNGs and reference
                    them in the markdown. Off by default — image extraction
                    spikes memory and can OOM on large (100+ page) PDFs.
    page_range:     (first, last), 1-indexed inclusive. Processes only those
                    pages. Useful for retrying one failed chunk. Mutually
                    exclusive with chunk_size.
    chunk_size:     if given and the source is a PDF with more than this many
                    pages, process the PDF in page-range chunks of this size,
                    each in a fresh subprocess for memory isolation, then
                    concatenate the markdown. PDF-only — ignored for other
                    formats. Mutually exclusive with page_range.
    """
    if page_range is not None and chunk_size is not None:
        raise ValueError("page_range and chunk_size are mutually exclusive")

    is_pdf = Path(source).suffix.lower() == ".pdf"
    if chunk_size is not None and is_pdf:
        n_pages = _pdf_page_count(source)
        if n_pages > chunk_size:
            return _convert_chunked(
                source, output, ocr_langs, extract_images, chunk_size, n_pages
            )

    return _convert_single(source, output, ocr_langs, extract_images, page_range)
