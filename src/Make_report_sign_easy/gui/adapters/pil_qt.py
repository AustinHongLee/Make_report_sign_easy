from __future__ import annotations

from PIL import Image
from PySide6.QtGui import QImage, QPixmap


def pil_to_qimage(image: Image.Image) -> QImage:
    """Convert a PIL image into an owned QImage."""
    rgba = image.convert("RGBA")
    data = rgba.tobytes("raw", "RGBA")
    qimage = QImage(
        data,
        rgba.width,
        rgba.height,
        QImage.Format.Format_RGBA8888,
    )
    return qimage.copy()


def pil_to_qpixmap(image: Image.Image) -> QPixmap:
    """Convert a PIL image into a QPixmap safe from buffer lifetime issues."""
    return QPixmap.fromImage(pil_to_qimage(image))

