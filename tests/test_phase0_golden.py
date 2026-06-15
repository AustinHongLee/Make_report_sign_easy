import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import fitz


REPO_ROOT = Path(__file__).resolve().parents[1]
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


def _field_keys(pdf_path):
    doc = fitz.open(pdf_path)
    try:
        page = doc[0]
        keys = []
        for annot in page.annots() or []:
            if annot.type[1] == "FreeText":
                content = annot.info.get("content", "").strip()
                if content:
                    keys.append(content)
        return sorted(keys)
    finally:
        doc.close()


def _run_cli(args, output_path):
    cmd = [
        sys.executable,
        *args,
        "--template",
        str(TEMPLATE),
        "--values",
        str(VALUES),
        "--output",
        str(output_path),
        "--clear-annots",
        "--seed",
        "0",
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert output_path.exists()


def test_phase0_template_fields_match_expected():
    expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
    assert _field_keys(TEMPLATE) == expected["template_field_keys"]


def test_phase0_root_and_package_cli_match_golden(tmp_path):
    expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
    root_output = tmp_path / "root_cli.pdf"
    package_output = tmp_path / "package_cli.pdf"

    _run_cli(["tools/fill_pdf_simple.py"], root_output)
    _run_cli(["-m", "Make_report_sign_easy.tools.fill_pdf_simple"], package_output)

    root_render = _page_render_hash(root_output)
    package_render = _page_render_hash(package_output)

    assert root_render == package_render
    assert root_render == expected["filled_pdf_render"]
