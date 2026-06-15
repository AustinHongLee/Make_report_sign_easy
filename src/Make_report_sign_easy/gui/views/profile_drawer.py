from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from Make_report_sign_easy.gui.adapters.pil_qt import pil_to_qpixmap


class ProfileDrawer(QWidget):
    """Right-side drawer for high-impact handwriting profile controls."""

    def __init__(self, view_model) -> None:
        super().__init__()
        self.view_model = view_model
        self._controls = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        title = QLabel("手寫微調")
        title.setObjectName("Muted")
        self.sample_label = QLabel("樣字預覽")
        self.sample_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sample_label.setMinimumHeight(92)
        self.sample_label.setStyleSheet("background: white; border: 1px solid #E4E7EC; border-radius: 6px;")

        form = QFormLayout()
        form.setSpacing(8)
        self._add_double(form, "筆跡抖動", "perturb", 0, 80, 1)
        self._add_double(form, "傾斜角度", "shear_angle", -45, 45, 1)
        self._add_double(form, "模糊", "blur_amount", 0, 10, 0.1)
        self._add_int(form, "線寬", "line_width", 1, 12)
        self._add_double(form, "中文字縮放", "cjk_scale", 0.3, 2.0, 0.05)
        self._add_double(form, "符號縮放", "special_scale", 0.3, 2.0, 0.05)

        preview_button = QPushButton("更新樣字")
        reset_button = QPushButton("重設預設")
        preview_button.clicked.connect(self.view_model.render_sample)
        reset_button.clicked.connect(self.view_model.reset_default)

        layout.addWidget(title)
        layout.addWidget(self.sample_label)
        layout.addLayout(form)
        layout.addWidget(preview_button)
        layout.addWidget(reset_button)
        layout.addStretch(1)

        self.view_model.profile_changed.connect(self.set_profile)
        self.view_model.sample_preview_ready.connect(self.set_sample_image)
        if self.view_model.session.profile is not None:
            self.set_profile(self.view_model.session.profile)

    def set_profile(self, profile) -> None:
        for name, control in self._controls.items():
            control.blockSignals(True)
            control.setValue(getattr(profile, name))
            control.blockSignals(False)

    def set_sample_image(self, image) -> None:
        pixmap = pil_to_qpixmap(image)
        scaled = pixmap.scaled(
            self.sample_label.width(),
            self.sample_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.sample_label.setPixmap(scaled)

    def _add_double(
        self,
        form: QFormLayout,
        label: str,
        name: str,
        minimum: float,
        maximum: float,
        step: float,
    ) -> None:
        control = QDoubleSpinBox()
        control.setRange(minimum, maximum)
        control.setSingleStep(step)
        control.setDecimals(2)
        control.valueChanged.connect(lambda value, attr=name: self.view_model.set_numeric(attr, value))
        self._controls[name] = control
        form.addRow(label, control)

    def _add_int(
        self,
        form: QFormLayout,
        label: str,
        name: str,
        minimum: int,
        maximum: int,
    ) -> None:
        control = QSpinBox()
        control.setRange(minimum, maximum)
        control.valueChanged.connect(lambda value, attr=name: self.view_model.set_numeric(attr, value))
        self._controls[name] = control
        form.addRow(label, control)
