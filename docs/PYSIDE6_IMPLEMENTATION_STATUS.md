# PySide6 Implementation Status

Date: 2026-06-16

This is the current runnable state of the PySide6 UI work. The design source is
`docs/PYSIDE6_UI_DESIGN.md`; this file records what is actually implemented.

## Implemented

- G0 shell: `handfont-gui` launches a PySide6 main window with workflow rail,
  central workspace, right inspector, status bar, and service injection.
- G1 main path: load a PDF template with `TemplateService`, load values JSON
  with `ValueSetService`, edit selected field values in memory, and export via
  `FillDocumentService`.
- G2 preview path: full-page preview renders through a temporary PDF using the
  same `FillDocumentService`; selected-field preview uses `RenderTextService`
  and overlays the rendered handwriting on the field rectangle.
- G3 profile drawer: handwriting controls update the active `RenderProfile`
  through `ProfileViewModel`; sample preview uses `RenderTextService`.
- G4 batch workbench: switch between single and batch modes; add current
  in-memory values as multiple batch items; run them through
  `BatchFillService`.

## Run

```powershell
python -m pip install -r requirements.txt
python -m pip install -e .
handfont-gui
```

## Smoke Test

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
handfont-gui `
  --smoke `
  --template "samples\附件六_管線工程施工自主檢查表.pdf" `
  --values samples\values_sample.json `
  --smoke-preview `
  --smoke-profile `
  --smoke-batch-dir "$env:TEMP\mrse-batch-smoke" `
  --smoke-output "$env:TEMP\mrse-gui-smoke.pdf"
```

Expected summary:

```text
GUI smoke OK fields=13 values=13 complete=True preview=True field_preview=True profile=True batch=2
```

## Next

- G5 polish: empty/error states, visual spacing, keyboard flow, and window-state
  cleanup.
- Move long PDF operations to `QThreadPool` workers for visible UI use; the
  worker wrapper already exists, but preview/export/batch are still synchronous.
- Expand batch import beyond "current values" to multiple JSON files and later
  CSV/Excel rows.
- Keep old Tkinter/CustomTkinter GUIs until the PySide6 path fully covers confirm
  and router-curation workflows.
