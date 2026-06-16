from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

from Make_report_sign_easy.gui.main_window import MainWindow


UI_FONT_CANDIDATES = (
    "Microsoft JhengHei UI",
    "Microsoft JhengHei",
    "Noto Sans CJK TC",
    "Segoe UI",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch the HandFont Studio GUI.")
    parser.add_argument("--template", default=None, help="Optional PDF template to load")
    parser.add_argument("--values", default=None, help="Optional values JSON to load")
    parser.add_argument("--smoke", action="store_true", help="Run a no-event-loop GUI smoke")
    parser.add_argument("--smoke-preview", action="store_true", help="Generate full and field previews in smoke mode")
    parser.add_argument("--smoke-profile", action="store_true", help="Render the profile drawer sample in smoke mode")
    parser.add_argument("--smoke-batch-dir", default=None, help="Optional directory for batch smoke outputs")
    parser.add_argument("--smoke-output", default=None, help="Optional PDF output for smoke mode")
    parser.add_argument("--smoke-screenshot", default=None, help="Optional PNG screenshot path for smoke mode")
    return parser


def apply_ui_font(app: QApplication) -> None:
    available = set(QFontDatabase.families())
    for family in UI_FONT_CANDIDATES:
        if family in available:
            app.setFont(QFont(family, 10))
            return


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.smoke:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    app = QApplication.instance() or QApplication(sys.argv[:1])
    apply_ui_font(app)
    window = MainWindow()

    if args.template:
        window.load_template(Path(args.template))
    if args.values:
        window.load_values(Path(args.values))
    preview_path = None
    field_preview = None
    profile_sample = None
    if args.smoke_preview:
        preview_path = window.generate_full_preview(blocking=True)
        field_preview = window.preview_selected_field()
    if args.smoke_profile:
        profile_sample = window.render_profile_sample()
    batch_result = None
    if args.smoke_batch_dir:
        batch_dir = Path(args.smoke_batch_dir)
        batch_dir.mkdir(parents=True, exist_ok=True)
        window.show_batch_mode()
        window.add_batch_current_values(batch_dir / "batch-1.pdf", label="batch-1", seed=0)
        window.add_batch_current_values(batch_dir / "batch-2.pdf", label="batch-2", seed=0)
        batch_result = window.run_batch(blocking=True)
    if args.smoke_output:
        window.export_pdf(Path(args.smoke_output), blocking=True, notify=False)

    if args.smoke:
        screenshot_ok = False
        if args.smoke_screenshot:
            screenshot_path = Path(args.smoke_screenshot)
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            window.show()
            app.processEvents()
            screenshot_ok = window.grab().save(str(screenshot_path))

        fields = len(window.session.template.fields) if window.session.template else 0
        values = len(window.session.values)
        complete = bool(window.session.inspection and window.session.inspection.is_complete)
        preview_ok = bool(preview_path and preview_path.exists())
        field_preview_ok = field_preview is not None
        profile_ok = profile_sample is not None
        batch_count = len(batch_result.output_paths) if batch_result else 0
        print(
            "GUI smoke OK "
            f"fields={fields} values={values} complete={complete} "
            f"preview={preview_ok} field_preview={field_preview_ok} profile={profile_ok} "
            f"batch={batch_count} screenshot={screenshot_ok}"
        )
        window.close()
        app.quit()
        return 0

    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
