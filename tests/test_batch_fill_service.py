import hashlib
import json
import os
import sys
from pathlib import Path

import fitz

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if os.path.isdir(SRC):
    sys.path.insert(0, str(SRC))

from Make_report_sign_easy.services import (  # noqa: E402
    BatchFillItem,
    BatchFillRequest,
    BatchFillService,
)


TEMPLATE = REPO_ROOT / "samples" / "附件六_管線工程施工自主檢查表.pdf"
VALUES = REPO_ROOT / "samples" / "values_sample.json"
EXPECTED = REPO_ROOT / "tests" / "golden" / "phase0_expected.json"


def _page_render_hash(pdf_path):
    doc = fitz.open(pdf_path)
    try:
        page = doc[0]
        pix = page.get_pixmap(alpha=False)
        return {
            "pages": doc.page_count,
            "width": pix.width,
            "height": pix.height,
            "sha256": hashlib.sha256(pix.samples).hexdigest(),
            "annots": sum(1 for _ in (page.annots() or [])),
        }
    finally:
        doc.close()


def test_batch_fill_service_fills_multiple_outputs(tmp_path):
    expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
    values = json.loads(VALUES.read_text(encoding="utf-8"))
    first = tmp_path / "first.pdf"
    second = tmp_path / "second.pdf"

    result = BatchFillService().run(
        BatchFillRequest(
            template_path=TEMPLATE,
                items=(
                    BatchFillItem(output_path=first, values=values, seed=0),
                    BatchFillItem(output_path=second, values_path=VALUES, seed=0),
                ),
                clear_annots=True,
            )
        )

    assert result.output_paths == (first, second)
    assert all(path.exists() for path in result.output_paths)
    assert _page_render_hash(first) == expected["filled_pdf_render"]
    assert _page_render_hash(second) == expected["filled_pdf_render"]


def test_batch_fill_service_requires_items():
    try:
        BatchFillService().run(BatchFillRequest(template_path=TEMPLATE, items=()))
    except ValueError as exc:
        assert "at least one item" in str(exc)
    else:
        raise AssertionError("expected batch fill to require at least one item")
