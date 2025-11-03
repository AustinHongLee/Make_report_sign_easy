# Project Structure and Conventions

This repository uses a single-package layout where the repository root is the
package directory for `Make_report_sign_easy`. To evolve towards a
project-grade, extensible layout while minimizing churn, we follow these rules:

- Root folder is the package. Subpackages live as folders with `__init__.py`
  at the root (e.g., `tools/`).
- Public modules/APIs remain stable; new UI/CLI are grouped under subpackages.
- Console scripts in `pyproject.toml` point to packaged modules only.

## Current layout (after cleanup)

- [package root]
  - `__init__.py` – package marker
  - Core modules: `builder.py`, `config.py`, `extractor.py`, `transform.py`,
    `draw_cjk.py`, `draw_hollow.py`, `utils.py`, `auto_update.py`
  - GUI components:
    - `config_panel.py` – reusable advanced config panel (Frame)
  - Subpackages:
    - `tools/` – packaged tools and GUIs
      - `__init__.py`
      - `fill_pdf_gui.py` – PDF filler GUI (preview + export)
      - `fill_pdf_simple.py` – minimal CLI/utility
  - Data & assets:
    - `fonts/` – packaged fonts (ttf)
    - `configs/` – presets and templates
    - `version.json`
  - Tests: `tests/`
  - Samples: `Sample/` (values examples)

## Phase A status (2025-11-03)

- A src skeleton exists at `src/Make_report_sign_easy/` to prepare for a future src-layout.
- Direct-run scripts (e.g., `tools/fill_pdf_gui.py`, `tools/fill_pdf_simple.py`) now prefer the `src/` path if present, then fall back to repo root. This lets you experiment with src-layout locally without breaking imports.
- To try the src-layout without installing:
  - PowerShell (temporary):
    ```powershell
    $env:PYTHONPATH = "src"; python tools/fill_pdf_gui.py
    ```
  - Or install in editable mode (recommended for dev):
    ```powershell
    pip install -e .
    handfont-fill-pdf-gui
    ```

## Roadmap to src-layout (optional, future)

To migrate to a canonical src-layout without breaking users:

1. Create `src/Make_report_sign_easy/` and move all package code there.
2. Update `pyproject.toml` to:
   ```toml
   [tool.setuptools]
   package-dir = {"" = "src"}
   packages = ["Make_report_sign_easy"]
   include-package-data = true
   ```
3. Keep console scripts pointing to the new module paths.
4. Add thin compatibility shims (deprecated modules re-export) if needed.

## Extensibility guidance

- New CLIs → add under `tools/` and register via `[project.scripts]`.
- New GUIs → prefer reusable panels (Frames) under root or `gui/` (future), and
  small launchers under `tools/`.
- New rendering behaviors → add pure functions in core modules; expose via
  `builder.generate_text_image` options to avoid tight coupling.
- Config knobs → add to `config.PARAM_INFO` and document ranges; GUIs pick them
  up automatically via `ConfigPanel`.

## VS Code tips

- Run GUIs directly: `python tools/fill_pdf_gui.py`
- Or via entry points once installed: `handfont-fill-pdf-gui`
 - When experimenting with src-layout: set `PYTHONPATH=src` or use `pip install -e .` as above.

