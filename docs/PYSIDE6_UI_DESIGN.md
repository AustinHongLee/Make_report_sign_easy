# PySide6 產品級 UI/UX 與模組落地方案

| 項目 | 內容 |
| --- | --- |
| 狀態 | Proposed(提案) |
| 日期 | 2026-06-15 |
| 依據 | `docs/AI_HANDOFF.md`(現況)、`docs/REFACTOR_BLUEPRINT.md`(架構權威)、`docs/UI_REDESIGN_BRIEF.md`(UX 動線) |
| 前提 | **不重寫渲染核心**;所有功能一律經既有 service 呼叫:`TemplateService`、`ValueSetService`、`ProfileService`、`RenderTextService`、`FillDocumentService`、`BatchFillService`。 |
| 新增依賴 | `PySide6`(Qt for Python, LGPL);`customtkinter` 在舊 GUI 全部退場前暫留。 |
| 進入點 | 新增 `handfont-gui = "Make_report_sign_easy.gui.app:main"`。 |

---

## 1. 設計語言:一個冷靜的「表單生產工具」

北極星(沿用 UI brief):**這不是字型實驗室,是讓人把同一份 PDF 重複填好的工具。** 預設使用者只需要懂四件事:範本、數值、預覽、匯出。

產品級的判準,落在五個可驗收的點:

1. **單一主動線**:範本 → 欄位 → 數值 → 預覽 → 匯出,永遠看得到「下一步」。
2. **所見即所得**:中央是 PDF 預覽,不是參數表。
3. **進階收納**:手寫微調(`RenderProfile`)藏在抽屜/對話框,不佔第一螢幕。
4. **可信任**:缺值、多餘 key、匯出成功/失敗、檔案落點,都有明確狀態,不靠猜。
5. **反應靈敏**:任何 PDF/渲染重活都在背景執行緒,UI 永不凍結。

視覺基調冷靜、留白、低彩度;**唯一強調色用「墨水藍」**(`COLOR_BASE = (65,105,225)` royal blue,正好是手寫輸出的顏色,品牌與產品一致)。

---

## 2. 既有 service 介面盤點(UI 接線的事實來源)

設計的每個動作都對應到下面真實簽名,GUI 不得自行碰渲染核心。

| 資料模型 | 重點欄位 |
| --- | --- |
| `Template` | `path`、`fields: tuple[Field]`、`field_keys` |
| `Field` | `key`、`page_index`、`rect=(x0,y0,x1,y1)`(PDF 點座標)、`field_type` |
| `ValueSet` | `values: Mapping[str, object]`、`keys` |
| `TemplateInspection` | `value_keys`、`matched_keys`、`missing_value_keys`、`extra_value_keys`、`is_complete` |
| `RenderProfile`(frozen) | 26 個渲染欄位;`jittered(seed,…)`、`from_config()`、`to_config_overrides()` |
| `FillResult` | `output_path`、`filled_fields`、`missing_fields` |
| `BatchFillResult` | `results: tuple[FillResult]`、`output_paths` |

| 服務 | 主要呼叫 | 回傳 |
| --- | --- | --- |
| `TemplateService` | `load_template(path, page_index=0)` / `inspect(path, values=…, page_index=0)` | `Template` / `TemplateInspection` |
| `ValueSetService` | `load_json(path)` | `ValueSet` |
| `ProfileService` | `default_profile()` / `load_json(path)` / `from_dict(d)` / `to_dict(p)` / `save_json(p,path)` | `RenderProfile` / dict |
| `RenderTextService` | `run(RenderTextRequest(text, profile, random, …))` | `PIL.Image \| None` |
| `FillDocumentService` | `run(FillDocumentRequest(template_path, output_path, values=…, profile, random, seed, clear_annots))` | `FillResult` |
| `BatchFillService` | `run(BatchFillRequest(template_path, items=[BatchFillItem(values, output_path, seed)], profile, seed_start))` | `BatchFillResult` |

三個對 UI 影響重大的事實:

- **`FillDocumentRequest.values` 可直接吃記憶體 Mapping** → GUI 的可編輯欄位表格不必先存成 JSON,改一格就能即時預覽。
- **`RenderTextService.run` 回傳 PIL Image** → 需要 PIL→`QPixmap` 介面卡;這是預覽顯示的唯一橋。
- **`fill_pdf` 目前單頁(`page_index=0`)** → MVP UI 以單頁為準,多頁列為後續(見 §11 風險)。

---

## 3. 資訊架構與主畫面佈局

沿用 UI brief 的四區,固定不變,降低認知負擔:

