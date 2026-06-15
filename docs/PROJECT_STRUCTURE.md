# Project Structure

This repo now uses a standard `src/` layout. The root directory should stay
small and only contain project metadata, install helpers, samples, docs, tests,
and development launchers.

## Active Layout

- `src/Make_report_sign_easy/`
  - `builder.py` - public handwriting image generation API.
  - `config.py` - render parameters, font lookup, routes, and custom config.
  - `draw_cjk.py`, `draw_hollow.py`, `transform.py`, `utils.py` - render helpers.
  - `config_panel.py`, `config_gui.py`, `ctk_gui.py` - current config UIs.
  - `tools/fill_pdf_simple.py` and `tools/fill_pdf_gui.py` - packaged PDF tools.
  - `fonts/` and `configs/` - bundled fonts and JSON defaults.
- `tools/`
  - Root-level development launchers. These import from `src/` directly.
  - Keep these thin. Move reusable behavior into `src/Make_report_sign_easy/`.
- `samples/`
  - Sample PDF template and `values_sample.json` used by smoke tests.
- `tests/`
  - Focused pytest coverage for the handwriting renderer.
- `docs/`
  - Handoff, redesign brief, structure notes, font licenses, and old logs.

## Ignored Generated Output

The following are generated or local state and should not be committed:

- `__pycache__/`
- `.pytest_cache/`
- `demo_output/`
- `previews/`
- `confirm/`
- `src/Make_report_sign_easy/confirm/`

## Development Rule Of Thumb

Use `src/Make_report_sign_easy/` for real code, `tools/` for temporary launchers,
and `docs/AI_HANDOFF.md` as the shortest map for future AI-assisted work.
