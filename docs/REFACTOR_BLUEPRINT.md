# 重構藍圖 RFC:Big Bang 等級架構重構

| 項目 | 內容 |
| --- | --- |
| 狀態 | Proposed(提案,待拍板) |
| 日期 | 2026-06-15 |
| 範圍 | 整個 `Make_report_sign_easy`:核心渲染、PDF 流程、設定、所有 GUI/CLI |
| 定位 | 本檔是「目標架構」的權威來源。`docs/AI_HANDOFF.md` 描述**現況**, 本檔描述**要走到哪**, `docs/UI_REDESIGN_BRIEF.md` 提供 UX 細節。 |
| 平台抉擇 | 主目標 **PySide6 桌面**;保留 headless service 邊界,讓未來 **Tauri/Web** 是「加前端」而非再一次重寫。 |

---

## 1. 為什麼是 Big Bang,而不是繼續小修

小修補不掉的是**結構**,不是版面。現有程式碼有四個彼此咬死的問題,任何一個單獨修都會被其他三個拉回去:

1. **核心靠全域可變狀態運作。** `builder.generate_text_image` 直接讀 `config.py` 的模組級全域變數(`PERTURB`、`SHEAR_ANGLE`、`COLOR_BASE`、`FONT_ROUTER`…),而且在渲染途中用 `_apply_random_config` / `_apply_overrides` 以 `setattr(config, ...)` **臨時改寫全域**。後果:不可重入、不可並行、兩個不同設定的工作會互相污染。批次、Web、多執行緒一律免談。
2. **一份工具兩個版本。** root `tools/fill_pdf_gui.py`(1279 行)與 `src/.../tools/fill_pdf_gui.py`(484 行)、`fill_pdf_simple` 也是兩份。改一邊另一邊就漂走。
3. **路徑邏輯被迫變成考古學。** `config.py` 的 `_CANDIDATE_BASE_DIRS` 要同時猜 root 套件、src 套件、PyInstaller `_MEIPASS` 三種位置 —— 這整坨複雜度的**根因就是上面那份重複**。
4. **3~5 個重疊 GUI、一個 god config。** `ctk_gui` / `config_gui` / `config_panel` / `tools/main_gui` / `tools/confirm_gui`(672 行)/ `tools/ctk_config_gui` 各刻各的;`config.py`(479 行)同時管路徑、router、參數中繼資料、驗證、自訂設定。

這四點環環相扣:沒有乾淨核心 → 邏輯無法共用 → 只能每個 GUI 各刻一份 → 重複又長出新的全域依賴。**Big bang 的意義是一次把「核心 → 服務 → 介面」的分層立起來,之後所有功能都長在乾淨地基上。**

---

## 2. 目標與非目標

**目標**

- 核心渲染變成**純函式 + 不可變設定**,可重入、可並行、可單元測試。
- 單一套件、單一事實來源,刪掉所有重複檔與路徑 hack。
- 一條 UI 無關的 **service(use-case)層**,CLI / GUI / 批次 / 未來 Web 全部呼叫同一組。
- 一個現代 **PySide6** 桌面 App,取代全部 Tkinter/CTk。
- 型別化領域模型(Template / Field / ValueSet / Preset / RenderProfile / FillJob)。

**非目標(這次不做,但架構要留路)**

- 不在這次就做 Tauri/Web 前端(只確保 service 邊界乾淨,日後可加)。
- 不重新發明手寫演算法 —— `draw_cjk` / `draw_hollow` / `transform` 的數學照搬,只是換成吃參數而非吃全域。
- 不做雲端/多人(列入 roadmap,不入本次範圍)。

---

## 3. 設計原則

- **核心無 I/O、無框架。** `core/` 不 import PySide6、不 import fitz、不碰檔案系統。輸入資料、輸出資料。
- **設定用傳的,不用全域。** 所有渲染參數收進不可變的 `RenderProfile`,顯式傳入。砍掉 `setattr(config, ...)`。
- **單一事實來源。** 一份套件、一份工具實作、一個 router 來源。
- **介面是薄殼。** GUI/CLI 只做「收集輸入 → 呼叫 service → 顯示結果」,零商業邏輯。
- **可測試優先。** 純核心 + service 都能在沒有視窗、沒有真 PDF 的情況下測。
- **漸進可驗證。** 雖是 big bang 目標,落地用 phase 切,每階段都能跑、能比對舊輸出。

---

## 4. 目標架構

