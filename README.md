# ✍️ Make Report Sign Easy

> 中文 / English

## 介紹 Introduction

### 中文
HandFont 是一套模擬手寫風格的文字渲染工具，能在電腦上產生具有筆跡感的中文字、英數與符號。它支援多字型路由，可為特定字元指定專屬字體，並透過參數調整模擬筆劃抖動、墨色變化與模糊等效果。社群可共同貢獻最佳字型組合，逐步完善整體書寫風格。

### English
HandFont is a handwriting-style renderer for Chinese characters, Latin letters and symbols. It simulates realistic jitter, pen pressure and ink effects. Each character can be routed to its own font file, allowing fine‑grained control over appearance. Parameters are configurable and the community is encouraged to contribute font routes to improve the overall handwriting feel.

## 安裝 Installation
安裝方式有兩種：直接用原始碼開發（推薦）或安裝為套件。

- 下載專案並安裝相依套件：
  - Linux/macOS (bash/zsh)：
    ```bash
    git clone https://github.com/AustinHongLee/Make_report_sign_easy.git
    cd Make_report_sign_easy
    pip install -r requirements.txt
    ```
  - Windows (PowerShell)：
    ```powershell
    git clone https://github.com/AustinHongLee/Make_report_sign_easy.git
    Set-Location Make_report_sign_easy
    pip install -r requirements.txt
    ```
- 選擇性：以可編輯模式安裝本套件，方便開發時即時生效：
  ```bash
  pip install -e .
  ```

字型來源建議使用外部資料夾以降低套件體積：
- 設定環境變數 MRSE_FONTS_DIR → 指到你的字型資料夾
  - Windows (PowerShell)：
    ```powershell
    $env:MRSE_FONTS_DIR = "C:\fonts\handwriting"  # 本次工作階段有效
    # 如需永久設定，建議透過 系統環境變數 -> 使用者變數 新增 MRSE_FONTS_DIR
    ```
  - Linux/macOS (bash)：
    ```bash
    export MRSE_FONTS_DIR=~/fonts/handwriting
    ```
若未設定，程式會依序尋找：使用者資料夾字型 → 內建字型 →（Windows）系統字型。

## 快速使用 Quick Start
```python
from Make_report_sign_easy.builder import generate_text_image
img = generate_text_image("手寫效果", random=True)  # randomize parameters for variety
img.save("example.png")
```

### GUI 快速入門（推薦）
```powershell
# 在專案根（或安裝後）執行：
python tools/fill_pdf_gui.py
```
- 選擇含有 FreeText 註解的 PDF（註解內容作為欄位鍵）
- 讀取欄位 → 可載入 `samples/values_sample.json`
- 進階設定（全域/欄位）可細調線寬、模糊、抖動、縮放等
- 預覽確認後，可直接輸出 PDF

字型來源說明：
- 專案內建 `fonts/` 可直接使用；也支援外部字型資料夾以減少套件體積：
  - 環境變數 `MRSE_FONTS_DIR`
  - 使用者目錄（Windows: `%APPDATA%/MakeReportSignEasy/fonts`；macOS: `~/Library/Application Support/MakeReportSignEasy/fonts`；Linux: `~/.local/share/MakeReportSignEasy/fonts`）
  - Windows 系統字型資料夾做備援
Router 內如使用 `fonts/xxx.ttf` 相對路徑，會優先在外部/使用者字型資料夾中尋找，找不到再回退到專案內 `fonts/`。

### 進階設定 Advanced Config
在 `config.py` 中可調整筆劃抖動與傾斜角度，
並透過 `PERTURB_JITTER`、`SHEAR_JITTER` 讓每個字產生些許隨機變化，
也可以變更 `FONT_PATH` 或使用下方的 GUI 選擇不同字型，
使整體效果更接近自然手寫。
若想在每次渲染時自動微調設定參數，可將 `generate_text_image` 的
`random` 參數設為 `True`。

### 參數圖形介面 Config GUI
執行 `python -m Make_report_sign_easy.config_gui` 可開啟圖形介面調整參數，
介面提供中文說明並支援「字距調整」與**字體檔選擇**功能，
在左側選擇想要的 `.ttf` 字型後即可即時預覽，按下「儲存設定」會將選擇寫入
`configs/custom_config.json`，下次載入模組時便會套用。
若偏好較現代的外觀，可改用 `python -m Make_report_sign_easy.ctk_gui`
開啟 CustomTkinter 版本的深色介面。

### 執行範例 Running the demo
請在 *專案資料夾的上層* （或於安裝後）使用 `python -m` 執行，
若在模組資料夾內執行將出現 `ModuleNotFoundError`：

```bash
python -m Make_report_sign_easy.demo "自訂文字" -o output_dir
python -m Make_report_sign_easy.tools.preview_fonts 李
```
`preview_fonts.py` 執行完會告知預覽圖片存放的路徑（預設在 `previews/`）。

## 字型路由 Font Routing
在 `configs/font_routes_template.json` 中指定字 → 字體的映射，例如：
```json
{
  "李": "fonts/JasonHandwriting2.ttf",
  "4":  "fonts/851tegaki_zatsu_normal.ttf"
}
```
`tools/preview_fonts.py` 可預覽指定字元的所有字型，協助挑選最合適的筆感。

## 專案結構 Project Structure
本專案已採用標準 src 佈局，套件原始碼位於 `src/Make_report_sign_easy/`；
工具腳本位於根目錄的 `tools/`，直接執行會優先引用 src。

```
src/
  Make_report_sign_easy/
    (核心模組、tools 子套件、fonts/、configs/、version.json)
tools/            # 輔助腳本（直接執行）
samples/          # 範例資料
docs/             # 說明與日誌
tests/            # 測試
```

更多細節請參考 [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)。

## 貢獻方式 Contributing
1. Fork 本倉庫並新增或修改 `configs/font_routes_template.json`。
2. 若有自製字型，請附上授權說明。
3. 提交 Pull Request，我們會一同確認與測試。

## 字型授權 Font Licenses
專案使用的所有字型來源與授權說明已整理於 [docs/FONT_LICENSES.md](docs/FONT_LICENSES.md)。
在商業用途之前請務必確認各字型的授權條件。

## 代碼授權 Code License
本倉庫中除字型檔外的所有程式碼以 [MIT License](LICENSE) 授權釋出。
字型檔案則依 [docs/FONT_LICENSES.md](docs/FONT_LICENSES.md) 所列之授權條款分別管理。

## Packaging

This project can be built as a Python package:
```bash
python -m build
```
Upload the generated wheel in `dist/` to PyPI using `twine`.

### PyInstaller
To create a standalone executable:
```bash
pyinstaller -F -m Make_report_sign_easy
```
The configuration automatically detects the PyInstaller runtime path.

### Auto Update
The command-line and GUI tools check GitHub for a newer version on startup.
If a new release is found, a reminder message will be shown.

## 測試 Tests
專案隨附基本的 `pytest` 測試，可透過下列指令執行：

```bash
bash setup.sh  # 安裝依賴與套件後執行測試
pytest
```

### 進階開發指引
更多關於部署與後續優化的建議，請參考 [docs/DEVELOPMENT_GUIDE.md](docs/DEVELOPMENT_GUIDE.md)。

Made with ❤️ by [AustinHongLee]
