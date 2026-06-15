"""Development wrapper for the packaged PDF fill CLI."""

from __future__ import annotations

import os
import sys


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_ROOT = os.path.join(REPO_ROOT, "src")
if os.path.isdir(SRC_ROOT) and SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

from Make_report_sign_easy.pdf import extract_freetext_positions  # noqa: E402,F401
from Make_report_sign_easy.pdf.fill import paste_image_centered  # noqa: E402,F401
from Make_report_sign_easy.tools.fill_pdf_simple import main  # noqa: E402


if __name__ == "__main__":
    main()