```
┌───────────────────────────────────────────────────────────────┐
│  介面層 Interfaces(薄殼,零商業邏輯)                          │
│  ├─ gui/      PySide6 單一桌面 App(取代全部 Tkinter/CTk)      │
│  ├─ cli/      handfont CLI(typer/argparse)                    │
│  └─ (future)  Tauri / Web 前端 ── 透過同一組 service           │
└────────────────────────────┬──────────────────────────────────┘
                             │ 只呼叫 service,不碰 core 細節
┌────────────────────────────▼──────────────────────────────────┐
│  應用服務層 Services / Use-Cases(headless,UI 無關)           │
│  ├─ RenderTextService      文字 + profile → 手寫影像           │
│  ├─ FillDocumentService    範本 + 數值 + profile → 輸出 PDF    │
│  ├─ TemplateService        偵測欄位、讀寫範本                  │
│  ├─ PresetService          數值 / 句庫 preset                  │
│  └─ RouterCurationService  confirm 校稿 → 更新 font router     │
└────────────────────────────┬──────────────────────────────────┘
              ┌──────────────┼───────────────┐
┌─────────────▼────┐ ┌───────▼─────────┐ ┌───▼────────────────────┐
│ core/ 純領域      │ │ pdf/ PDF 轉接    │ │ assets/ 資源(字型/設定)│
│ (無 I/O,可測)    │ │ (PyMuPDF 封裝)   │ │                        │
│ ├ 渲染引擎        │ │ ├ 欄位偵測        │ │ ├ fonts/               │
│ ├ glyph pipeline  │ │ │  FreeText/Acro  │ │ ├ routes/              │
│ ├ FontRouter      │ │ ├ 影像置入        │ │ └ presets/             │
│ ├ RenderProfile   │ │ └ 匯出            │ │                        │
│ └ domain models   │ └─────────────────┘ └────────────────────────┘
└──────────────────┘
```

**建議套件佈局(目標狀態;先不急著改 package name)**

第一階段先在現有 `src/Make_report_sign_easy/` 內建立 `core/`、`pdf/`、
`services/` 等分層,保留既有 entry points 與 import 相容性。等 golden
output 與 service 層穩定後,再評估是否把套件名簡化成 `mrse`。避免把
「改架構」和「改套件名」綁在同一刀,讓回歸成本失控。

```
src/Make_report_sign_easy/   # long-term may become src/mrse/
├─ core/
│  ├─ models.py          # RenderProfile, Glyph, TextImage, FontRoute…(dataclass/pydantic)
│  ├─ render.py          # render_text(text, profile, router) -> TextImage  純函式
│  ├─ pipeline.py        # extract → perturb/shear/flip → cjk|hollow → compose
│  ├─ glyphs/
│  │   ├─ cjk.py         # 由舊 draw_cjk 改成吃 profile
│  │   └─ hollow.py      # 由舊 draw_hollow 改成吃 profile
│  ├─ transform.py       # perturb/shear/flip(照搬)
│  ├─ fonts.py           # 字形輪廓抽取(舊 extractor)、字型快取
│  └─ router.py          # FontRouter:char→font + fallback
├─ pdf/
│  ├─ template.py        # 讀 PDF、偵測欄位(FreeText 現況 + Acro 預留)
│  ├─ fill.py            # 置入手寫影像、clear-annots、匯出
│  └─ models.py          # Template, Field, FillResult
├─ services/             # 上述五個 use-case
├─ config/
│  ├─ settings.py        # app 層設定(路徑、預設 profile)
│  └─ profiles.py        # RenderProfile 的載入/儲存/驗證(取代 god config)
├─ gui/                  # PySide6 單一 App(MVVM)
├─ cli/                  # 薄 CLI
└─ assets/               # fonts/ routes/ presets/(打包進套件)
```

---

## 5. 核心領域模型

把目前散在全域變數與 JSON 裡的概念,收斂成型別化物件:

| 模型 | 取代現況 | 重點欄位 |
| --- | --- | --- |
| `RenderProfile`(不可變) | `config.py` 全域變數 | image_size、perturb(+jitter)、shear(+jitter)、color_base/variation、alpha_range、line_width、各 script 的 scale/offset(digit/alpha/cjk/special)、enable_solid_fill |
| `FontRouter` | `FONT_ROUTER` dict + 路徑解析 | char→font 對應、fallback 鏈、hollow 字元集(目前寫死在 `builder.HOLLOW_CHARS`,改成資料) |
| `TextImage` | `generate_text_image` 回傳的 PIL Image | 影像 + 尺寸/基線中繼資料 |
| `Template` | FreeText 偵測的臨時結構 | 來源 PDF、頁、`Field[]` |
| `Field` | `annot.info["content"]` + `annot.rect` | key、rect、page、type(FreeText/Acro) |
| `ValueSet` | `values_sample.json` | key→text(key 慣例 `*_words`) |
| `Preset` | `sentence_presets.json` / presets/ | 具名的可重用數值組 |
| `FillJob` / `FillResult` | CLI 參數的零散組合 | template + valueset + profile → 輸出路徑 + 成功/失敗/缺漏報告 |

