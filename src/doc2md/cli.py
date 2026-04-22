from pathlib import Path
from typing import Optional, Tuple

import typer

from .converter import convert

app = typer.Typer(
    add_completion=False,
    help="Convert documents (PDF, DOCX, PPTX, HTML, images) to Markdown.",
)


def _parse_pages(value: str) -> Tuple[int, int]:
    try:
        start_s, end_s = value.split("-", 1)
        return (int(start_s), int(end_s))
    except Exception as exc:
        raise typer.BadParameter(
            f"Invalid --pages value {value!r}. Expected 'START-END', e.g. '1-50'."
        ) from exc


@app.command()
def main(
    source: str = typer.Argument(..., help="Input file path or URL."),
    output: Path = typer.Argument(..., help="Output .md file path."),
    ocr: Optional[str] = typer.Option(
        None,
        "--ocr",
        help=(
            "Comma-separated Tesseract language codes (e.g. 'eng' or 'eng,tam'). "
            "Forces OCR; omit for Docling auto-detection."
        ),
    ),
    images: bool = typer.Option(
        False,
        "--images",
        help=(
            "Extract embedded pictures as PNGs and reference them in the "
            "markdown. Off by default — image extraction spikes memory use "
            "and can OOM on large (100+ page) PDFs."
        ),
    ),
    pages: Optional[str] = typer.Option(
        None,
        "--pages",
        help=(
            "Process only this 1-indexed inclusive page range, e.g. '1-50'. "
            "Useful for retrying a single failed chunk. Mutually exclusive "
            "with --chunk-size."
        ),
    ),
    chunk_size: Optional[int] = typer.Option(
        None,
        "--chunk-size",
        help=(
            "Auto-chunk PDFs with more pages than this. Each chunk is "
            "processed in a fresh subprocess (so memory is fully released "
            "between chunks), and the results are concatenated. PDF-only — "
            "ignored for other formats. Typical value: 50."
        ),
    ),
) -> None:
    """Convert SOURCE to Markdown at OUTPUT."""
    langs = [lang.strip() for lang in ocr.split(",")] if ocr else None
    page_range = _parse_pages(pages) if pages else None
    result_path = convert(
        source,
        str(output),
        ocr_langs=langs,
        extract_images=images,
        page_range=page_range,
        chunk_size=chunk_size,
    )
    typer.echo(f"Wrote {result_path}")


if __name__ == "__main__":
    app()
