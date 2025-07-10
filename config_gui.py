import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import ImageTk, Image

if __name__ == "__main__" and __package__ is None:
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    __package__ = "Make_report_sign_easy"

from .builder import generate_text_image
from . import config, builder

CUSTOM_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "custom_config.json")

class ConfigGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🖋️ HandFont 手寫風格參數設定")
        self.geometry("820x400")
        self.resizable(False, False)

        self.params = {
            "PERTURB": {
                "label": "筆畫顫抖",
                "desc": "越高越亂",
                "var": tk.IntVar(value=config.PERTURB),
                "min": 0,
                "max": 20,
            },
            "PERTURB_JITTER": {
                "label": "顫抖隨機",
                "desc": "變化幅度",
                "var": tk.IntVar(value=config.PERTURB_JITTER),
                "min": 0,
                "max": 5,
            },
            "SHEAR_ANGLE": {
                "label": "傾斜角度",
                "desc": "正右負左",
                "var": tk.IntVar(value=config.SHEAR_ANGLE),
                "min": -30,
                "max": 30,
            },
            "COLOR_VARIATION": {
                "label": "墨色波動",
                "desc": "深淺隨機",
                "var": tk.IntVar(value=config.COLOR_VARIATION),
                "min": 0,
                "max": 60,
            },
            "LINE_WIDTH": {
                "label": "線條粗細",
                "desc": "影響筆觸",
                "var": tk.IntVar(value=config.LINE_WIDTH),
                "min": 1,
                "max": 5,
            },
            "CHAR_SPACING": {
                "label": "字距調整",
                "desc": "正多負少",
                "var": tk.IntVar(value=getattr(config, 'CHAR_SPACING', 0)),
                "min": -100,
                "max": 100,
            },
        }

        self.default_values = {k: v["var"].get() for k, v in self.params.items()}
        self._build_ui()
        self.update_preview()

    def _build_ui(self):
        frame = ttk.Frame(self)
        frame.pack(side="left", fill="y", padx=10, pady=10)

        row = 0
        ttk.Label(frame, text="請調整下列參數，預覽即時更新", foreground="blue").grid(row=row, column=0, columnspan=3, sticky="w", pady=(0,10))
        row += 1
        for name, info in self.params.items():
            ttk.Label(frame, text=f"{info['label']}（{info['desc']}）").grid(row=row, column=0, sticky="w", pady=3)
            ttk.Entry(frame, textvariable=info["var"], width=6).grid(row=row, column=1, padx=3)
            ttk.Scale(
                frame,
                from_=info["min"],
                to=info["max"],
                orient="horizontal",
                variable=info["var"],
                command=lambda e: self.update_preview(),
            ).grid(row=row, column=2, padx=5, sticky="we")
            row += 1

        ttk.Label(frame, text="預覽文字：").grid(row=row, column=0, sticky="w", pady=10)
        self.preview_text = tk.StringVar(value="李宗鴻")
        ttk.Entry(frame, textvariable=self.preview_text, width=20).grid(row=row, column=1, columnspan=2, pady=10, sticky="we")
        row += 1

        ttk.Button(frame, text="⟳ 重新產圖", command=self.update_preview).grid(row=row, column=0, pady=5)
        ttk.Button(frame, text="💾 儲存設定", command=self.save_config).grid(row=row, column=1, pady=5)
        ttk.Button(frame, text="↩ 回復預設", command=self.reset_defaults).grid(row=row, column=2, pady=5)

        self.preview_label = ttk.Label(self)
        self.preview_label.pack(side="right", padx=20, pady=20)

    def update_preview(self, *_):
        for name, info in self.params.items():
            val = int(info["var"].get())
            setattr(config, name, val)
            setattr(builder, name, val)
        text = self.preview_text.get().strip() or "李宗鴻"
        img = generate_text_image(text)
        if img:
            img.thumbnail((260, 260))
            self._tk_img = ImageTk.PhotoImage(img)
            self.preview_label.configure(image=self._tk_img)
        else:
            self.preview_label.configure(image="", text="⚠️ 渲染失敗")

    def save_config(self):
        data = {name: int(info["var"].get()) for name, info in self.params.items()}
        with open(CUSTOM_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("儲存成功", f"參數已儲存至\n{CUSTOM_CONFIG_PATH}")

    def reset_defaults(self):
        for name, val in self.default_values.items():
            self.params[name]["var"].set(val)
        self.update_preview()


def main():
    app = ConfigGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
