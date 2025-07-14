#!/usr/bin/env bash
# Setup script for Make_report_sign_easy
# Installs Python dependencies listed in requirements.txt

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

python -m pip install -r requirements.txt

echo "Dependencies installed."
