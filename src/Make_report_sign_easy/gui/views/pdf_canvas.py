from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QPen, QPixmap
from PySide6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
)

from Make_report_sign_easy.gui.adapters.pdf_raster import field_rect_to_pixels, render_page
from Make_report_sign_easy.gui.adapters.pil_qt import pil_to_qpixmap
from Make_report_sign_easy.gui.theme.tokens import INK_BLUE, MISSING_YELLOW, READY_GREEN
from Make_report_sign_easy.pdf.models import Field, Template
from Make_report_sign_easy.services import TemplateInspection


EXTRA_GRAY = "#98A2B3"
UNKNOWN_GRAY = "#D0D5DD"


class FieldRectItem(QGraphicsRectItem):
    def __init__(self, field: Field, rect, on_select) -> None:
        super().__init__(rect)
        self.field = field
        self._on_select = on_select
        self._status_color = QColor(UNKNOWN_GRAY)
        self._selected = False
        self.setAcceptHoverEvents(True)
        self.setZValue(2)
        self.setToolTip(field.key)
        self.label = QGraphicsSimpleTextItem(field.key, self)
        self.label.setBrush(QBrush(QColor(INK_BLUE)))
        self.label.setPos(rect.width() + 4, 0)
        self.label.setVisible(False)
        self._apply_style()

    def mousePressEvent(self, event) -> None:
        self._on_select(self.field.key)
        super().mousePressEvent(event)

    def hoverEnterEvent(self, event) -> None:
        self.label.setVisible(True)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        self.label.setVisible(self._selected)
        super().hoverLeaveEvent(event)

    def set_status_color(self, color: str) -> None:
        self._status_color = QColor(color)
        self._apply_style()

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self.label.setVisible(selected)
        self._apply_style()

    def _apply_style(self) -> None:
        color = QColor(INK_BLUE) if self._selected else self._status_color
        self.setPen(QPen(color, 3 if self._selected else 1.5, Qt.PenStyle.SolidLine))
        alpha = 34 if self._selected else 18
        self.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), alpha)))


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
        self._inspection: TemplateInspection | None = None
        self._zoom = 2.0

    def set_template(self, template: Template) -> None:
        self._template = template
        self._render_pdf(template.path)

    def set_inspection(self, inspection: TemplateInspection) -> None:
        self._inspection = inspection
        self._apply_inspection()

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

        self._apply_inspection()
        self.set_selected_key(self._selected_key)
        self.fitInView(self._scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def set_selected_key(self, key: str | None) -> None:
        self._selected_key = key
        for field_key, item in self._field_items.items():
            item.set_selected(field_key == key)

    def _apply_inspection(self) -> None:
        matched = set(self._inspection.matched_keys) if self._inspection else set()
        missing = set(self._inspection.missing_value_keys) if self._inspection else set()
        extra = set(self._inspection.extra_value_keys) if self._inspection else set()
        for key, item in self._field_items.items():
            if key in matched:
                item.set_status_color(READY_GREEN)
            elif key in missing:
                item.set_status_color(MISSING_YELLOW)
            elif key in extra:
                item.set_status_color(EXTRA_GRAY)
            else:
                item.set_status_color(UNKNOWN_GRAY)

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
