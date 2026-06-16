import importlib.util
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import fitz
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = REPO_ROOT / "samples" / "附件六_管線工程施工自主檢查表.pdf"
VALUES = REPO_ROOT / "samples" / "values_sample.json"
EXPECTED_BATCH_FILES = ("job-one.pdf", "job-two.pdf")


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
    values_one = tmp_path / "job-one.json"
    values_two = tmp_path / "job-two.json"
    values_data = json.loads(VALUES.read_text(encoding="utf-8"))
    values_one.write_text(json.dumps(values_data, ensure_ascii=False), encoding="utf-8")
    values_data["Sign_words"] = "王小明"
    values_data["Company_words"] = "第二份測試公司"
    values_two.write_text(json.dumps(values_data, ensure_ascii=False), encoding="utf-8")

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
            "--smoke-batch-values",
            str(values_one),
            str(values_two),
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
    assert hashlib.sha256((batch_dir / "job-one.pdf").read_bytes()).digest() != hashlib.sha256(
        (batch_dir / "job-two.pdf").read_bytes()
    ).digest()
