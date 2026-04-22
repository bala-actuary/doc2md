from pathlib import Path
from typing import Iterable, Optional

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractCliOcrOptions
from docling.document_converter import DocumentConverter, PdfFormatOption


def convert(
    source: str,
    output: str,
    ocr_langs: Optional[Iterable[str]] = None,
) -> Path:
    """Convert a document to Markdown.

    source:    path or URL to input (PDF, DOCX, PPTX, HTML, image).
    output:    path for the .md file. Parent dirs are created.
    ocr_langs: e.g. ["eng"] or ["eng", "tam"]. Forces Tesseract OCR with
               those languages. Leave as None for Docling auto-detection
               (OCR fires only on pages that need it).
    """
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pipeline = PdfPipelineOptions()
    pipeline.generate_picture_images = True

    if ocr_langs is not None:
        pipeline.do_ocr = True
        pipeline.ocr_options = TesseractCliOcrOptions(lang=list(ocr_langs))

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline),
        }
    )

    result = converter.convert(str(source))
    markdown = result.document.export_to_markdown()
    output_path.write_text(markdown, encoding="utf-8")
    return output_path
