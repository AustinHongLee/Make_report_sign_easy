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

from Make_report_sign_easy.pdf import extract_freetext_fields  # noqa: E402
from Make_report_sign_easy.services import (  # noqa: E402
    FillDocumentRequest,
    FillDocumentService,
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


def test_extract_freetext_fields_matches_phase0_keys():
    expected = json.loads(EXPECTED.read_text(encoding="utf-8"))

    fields = extract_freetext_fields(TEMPLATE)

    assert sorted(field.key for field in fields) == expected["template_field_keys"]
    assert all(field.field_type == "FreeText" for field in fields)


def test_fill_document_service_matches_phase0_golden(tmp_path):
    expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
    output_path = tmp_path / "service.pdf"

    result = FillDocumentService().run(
        FillDocumentRequest(
            template_path=TEMPLATE,
            values_path=VALUES,
            output_path=output_path,
            clear_annots=True,
            seed=0,
        )
    )

    assert result.output_path == output_path
    assert result.missing_fields == ()
    assert len(result.filled_fields) == len(expected["template_field_keys"])
    assert _page_render_hash(output_path) == expected["filled_pdf_render"]


def test_fill_document_service_accepts_in_memory_values(tmp_path):
    expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
    values = json.loads(VALUES.read_text(encoding="utf-8"))
    output_path = tmp_path / "service-from-memory.pdf"

    result = FillDocumentService().run(
        FillDocumentRequest(
            template_path=TEMPLATE,
            values=values,
            output_path=output_path,
            clear_annots=True,
            seed=0,
        )
    )

    assert result.missing_fields == ()
    assert len(result.filled_fields) == len(expected["template_field_keys"])
    assert _page_render_hash(output_path) == expected["filled_pdf_render"]
