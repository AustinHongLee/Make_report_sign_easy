from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from Make_report_sign_easy.gui.main_window import MainWindow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch the HandFont Studio GUI.")
    parser.add_argument("--template", default=None, help="Optional PDF template to load")
    parser.add_argument("--values", default=None, help="Optional values JSON to load")
    parser.add_argument("--smoke", action="store_true", help="Run a no-event-loop GUI smoke")
    parser.add_argument("--smoke-preview", action="store_true", help="Generate full and field previews in smoke mode")
    parser.add_argument("--smoke-output", default=None, help="Optional PDF output for smoke mode")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.smoke:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    app = QApplication.instance() or QApplication(sys.argv[:1])
    window = MainWindow()

    if args.template:
        window.load_template(Path(args.template))
    if args.values:
        window.load_values(Path(args.values))
    preview_path = None
    field_preview = None
    if args.smoke_preview:
        preview_path = window.generate_full_preview()
        field_preview = window.preview_selected_field()
    if args.smoke_output:
        window.export_pdf(Path(args.smoke_output), notify=False)

    if args.smoke:
        fields = len(window.session.template.fields) if window.session.template else 0
        values = len(window.session.values)
        complete = bool(window.session.inspection and window.session.inspection.is_complete)
        preview_ok = bool(preview_path and preview_path.exists())
        field_preview_ok = field_preview is not None
        print(
            "GUI smoke OK "
            f"fields={fields} values={values} complete={complete} "
            f"preview={preview_ok} field_preview={field_preview_ok}"
        )
        window.close()
        app.quit()
        return 0

    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
