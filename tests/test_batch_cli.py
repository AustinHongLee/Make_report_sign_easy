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


def test_batch_cli_fills_jobs_json(tmp_path):
    expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
    jobs_path = tmp_path / "jobs.json"
    output_dir = tmp_path / "out"
    values = json.loads(VALUES.read_text(encoding="utf-8"))
    jobs_path.write_text(
        json.dumps(
            [
                {"output": "first.pdf", "values": values, "seed": 0},
                {
                    "output": "nested/second.pdf",
                    "values_path": str(VALUES),
                    "seed": 0,
                },
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "Make_report_sign_easy.tools.fill_pdf_batch",
            "--template",
            str(TEMPLATE),
            "--jobs",
            str(jobs_path),
            "--output-dir",
            str(output_dir),
            "--clear-annots",
        ],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    first = output_dir / "first.pdf"
    second = output_dir / "nested" / "second.pdf"
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Saved 2 PDFs" in result.stdout
    assert _page_render_hash(first) == expected["filled_pdf_render"]
    assert _page_render_hash(second) == expected["filled_pdf_render"]
