此資料夾放置可供選擇的 `.ttf` 字型檔。
`config_gui` 會自動列出這裡的檔案供使用者挑選。

為了避免安裝套件過大，建議將字型放在「外部字型目錄」，程式會自動搜尋：

1) 環境變數 MRSE_FONTS_DIR 指向的資料夾
2) 使用者目錄（依平台）
	- Windows: %APPDATA%/MakeReportSignEasy/fonts
	- macOS:   ~/Library/Application Support/MakeReportSignEasy/fonts
	- Linux:   ~/.local/share/MakeReportSignEasy/fonts
3) 套件/專案內的 fonts/（本資料夾）
4) Windows 系統字型資料夾（唯讀備援）

Router（configs/font_routes_template.json）內若使用相對路徑（例如 "fonts/xxx.ttf"），
會優先於上述 1)~2) 的外部/使用者字型目錄查找，找不到才回退到本資料夾與 router 檔案所在目錄。

建議做法：
- 在本機建立外部字型資料夾，將大量字型放於外部；專案內只留必要最小集合或不放字型。
- 如有客製 router，請確保路徑能在上述搜尋規則中找到對應字型。