```
┌───────────────────────────────────────────────────────────────────────┐
│ 頂列:範本名稱 · 頁碼 · [模式: 單份 ▸ 批次]            [說明] [設定 ⚙]  │
├──────────────┬──────────────────────────────────────┬─────────────────┤
│ 左欄(280)   │           中央畫布(彈性)            │ 右欄(320)      │
│ 步驟與狀態   │           PDF 預覽 + 欄位疊圖         │ 選取欄位設定    │
│              │                                      │                 │
│ ① 範本 ✓     │   ┌────────────────────────────┐     │ Key: Sign_words │
│ ② 欄位 12    │   │  [   渲染後的 PDF 頁面    ] │     │ 值: [李宗鴻   ] │
│ ③ 數值 9/12  │   │  [ 欄位框 · 選取高亮      ] │     │ 字型: 自動 ▾    │
│ ④ 預覽       │   │  [                        ] │     │ □ 此欄覆寫 profile│
│ ⑤ 匯出       │   └────────────────────────────┘     │ [預覽此欄]      │
│              │                                      │                 │
│ 缺值: 3 ⚠    │   [‹ 上一步]        [整頁預覽 ↻]     │ 進階微調 → 抽屜  │
├──────────────┴──────────────────────────────────────┴─────────────────┤
│ 底列:驗證摘要(✓ 9 已填 · ⚠ 3 缺值 · ◦ 0 多餘)   [隨機 ⟲][匯出 PDF ▸]│
└───────────────────────────────────────────────────────────────────────┘
```

- **中央畫布是主角**:渲染後的 PDF 頁面 + 半透明欄位框;點框=選欄,選欄同步右欄與左欄清單(雙向高亮)。
- **左欄是動線狀態機**:五步驟附即時狀態徽章(✓/數量/⚠),點任一步跳到對應狀態。
- **右欄是「選取欄位」的上下文**:只顯示當前欄位的值、字型、是否覆寫;不選任何欄位時收合。
- **底列是動作與信任區**:驗證摘要常駐;主行動鈕(匯出)恆在右下,符合肌肉記憶。

---

## 4. 主工作流程與畫面狀態

五個狀態,對應 UI brief 的 Suggested UI States,每個都標明「觸發的 service」:

| 狀態 | 畫面 | 觸發 service |
| --- | --- | --- |
| **Empty** | 中央放「選擇 PDF 範本」大區塊 + 最近檔/範例(`samples/`);其餘區收合 | — |
| **Template loaded** | 偵測出欄位、畫出欄位框、左欄顯示欄位數 | `TemplateService.load_template` |
| **Values loaded** | 欄位表填入值;缺值/多餘以徽章標示;「整頁預覽」啟用 | `ValueSetService.load_json` + `TemplateService.inspect` |
| **Preview ready** | 中央顯示渲染後整頁;可點欄位逐格微調 | `FillDocumentService.run`(輸出到暫存檔再 raster) |
| **Exported** | 成功狀態:輸出路徑、`filled/missing` 摘要、[開啟檔案][再匯出][開資料夾] | `FillDocumentService.run`(輸出到使用者選定路徑) |

動線細節:

- **Empty → Loaded**:拖放或選 PDF;載入後自動 `inspect`(若已有數值),立即看到缺值數。
- **數值來源雙軌**:可載入 values JSON,也可直接在欄位表內編輯(in-memory Mapping)。兩者都即時重新 `inspect`。
- **預覽策略(見 §10)**:預覽 = 用真正的 `FillDocumentService` 填到暫存 PDF 再 raster,**保證所見即所得**;逐欄微調時用輕量 overlay 即時回饋,放手後再做一次 true render。
- **匯出**:選輸出路徑 → `FillDocumentService.run` → 用 `FillResult.missing_fields` 給明確警告(「3 個值在範本找不到對應欄位」)。

---

## 5. 關鍵互動設計

- **欄位↔數值雙向同步**:中央點欄位框、左欄點欄位名、右欄編輯值,三者選取狀態一致;選取的欄位框用墨水藍描邊 + 微放大。
- **缺值/多餘的明確語言**:用 `TemplateInspection` 三組 key 直接驅動 ——
  `missing_value_keys`→「範本有欄位但沒給值」(黃);`extra_value_keys`→「給了值但範本沒這欄」(灰);`matched_keys`→已就緒(綠)。
