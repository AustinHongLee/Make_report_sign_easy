# 專案結構與慣例（繁中）

本專案已切換為「標準 src 佈局」：套件原始碼皆位於 `src/Make_report_sign_easy/`。
根目錄僅保留工具腳本與若干過渡檔（將逐步清理），打包時只從 `src/` 發佈。

- 主套件路徑：`src/Make_report_sign_easy/`
- 工具腳本：`tools/`（直接執行仍可用，會優先引用 src）
- `pyproject.toml` 使用 `setuptools` 的 `find`（`where = ["src"]`）。

## 目前佈局（2025-11-04）

- `src/Make_report_sign_easy/`
  - 核心模組：`builder.py`, `config.py`, `extractor.py`, `transform.py`,
    `draw_cjk.py`, `draw_hollow.py`, `utils.py`, `auto_update.py`
  - GUI 元件：`config_panel.py`
  - 工具子套件：`tools/`（供安裝後的 entry points 使用）
  - 資料與資產：`fonts/`, `configs/`, `version.json`
- 根目錄（開發/過渡）
  - `tools/`：可直接執行（會優先引用 `src/`）
  - `samples/`：範例資料
  - `tests/`：測試
  - 若根目錄仍有重複模組/資源，將在後續清理

## 狀態（2025-11-04）

- 已正式啟用 src 佈局，打包只含 `src/` 的套件與資源。
- `tools/` 腳本在專案根直接執行仍可用（內含路徑偏好 `src/` 的邏輯）。
- 推薦以可編輯安裝進行開發：
  ```powershell
  pip install -e .
  handfont-fill-pdf-gui
  ```

## 接下來的小清理（可逐步）

1. 移除根目錄中已重複的模組與資源（保留必要的啟動腳本）。
2. 測試改用 `src` 匯入（或直接依安裝後環境）。
3. MANIFEST 精簡為僅追蹤 `src/` 的資產（目前仍兼容雙路徑）。

## 擴充建議

- 新 CLI → 放到 `tools/` 並透過 `[project.scripts]` 暴露命令。
- 新 GUI → 優先做成可重用的 Panel，啟動器放在 `tools/`。
- 新的渲染行為 → 盡量以純函式加入核心模組，並以 `builder.generate_text_image` 的參數來暴露能力，降低耦合。
- 新增設定 → 將參數登錄到 `config.PARAM_INFO` 並標明安全範圍；GUI 會自動讀取。

## VS Code 小撇步

- 直接執行 GUI：`python tools/fill_pdf_gui.py`
- 已安裝後可用 entry point：`handfont-fill-pdf-gui`
- 試玩 src 佈局：設定 `PYTHONPATH=src` 或用 `pip install -e .`。
