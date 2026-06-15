#!/usr/bin/env bash
# Setup script for Make_report_sign_easy
# Installs Python dependencies listed in requirements.txt

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

python -m pip install -r requirements.txt
python -m pip install -e .
echo "Installed Make Report Sign Easy."
echo "Start the GUI with: python tools/fill_pdf_gui.py"
echo "Or run the CLI with: handfont-fill-pdf --help"