- **即時預覽**:右欄「預覽此欄」呼叫 `RenderTextService.run`,把單欄手寫影像疊到該 `Field.rect`,不必整頁重算。
- **隨機/可重現**:底列「隨機 ⟲」對應 `random=True`;進階可填 `seed`,讓輸出可重現(`FillDocumentRequest.seed`)。
- **非破壞性**:`clear_annots` 預設關;以選項呈現「匯出時移除原始標註」,避免誤刪。
- **空狀態與錯誤**:每個區塊都有空狀態文案與可復原的錯誤提示(service 丟出的 `FileNotFoundError`/`ValueError` 轉成人話)。

---

## 6. 進階手寫微調(收進抽屜,不上第一螢幕)

`RenderProfile` 的 26 個參數**不可**散在主畫面。設計成右側滑出的「手寫微調」抽屜:

- 分組呈現:**力度**(perturb/jitter)、**傾斜**(shear)、**墨色**(color/alpha/blur)、**字距/縮放**(各 script 的 scale/offset)。
- 即時小預覽:抽屜頂端固定一個樣本字串,改參數即時用 `RenderTextService` 重渲染。
- **Profile 即 preset**:`ProfileService.save_json / load_json` → 命名儲存常用手寫風格;主畫面只露一個「風格 ▾」下拉切換。
- **逐欄覆寫**:右欄的「□ 此欄覆寫 profile」讓單一欄位用不同風格(例如簽名比較草),其餘沿用全域 profile。
- 「重設為預設」= `ProfileService.default_profile()`。

設計原則:抽屜開著也能看到中央預覽;關掉抽屜,主動線完全不受影響。

---

## 7. 批次模式(mail-merge,對應 BatchFillService)

頂列模式切到「批次」,中央改為批次工作台 —— 這是「例行重複表單」的殺手級場景:

- **輸入**:一份範本 + 多組數值(多個 values JSON,或一張 CSV/Excel 每列一組)。MVP 先支援多個 JSON;CSV→多組 `values` 的轉換在 GUI 端做,送進 `BatchFillItem(values=…)`。
- **清單視圖**:每列一個 `BatchFillItem`(標籤、輸出檔名、seed、狀態)。
- **執行**:`BatchFillService.run(BatchFillRequest(...))` 在背景執行緒跑;逐筆回報進度與 `FillResult`。
- **結果**:成功/失敗逐筆顯示,可一鍵開資料夾;失敗筆顯示 `missing_fields`。
- **可重現**:`seed_start` 讓整批可重現;不可變 `RenderProfile` 確保可安全並行(未來可加 thread pool,服務介面不必改)。

---

## 8. 視覺設計規範(Design Tokens)

| 類別 | 規範 |
| --- | --- |
| 佈局 | 8px 間距網格;左 280 / 右 320 固定,中央彈性;最小視窗 1100×720 |
| 強調色 | 墨水藍 `#4169E1`(= 渲染 ink);hover/active 加深一階 |
| 中性色(亮) | 背景 `#F7F8FA`、面板 `#FFFFFF`、邊框 `#E4E7EC`、主文字 `#1D2433`、次文字 `#667085` |
| 狀態色 | 就緒綠 `#12B76A`、缺值黃 `#F79009`、錯誤紅 `#F04438`、多餘灰 `#98A2B3` |
| 暗色 | 提供暗色主題(背景 `#15171C`、面板 `#1E2128`);用 Qt palette + qss 切換 |
| 字體 | UI 用系統無襯線(Windows: Segoe UI / 微軟正黑);資料/路徑用等寬 |
| 圓角/陰影 | 卡片圓角 8px;極淡陰影,避免「重」;不用漸層 |
| 圖示 | 線性單色圖示(可用 qtawesome 或內嵌 SVG),與墨水藍一致 |
| 密度 | 舒適預設;欄位表提供「緊湊」切換給大量欄位 |

主題以 **qss(Qt Style Sheets)+ QPalette** 實作,集中在 `gui/theme/`,亮/暗一鍵切換。

---

## 9. 模組落地:`gui/` 套件結構(MVVM)

關鍵原則:**View 不碰 service,ViewModel 才碰 service;ViewModel 不碰 Qt widget,只發訊號。** 這讓 ViewModel 可在無視窗下測試,也讓未來換 Tauri 時,等價的「前端狀態」邏輯有跡可循。

