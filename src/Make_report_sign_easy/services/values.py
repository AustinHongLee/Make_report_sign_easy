from __future__ import annotations

from pathlib import Path
import json

from Make_report_sign_easy.pdf.models import ValueSet


class ValueSetService:
    """Load and validate field value mappings."""

    def load_json(self, values_path: str | Path) -> ValueSet:
        path = Path(values_path)
        if not path.exists():
            raise FileNotFoundError(path)

        with path.open("r", encoding="utf-8") as f:
            values = json.load(f)
        if not isinstance(values, dict):
            raise ValueError("values must be a JSON object mapping {field_key: text}")

        return ValueSet(values=values)
