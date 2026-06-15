from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class Field:
    key: str
    page_index: int
    rect: tuple[float, float, float, float]
    field_type: str = "FreeText"


@dataclass(frozen=True)
class Template:
    path: Path
    fields: tuple[Field, ...]

    @property
    def field_keys(self) -> tuple[str, ...]:
        return tuple(field.key for field in self.fields)


@dataclass(frozen=True)
class ValueSet:
    values: Mapping[str, object]

    @property
    def keys(self) -> tuple[str, ...]:
        return tuple(self.values.keys())


@dataclass(frozen=True)
class FillResult:
    output_path: Path
    filled_fields: tuple[str, ...]
    missing_fields: tuple[str, ...]
