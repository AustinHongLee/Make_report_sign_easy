from __future__ import annotations

from pathlib import Path

import fitz
from PySide6.QtCore import QRectF
from PySide6.QtGui import QImage


def render_page(
    path: str | Path,
    page_index: int = 0,
    zoom: float = 2.0,
    *,
    show_annotations: bool = False,
) -> tuple[QImage, float]:
    """Raster a PDF page into an owned QImage."""
    doc = fitz.open(path)
    try:
        page = doc[page_index]
        pix = page.get_pixmap(
            matrix=fitz.Matrix(zoom, zoom),
            alpha=False,
            annots=show_annotations,
        )
        qimage = QImage(
            pix.samples,
            pix.width,
            pix.height,
            pix.stride,
            QImage.Format.Format_RGB888,
        )
        return qimage.copy(), zoom
    finally:
        doc.close()


def field_rect_to_pixels(
    rect: tuple[float, float, float, float],
    zoom: float,
) -> QRectF:
    """Map a PyMuPDF point-space rect to raster pixel coordinates."""
    x0, y0, x1, y1 = rect
    return QRectF(x0 * zoom, y0 * zoom, (x1 - x0) * zoom, (y1 - y0) * zoom)
