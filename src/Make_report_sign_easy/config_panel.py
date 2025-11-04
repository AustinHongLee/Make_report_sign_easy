import os
import tkinter as tk
from tkinter import ttk
from PIL import ImageTk, Image

from . import builder, config


class ConfigPanel(ttk.Frame):
    """Reusable configuration panel as a Frame.

    Exposes all parameters in config.PARAM_INFO, font selection, live preview,
    and provides get_values()/set_values() to exchange a full config snapshot.
    """

    def __init__(self, master, start_values: dict | None = None, on_apply=None):
        super().__init__(master)
        self.on_apply = on_apply

        # Fonts
        self.fonts_dir = os.path.join(os.path.dirname(__file__), "fonts")
        self.fonts_list = [
            f for f in os.listdir(self.fonts_dir) if f.lower().endswith(".ttf")
        ] if os.path.isdir(self.fonts_dir) else []
        default_font = os.path.basename(config.FONT_PATH)
        if default_font not in self.fonts_list and self.fonts_list:
            default_font = self.fonts_list[0]
        self.font_var = tk.StringVar(value=default_font)

        # Params from PARAM_INFO with ranges
        self.params = {}
        for name, (desc, _range) in getattr(config, "PARAM_INFO", {}).items():
            current = getattr(config, name)
            # Derive min/max from range string like "0~20" or "-30~30"
            try:
                parts = _range.replace(" ", "").split("~")
                min_v = float(parts[0])
                max_v = float(parts[1])
            except Exception:
                min_v, max_v = 0.0, 100.0
            if isinstance(current, tuple) and len(current) == 2 and all(
                isinstance(x, (int, float)) for x in current
            ):
                var = tk.StringVar(value=f"{current[0]},{current[1]}")
                self.params[name] = {
                    "var": var,
                    "min": min_v,
                    "max": max_v,
                    "is_tuple": True,
                    "desc": desc,
                }
            else:
                if isinstance(current, float):
                    var = tk.DoubleVar(value=float(current))
                    is_float = True
                else:
                    var = tk.IntVar(value=int(current))
                    is_float = False
                self.params[name] = {
                    "var": var,
                    "min": min_v,
                    "max": max_v,
                    "is_float": is_float,
                    "desc": desc,
                }

        self._build_ui()

        if start_values:
            self.set_values(start_values)
        self.update_preview()

    def _build_ui(self):
        # Layout: left controls, right preview, bottom buttons
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        left = ttk.Frame(self)
        left.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        left.columnconfigure(2, weight=1)
        row = 0
        ttk.Label(left, text="字體 Font").grid(row=row, column=0, sticky="w")
        font_cb = ttk.Combobox(
            left,
            textvariable=self.font_var,
            values=self.fonts_list,
            state="readonly",
        )
        font_cb.grid(row=row, column=1, columnspan=2, sticky="we", padx=6)
        font_cb.bind("<<ComboboxSelected>>", lambda e: self.update_preview())
        row += 1

        for name, info in self.params.items():
            ttk.Label(left, text=f"{info['desc']} ({name})").grid(
                row=row, column=0, sticky="w"
            )
            if info.get("is_tuple"):
                entry = ttk.Entry(left, textvariable=info["var"], width=12)
                entry.grid(row=row, column=1, padx=6)
                # 無滑桿，僅透過逗號輸入
                ttk.Label(left, text="格式: a,b").grid(
                    row=row, column=2, sticky="w"
                )
                entry.bind("<KeyRelease>", lambda e: self.update_preview())
            else:
                entry = ttk.Entry(left, textvariable=info["var"], width=8)
                entry.grid(row=row, column=1, padx=6)
                scale = ttk.Scale(
                    left,
                    from_=info["min"],
                    to=info["max"],
                    orient=tk.HORIZONTAL,
                    variable=info["var"],
                    command=lambda e: self.update_preview(),
                )
                scale.grid(row=row, column=2, sticky="we")
            row += 1

        right = ttk.Frame(self)
        right.grid(row=0, column=1, sticky="nsew", padx=(0, 8), pady=8)
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)
        self.preview_label = ttk.Label(right)
        self.preview_label.grid(row=0, column=0, sticky="nsew")

        btns = ttk.Frame(self)
        btns.grid(row=1, column=0, columnspan=2, pady=(0, 8))
        ttk.Button(btns, text="套用", command=self._apply_clicked).grid(
            row=0, column=0, padx=6
        )
        ttk.Button(btns, text="重設預設", command=self.reset_defaults).grid(
            row=0, column=1, padx=6
        )

    def update_preview(self):
        # Apply current values to config/builder (temporary in-process)
        self._apply_to_runtime()
        img = builder.generate_text_image("預覽123ABC!?中文", config.FONT_PATH)
        if img:
            target_h = 220
            scale = target_h / img.height
            new_size = (max(1, int(img.width * scale)), target_h)
            img = img.resize(new_size, Image.LANCZOS)
            self._tk_img = ImageTk.PhotoImage(img)
            self.preview_label.configure(image=self._tk_img)

    def _apply_to_runtime(self):
        # Push current UI values into config & builder
        for name, info in self.params.items():
            if info.get("is_tuple"):
                raw = info["var"].get()
                try:
                    parts = [p.strip() for p in str(raw).split(",")]
                    a = float(parts[0])
                    b = float(parts[1])
                    # 保持輸入型別風格（整數維持 int）
                    if isinstance(getattr(config, name)[0], int):
                        a = int(round(a))
                    if isinstance(getattr(config, name)[1], int):
                        b = int(round(b))
                    v = (a, b)
                except Exception:
                    v = getattr(config, name)
            else:
                v = info["var"].get()
                v = float(v) if info.get("is_float") else int(v)
            setattr(config, name, v)
            setattr(builder, name, v)
        # Font path
        if self.fonts_list:
            config.FONT_PATH = os.path.join(
                self.fonts_dir, self.font_var.get()
            )
        if hasattr(config, "sync_digit_overrides"):
            config.sync_digit_overrides()

    def get_values(self) -> dict:
        # Return a snapshot of all params + FONT_PATH
        data = {}
        for name, info in self.params.items():
            if info.get("is_tuple"):
                raw = info["var"].get()
                try:
                    parts = [p.strip() for p in str(raw).split(",")]
                    a = float(parts[0])
                    b = float(parts[1])
                    if isinstance(getattr(config, name)[0], int):
                        a = int(round(a))
                    if isinstance(getattr(config, name)[1], int):
                        b = int(round(b))
                    data[name] = (a, b)
                except Exception:
                    data[name] = getattr(config, name)
            else:
                v = info["var"].get()
                data[name] = float(v) if info.get("is_float") else int(v)
        if self.fonts_list:
            data["FONT_PATH"] = os.path.join(
                self.fonts_dir, self.font_var.get()
            )
        else:
            data["FONT_PATH"] = config.FONT_PATH
        return data

    def set_values(self, values: dict):
        # Load from dict, fallback to current config if missing
        if values.get("FONT_PATH"):
            try:
                base = os.path.basename(values["FONT_PATH"])
                if base in self.fonts_list:
                    self.font_var.set(base)
            except Exception:
                pass
        for name, info in self.params.items():
            if name in values:
                val = values[name]
                try:
                    if (
                        info.get("is_tuple")
                        and isinstance(val, (tuple, list))
                        and len(val) == 2
                    ):
                        info["var"].set(f"{val[0]},{val[1]}")
                    else:
                        info["var"].set(val)
                except Exception:
                    pass
        self.update_preview()

    def reset_defaults(self):
        try:
            config.reset_to_defaults()
        except Exception:
            pass
        # Sync UI vars from config defaults
        base = os.path.basename(config.FONT_PATH)
        if base in self.fonts_list:
            self.font_var.set(base)
        for name, info in self.params.items():
            if hasattr(config, name):
                val = getattr(config, name)
                info["var"].set(val)
        self.update_preview()

    def _apply_clicked(self):
        # Apply current UI to runtime and notify
        self._apply_to_runtime()
        if callable(self.on_apply):
            self.on_apply(self.get_values())
