# AI 交接前導書

> 下一位接手者請先讀本檔(技術現況、指令、程式碼地圖),再讀
> `docs/UI_REDESIGN_BRIEF.md`(UI/UX 重構方向),即可掌握功能、痛點與下一步。

## 一句話產品

Make Report Sign Easy 把重複性的 PDF 表單自動填好:將文字/簽名渲染成「手寫風格」
影像,再貼回 PDF 上預先標好的欄位。

## 使用者目標

目標使用者有大量例行紙本作業:重複的施工自主檢查表、簽名單、每日報表或檢核表,
同樣的姓名、日期、記號要一填再填。理想體驗應是:

1. 選一份 PDF 範本。
2. 確認偵測到的欄位。
3. 輸入或沿用既有數值。
4. 預覽手寫風格輸出。
5. 匯出完成的 PDF。

核心流程一句話:範本 → 欄位 → 數值 → 預覽 → 匯出。

## 目前現況

- 核心手寫渲染可用(`builder.generate_text_image`)。
- PDF 填寫 CLI 路徑可用(`handfont-fill-pdf`)。
- Tkinter/customtkinter GUI 可啟動並預覽,但版面雜亂、產品概念被實作細節蓋住。
- 仍保留多個舊版輔助 GUI(字型/設定微調用),散落在 `tools/` 與 `src/.../`。
- 先前重複的文件與已提交的預覽圖已清掉。

## 技術堆疊與依賴

- Python 3.8+。
- 影像:Pillow。字型:fonttools。GUI:customtkinter。版本檢查:packaging。
- **PDF:PyMuPDF(`import fitz`)** ── 範本讀取、欄位偵測、影像貼回都靠它,務必安裝。
- 開發依賴(`requirements-dev.txt`):build、pytest、ruff。

執行階段依賴定義於 `requirements.txt`;打包與進入點定義於 `pyproject.toml`。

## 重要指令(PowerShell)

```powershell
# 安裝(執行階段 + 可編輯安裝)
python -m pip install -r requirements.txt
python -m pip install -e .

# 測試(pytest 在開發依賴內)
python -m pip install -r requirements-dev.txt
python -m pytest

# 啟動開發用 GUI
python tools\fill_pdf_gui.py

# CLI 煙霧測試:用 FreeText 欄位 + JSON 數值填好一份 PDF
python tools\fill_pdf_simple.py `
  --template "samples\附件六_管線工程施工自主檢查表.pdf" `
  --values samples\values_sample.json `
  --output "$env:TEMP\mrse_output.pdf" `
  --random `
  --clear-annots
