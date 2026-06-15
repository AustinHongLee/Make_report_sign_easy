"""PDF adapters for template detection and filling."""

from .fill import fill_pdf
from .template import (
    extract_freetext_fields,
    extract_freetext_positions,
    load_freetext_template,
)

__all__ = [
    "fill_pdf",
    "extract_freetext_fields",
    "extract_freetext_positions",
    "load_freetext_template",
]
