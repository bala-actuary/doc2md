from pathlib import Path
from typing import Optional

import typer

from .converter import convert

app = typer.Typer(
    add_completion=False,
    help="Convert documents (PDF, DOCX, PPTX, HTML, images) to Markdown.",
)


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
) -> None:
    """Convert SOURCE to Markdown at OUTPUT."""
    langs = [lang.strip() for lang in ocr.split(",")] if ocr else None
    result_path = convert(source, str(output), ocr_langs=langs, extract_images=images)
    typer.echo(f"Wrote {result_path}")


if __name__ == "__main__":
    app()
