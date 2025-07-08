# ✍️ HandFont Playground

一個模擬手寫風格中文字與符號的渲染引擎，支援：
- 🖋️ 擬真人手寫抖動、筆壓濃淡、墨點隨機化
- 🔠 自由指定字元專屬字型（自定路由）
- 📐 中文／英數／符號混排完整支援
- 🧪 可擴充參數調整與社群共同參與字型挑選

> 本專案為開源字型風格實驗場，鼓勵大家參與字型測試、貢獻配置組合，讓每個字都找到最適合的「個性筆」！

---

## 📦 安裝方式

```bash
git clone https://github.com/AustinHongLee/handfont-playground.git
cd handfont-playground
pip install -r requirements.txt
🧪 如何產出圖片

from handfont.builder import generate_text_image

img = generate_text_image("李鴻宗")
img.save("example.png")

🔣 自訂字型路由（字 → 專屬字體）
所有特別對應關係都寫在 font_routes.json：

{
  "李": "fonts/JasonHandwriting2.ttf",
  "鴻": "fonts/JasonHandwriting3p.ttf",
  "4":  "fonts/851tegaki_zatsu_normal.ttf"
}

🤝 歡迎貢獻（加入你認為最合適的字型）
1.Fork 本專案

2.編輯或新增 font_routes.json

3.若你有自製字型，也可以附上說明（請勿侵犯他人版權）

4.發出 PR，我們會一起審核與測試

🧰 工具腳本
位於 tools/ 資料夾：
preview_fonts.py
輸入一個字元，預覽所有 .ttf 渲染結果
python tools/preview_fonts.py 李
會自動列出所有可能字型版本，協助你挑選最佳筆感！

🖼️ 預覽成果（範例）
字元	字型	圖示
李	JasonHandwriting2	
鴻	JasonHandwriting3p	
4	手寫數字風格

📂 專案結構概覽
handfont/        ← 核心模組邏輯
tools/           ← 工具腳本與實驗測試
fonts/           ← 所使用字型（請勿放未授權字型）
font_routes.json ← 字 → 字型路由表

📬 聯絡 & 說明
歡迎你一起加入討論，也可以開 issue 討論某個字型的適配度、提出風格問題、甚至幫忙優化渲染邏輯。
Made with ❤️ by [AustinHongLee]
