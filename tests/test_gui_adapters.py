from __future__ import annotations

import os

import pytest
from PIL import Image

pytest.importorskip("PySide6")

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from Make_report_sign_easy.gui.adapters.pdf_raster import field_rect_to_pixels
from Make_report_sign_easy.gui.adapters.pil_qt import pil_to_qimage, pil_to_qpixmap


def test_field_rect_to_pixels_maps_pdf_points_to_raster_pixels():
    rect = field_rect_to_pixels((10.0, 20.0, 30.0, 45.0), zoom=2.5)

    assert rect.x() == 25.0
    assert rect.y() == 50.0
    assert rect.width() == 50.0
    assert rect.height() == 62.5


def test_pil_to_qimage_returns_owned_rgba_image():
    image = Image.new("RGB", (3, 2), "red")

    qimage = pil_to_qimage(image)

    assert qimage.width() == 3
    assert qimage.height() == 2
    assert qimage.format() == QImage.Format.Format_RGBA8888


def test_pil_to_qpixmap_returns_non_null_pixmap():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])

    pixmap = pil_to_qpixmap(Image.new("RGBA", (4, 3), (0, 128, 255, 255)))

    assert app is not None
    assert not pixmap.isNull()
    assert pixmap.width() == 4
    assert pixmap.height() == 3