```
src/Make_report_sign_easy/gui/
├─ app.py                 # main():建立 QApplication、主視窗、注入 services
├─ main_window.py         # 組裝四區佈局、模式切換、選單
├─ session.py             # AppSession:當前 Template / 可編輯 values / RenderProfile / 輸出設定
├─ viewmodels/
│  ├─ template_vm.py      # 載入範本、inspect、欄位選取狀態
│  ├─ values_vm.py        # 可編輯欄位表、缺值/多餘衍生狀態
│  ├─ preview_vm.py       # 觸發整頁/單欄預覽、保存 QPixmap
│  ├─ profile_vm.py       # 載入/存檔/編輯 RenderProfile、jitter
│  └─ batch_vm.py         # 批次清單、執行、進度
├─ views/
│  ├─ workflow_panel.py   # 左欄五步驟狀態
│  ├─ pdf_canvas.py       # 中央:QGraphicsView 顯示頁面 + 欄位框 overlay
│  ├─ field_inspector.py  # 右欄:選取欄位設定
│  ├─ profile_drawer.py   # 進階手寫微調抽屜
│  ├─ batch_workbench.py  # 批次工作台
│  └─ statusbar.py        # 底列驗證摘要 + 動作
├─ workers/
│  ├─ task_runner.py      # QThreadPool + QRunnable 包裝,signal: started/progress/done/error
│  └─ jobs.py             # FillJob / BatchJob / RenderJob(只呼叫 service)
├─ adapters/
│  ├─ pil_qt.py           # PIL.Image ↔ QImage/QPixmap
│  └─ pdf_raster.py       # PyMuPDF 頁面 raster + PDF↔像素座標映射
└─ theme/
   ├─ light.qss / dark.qss
   └─ tokens.py
```

`app.py` 在啟動時把六個 service 實例化一次,透過建構子注入各 ViewModel(方便測試替換)。

---

## 10. View ↔ Service 接線表(落地對照)

| UI 動作 | ViewModel | 呼叫的 service | 結果處理 |
| --- | --- | --- | --- |
| 選/拖入 PDF | `template_vm` | `TemplateService.load_template` | 存入 `AppSession.template`,畫欄位框 |
| 載入 values JSON | `values_vm` | `ValueSetService.load_json` | 填欄位表(可再編輯) |
| 編輯任一格值 | `values_vm` | `TemplateService.inspect(values=…)` | 更新缺值/多餘徽章 |
| 預覽單欄 | `preview_vm` | `RenderTextService.run(RenderTextRequest)` | PIL→QPixmap,疊到 `Field.rect` |
| 整頁預覽 | `preview_vm` (worker) | `FillDocumentService.run`(暫存輸出) | raster 暫存 PDF → 中央顯示 |
| 匯出 | `preview_vm` (worker) | `FillDocumentService.run`(正式路徑) | 用 `FillResult` 顯示成功/缺漏 |
| 批次執行 | `batch_vm` (worker) | `BatchFillService.run(BatchFillRequest)` | 逐筆進度 + `output_paths` |
| 開/存手寫風格 | `profile_vm` | `ProfileService.load_json/save_json/from_dict` | 更新 `AppSession.profile` |
| 隨機/重現 | `preview_vm`/`profile_vm` | `RenderProfile.jittered(seed)` 或 `request.random/seed` | 影響後續渲染 |

**預覽的所見即所得策略**:整頁預覽與最終匯出都走 `FillDocumentService` 同一條路徑(差別只在輸出到暫存或正式檔),保證預覽 = 成品。逐欄微調時才用 `RenderTextService` 的輕量 overlay 做即時回饋,放手後補一次 true render 收斂。

---

## 11. 執行緒模型(UI 永不凍結)

- PDF 填寫、批次、整頁 raster 都是重活 → 一律進 `QThreadPool`,用 `QRunnable` 包 service 呼叫,以 signal 回報 `started/progress/done/error`。
- **不可變 `RenderProfile` 是並行安全的前提**(REFACTOR_BLUEPRINT D1 的紅利):worker 拿到的是 profile 快照,主執行緒繼續改不會污染進行中的工作。
- UI 只在主執行緒更新;worker 不得碰 widget,只能發資料訊號。
- 規則:**`gui/` 之外不得 import 任何 Qt;`viewmodels/` 不得 import widget**。守住這條,Tauri/Web 之日才不會退化成第二次 big bang。

---

## 12. 介面卡:PIL→Qt 與 PDF 座標映射

兩個一定要做對的膠水點:

```python
# adapters/pil_qt.py —— 渲染影像上畫面的唯一橋
def pil_to_qpixmap(img: "PIL.Image.Image") -> QPixmap:
    img = img.convert("RGBA")
    data = img.tobytes("raw", "RGBA")
    qimg = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
    return QPixmap.fromImage(qimg.copy())   # copy() 避免 buffer 被回收

# adapters/pdf_raster.py —— 頁面點陣 + 欄位框座標映射
def render_page(path, page_index=0, zoom=2.0) -> tuple[QImage, float]:
    doc = fitz.open(path); page = doc[page_index]
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888).copy()
    doc.close(); return qimg, zoom

def field_rect_to_pixels(rect, zoom):           # Field.rect=(x0,y0,x1,y1) PDF 點
    x0, y0, x1, y1 = rect                        # PyMuPDF 與影像同為左上原點
    return QRectF(x0*zoom, y0*zoom, (x1-x0)*zoom, (y1-y0)*zoom)
```

