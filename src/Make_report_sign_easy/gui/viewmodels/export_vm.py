from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from Make_report_sign_easy.gui.session import AppSession
from Make_report_sign_easy.services import FillDocumentRequest, FillDocumentService


class ExportViewModel(QObject):
    """View-model for exporting the active session to a PDF."""

    export_finished = Signal(object)
    error = Signal(str)

    def __init__(
        self,
        session: AppSession,
        documents: FillDocumentService | None = None,
    ) -> None:
        super().__init__()
        self.session = session
        self.documents = documents or FillDocumentService()

    def export_pdf(self, output_path: str | Path, *, emit_signal: bool = True):
        if self.session.template is None:
            self.error.emit("請先載入 PDF 範本")
            return None

        try:
            result = self.documents.run(
                FillDocumentRequest(
                    template_path=self.session.template.path,
                    values=self.session.values,
                    output_path=Path(output_path),
                    profile=self.session.profile,
                    clear_annots=self.session.clear_annots,
                    random=self.session.random,
                    seed=self.session.seed,
                )
            )
        except Exception as exc:
            self.error.emit(str(exc))
            return None

        self.session.last_output_path = result.output_path
        if emit_signal:
            self.export_finished.emit(result)
        return result
