# ✍️ Make Report Sign Easy

> 中文 / English

## 介紹 Introduction

### 中文
HandFont 是一套模擬手寫風格的文字渲染工具，能在電腦上產生具有筆跡感的中文字、英數與符號。它支援多字型路由，可為特定字元指定專屬字體，並透過參數調整模擬筆劃抖動、墨色變化與模糊等效果。社群可共同貢獻最佳字型組合，逐步完善整體書寫風格。

### English
HandFont is a handwriting-style renderer for Chinese characters, Latin letters and symbols. It simulates realistic jitter, pen pressure and ink effects. Each character can be routed to its own font file, allowing fine‑grained control over appearance. Parameters are configurable and the community is encouraged to contribute font routes to improve the overall handwriting feel.

## 安裝 Installation
```bash
pip install pillow fonttools
# 下載本專案
git clone https://github.com/AustinHongLee/Make_report_sign_easy.git
cd Make_report_sign_easy
bash setup.sh  # 安裝相依套件
```

## 快速使用 Quick Start
```python
from Make_report_sign_easy.builder import generate_text_image
img = generate_text_image("手寫效果")
img.save("example.png")
```

### 進階設定 Advanced Config
在 `config.py` 中可調整筆劃抖動與傾斜角度，
並透過 `PERTURB_JITTER`、`SHEAR_JITTER` 讓每個字產生些許隨機變化，
也可以變更 `FONT_PATH` 或使用下方的 GUI 選擇不同字型，
使整體效果更接近自然手寫。

### 參數圖形介面 Config GUI
執行 `python -m Make_report_sign_easy.config_gui` 可開啟圖形介面調整參數，
介面提供中文說明並支援「字距調整」與**字體檔選擇**功能，
在左側選擇想要的 `.ttf` 字型後即可即時預覽，按下「儲存設定」會將選擇寫入
`custom_config.json`，下次載入模組時便會套用。

### 執行範例 Running the demo
請在 *專案資料夾的上層* （或於安裝後）使用 `python -m` 執行，
若在模組資料夾內執行將出現 `ModuleNotFoundError`：

```bash
python -m Make_report_sign_easy.demo "自訂文字" -o output_dir
python -m Make_report_sign_easy.tools.preview_fonts 李
```
`preview_fonts.py` 執行完會告知預覽圖片存放的路徑（預設在 `previews/`）。

## 字型路由 Font Routing
在 `font_routes_template.json` 中指定字 → 字體的映射，例如：
```json
{
  "李": "fonts/JasonHandwriting2.ttf",
  "4":  "fonts/851tegaki_zatsu_normal.ttf"
}
```
`tools/preview_fonts.py` 可預覽指定字元的所有字型，協助挑選最合適的筆感。

## 專案結構 Project Structure
```
Make_report_sign_easy/        # 核心模組
fonts/           # 字型檔案
previews/        # 產生的字型預覽
confirm/         # 社群確認的最佳字型
tools/           # 輔助腳本
```

## 貢獻方式 Contributing
1. Fork 本倉庫並新增或修改 `font_routes_template.json`。
2. 若有自製字型，請附上授權說明。
3. 提交 Pull Request，我們會一同確認與測試。

## 字型授權 Font Licenses
專案使用的所有字型來源與授權說明已整理於 [FONT_LICENSES.md](FONT_LICENSES.md)。
在商業用途之前請務必確認各字型的授權條件。

## 代碼授權 Code License
本倉庫中除字型檔外的所有程式碼以 [MIT License](LICENSE) 授權釋出。
字型檔案則依 [FONT_LICENSES.md](FONT_LICENSES.md) 所列之授權條款分別管理。

## 測試 Tests
專案隨附基本的 `pytest` 測試，可透過下列指令執行：

```bash
bash setup.sh  # 或直接安裝需求套件
pytest
```

Made with ❤️ by [AustinHongLee]