中央用 `QGraphicsView`/`QGraphicsScene`:底圖一個 pixmap item,欄位框是可點選的 rect item(攜帶 `Field.key`),選取即發訊號同步左右欄。

---

## 13. 進入點、打包、依賴

- `pyproject.toml` 新增 `handfont-gui = "Make_report_sign_easy.gui.app:main"`。
- `requirements.txt` 加 `PySide6`;`customtkinter` 待舊 GUI 全退場後移除。
- 打包用 PyInstaller(承接現有 `_MEIPASS` 處理);字型/qss/圖示以套件資源 (`importlib.resources`) 帶入。
- 舊 GUI(`ctk_gui`、`config_gui`、`tools/*_gui`、`tools/confirm_gui` 等)先標 deprecated,於落地最後一階段移除(對應 BLUEPRINT Phase 6)。

---

## 14. 測試策略

- **ViewModel 純邏輯測試**(無視窗):注入假 service,驗證狀態轉換(載入範本→欄位數、改值→缺值數、批次→結果彙整)。這是覆蓋率主力。
- **adapters 單元測試**:PIL→QPixmap 尺寸/格式、PDF 座標映射數值正確。
- **pytest-qt 元件測試**:關鍵 widget 的選取同步、抽屜開關。
- **回歸**:沿用 BLUEPRINT Phase 0 的 golden output;GUI 匯出路徑與 CLI 走同一 `FillDocumentService`,確保不分岔。

---

## 15. 落地階段(每階段都可跑、且只呼叫既有 service)

| 階段 | 範圍 | 完成定義(DoD) |
| --- | --- | --- |
| **G0 殼** | `app.py`+`main_window` 四區空殼、主題、執行緒骨架、PIL→Qt/raster adapters | 能開窗、能顯示一張 PDF 頁面 raster |
| **G1 主動線** | 範本→欄位→數值(可編輯表)→匯出,接 `Template/ValueSet/FillDocument` service | 能載範本、填值、匯出一份正確 PDF;缺值有提示 |
| **G2 預覽** | 中央整頁預覽 + 欄位框疊圖 + 雙向選取 + 單欄即時預覽 | 預覽 = 匯出成品;點欄位三區同步 |
| **G3 手寫微調** | `profile_drawer` + `ProfileService` 存取 + 逐欄覆寫 + 隨機/seed | 可命名儲存風格、單欄覆寫、可重現 |
| **G4 批次** | `batch_workbench` + `BatchFillService` + 進度/結果 | 一份範本多組值一次產出、逐筆狀態 |
| **G5 收尾** | 暗色完善、空狀態/錯誤文案、PyInstaller 打包、移除舊 GUI | 取代所有舊 GUI;`handfont-gui` 可散布 |

---

## 16. 風險與取捨

- **單頁限制**:`fill_pdf` 目前單頁。MVP UI 標示頁碼但只處理第 0 頁;多頁需在 pdf 層擴充(GUI 介面預留頁碼切換,service 介面不變即可接)。
- **預覽延遲**:整頁 true render 走 PDF 來回有成本 → 用「逐欄輕量 overlay 即時、放手後 true render」兩段式吸收;raster 加快取(同 zoom/同檔不重算)。
- **PySide6 體積/授權**:LGPL,商用友善;打包體積比 Tkinter 大,可接受。
- **座標/Y 軸**:PyMuPDF `get_pixmap` 與影像同為左上原點,欄位框直接 `×zoom`;若日後改用 PDF 使用者空間需注意翻轉。
- **守紀律**:ViewModel/worker 一旦偷接渲染核心或在 worker 動 widget,會破壞並行安全與未來換前端的路。Code review 守 §11 兩條規則。

---

## 17. 一句話總結

中央放 PDF、四區固定、進階收抽屜、重活進背景;**每個按鈕背後都是一個既有 service 呼叫**,GUI 只負責把「範本→數值→預覽→匯出」這條線走得冷靜、可信、可重現。渲染核心一行都不用改。

*本檔為 `UI_REDESIGN_BRIEF.md` 的工程落地版;UX 動線以 brief 為準,服務接線以本檔為準。*
