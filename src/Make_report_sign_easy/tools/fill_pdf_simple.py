"""
# flake8: noqa
# pylint: disable=C0301

Minimal CLI: fill a PDF using FreeText annotation keys mapped to handwriting-style images.
"""
import os
import sys
import argparse
from pathlib import Path

# Allow running directly: prefer src on sys.path
if __name__ == "__main__" and __package__ is None:
    here = os.path.dirname(__file__)
    repo_root = os.path.abspath(os.path.join(here, "..", "..", ".."))
    src_root = os.path.join(repo_root, "src")
    if os.path.isdir(src_root):
        sys.path.insert(0, src_root)
    sys.path.insert(0, repo_root)

from Make_report_sign_easy.pdf import extract_freetext_positions  # noqa: E402,F401
from Make_report_sign_easy.pdf.fill import paste_image_centered  # noqa: E402,F401
from Make_report_sign_easy.services import (  # noqa: E402
    FillDocumentRequest,
    FillDocumentService,
)


def _console_text(value):
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Fill a PDF template using FreeText annotation keys and hand-"
            "written style text images."
        )
    )
    parser.add_argument("--template", required=True, help="Path to the PDF template")
    parser.add_argument("--output", required=True, help="Path to save the filled PDF")
    parser.add_argument(
        "--values", required=True, help="Path to JSON mapping: {field_key: text}"
    )
    parser.add_argument(
        "--clear-annots", action="store_true", help="Remove annotations after insertion"
    )
    parser.add_argument(
        "--random", action="store_true", help="Enable random jitter for each character"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed the renderer randomness for reproducible smoke/golden runs",
    )
    args = parser.parse_args()

    if not os.path.exists(args.template):
        raise FileNotFoundError(args.template)
    if not os.path.exists(args.values):
        raise FileNotFoundError(args.values)

    result = FillDocumentService().run(
        FillDocumentRequest(
            template_path=Path(args.template),
            values_path=Path(args.values),
            output_path=Path(args.output),
            clear_annots=args.clear_annots,
            random=args.random,
            seed=args.seed,
        )
    )

    if result.missing_fields:
        print(
            "Warning: missing fields:",
            _console_text(", ".join(result.missing_fields)),
        )
    print(f"Saved output: {_console_text(result.output_path)}")


if __name__ == "__main__":
    main()
