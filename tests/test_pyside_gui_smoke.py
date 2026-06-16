import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import fitz
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = REPO_ROOT / "samples" / "附件六_管線工程施工自主檢查表.pdf"
VALUES = REPO_ROOT / "samples" / "values_sample.json"
EXPECTED_BATCH_FILES = ("batch-1.pdf", "batch-2.pdf")


def _page_count(pdf_path: Path) -> int:
    doc = fitz.open(pdf_path)
    try:
        return doc.page_count
    finally:
        doc.close()


@pytest.mark.skipif(
    importlib.util.find_spec("PySide6") is None,
    reason="PySide6 is not installed",
)
def test_pyside_gui_smoke_loads_template_and_values(tmp_path):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    env["QT_QPA_PLATFORM"] = "offscreen"
    output = tmp_path / "gui-smoke.pdf"
    batch_dir = tmp_path / "batch"
    screenshot = tmp_path / "gui-smoke.png"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "Make_report_sign_easy.gui.app",
            "--smoke",
            "--template",
            str(TEMPLATE),
            "--values",
            str(VALUES),
            "--smoke-preview",
            "--smoke-profile",
            "--smoke-batch-dir",
            str(batch_dir),
            "--smoke-output",
            str(output),
            "--smoke-screenshot",
            str(screenshot),
        ],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (
        "GUI smoke OK fields=13 values=13 complete=True "
        "preview=True field_preview=True profile=True batch=2 screenshot=True"
    ) in result.stdout
    assert output.exists()
    assert screenshot.exists()
    assert screenshot.stat().st_size > 0
    for filename in EXPECTED_BATCH_FILES:
        pdf_path = batch_dir / filename
        assert pdf_path.exists()
        assert _page_count(pdf_path) == 1
