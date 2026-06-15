from __future__ import annotations

from pathlib import Path
import tempfile
import uuid

from PySide6.QtCore import QObject, Signal

from Make_report_sign_easy.gui.session import AppSession
from Make_report_sign_easy.services import (
    FillDocumentRequest,
    FillDocumentService,
    RenderTextRequest,
    RenderTextService,
)


class PreviewViewModel(QObject):
    """View-model for full-page and selected-field previews."""

    full_preview_ready = Signal(object, object)
    field_preview_ready = Signal(str, object)
    error = Signal(str)

    def __init__(
        self,
        session: AppSession,
        documents: FillDocumentService | None = None,
        renderer: RenderTextService | None = None,
    ) -> None:
        super().__init__()
        self.session = session
        self.documents = documents or FillDocumentService()
        self.renderer = renderer or RenderTextService()

    def generate_full_preview(self) -> Path | None:
        if self.session.template is None:
            self.error.emit("請先載入 PDF 範本")
            return None

        output_path = Path(tempfile.gettempdir()) / f"mrse-preview-{uuid.uuid4().hex}.pdf"
        try:
            result = self.documents.run(
                FillDocumentRequest(
                    template_path=self.session.template.path,
                    values=self.session.values,
                    output_path=output_path,
                    profile=self.session.profile,
                    clear_annots=self.session.clear_annots,
                    random=self.session.random,
                    seed=self.session.seed,
                )
            )
        except Exception as exc:
            self.error.emit(str(exc))
            return None

        self.session.preview_pdf_path = output_path
        self.session.preview_result = result
        self.full_preview_ready.emit(output_path, result)
        return output_path

    def preview_selected_field(self) -> object | None:
        key = self.session.selected_key
        if key is None:
            self.error.emit("請先選取欄位")
            return None

        text = self.session.values.get(key, "")
        try:
            image = self.renderer.run(
                RenderTextRequest(
                    str(text),
                    profile=self.session.profile,
                    random=self.session.random,
                )
            )
        except Exception as exc:
            self.error.emit(str(exc))
            return None

        if image is None:
            self.error.emit("此欄位沒有產生預覽影像")
            return None

        self.session.field_preview_key = key
        self.field_preview_ready.emit(key, image)
        return image
