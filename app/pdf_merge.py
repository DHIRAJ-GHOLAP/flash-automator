"""PDF merging module with blank separator page insertion.

Merges daily bank statement PDFs chronologically and inserts exactly one
blank/empty page between consecutive statements for clean duplex/physical filing separation.
"""
from __future__ import annotations

import datetime
import logging
import re
from pathlib import Path
from typing import List, Optional, Tuple

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

logger = logging.getLogger("flash_automator.merge")

DATE_PATTERN = re.compile(r"BankStatement_(\d{2})[-_](\d{2})[-_](\d{4})", re.IGNORECASE)


def extract_date_from_filename(filename: str) -> Optional[datetime.date]:
    """Extract datetime.date from a statement filename like BankStatement_10-07-2023.pdf."""
    match = DATE_PATTERN.search(filename)
    if match:
        day, month, year = match.groups()
        try:
            return datetime.date(int(year), int(month), int(day))
        except ValueError:
            return None
    return None


def get_sorted_statement_pdfs(input_dir: Path | str) -> List[Path]:
    """
    Scan input_dir for BankStatement_*.pdf files and sort them chronologically by statement date.
    Files that do not match the date pattern are sorted alphabetically at the end.
    """
    directory = Path(input_dir)
    if not directory.exists() or not directory.is_dir():
        raise FileNotFoundError(f"Directory not found: {directory}")

    pdf_files = list(directory.glob("*.pdf"))
    # Exclude any previously generated merged PDFs
    pdf_files = [f for f in pdf_files if not f.name.startswith("Merged_") and "merged" not in f.name.lower()]

    def sort_key(path: Path) -> Tuple[int, datetime.date, str]:
        extracted_date = extract_date_from_filename(path.name)
        if extracted_date is not None:
            return (0, extracted_date, path.name)
        return (1, datetime.date.max, path.name)

    return sorted(pdf_files, key=sort_key)


def merge_statement_pdfs(
    pdf_paths: List[Path],
    output_path: Path | str,
    insert_blank_page: bool = True,
) -> Tuple[Path, int, int]:
    """
    Merge a list of PDF files into a single document.
    
    Args:
        pdf_paths: Ordered list of PDF file paths to merge.
        output_path: Destination path for the merged PDF.
        insert_blank_page: If True, inserts one blank page between consecutive PDFs.
                          (No blank page is added after the final PDF).
                          
    Returns:
        Tuple of (output_path: Path, total_documents_merged: int, total_pages_in_output: int)
    """
    if not PYPDF_AVAILABLE:
        raise RuntimeError("pypdf is required to merge PDF files. Install it via 'pip install pypdf'.")

    if not pdf_paths:
        raise ValueError("No PDF files provided to merge.")

    writer = pypdf.PdfWriter()
    total_docs = len(pdf_paths)

    for i, path in enumerate(pdf_paths, start=1):
        logger.debug(f"Adding [{i}/{total_docs}]: {path.name}")
        try:
            reader = pypdf.PdfReader(str(path))
            doc_pages = len(reader.pages)
            if doc_pages == 0:
                logger.warning(f"Skipping empty PDF: {path.name}")
                continue

            # Add all pages of this document
            for page in reader.pages:
                writer.add_page(page)

            # Insert one blank page between documents (not after the last document)
            if insert_blank_page and i < total_docs:
                first_page = reader.pages[0]
                width = float(first_page.mediabox.width)
                height = float(first_page.mediabox.height)
                writer.add_blank_page(width=width, height=height)
                logger.debug(f"Inserted 1 blank separator page after {path.name}")

        except Exception as e:
            logger.error(f"Error reading {path.name}: {e}")
            raise RuntimeError(f"Failed to read and merge {path.name}: {e}") from e

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    with open(out_file, "wb") as f:
        writer.write(f)

    total_pages = len(writer.pages)
    logger.info(
        f"Merged {total_docs} PDFs into {out_file.name} "
        f"({total_pages} total pages, blank_separator={insert_blank_page})"
    )
    return out_file, total_docs, total_pages
