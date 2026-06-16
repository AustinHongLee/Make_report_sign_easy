from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QThreadPool, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDockWidget,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from Make_report_sign_easy.gui.session import AppSession
from Make_report_sign_easy.gui.theme.tokens import LIGHT_QSS
from Make_report_sign_easy.gui.viewmodels.export_vm import ExportViewModel
from Make_report_sign_easy.gui.viewmodels.batch_vm import BatchViewModel
from Make_report_sign_easy.gui.viewmodels.profile_vm import ProfileViewModel
from Make_report_sign_easy.gui.viewmodels.preview_vm import PreviewViewModel
from Make_report_sign_easy.gui.viewmodels.template_vm import TemplateViewModel
from Make_report_sign_easy.gui.workers.task_runner import FunctionTask
from Make_report_sign_easy.gui.views.batch_workbench import BatchWorkbench
from Make_report_sign_easy.gui.views.field_inspector import FieldInspector
from Make_report_sign_easy.gui.views.pdf_canvas import PdfCanvas
from Make_report_sign_easy.gui.views.profile_drawer import ProfileDrawer
from Make_report_sign_easy.gui.views.statusbar import ActionStatusBar
from Make_report_sign_easy.gui.views.workflow_panel import WorkflowPanel
from Make_report_sign_easy.services import (
    FillDocumentService,
    BatchFillService,
    ProfileService,
    RenderTextService,
    TemplateService,
    ValueSetService,
)


