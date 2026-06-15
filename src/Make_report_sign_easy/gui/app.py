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
    if args.smoke_output:
        window.export_pdf(Path(args.smoke_output), notify=False)

    if args.smoke:
        fields = len(window.session.template.fields) if window.session.template else 0
        values = len(window.session.values)
        complete = bool(window.session.inspection and window.session.inspection.is_complete)
        print(f"GUI smoke OK fields={fields} values={values} complete={complete}")
        window.close()
        app.quit()
        return 0

    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
