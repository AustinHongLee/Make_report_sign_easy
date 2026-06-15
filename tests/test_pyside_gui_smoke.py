import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = REPO_ROOT / "samples" / "附件六_管線工程施工自主檢查表.pdf"
VALUES = REPO_ROOT / "samples" / "values_sample.json"


@pytest.mark.skipif(
    importlib.util.find_spec("PySide6") is None,
    reason="PySide6 is not installed",
)
def test_pyside_gui_smoke_loads_template_and_values(tmp_path):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    env["QT_QPA_PLATFORM"] = "offscreen"
    output = tmp_path / "gui-smoke.pdf"

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
            "--smoke-output",
            str(output),
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
        "preview=True field_preview=True"
    ) in result.stdout
    assert output.exists()
