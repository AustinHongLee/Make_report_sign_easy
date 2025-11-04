"""
Make_report_sign_easy root shim

此檔為過渡期相容用：
- 將套件搜尋路徑指向 `src/Make_report_sign_easy/`，避免根目錄重複檔案。
- 保留 __version__，其餘 API 與子模組請由 src 版位提供。
"""
import os

__version__ = "0.1.0"

# 讓此 package 的子模組解析，優先走 src 版位
_REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
_SRC_PKG = os.path.join(_REPO_ROOT, 'src', 'Make_report_sign_easy')
if os.path.isdir(_SRC_PKG):
    # 調整 __path__ 供相對子模組探索（e.g., from . import config）
    # 僅以 src 套件目錄作為子模組搜尋路徑，避免根目錄殘留檔案被誤用
    __path__ = [_SRC_PKG]  # type: ignore[var-annotated]