`generate_text_image(text, ...)` 的新形狀:

```python
# 之前:讀全域 + 途中改全域(不可並行)
img = generate_text_image(text, random=True, overrides={...})

# 之後:純函式,設定用傳的(可並行、可測)
img = render_text(text, profile=profile, router=router)        # core,無副作用
img = render_text(text, profile=profile.jittered(seed=42), router=router)  # 隨機=產生新的不可變 profile
```

---

## 6. 關鍵設計決策(ADR)

**D1 — 不可變 `RenderProfile` 取代全域可變 config(樞紐)**
渲染參數全部收進 `RenderProfile`,核心函式顯式接收。「隨機抖動」不再是 `setattr` 改全域,而是 `profile.jittered(seed)` 回傳一個新 profile。這一刀解鎖:可並行批次、可重現(seed)、可單元測試、Web 安全。**這是整份重構的地基,先做。**

**D2 — 單一事實來源,但先判定 canonical behavior**
目標是只留一份實作,但不能直接假設 `src/.../tools/` 版比較正確。目前 root
`tools/fill_pdf_gui.py` 比 `src/.../tools/fill_pdf_gui.py` 大很多,很可能保留了
較完整的活功能。Phase 0 必須先比對 root 與 src 兩份 GUI/CLI 的功能差異,
用可跑的現況建立 golden output,再決定 canonical behavior。確認前,root
GUI 只能標記為 legacy/candidate,不能直接刪。等 canonical 行為固定後,
再收斂為單一實作,並移除 `_CANDIDATE_BASE_DIRS`、`_resolve_router_path`
等多候選路徑 hack(資源改用 `importlib.resources`)。

**D3 — UI 無關的 service 層**
所有商業流程(偵測欄位、綁數值、渲染、置入、匯出、校稿)只存在於 `services/`。GUI 與 CLI 都只是呼叫者。這是「PySide6 now、Tauri later」能成立的唯一前提。

**D4 — 平台:PySide6 主目標,Tauri 是日後的加法**
你看得懂、不用拆前後端、與現有 Python 核心零阻抗 → **現在用 PySide6**。Tauri 要產品級才划算,代價是多一套前端工具鏈 + Python 橋接。因為 service 層是 headless 的,日後要上 Tauri/Web 時,核心與服務**原封不動**,只是換一個前端呼叫同一組 API。**切換的觸發點**:要對外散布給非技術多人、要跨平台一鍵安裝、或要雲端化時,才啟動 Tauri;在那之前 PySide6 足夠。

**D5 — PDF adapter 抽象**
欄位偵測抽成介面。現況實作 = FreeText(`annot.type[1]=="FreeText"`,content=key,rect=框);預留 AcroForm widget 與「座標範本」(無標註、用座標表)兩種未來偵測器,GUI 不需改。

**D6 — 拆掉 god config**
`config.py` 一分為三:`config/settings.py`(app 路徑與預設)、`core/models.py` 的 `RenderProfile`(渲染參數 + 驗證)、`core/router.py`(字型路由)。參數的範圍/中繼資料(舊 `PARAM_INFO`)變成 profile 欄位的型別與驗證規則。

**D7 — 工程衛生**
`print()` 全換成 `logging`;全核心加型別註記;pytest 從只測 builder 擴到 core + services + pdf;ruff 已在 dev 依賴,納入 CI。

---

## 7. 前瞻未來(重構之後的 Roadmap)

乾淨的 service 邊界一旦立起,這些都從「不可能」變成「加一個 service / 加一個前端」:

- **批次 / mail-merge:** 一份範本 + 一張 CSV/Excel(每列一組數值)→ 一次產出多份 PDF。`RenderProfile` 不可變後可並行,直接吃滿多核。
- **範本作者模式:** 在 App 內畫框、命名欄位、存成範本(不必先在 PDF 裡手動加 FreeText 標註)。
- **Preset / 句庫庫:** 把 `sentence_presets.json` 與 confirm 校稿成果升級成可管理的資源庫。
- **Plugin 化:** renderer(手寫風格)、字型 router、欄位偵測器都做成可插拔,日後加風格不動核心。
- **AcroForm 支援:** 擴大到標準 PDF 表單欄位,不只 FreeText。
- **散布與更新:** PySide6 用 PyInstaller 打包;`auto_update.py` 升級成正式更新通道。
- **(遠期)Tauri/Web → 雲端/多人:** 同一組 service 換 Web 前端即可起步,再談帳號與雲端儲存。

