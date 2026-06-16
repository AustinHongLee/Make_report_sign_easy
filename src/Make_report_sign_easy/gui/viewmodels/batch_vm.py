from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from Make_report_sign_easy.gui.session import AppSession
from Make_report_sign_easy.services import (
    BatchFillItem,
    BatchFillRequest,
    BatchFillResult,
    BatchFillService,
)


class BatchViewModel(QObject):
    """View-model for the batch fill workbench."""

    items_changed = Signal(tuple)
    batch_finished = Signal(object)
    error = Signal(str)

    def __init__(
        self,
        session: AppSession,
        batches: BatchFillService | None = None,
    ) -> None:
        super().__init__()
        self.session = session
        self.batches = batches or BatchFillService()

    def add_current_values(
        self,
        output_path: str | Path,
        *,
        label: str | None = None,
        seed: int | None = None,
    ) -> BatchFillItem | None:
        if not self.session.values:
            self.error.emit("請先載入或輸入 values")
            return None

        item = BatchFillItem(
            output_path=Path(output_path),
            values=dict(self.session.values),
            label=label,
            seed=seed,
        )
        self.session.batch_items.append(item)
        self.items_changed.emit(tuple(self.session.batch_items))
        return item

    def add_values_path(
        self,
        values_path: str | Path,
        output_path: str | Path,
        *,
        label: str | None = None,
        seed: int | None = None,
    ) -> BatchFillItem:
        item = BatchFillItem(
            output_path=Path(output_path),
            values_path=Path(values_path),
            label=label,
            seed=seed,
        )
        self.session.batch_items.append(item)
        self.items_changed.emit(tuple(self.session.batch_items))
        return item

    def clear(self) -> None:
        self.session.batch_items.clear()
        self.session.batch_result = None
        self.items_changed.emit(())

    def run(self) -> BatchFillResult | None:
        if self.session.template is None:
            self.error.emit("請先載入 PDF 範本")
            return None
        if not self.session.batch_items:
            self.error.emit("批次清單沒有工作項")
            return None

        try:
            result = self.batches.run(
                BatchFillRequest(
                    template_path=self.session.template.path,
                    items=tuple(self.session.batch_items),
                    clear_annots=self.session.clear_annots,
                    random=self.session.random,
                    profile=self.session.profile,
                )
            )
        except Exception as exc:
            self.error.emit(str(exc))
            return None

        self.session.batch_result = result
        self.batch_finished.emit(result)
        return result
