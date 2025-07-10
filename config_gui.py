import os
import json
import tkinter as tk
from tkinter import ttk
from PIL import ImageTk, Image

if __name__ == "__main__" and __package__ is None:
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    __package__ = "Make_report_sign_easy"

from . import builder, config

CUSTOM_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "custom_config.json")

class ConfigGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HandFont 參數設定")
        self.params = {
            "PERTURB": {"var": tk.IntVar(value=config.PERTURB), "min": 0, "max": 20},
            "PERTURB_JITTER": {"var": tk.IntVar(value=config.PERTURB_JITTER), "min": 0, "max": 5},
            "SHEAR_ANGLE": {"var": tk.IntVar(value=config.SHEAR_ANGLE), "min": -30, "max": 30},
            "COLOR_VARIATION": {"var": tk.IntVar(value=config.COLOR_VARIATION), "min": 0, "max": 60},
            "LINE_WIDTH": {"var": tk.IntVar(value=config.LINE_WIDTH), "min": 1, "max": 5},
        }
        self._build_ui()
        self.update_preview()

    def _build_ui(self):
        row = 0
        for name, info in self.params.items():
            ttk.Label(self, text=name).grid(row=row, column=0, sticky="w", padx=5, pady=2)
            entry = ttk.Entry(self, textvariable=info["var"], width=6)
            entry.grid(row=row, column=1, padx=5)
            scale = ttk.Scale(
                self,
                from_=info["min"],
                to=info["max"],
                orient=tk.HORIZONTAL,
                variable=info["var"],
                command=lambda e: self.update_preview(),
            )
            scale.grid(row=row, column=2, sticky="we", padx=5)
            row += 1

        self.columnconfigure(2, weight=1)
        self.preview_label = ttk.Label(self)
        self.preview_label.grid(row=0, column=3, rowspan=row, padx=10, pady=10)

        ttk.Button(self, text="儲存設定", command=self.save_config).grid(
            row=row, column=0, columnspan=3, pady=10
        )

    def update_preview(self):
        for name, info in self.params.items():
            value = int(info["var"].get())
            setattr(config, name, value)
            setattr(builder, name, value)
        img = builder.generate_text_image("李宗鴻")
        if img:
            img.thumbnail((200, 200))
            self._tk_img = ImageTk.PhotoImage(img)
            self.preview_label.configure(image=self._tk_img)

    def save_config(self):
        data = {name: int(info["var"].get()) for name, info in self.params.items()}
        with open(CUSTOM_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 已儲存 {CUSTOM_CONFIG_PATH}")


def main():
    app = ConfigGUI()
    app.mainloop()


if __name__ == "__main__":
    main()