class MainWindow(QMainWindow):
    """G0/G1 PySide6 main workbench."""

    def __init__(
        self,
        *,
        session: AppSession | None = None,
        templates: TemplateService | None = None,
        value_sets: ValueSetService | None = None,
        profiles: ProfileService | None = None,
        documents: FillDocumentService | None = None,
        renderer: RenderTextService | None = None,
        batches: BatchFillService | None = None,
    ) -> None:
        super().__init__()
        self.profiles = profiles or ProfileService()
        self.session = session or AppSession(profile=self.profiles.default_profile())
        self.documents = documents or FillDocumentService()
        self.renderer = renderer or RenderTextService()
        self.thread_pool = QThreadPool.globalInstance()
        self._active_tasks: set[FunctionTask] = set()
        self.template_vm = TemplateViewModel(
            self.session,
            templates=templates,
            value_sets=value_sets,
        )
        self.preview_vm = PreviewViewModel(
            self.session,
            documents=self.documents,
            renderer=self.renderer,
        )
        self.export_vm = ExportViewModel(
            self.session,
            documents=self.documents,
        )
        self.profile_vm = ProfileViewModel(
            self.session,
            profiles=self.profiles,
            renderer=self.renderer,
        )
        self.batch_vm = BatchViewModel(
            self.session,
            batches=batches,
        )

        self.setWindowTitle("HandFont Studio")
        self.resize(1180, 760)
        self.setMinimumSize(980, 640)
        self.setStyleSheet(LIGHT_QSS)

        self._build_toolbar()
        self._build_layout()
        self._connect_signals()

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        self.title_label = QLabel("HandFont Studio")
        self.title_label.setMinimumWidth(360)
        template_button = QPushButton("選範本")
        values_button = QPushButton("載入數值")
        single_button = QPushButton("單份")
        batch_button = QPushButton("批次")
        profile_button = QPushButton("手寫微調")

        template_button.clicked.connect(self.choose_template)
        values_button.clicked.connect(self.choose_values)
        single_button.clicked.connect(self.show_single_mode)
        batch_button.clicked.connect(self.show_batch_mode)
        profile_button.clicked.connect(self.toggle_profile_drawer)

        toolbar.addWidget(self.title_label)
        toolbar.addSeparator()
        toolbar.addWidget(template_button)
        toolbar.addWidget(values_button)
        toolbar.addSeparator()
        toolbar.addWidget(single_button)
        toolbar.addWidget(batch_button)
        toolbar.addWidget(profile_button)

    def _build_layout(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(10)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(10)

        self.workflow_panel = WorkflowPanel()
        self.canvas = PdfCanvas(self.template_vm.select_key)
        self.batch_workbench = BatchWorkbench(self.batch_vm)
        self.workspace_stack = QStackedWidget()
        self.workspace_stack.addWidget(self.canvas)
        self.workspace_stack.addWidget(self.batch_workbench)
        self.field_inspector = FieldInspector(self.template_vm)
        self.status_bar = ActionStatusBar()
        self.profile_drawer = ProfileDrawer(self.profile_vm)
        self.profile_dock = QDockWidget("手寫微調", self)
        self.profile_dock.setObjectName("ProfileDock")
        self.profile_dock.setWidget(self.profile_drawer)
        self.profile_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.profile_dock)
        self.profile_dock.hide()

        body_layout.addWidget(self.workflow_panel)
        body_layout.addWidget(self.workspace_stack, 1)
        body_layout.addWidget(self.field_inspector)

        root_layout.addWidget(body, 1)
        root_layout.addWidget(self.status_bar)
        self.setCentralWidget(root)

    def _connect_signals(self) -> None:
        self.template_vm.template_loaded.connect(self.workflow_panel.set_template)
        self.template_vm.template_loaded.connect(self.canvas.set_template)
        self.template_vm.template_loaded.connect(self._set_template_title)
        self.template_vm.inspection_changed.connect(self.workflow_panel.set_inspection)
        self.template_vm.inspection_changed.connect(self.status_bar.set_inspection)
        self.template_vm.inspection_changed.connect(self.canvas.set_inspection)
        self.template_vm.selected_key_changed.connect(self.canvas.set_selected_key)
        self.template_vm.error.connect(self._show_error)
        self.preview_vm.full_preview_ready.connect(self._show_full_preview)
        self.preview_vm.full_preview_ready.connect(lambda *_: self.workflow_panel.set_preview_ready())
        self.preview_vm.field_preview_ready.connect(self.canvas.set_field_preview)
        self.preview_vm.error.connect(self._show_error)
        self.export_vm.export_finished.connect(self._show_export_finished)
        self.export_vm.error.connect(self._show_error)
        self.profile_vm.error.connect(self._show_error)
        self.batch_vm.error.connect(self._show_error)
        self.batch_vm.batch_finished.connect(lambda *_: self.workflow_panel.set_export_ready())
        self.batch_vm.items_changed.connect(lambda items: self.status_bar.set_batch_mode(len(items)))
        self.batch_vm.items_changed.connect(lambda items: self.workflow_panel.set_batch_mode(len(items)))
        self.batch_vm.batch_finished.connect(self.status_bar.set_batch_result)
        self.batch_vm.batch_finished.connect(self.workflow_panel.set_batch_result)
        self.field_inspector.field_preview_requested.connect(self.preview_selected_field)
        self.status_bar.preview_requested.connect(self.generate_full_preview)
        self.status_bar.export_requested.connect(self.export_dialog)
        self.status_bar.batch_requested.connect(self.run_batch)

    def choose_template(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "選擇 PDF 範本",
            "",
            "PDF files (*.pdf)",
        )
        if path:
            self.load_template(path)

    def choose_values(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "載入 values JSON",
            "",
            "JSON files (*.json)",
        )
        if path:
            self.load_values(path)

    def export_dialog(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "匯出 PDF",
            "",
            "PDF files (*.pdf)",
        )
        if path:
            self.export_pdf(path)

    def load_template(self, path: str | Path) -> None:
        self.template_vm.load_template(path)

    def load_values(self, path: str | Path) -> None:
        self.template_vm.load_values(path)

    def generate_full_preview(self, *, blocking: bool = False) -> Path | None:
        if blocking:
            return self.preview_vm.generate_full_preview()

        task = FunctionTask(self.preview_vm.generate_full_preview)
        self._start_task(task, message="整頁預覽產生中...")
        return None

    def preview_selected_field(self):
        return self.preview_vm.preview_selected_field()

    def render_profile_sample(self):
        return self.profile_vm.render_sample()

    def toggle_profile_drawer(self) -> None:
        self.profile_dock.setVisible(not self.profile_dock.isVisible())

    def show_single_mode(self) -> None:
        self.workspace_stack.setCurrentWidget(self.canvas)
        self.field_inspector.show()
        self.status_bar.set_single_mode(self.session.inspection)
        self.workflow_panel.set_single_mode()

    def show_batch_mode(self) -> None:
        self.workspace_stack.setCurrentWidget(self.batch_workbench)
        self.field_inspector.hide()
        self.status_bar.set_batch_mode(len(self.session.batch_items))
        self.workflow_panel.set_batch_mode(len(self.session.batch_items))

    def add_batch_current_values(self, output_path: str | Path, *, label: str | None = None, seed: int | None = None):
        return self.batch_vm.add_current_values(output_path, label=label, seed=seed)

    def run_batch(self, *, blocking: bool = False):
        if blocking:
            return self.batch_vm.run()

        task = FunctionTask(self.batch_vm.run)
        self._start_task(task, message="批次執行中...", batch_busy=True)
        return None

    def export_pdf(self, output_path: str | Path, *, blocking: bool = False, notify: bool = True):
        if blocking:
            return self.export_vm.export_pdf(output_path, emit_signal=notify)

        task = FunctionTask(lambda: self.export_vm.export_pdf(output_path))
        self._start_task(task, message="匯出 PDF 中...")
        return None

    def _show_full_preview(self, path, _result) -> None:
        self.canvas.set_preview_pdf(path)

    def _show_export_finished(self, result) -> None:
        self.workflow_panel.set_export_ready()
        message = QMessageBox(self)
        message.setIcon(QMessageBox.Icon.Information)
        message.setWindowTitle("匯出完成")
        message.setText(f"已匯出: {result.output_path}\n缺漏欄位: {len(result.missing_fields)}")
        open_file = message.addButton("開啟檔案", QMessageBox.ButtonRole.ActionRole)
        open_folder = message.addButton("開資料夾", QMessageBox.ButtonRole.ActionRole)
        message.addButton(QMessageBox.StandardButton.Ok)
        message.exec()
        clicked = message.clickedButton()
        if clicked == open_file:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(result.output_path)))
        elif clicked == open_folder:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(result.output_path.parent)))

    def _set_template_title(self, template) -> None:
        self.title_label.setText(f"HandFont Studio · {template.path.name}")

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "操作失敗", message)

    def _start_task(self, task: FunctionTask, *, message: str, batch_busy: bool = False) -> None:
        self._active_tasks.add(task)
        task.signals.started.connect(lambda: self._set_busy(True, message, batch_busy=batch_busy))
        task.signals.done.connect(lambda _result, current=task: self._finish_task(current, batch_busy=batch_busy))
        task.signals.error.connect(self._show_error)
        task.signals.error.connect(lambda _message, current=task: self._finish_task(current, batch_busy=batch_busy))
        self.thread_pool.start(task)

    def _finish_task(self, task: FunctionTask, *, batch_busy: bool = False) -> None:
        self._active_tasks.discard(task)
        self._set_busy(False, "", batch_busy=batch_busy)

    def _set_busy(self, busy: bool, message: str, *, batch_busy: bool = False) -> None:
        if busy:
            self.status_bar.set_busy(True, message)
            if batch_busy:
                self.batch_workbench.set_busy(True)
            return

        if self.workspace_stack.currentWidget() is self.batch_workbench:
            self.status_bar.set_batch_mode(len(self.session.batch_items))
            self.batch_workbench.set_busy(False)
        else:
            self.status_bar.set_single_mode(self.session.inspection)
