# Tools Overview

This repo provides two ways to run tools during development:

- Root scripts (recommended while developing):
  - `tools/fill_pdf_gui.py` — GUI to fill FreeText fields with handwriting-style text
  - `tools/fill_pdf_simple.py` — CLI that fills page-1 FreeText fields from a JSON mapping

- Packaged tools (for installed environments):
  - `src/Make_report_sign_easy/tools/*` (do not edit here during development)
  - Exposed via entry points: `handfont-fill-pdf-gui`, `handfont-fill-pdf`

Notes:
- Root tools prefer `src/` on sys.path when present, so you can test the latest package code.
- The `src/.../tools` copies exist to support packaging; the workspace hides `src/Make_report_sign_easy/` by default to reduce clutter.
- Fonts can be placed in the repo `fonts/` (bundled) or external locations via `MRSE_FONTS_DIR` or user-level font folders. See `fonts/README.txt`.
