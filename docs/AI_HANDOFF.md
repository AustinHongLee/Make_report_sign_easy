# AI Handoff

## One-Sentence Product

Make Report Sign Easy fills repetitive PDF forms by rendering handwritten-looking
text/signatures and placing them into predefined PDF fields.

## User Goal

The intended user has routine paperwork: repeated inspection sheets, signature
forms, daily reports, or checklists where the same names, dates, and marks are
typed over and over. The app should make that feel like:

1. Pick a PDF template.
2. Confirm detected fields.
3. Enter or reuse values.
4. Preview handwritten output.
5. Export the finished PDF.

## Current Reality

- Core rendering works.
- PDF CLI fill path works.
- Tkinter GUI can initialize and preview, but the UI is visually noisy.
- There are multiple legacy helper GUIs for font/config tuning.
- The project had duplicated docs and generated preview images committed; those
  have been cleaned out.

## Important Commands

```powershell
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pytest
python tools\fill_pdf_gui.py
python tools\fill_pdf_simple.py --template "samples\附件六_管線工程施工自主檢查表.pdf" --values samples\values_sample.json --output "$env:TEMP\mrse_output.pdf" --random --clear-annots
```

## Code Anchors

- `src/Make_report_sign_easy/builder.py`
  Main `generate_text_image(...)` API.
- `src/Make_report_sign_easy/config.py`
  Font lookup, routing, rendering defaults, and custom config loading.
- `tools/fill_pdf_gui.py`
  Legacy development GUI for PDF filling.
- `tools/fill_pdf_simple.py`
  Development CLI for PDF filling.
- `src/Make_report_sign_easy/tools/fill_pdf_simple.py`
  Packaged CLI implementation used by the entry point `handfont-fill-pdf`.
- `samples/values_sample.json`
  Concrete sample of field keys and values.

## Known Pain Points

- UI hierarchy is unclear. Too many controls compete on the first screen.
- The product concept is hidden behind implementation details.
- Font picking, per-field overrides, and export are mixed together too early.
- Field detection and "what should I do next?" need a clearer guided path.
- Preview/edit/export should be the main workspace, not scattered controls.

## Redesign Direction

Build around one workflow: template -> fields -> values -> preview -> export.

Keep advanced handwriting tuning available, but put it behind focused panels or
dialogs. The default path should work for a non-engineer doing repeated forms.

See `docs/UI_REDESIGN_BRIEF.md` for the UX brief.
