import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

# src layout 優先
repo_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
src_root = os.path.join(repo_root, "src")
if os.path.isdir(src_root):
    sys.path.insert(0, src_root)
sys.path.insert(0, repo_root)


class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Make Report Sign Easy - 主介面")
        self.geometry("1100x750")

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        # Tab: PDF 填值（提供啟動按鈕）
        pdf_tab = ttk.Frame(nb)
        nb.add(pdf_tab, text="PDF 填值")
        ttk.Label(
            pdf_tab,
            text=(
                "PDF 填值工具將以獨立視窗開啟，避免與其他功能互相干擾。\n"
                "按下按鈕啟動。"
            ),
        ).pack(padx=16, pady=16)
        ttk.Button(
            pdf_tab,
            text="開啟 PDF 填值工具",
            command=self.open_pdf_tool,
        ).pack(pady=8)

        # Tab: 字型挑選 / confirm 管理
        confirm_tab = ttk.Frame(nb)
        nb.add(confirm_tab, text="字型挑選 / confirm")
        # 延遲匯入，且以同資料夾同名模組匯入避免 'python tools/main_gui.py' 的套件路徑問題
        import importlib
        confirm_gui = importlib.import_module("confirm_gui")
        ConfirmManager = getattr(confirm_gui, "ConfirmManager")
        cm = ConfirmManager(confirm_tab)
        cm.pack(fill="both", expand=True)

    def open_pdf_tool(self):
        # 以 Toplevel 啟動現有 GUI，維持獨立視窗
        win = tk.Toplevel(self)
        win.title("PDF 填值工具")
        # 直接啟動原腳本中的主視窗（它是 Tk），改為在新 process 更安全，這邊用簡易方式：
        import subprocess
        import sys
        exe = sys.executable
        script = os.path.join(os.path.dirname(__file__), 'fill_pdf_gui.py')
        try:
            subprocess.Popen([exe, script])
        except Exception:
            # 回退：用訊息提醒
            messagebox.showinfo("提示", "已嘗試啟動 fill_pdf_gui.py")


def main():
    app = MainApp()
    app.mainloop()


if __name__ == "__main__":
    main()
