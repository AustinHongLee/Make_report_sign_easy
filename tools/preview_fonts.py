import os
import sys

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
src_root = os.path.join(repo_root, "src")
if os.path.isdir(src_root):
    sys.path.insert(0, src_root)

from Make_report_sign_easy.builder import generate_text_image  # noqa: E402
from Make_report_sign_easy import config  # noqa: E402
from Make_report_sign_easy.utils import sanitize_filename_char  # noqa: E402


def _console_text(value):
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


# 可支援：python preview_fonts.py 李宗鴻
target_text = sys.argv[1] if len(sys.argv) > 1 else "7"
safe_text = "".join(sanitize_filename_char(ch) for ch in target_text)

FONT_DIR = config.FONTS_DIR or os.path.join(config.BASE_DIR, "fonts")
OUTPUT_BASE = os.path.join(repo_root, "previews", safe_text)
os.makedirs(OUTPUT_BASE, exist_ok=True)
print(f"Preview output: {_console_text(OUTPUT_BASE)}")

for font_file in os.listdir(FONT_DIR):
    if not font_file.lower().endswith(".ttf"):
        continue

    font_path = os.path.join(FONT_DIR, font_file)
    
    for ch in target_text:
        try:
            img = generate_text_image(
                ch,
                font_path=font_path,
                size=config.IMAGE_SIZE,
                ignore_router=True,
            )
            if img:
                safe_ch = sanitize_filename_char(ch)
                output_path = os.path.join(OUTPUT_BASE, f"{safe_ch}_{font_file}.png")
                img.save(output_path)
                print(
                    "Rendered: "
                    f"{_console_text(safe_ch)} - {font_file} -> "
                    f"{_console_text(output_path)}"
                )
            else:
                print(
                    "Skipped: "
                    f"{_console_text(sanitize_filename_char(ch))} - {font_file}"
                )
        except Exception as e:
            print(
                "Error: "
                f"{_console_text(sanitize_filename_char(ch))} - "
                f"{font_file}: {_console_text(e)}"
            )
