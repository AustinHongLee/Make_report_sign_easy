from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from Make_report_sign_easy.builder import generate_text_image
from Make_report_sign_easy.core import RenderProfile


@dataclass(frozen=True)
class RenderTextRequest:
    text: str
    font_path: Path | None = None
    size: int | None = None
    ignore_router: bool = False
    clear_cache: bool = False
    random: bool = False
    random_per: float = 10
    profile: RenderProfile | None = None


class RenderTextService:
    """Use-case service for rendering handwriting-style text images."""

    def run(self, request: RenderTextRequest) -> Image.Image | None:
        font_path = str(request.font_path) if request.font_path else None
        return generate_text_image(
            request.text,
            font_path=font_path,
            size=request.size,
            ignore_router=request.ignore_router,
            clear_cache=request.clear_cache,
            random=request.random,
            random_per=request.random_per,
            profile=request.profile,
        )
