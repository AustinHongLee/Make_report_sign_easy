from __future__ import annotations

from pathlib import Path

import fitz

from .models import Field


def extract_freetext_fields(
    pdf_path: str | Path,
    page_index: int = 0,
) -> list[Field]:
    """Return FreeText annotation fields from one PDF page."""
    doc = fitz.open(pdf_path)
    try:
        page = doc[page_index]
        fields = []
        for annot in page.annots() or []:
            if annot.type[1] != "FreeText":
                continue
            content = annot.info.get("content", "").strip()
            if not content:
                continue
            rect = fitz.Rect(annot.rect)
            fields.append(
                Field(
                    key=content,
                    page_index=page_index,
                    rect=(rect.x0, rect.y0, rect.x1, rect.y1),
                )
            )
        return fields
    finally:
        doc.close()


def extract_freetext_positions(
    pdf_path: str | Path,
    page_index: int = 0,
) -> dict[str, fitz.Rect]:
    """Compatibility map used by the legacy GUI and CLI."""
    return {
        field.key: fitz.Rect(field.rect)
        for field in extract_freetext_fields(pdf_path, page_index=page_index)
    }
