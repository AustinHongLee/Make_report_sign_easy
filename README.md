# Make Report Sign Easy

Make Report Sign Easy is a small Python tool for repetitive PDF paperwork.
It turns field values such as names, dates, checks, and signatures into
handwriting-style images, then places them back into matching PDF fields.

The practical target is boring recurring forms: the same inspection sheet,
signature sheet, or daily report that needs the same human-looking writing
again and again.

## What It Does

- Reads FreeText annotations from a PDF template as field keys.
- Loads values from JSON.
- Renders each value with handwriting fonts, jitter, scaling, blur, and routing.
- Inserts the rendered images into the matching PDF positions.
- Provides a legacy Tkinter GUI and a CLI for the same PDF fill path.
- Starts a new PySide6 GUI shell through `handfont-gui` for the service-backed
  redesign work.

The current GUI is a prototype. It works, but the layout is cluttered and should
be redesigned around the main workflow.

## Quick Start

```powershell
python -m pip install -r requirements.txt
python -m pip install -e .
handfont-gui
```

CLI smoke test:

```powershell
handfont-fill-pdf `
  --template "samples\附件六_管線工程施工自主檢查表.pdf" `
  --values samples\values_sample.json `
  --output "%TEMP%\mrse_output.pdf" `
  --random `
  --clear-annots
```

## Repo Map

- `src/Make_report_sign_easy/` - packaged app code and bundled assets.
- `tools/` - development launchers for the current GUI and helper tools.
- `samples/` - sample PDF template and JSON field values.
- `tests/` - focused tests for the handwriting renderer.
- `docs/AI_HANDOFF.md` - fast technical handoff for the next AI/dev session.
- `docs/UI_REDESIGN_BRIEF.md` - product and UX brief for redesign work.
- `docs/FONT_LICENSES.md` - bundled font license notes.

Generated preview images are intentionally ignored by Git. Recreate them with:

```powershell
python tools\preview_fonts.py 李宗鴻
```

## Current Verification

Last verified locally on 2026-06-15:

- `python -m pytest`
- Root CLI PDF fill smoke test.
- Package CLI PDF fill smoke test.
- GUI initialization smoke test.
- PDF preview render smoke test.

See `docs/AI_HANDOFF.md` for exact commands and current redesign notes.
