from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import QObject, Signal

from Make_report_sign_easy.gui.session import AppSession
from Make_report_sign_easy.services import ProfileService, RenderTextRequest, RenderTextService


class ProfileViewModel(QObject):
    """View-model for editing the active RenderProfile."""

    profile_changed = Signal(object)
    sample_preview_ready = Signal(object)
    error = Signal(str)

    def __init__(
        self,
        session: AppSession,
        profiles: ProfileService | None = None,
        renderer: RenderTextService | None = None,
    ) -> None:
        super().__init__()
        self.session = session
        self.profiles = profiles or ProfileService()
        self.renderer = renderer or RenderTextService()
        if self.session.profile is None:
            self.session.profile = self.profiles.default_profile()

    def reset_default(self) -> None:
        self.session.profile = self.profiles.default_profile()
        self.profile_changed.emit(self.session.profile)
        self.render_sample()

    def set_numeric(self, name: str, value: float | int) -> None:
        if self.session.profile is None:
            self.reset_default()
        try:
            self.session.profile = replace(self.session.profile, **{name: value})
        except TypeError as exc:
            self.error.emit(str(exc))
            return

        self.profile_changed.emit(self.session.profile)
        self.render_sample()

    def render_sample(self, text: str = "李宗鴻 114/11/03") -> object | None:
        if self.session.profile is None:
            self.reset_default()

        try:
            image = self.renderer.run(
                RenderTextRequest(
                    text,
                    profile=self.session.profile,
                    random=self.session.random,
                )
            )
        except Exception as exc:
            self.error.emit(str(exc))
            return None

        if image is None:
            self.error.emit("樣字沒有產生預覽影像")
            return None

        self.sample_preview_ready.emit(image)
        return image
