from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from Make_report_sign_easy.core import RenderProfile
from Make_report_sign_easy.pdf.models import FillResult

from .fill_document import FillDocumentRequest, FillDocumentService


@dataclass(frozen=True)
class BatchFillItem:
    output_path: Path
    values_path: Path | None = None
    values: Mapping[str, object] | None = None
    seed: int | None = None
    label: str | None = None


@dataclass(frozen=True)
class BatchFillRequest:
    template_path: Path
    items: Sequence[BatchFillItem]
    clear_annots: bool = False
    random: bool = False
    seed_start: int | None = None
    profile: RenderProfile | None = None


@dataclass(frozen=True)
class BatchFillResult:
    results: tuple[FillResult, ...]

    @property
    def output_paths(self) -> tuple[Path, ...]:
        return tuple(result.output_path for result in self.results)


class BatchFillService:
    """Use-case service for filling one template with multiple value sets."""

    def __init__(self, documents: FillDocumentService | None = None) -> None:
        self.documents = documents or FillDocumentService()

    def run(self, request: BatchFillRequest) -> BatchFillResult:
        if not request.items:
            raise ValueError("batch fill requires at least one item")

        results = []
        for index, item in enumerate(request.items):
            seed = item.seed
            if seed is None and request.seed_start is not None:
                seed = request.seed_start + index

            results.append(
                self.documents.run(
                    FillDocumentRequest(
                        template_path=request.template_path,
                        values_path=item.values_path,
                        values=item.values,
                        output_path=item.output_path,
                        clear_annots=request.clear_annots,
                        random=request.random,
                        seed=seed,
                        profile=request.profile,
                    )
                )
            )

        return BatchFillResult(results=tuple(results))
