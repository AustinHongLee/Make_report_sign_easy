from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class WorkerSignals(QObject):
    started = Signal()
    done = Signal(object)
    error = Signal(str)


class FunctionTask(QRunnable):
    """Small QRunnable wrapper for service calls."""

    def __init__(self, fn: Callable[[], object]) -> None:
        super().__init__()
        self.fn = fn
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        self.signals.started.emit()
        try:
            result = self.fn()
        except Exception as exc:
            self.signals.error.emit(str(exc))
            return
        self.signals.done.emit(result)

