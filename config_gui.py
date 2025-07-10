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
        self.fonts_dir = os.path.join(os.path.dirname(__file__), "fonts")
        self.fonts_list = [f for f in os.listdir(self.fonts_dir) if f.lower().endswith('.ttf')]
        default_font = os.path.basename(config.FONT_PATH)
        if default_font not in self.fonts_list and self.fonts_list:
            default_font = self.fonts_list[0]
        self.font_var = tk.StringVar(value=default_font)
        self.params = {
            "PERTURB": {"var": tk.IntVar(value=config.PERTURB), "min": 0, "max": 20, "type": int},
            "PERTURB_JITTER": {"var": tk.IntVar(value=config.PERTURB_JITTER), "min": 0, "max": 5, "type": int},
            "SHEAR_ANGLE": {"var": tk.IntVar(value=config.SHEAR_ANGLE), "min": -30, "max": 30, "type": int},
            "COLOR_VARIATION": {"var": tk.IntVar(value=config.COLOR_VARIATION), "min": 0, "max": 60, "type": int},
            "LINE_WIDTH": {"var": tk.IntVar(value=config.LINE_WIDTH), "min": 1, "max": 5, "type": int},
            "CHAR_SPACING_OFFSET": {"var": tk.IntVar(value=config.CHAR_SPACING_OFFSET), "min": -100, "max": 100, "type": int},
            "DIGIT_SCALE": {"var": tk.DoubleVar(value=config.DIGIT_SCALE), "min": 0.5, "max": 1.5, "type": float},
            "DIGIT_OFFSET_Y": {"var": tk.DoubleVar(value=config.DIGIT_OFFSET_Y), "min": -0.5, "max": 0.5, "type": float},
            "ALPHA_SCALE": {"var": tk.DoubleVar(value=config.ALPHA_SCALE), "min": 0.5, "max": 1.5, "type": float},
            "ALPHA_OFFSET_Y": {"var": tk.DoubleVar(value=config.ALPHA_OFFSET_Y), "min": -0.5, "max": 0.5, "type": float},
            "CJK_SCALE": {"var": tk.DoubleVar(value=config.CJK_SCALE), "min": 0.5, "max": 1.5, "type": float},
            "CJK_OFFSET_Y": {"var": tk.DoubleVar(value=config.CJK_OFFSET_Y), "min": -0.5, "max": 0.5, "type": float},
            "SPECIAL_SCALE": {"var": tk.DoubleVar(value=config.SPECIAL_SCALE), "min": 0.5, "max": 1.5, "type": float},
            "SPECIAL_OFFSET_Y": {"var": tk.DoubleVar(value=config.SPECIAL_OFFSET_Y), "min": -0.5, "max": 0.5, "type": float},
        }
        self._build_ui()
        self.update_preview()

    def _build_ui(self):
        row = 0
        ttk.Label(self, text="字體 Font").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        font_cb = ttk.Combobox(self, textvariable=self.font_var, values=self.fonts_list, state="readonly")
        font_cb.grid(row=row, column=1, columnspan=2, sticky="we", padx=5)
        font_cb.bind("<<ComboboxSelected>>", lambda e: self.update_preview())
        row += 1
        for name, info in self.params.items():
            desc = config.PARAM_INFO.get(name, (name,))[0]
            ttk.Label(self, text=f"{desc} ({name})").grid(row=row, column=0, sticky="w", padx=5, pady=2)
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
            var_value = info["var"].get()
            cast = info.get("type", float)
            value = cast(var_value)
            setattr(config, name, value)
            setattr(builder, name, value)
        font_path = os.path.join(self.fonts_dir, self.font_var.get())
        config.FONT_PATH = font_path
        # 更新數字專用設定，避免舊值殘留於 SPECIAL_RENDER_OVERRIDES
        config.sync_digit_overrides()
        img = builder.generate_text_image("預覽123ABC!?中文", font_path)
        if img:
            target_height = 200
            scale = target_height / img.height
            new_size = (max(1, int(img.width * scale)), target_height)
            img = img.resize(new_size, Image.LANCZOS)
            self._tk_img = ImageTk.PhotoImage(img)
            self.preview_label.configure(image=self._tk_img)

    def save_config(self):
        data = {}
        for name, info in self.params.items():
            cast = info.get("type", float)
            data[name] = cast(info["var"].get())
        data["FONT_PATH"] = os.path.join(self.fonts_dir, self.font_var.get())
        with open(CUSTOM_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 已儲存 {CUSTOM_CONFIG_PATH}")


def main():
    app = ConfigGUI()
    app.mainloop()


if __name__ == "__main__":
    main()