---

## 8. 遷移計畫(Big Bang 目標,分階段落地)

每階段都要能跑、且能與舊版輸出比對(像素級回歸),避免「重寫到一半全壞」。

| Phase | 內容 | 完成定義(DoD) |
| --- | --- | --- |
| **0 凍結與基線** | 鎖目前行為:用現有 CLI 對 `samples/` 產生「黃金輸出」存檔當回歸基準。比對 root `tools/` 與 `src/.../tools/` 的 GUI/CLI 功能差異,先決定 canonical behavior。建 CI(pytest + ruff)。 | 有可重跑的黃金輸出、root/src 差異清單、canonical 決策與綠燈 CI |
| **1 核心淨化(D1)** | 引入 `RenderProfile`,`render_text` 改純函式,移除全域 `setattr`。`draw_cjk/hollow/transform` 改吃 profile。 | 新核心對黃金輸出像素級一致(同 seed) |
| **2 去重 + 收斂套件(D2/D6)** | 依 Phase 0 的 canonical 決策收斂 root/src 重複檔,先統一到現有 `src/Make_report_sign_easy/`,資源改 `importlib.resources`,拆 god config。package rename 成 `mrse` 留到行為穩定後再評估。 | 只剩一份實作;刪除 `_CANDIDATE_BASE_DIRS` 仍可正常找資源 |
| **3 PDF 服務化(D3/D5)** | `pdf/` + `FillDocumentService`,CLI 改成薄殼呼叫 service。 | `handfont-fill-pdf` 行為不變,但邏輯全在 service |
| **4 PySide6 單一 App(D4)** | 依 `UI_REDESIGN_BRIEF` 動線(範本→欄位→數值→預覽→匯出)建新 GUI,呼叫 service。 | 走完主流程不需碰任何進階設定 |
| **5 校稿流程移植** | confirm 校稿 / router 更新(舊 `confirm_gui` + `import_confirmed_previews` + `safe_char_map`)收進 `RouterCurationService` + 新面板。 | 可在新 App 內完成字型校稿並寫回 router |
| **6 清場** | 刪掉全部舊 Tkinter/CTk GUI 與死碼,文件更新,釋出 packaging。 | repo 只剩新架構;`AI_HANDOFF` 改寫成新版地圖 |

---

## 9. 風險與取捨

- **像素回歸風險:** 改吃 profile 可能讓輸出些微位移。對策 = Phase 0 的黃金輸出 + 同 seed 比對,差異才放行。
- **PySide6 學習與授權:** PySide6 為 LGPL,商用相對友善(Qt 本體);打包體積較 Tkinter 大,可接受。
- **一次大改的時間成本:** 用 phase 切、每階段可跑可比對來控管;任何一階段卡住都能停在綠燈狀態。
- **Tauri 的未來成本:** 現在不付;但 service 邊界要守乾淨,否則日後上 Tauri 會退化成第二次 big bang。守則:**core/service 不得 import 任何 UI 套件。**

## 10. 成功指標

- 核心可在無視窗、無真 PDF 下被單元測試;測試覆蓋從「只有 builder」擴到 core + services + pdf。
- 同一份「填 PDF」邏輯被 CLI 與 GUI 共用,零複製。
- repo 內 PDF 工具與 GUI 各只有一份實作。
- 批次填多份 PDF 可並行且結果可重現(seed)。
- 非工程使用者能只靠「範本→欄位→數值→預覽→匯出」走完,不必碰任何字型內部設定。

## 11. 第一週可立刻做 / 立刻砍

**立刻做**
- 建黃金輸出 + CI(Phase 0)。
- 產出 root `tools/` vs `src/.../tools/` 的功能差異清單,確認哪一份才是目前活功能來源。
- 起 `core/models.py` 的 `RenderProfile`,把 `builder` 改成可接收 profile(暫時與全域並存,先讓測試掛上)。

**先標記,不要急著砍**
- root `tools/fill_pdf_gui.py`(1279 行)與 root 重複的 `fill_pdf_simple.py` 先標記 legacy/candidate canonical。等 Phase 0 比對與 golden output 完成後,再收斂。
- 多餘的 GUI 入口擇一保留,其餘標記 deprecated,Phase 6 移除。

---

*本檔取代 `UI_REDESIGN_BRIEF.md` 作為「架構權威」;UI brief 續為 UX 動線與畫面細節的依據。落地後請同步改寫 `AI_HANDOFF.md` 指向新架構。*
