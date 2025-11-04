import os
import json
import customtkinter as ctk
from PIL import ImageTk, Image

from . import builder, config
from . import auto_update

CUSTOM_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "configs", "custom_config.json")


class ConfigGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("HandFont 參數設定")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.fonts_dir = os.path.join(os.path.dirname(__file__), "fonts")
        self.fonts_list = [f for f in os.listdir(self.fonts_dir) if f.lower().endswith(".ttf")]
        default_font = os.path.basename(config.FONT_PATH)
        if default_font not in self.fonts_list and self.fonts_list:
            default_font = self.fonts_list[0]
        self.font_var = ctk.StringVar(value=default_font)

        self.params = {
            "PERTURB": {"var": ctk.IntVar(value=config.PERTURB), "min": 0, "max": 20, "type": int},
            "PERTURB_JITTER": {"var": ctk.IntVar(value=config.PERTURB_JITTER), "min": 0, "max": 5, "type": int},
            "SHEAR_ANGLE": {"var": ctk.IntVar(value=config.SHEAR_ANGLE), "min": -30, "max": 30, "type": int},
            "COLOR_VARIATION": {"var": ctk.IntVar(value=config.COLOR_VARIATION), "min": 0, "max": 60, "type": int},
            "LINE_WIDTH": {"var": ctk.IntVar(value=config.LINE_WIDTH), "min": 1, "max": 5, "type": int},
            "CHAR_SPACING_OFFSET": {"var": ctk.IntVar(value=config.CHAR_SPACING_OFFSET), "min": -100, "max": 100, "type": int},
            "DIGIT_SCALE": {"var": ctk.DoubleVar(value=config.DIGIT_SCALE), "min": 0.5, "max": 1.5, "type": float},
            "DIGIT_OFFSET_Y": {"var": ctk.DoubleVar(value=config.DIGIT_OFFSET_Y), "min": -0.5, "max": 0.5, "type": float},
            "ALPHA_SCALE": {"var": ctk.DoubleVar(value=config.ALPHA_SCALE), "min": 0.5, "max": 1.5, "type": float},
            "ALPHA_OFFSET_Y": {"var": ctk.DoubleVar(value=config.ALPHA_OFFSET_Y), "min": -0.5, "max": 0.5, "type": float},
            "CJK_SCALE": {"var": ctk.DoubleVar(value=config.CJK_SCALE), "min": 0.5, "max": 1.5, "type": float},
            "CJK_OFFSET_Y": {"var": ctk.DoubleVar(value=config.CJK_OFFSET_Y), "min": -0.5, "max": 0.5, "type": float},
            "SPECIAL_SCALE": {"var": ctk.DoubleVar(value=config.SPECIAL_SCALE), "min": 0.5, "max": 1.5, "type": float},
            "SPECIAL_OFFSET_Y": {"var": ctk.DoubleVar(value=config.SPECIAL_OFFSET_Y), "min": -0.5, "max": 0.5, "type": float},
        }

        self._build_ui()
        self.update_preview()

    def _build_ui(self):
        self.grid_columnconfigure(2, weight=1)
        row = 0
        ctk.CTkLabel(self, text="字體 Font").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        font_cb = ctk.CTkComboBox(self, variable=self.font_var, values=self.fonts_list,
                                 command=lambda _: self.update_preview())
        font_cb.grid(row=row, column=1, columnspan=2, sticky="we", padx=5)
        row += 1

        for name, info in self.params.items():
            desc = config.PARAM_INFO.get(name, (name,))[0]
            ctk.CTkLabel(self, text=f"{desc} ({name})").grid(row=row, column=0, sticky="w", padx=5, pady=2)
            ctk.CTkEntry(self, textvariable=info["var"], width=60).grid(row=row, column=1, padx=5)
            slider = ctk.CTkSlider(self, from_=info["min"], to=info["max"],
                                   variable=info["var"], command=lambda _: self.update_preview())
            slider.grid(row=row, column=2, sticky="we", padx=5)
            row += 1

        self.preview_label = ctk.CTkLabel(self, text="")
        self.preview_label.grid(row=0, column=3, rowspan=row, padx=10, pady=10)

        btn_frame = ctk.CTkFrame(self)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=10, sticky="w")
        ctk.CTkButton(btn_frame, text="重設預設", command=self.reset_defaults).grid(row=0, column=0, padx=5)
        ctk.CTkButton(btn_frame, text="儲存設定", command=self.save_config).grid(row=0, column=1, padx=5)

    def update_preview(self):
        for name, info in self.params.items():
            cast = info.get("type", float)
            value = cast(info["var"].get())
            setattr(config, name, value)
            setattr(builder, name, value)
        font_path = os.path.join(self.fonts_dir, self.font_var.get())
        config.FONT_PATH = font_path
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

    def reset_defaults(self):
        try:
            config.reset_to_defaults()
        except Exception:
            pass
        for name, info in self.params.items():
            val = getattr(config, name)
            info["var"].set(val)
        default_font = os.path.basename(config.FONT_PATH)
        if default_font in self.fonts_list:
            self.font_var.set(default_font)
        self.update_preview()


def main():
    auto_update.check_for_update()
    app = ConfigGUI()
    app.mainloop()
