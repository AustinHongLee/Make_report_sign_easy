from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QPen, QPixmap
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsScene, QGraphicsView

from Make_report_sign_easy.gui.adapters.pdf_raster import field_rect_to_pixels, render_page
from Make_report_sign_easy.gui.adapters.pil_qt import pil_to_qpixmap
from Make_report_sign_easy.gui.theme.tokens import INK_BLUE, MISSING_YELLOW
from Make_report_sign_easy.pdf.models import Field, Template


class FieldRectItem(QGraphicsRectItem):
    def __init__(self, field: Field, rect, on_select) -> None:
        super().__init__(rect)
        self.field = field
        self._on_select = on_select
        self.setAcceptHoverEvents(True)
        self.setPen(QPen(QColor(INK_BLUE), 2))
        self.setBrush(QBrush(QColor(65, 105, 225, 28)))
        self.setToolTip(field.key)

    def mousePressEvent(self, event) -> None:
        self._on_select(self.field.key)
        super().mousePressEvent(event)

    def set_selected(self, selected: bool) -> None:
        color = QColor(INK_BLUE if selected else MISSING_YELLOW)
        self.setPen(QPen(color, 3 if selected else 1.5, Qt.PenStyle.SolidLine))
        self.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), 40 if selected else 20)))


class PdfCanvas(QGraphicsView):
    """Central PDF canvas with clickable field overlays."""

    def __init__(self, on_select) -> None:
        super().__init__()
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHints(self.renderHints())
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self._on_select = on_select
        self._field_items: dict[str, FieldRectItem] = {}
        self._field_preview_item: QGraphicsPixmapItem | None = None
        self._selected_key: str | None = None
        self._template: Template | None = None
        self._zoom = 2.0

    def set_template(self, template: Template) -> None:
        self._template = template
        self._render_pdf(template.path)

    def set_preview_pdf(self, path) -> None:
        self._render_pdf(path)

    def _render_pdf(self, path) -> None:
        if self._template is None:
            return
        self._scene.clear()
        self._field_items = {}
        self._field_preview_item = None
        image, zoom = render_page(path, page_index=0, zoom=self._zoom)
        self._zoom = zoom
        self._scene.addPixmap(QPixmap.fromImage(image))

        for field in self._template.fields:
            item = FieldRectItem(
                field,
                field_rect_to_pixels(field.rect, zoom),
                self._on_select,
            )
            self._scene.addItem(item)
            self._field_items[field.key] = item

        self.set_selected_key(self._selected_key)
        self.fitInView(self._scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def set_selected_key(self, key: str | None) -> None:
        self._selected_key = key
        for field_key, item in self._field_items.items():
            item.set_selected(field_key == key)

    def set_field_preview(self, key: str, image) -> None:
        if self._template is None:
            return

        field = next((item.field for item in self._field_items.values() if item.field.key == key), None)
        if field is None:
            return

        if self._field_preview_item is not None:
            self._scene.removeItem(self._field_preview_item)
            self._field_preview_item = None

        rect = field_rect_to_pixels(field.rect, self._zoom)
        pixmap = pil_to_qpixmap(image)
        scaled = pixmap.scaled(
            int(rect.width()),
            int(rect.height()),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        item = self._scene.addPixmap(scaled)
        item.setZValue(5)
        item.setPos(
            rect.x() + (rect.width() - scaled.width()) / 2,
            rect.y() + (rect.height() - scaled.height()) / 2,
        )
        self._field_preview_item = item
        self.set_selected_key(key)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._scene.items():
            self.fitInView(self._scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
