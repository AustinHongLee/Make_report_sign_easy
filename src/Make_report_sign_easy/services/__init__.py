"""Headless application services."""

from .fill_document import FillDocumentRequest, FillDocumentService
from .render_text import RenderTextRequest, RenderTextService

__all__ = [
    "FillDocumentRequest",
    "FillDocumentService",
    "RenderTextRequest",
    "RenderTextService",
]
