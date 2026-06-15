from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Field:
    key: str
    page_index: int
    rect: tuple[float, float, float, float]
    field_type: str = "FreeText"


@dataclass(frozen=True)
class FillResult:
    output_path: Path
    filled_fields: tuple[str, ...]
    missing_fields: tuple[str, ...]
