"""Subprocess entry point for chunked conversion. Not intended for direct use.

Invoked by `converter._run_chunk_in_subprocess` as:
    python -m doc2md._worker '<json-args>'

Running each chunk in a fresh process lets the OS reclaim Docling/PyTorch
memory between chunks, which is what prevents OOM on large PDFs.
"""
import json
import sys

from .converter import _convert_single


def main() -> None:
    args = json.loads(sys.argv[1])
    page_range = args.get("page_range")
    if page_range is not None:
        page_range = tuple(page_range)
    _convert_single(
        source=args["source"],
        output=args["output"],
        ocr_langs=args.get("ocr_langs"),
        extract_images=args.get("extract_images", False),
        page_range=page_range,
    )


if __name__ == "__main__":
    main()
