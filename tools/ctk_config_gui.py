import os
import sys

# Ensure src layout is importable
repo_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
src_root = os.path.join(repo_root, "src")
if os.path.isdir(src_root):
    sys.path.insert(0, src_root)
sys.path.insert(0, repo_root)

from Make_report_sign_easy.ctk_gui import main as ctk_main  # noqa: E402


def run():
    ctk_main()


if __name__ == "__main__":
    run()