```

## 進入點(`pyproject.toml` [project.scripts])

| 指令 | 對應 | 用途 |
| --- | --- | --- |
| `handfont-fill-pdf` | `Make_report_sign_easy.tools.fill_pdf_simple:main` | 主力 CLI:PDF 填寫 |
| `handfont-fill-pdf-batch` | `Make_report_sign_easy.tools.fill_pdf_batch:main` | 批次 CLI:一份範本搭配多組 values 產出多份 PDF |
| `handfont-fill-pdf-gui` | `Make_report_sign_easy.tools.fill_pdf_gui:main` | PDF 填寫 GUI |
| `handfont-ctk-gui` | `Make_report_sign_easy.ctk_gui:main` | customtkinter 主介面 |
| `handfont-config-gui` | `Make_report_sign_easy.config_gui:main` | 字型/設定調整 GUI |
| `handfont-demo` | `Make_report_sign_easy.demo:main` | 手寫渲染示範 |

CLI 參數(`handfont-fill-pdf`):`--template`、`--output`、`--values`(皆必填)、
`--clear-annots`(填完移除標註)、`--random`(逐字隨機抖動)。

批次 CLI(`handfont-fill-pdf-batch`)使用 jobs JSON list,每筆 job 需要 `output`,
並且在 `values` 或 `values_path` 二選一;可選 `seed` 用於重現輸出。

## 程式碼地圖(Code Anchors)

渲染核心
- `src/Make_report_sign_easy/core/models.py` ── Phase 1 起點:
  `RenderProfile.from_config(config)` 可凍結現有 render settings,
  `builder.generate_text_image(..., profile=profile)` 已可走相容層。
- `src/Make_report_sign_easy/services/render_text.py` ── headless
  `RenderTextService`,提供 UI/CLI 可共用的文字轉手寫影像入口。
- `src/Make_report_sign_easy/services/profiles.py` ── `ProfileService`,負責把
  legacy config / preset JSON 正規化成不可變 `RenderProfile`,也能存取新版
  lower-case profile JSON。
- `src/Make_report_sign_easy/builder.py` ── 公開 API `generate_text_image(...)`、
  `save_text_image(...)`。
- `src/Make_report_sign_easy/config.py` ── 字型搜尋路徑、router 路由、渲染預設值、
  自訂設定載入與驗證(`validate_and_apply`、`print_config_help`)。
- `src/Make_report_sign_easy/draw_cjk.py`、`draw_hollow.py`、`transform.py`、
  `utils.py` ── 渲染輔助(中日韓字形、空心字、幾何變形、共用工具)。
- `src/Make_report_sign_easy/extractor.py` ── `extract_paths(font_path, char)`,用
  fontTools 從 TTF 取字形輪廓路徑,供空心/輪廓渲染使用;由 `builder.py` 匯入。
  (注意:這是「字型輪廓」抽取,**不是** PDF 欄位偵測,別搞混。)
- `src/Make_report_sign_easy/safe_char_map.py` ── 字元對應/替代處理。

PDF 填寫
- `src/Make_report_sign_easy/services/batch.py` ── `BatchFillService`,同一份 PDF
  範本搭配多組 values 產出多份 PDF,對應「例行性重複簽名/填表」主需求。
- `src/Make_report_sign_easy/services/fill_document.py` ── headless
  `FillDocumentService`,目前 root/package CLI 都已呼叫這裡;也可直接吃記憶體內
  `values` mapping,供未來 GUI 編輯流程使用。
- `src/Make_report_sign_easy/services/template.py` ── `TemplateService`,負責載入
  PDF 範本欄位與檢查 values coverage(缺值 / 多餘 key / 已匹配 key)。
- `src/Make_report_sign_easy/services/values.py` ── `ValueSetService`,負責讀取與驗證
  JSON 欄位值 mapping。
- `src/Make_report_sign_easy/pdf/template.py`、`pdf/fill.py` ── FreeText 欄位偵測、
  PDF 影像置入與匯出 adapter。
- `src/Make_report_sign_easy/tools/fill_pdf_simple.py` ── 進入點 `handfont-fill-pdf`
  的薄 CLI。
- `src/Make_report_sign_easy/tools/fill_pdf_batch.py` ── 進入點
  `handfont-fill-pdf-batch` 的薄 CLI。
- `src/Make_report_sign_easy/tools/fill_pdf_gui.py` ── 打包版 PDF 填寫 GUI。
- `tools/fill_pdf_simple.py` ── 根目錄薄啟動器,只把 `src/` 放進 path 後交給
  package CLI。
- `tools/fill_pdf_gui.py` ── 根目錄 legacy GUI,目前仍是較完整的 GUI 行為來源。

GUI(目前散亂,重構主要對象)
- `src/Make_report_sign_easy/ctk_gui.py`、`config_gui.py`、`config_panel.py`。
- `tools/main_gui.py`、`tools/ctk_config_gui.py`、`tools/confirm_gui.py`、
  `tools/preview_fonts.py`。

範本與數值
- `samples/附件六_管線工程施工自主檢查表.pdf` ── 主要測試範本。
- `samples/Fount.pdf` ── 另一份範本。
- `samples/values_sample.json` ── 欄位 key 與數值的具體範例(key 結尾為 `_words`)。

## 欄位偵測機制(重構必懂)

PDF 範本的「欄位」就是 PDF 上的 **FreeText 標註(annotation)**,邏輯在
`fill_pdf_simple.py` / `fill_pdf_gui.py`:

1. 走訪 `page.annots()`,挑出 `annot.type[1] == "FreeText"`。
2. 用 `annot.info["content"]`(標註文字)當作**欄位 key**。
3. 用 `annot.rect` 當作**貼上位置框**。
4. 由 `values.json` 以 key 取數值 → `generate_text_image` 產生手寫影像 →
   等比縮放置中貼進該 rect。
5. `--clear-annots` 會在貼完後移除原始標註。

換言之:欄位 key = FreeText 標註內容;欄位位置 = 標註方框。重做 UI 的「欄位偵測 /
確認」步驟時,資料來源就是這裡。

## 已知痛點

- UI 層級不清,首頁太多控制項互相競爭。
- 產品概念被實作細節蓋住。
- 字型選擇、逐欄覆寫、匯出太早全部混在一起。
- 欄位偵測與「我下一步該做什麼」缺少清楚的引導動線。
- 預覽/編輯/匯出應該是主工作區,而不是散落的控制項。

## 重構方向

圍繞單一動線打造:範本 → 欄位 → 數值 → 預覽 → 匯出。

進階手寫微調保留,但收進專屬面板或對話框。預設動線要能讓「非工程師、做重複表單」
的使用者直接走完。詳見 `docs/UI_REDESIGN_BRIEF.md`。

## 重構施工警告

`docs/REFACTOR_BLUEPRINT.md` 是架構藍圖,但落地時請先做 Phase 0:

- 先用目前可跑的 CLI/GUI 建 golden output。
- 先比對 root `tools/` 與 `src/.../tools/` 的功能差異。
- 不要直接假設 `src/.../tools/` 版比較正確;root `tools/fill_pdf_gui.py`
  較大,可能才是目前活功能比較完整的來源。
- 不要在第一階段急著把 package rename 成 `mrse`;先在現有
  `src/Make_report_sign_easy/` 裡建立 `core/`、`pdf/`、`services/`
  分層,保留 entry point 相容性。

一句話:先凍結現況與決定 canonical behavior,再抽 service,最後才刪舊 GUI。
