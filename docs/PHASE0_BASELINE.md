# Phase 0 Baseline

This file records the current behavior that must survive the first refactor
phases.

## Canonical Decisions

- CLI behavior is currently equivalent between the root development script
  `tools/fill_pdf_simple.py` and the packaged module
  `src/Make_report_sign_easy/tools/fill_pdf_simple.py`; both now call
  `FillDocumentService`.
- GUI behavior is not equivalent. The root development GUI
  `tools/fill_pdf_gui.py` is the current functional superset and must be treated
  as the canonical behavior source until its root-only features are migrated.
- The packaged GUI `src/Make_report_sign_easy/tools/fill_pdf_gui.py` is a stale
  copy candidate, not the source of truth.
- Do not rename the package during Phase 0/1. Add new layers under the existing
  `src/Make_report_sign_easy/` package first.

## Tool Duplication Snapshot

- `tools/fill_pdf_simple.py`: 80 lines.
- `src/Make_report_sign_easy/tools/fill_pdf_simple.py`: 84 lines.
- `tools/fill_pdf_gui.py`: 1279 lines.
- `src/Make_report_sign_easy/tools/fill_pdf_gui.py`: 484 lines.

Root-only GUI behavior includes preview rendering, session overrides, filter
pipeline controls, quick adjustment, and rectangle adjustment. These cannot be
discarded before the PySide6 replacement or service layer has equivalent
coverage.

## Golden Checks

`tests/test_phase0_golden.py` regenerates output from the sample PDF and compares
it against `tests/golden/phase0_expected.json`.

The golden command path uses `--seed 0` so the existing renderer's global random
jitter is reproducible. Normal CLI behavior is unchanged when `--seed` is not
provided.

Run:

```powershell
python -m pytest
```
