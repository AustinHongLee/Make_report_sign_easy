"""
# flake8: noqa
# pylint: disable=C0301

GUI for filling PDF FreeText annotations with handwriting-style text.
"""

import io
import json
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import fitz  # PyMuPDF
from PIL import Image, ImageTk, ImageFilter

from Make_report_sign_easy.builder import generate_text_image
from Make_report_sign_easy.config_panel import ConfigPanel


def extract_freetext_positions(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc[0]
    pos_map = {}
    for annot in page.annots() or []:
        if annot.type[1] == "FreeText":
            content = annot.info.get("content", "").strip()
            if content:
                pos_map[content] = fitz.Rect(annot.rect)
    doc.close()
    return pos_map


def paste_image_centered(page, rect, pil_image):
    # 將 PIL 影像等比縮放，完整落在 rect 內，並置中
    img_w, img_h = pil_image.size
    rect_w = rect.width
    rect_h = rect.height
    if img_w == 0 or img_h == 0:
        return
    scale = min(rect_w / img_w, rect_h / img_h)
    w = max(1, int(img_w * scale))
    h = max(1, int(img_h * scale))
    # 計算置中位置
    x0 = rect.x0 + (rect_w - w) / 2
    y0 = rect.y0 + (rect_h - h) / 2
    x1 = x0 + w
    y1 = y0 + h
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    page.insert_image(fitz.Rect(x0, y0, x1, y1), stream=buf.getvalue())


class ScrollableFields(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.interior = ttk.Frame(self.canvas)
        self.interior.bind("<Configure>", self._on_configure)
        self.canvas.create_window((0, 0), window=self.interior, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def _on_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


class PDFFillGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HandFont PDF 填值工具 (簡版)")
        self.geometry("1000x720")
        self.pdf_path = None
        self.pos_map = {}
        self.entries = {}
        self.random_flag = tk.BooleanVar(value=True)
        self.global_thin_steps = tk.IntVar(value=0)   # 全域細化次數 0~3
        self.global_scale = tk.DoubleVar(value=1.0)   # 全域額外縮放 0.5~1.5
        self.global_line_width = tk.IntVar(value=0)   # 全域線寬 0 表示沿用
        self.global_blur = tk.IntVar(value=0)         # 全域模糊 0 表示沿用
        self.global_config_overrides = {}             # 全域進階設定（完整 config 覆寫）
        self.field_overrides = {}  # {key: {font, scale, thin, random, line_width, blur, config_overrides}}
        # 字型清單（供欄位覆寫使用）
        try:
            import Make_report_sign_easy.config as cfg
            fonts_dir = os.path.join(os.path.dirname(cfg.BASE_DIR), os.path.basename(cfg.BASE_DIR), 'fonts')
            if not os.path.isdir(fonts_dir):
                fonts_dir = os.path.join(cfg.BASE_DIR, 'fonts')
            self.fonts_dir = fonts_dir
            self.fonts_list = [f for f in os.listdir(fonts_dir) if f.lower().endswith('.ttf')]
        except Exception:
            self.fonts_dir = None
            self.fonts_list = []

        # 左：欄位區；右：預覽
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        # 頂部工具列
        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="we", padx=8, pady=8)
        ttk.Button(toolbar, text="選擇 PDF", command=self.pick_pdf).pack(side="left")
        ttk.Button(toolbar, text="讀取欄位", command=self.load_fields).pack(side="left", padx=6)
        ttk.Button(toolbar, text="載入 JSON", command=self.load_values).pack(side="left")
        ttk.Button(toolbar, text="儲存 JSON", command=self.save_values).pack(side="left", padx=6)
        ttk.Checkbutton(toolbar, text="手寫隨機化", variable=self.random_flag).pack(side="left", padx=12)
        ttk.Button(toolbar, text="全域設定", command=self.open_global_settings).pack(side="left")
        ttk.Button(toolbar, text="進階設定(全域)", command=self.open_advanced_global).pack(side="left", padx=6)
        ttk.Button(toolbar, text="預覽", command=self.update_preview).pack(side="left", padx=6)
        ttk.Button(toolbar, text="輸出 PDF", command=self.export_pdf).pack(side="left")

        # 左側：欄位輸入
        left = ttk.LabelFrame(self, text="欄位與文字")
        left.grid(row=1, column=0, sticky="nswe", padx=(8, 4), pady=(0, 8))
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)

        self.fields_panel = ScrollableFields(left)
        self.fields_panel.grid(row=0, column=0, sticky="nswe")

        # 右側：預覽
        right = ttk.LabelFrame(self, text="預覽（第一頁）")
        right.grid(row=1, column=1, sticky="nswe", padx=(4, 8), pady=(0, 8))
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)
        self.preview_label = ttk.Label(right)
        self.preview_label.grid(row=0, column=0, sticky="nsew")

    def pick_pdf(self):
        path = filedialog.askopenfilename(
            title="選擇 PDF 樣板",
            filetypes=[("PDF", "*.pdf"), ("All Files", "*.*")],
        )
        if path:
            self.pdf_path = path
            messagebox.showinfo("PDF 已選擇", os.path.basename(path))

    def load_fields(self):
        if not self.pdf_path:
            messagebox.showwarning("提示", "請先選擇 PDF 樣板")
            return
        self.pos_map = extract_freetext_positions(self.pdf_path)
        if not self.pos_map:
            messagebox.showwarning("提示", "找不到任何 FreeText 註解欄位")
            return
        # 清空舊欄位
        for child in self.fields_panel.interior.winfo_children():
            child.destroy()
        self.entries.clear()
        # 建立新欄位
        for r, key in enumerate(sorted(self.pos_map.keys())):
            ttk.Label(self.fields_panel.interior, text=key, width=30, anchor="w").grid(
                row=r, column=0, sticky="w", padx=6, pady=3
            )
            var = tk.StringVar(value="")
            ent = ttk.Entry(self.fields_panel.interior, textvariable=var, width=40)
            ent.grid(row=r, column=1, sticky="we", padx=6, pady=3)
            self.fields_panel.interior.columnconfigure(1, weight=1)
            self.entries[key] = var
            ttk.Button(self.fields_panel.interior, text="設定", command=lambda k=key: self.open_field_settings(k)).grid(
                row=r, column=2, padx=4
            )

    def load_values(self):
        path = filedialog.askopenfilename(
            title="載入 JSON 值檔",
            filetypes=[("JSON", "*.json"), ("All Files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("JSON 根必須是物件 {field: text}")
            for k, v in data.items():
                if k in self.entries:
                    self.entries[k].set(str(v))
            messagebox.showinfo("完成", "已載入 JSON")
        except Exception as e:
            messagebox.showerror("錯誤", str(e))

    def save_values(self):
        if not self.entries:
            messagebox.showwarning("提示", "沒有可儲存的欄位。請先讀取欄位")
            return
        values = {k: var.get() for k, var in self.entries.items()}
        path = filedialog.asksaveasfilename(
            title="儲存 JSON 值檔",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(values, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("完成", f"已儲存到 {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("錯誤", str(e))

    def update_preview(self):
        if not self.pdf_path:
            messagebox.showwarning("提示", "請先選擇 PDF")
            return
        values = {k: var.get() for k, var in self.entries.items()}
        try:
            img = self._render_preview_with_overrides(values, zoom=1.5)
            # 將圖縮到視窗適配
            max_w, max_h = 800, 1000
            scale = min(max_w / img.width, max_h / img.height, 1.0)
            if scale < 1.0:
                img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
            self._tk_img = ImageTk.PhotoImage(img)
            self.preview_label.configure(image=self._tk_img)
        except Exception as e:
            messagebox.showerror("預覽失敗", str(e))

    def export_pdf(self):
        if not self.pdf_path:
            messagebox.showwarning("提示", "請先選擇 PDF")
            return
        values = {k: var.get() for k, var in self.entries.items()}
        if not values:
            messagebox.showwarning("提示", "沒有要填的欄位內容")
            return
        out_path = filedialog.asksaveasfilename(
            title="輸出 PDF",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
        )
        if not out_path:
            return
        try:
            doc = fitz.open(self.pdf_path)
            page = doc[0]
            # 移除原註解，避免疊印
            for annot in page.annots() or []:
                page.delete_annot(annot)
            for key, text in values.items():
                # 找對應 rect
                rect = None
                for annot in page.annots() or []:
                    if annot.type[1] == "FreeText":
                        content = annot.info.get("content", "").strip()
                        if content == key:
                            rect = fitz.Rect(annot.rect)
                            break
                # 如果上面已經刪除註解，這邊再掃會找不到，因此改用前次的 pos_map
                if rect is None and self.pos_map:
                    rect = self.pos_map.get(key)
                if rect is None:
                    continue
                img = self._generate_image_with_overrides(key, str(text))
                if img:
                    # 套用欄位/全域縮放
                    scale_mult = self.field_overrides.get(key, {}).get('scale', 1.0) * self.global_scale.get()
                    img = self._apply_thinning_if_needed(key, img)
                    self._paste_image_scaled(page, rect, img, scale_mult)
            doc.save(out_path, garbage=4, deflate=True)
            doc.close()
            messagebox.showinfo("完成", f"已輸出：{os.path.basename(out_path)}")
        except Exception as e:
            messagebox.showerror("輸出失敗", str(e))

    # ====== 設定與覆寫 ======
    def open_global_settings(self):
        win = tk.Toplevel(self)
        win.title("全域設定")
        ttk.Label(win, text="線條細化 (0~3)：").grid(row=0, column=0, sticky='w', padx=8, pady=8)
        ttk.Spinbox(win, from_=0, to=3, textvariable=self.global_thin_steps, width=5).grid(row=0, column=1, padx=8)
        ttk.Label(win, text="額外縮放 (50%~150%)：").grid(row=1, column=0, sticky='w', padx=8, pady=8)
        scale_var = tk.DoubleVar(value=self.global_scale.get() * 100)
        def _apply_global():
            self.global_scale.set(max(0.5, min(1.5, scale_var.get()/100)))
            # 全域線寬/模糊無需轉換，直接保留 IntVar 值（0=沿用）
            win.destroy()
        ttk.Spinbox(win, from_=50, to=150, textvariable=scale_var, width=6).grid(row=1, column=1, padx=8)
        # 全域線寬
        ttk.Label(win, text="全域線寬 (0=沿用,1~5)：").grid(row=2, column=0, sticky='w', padx=8, pady=8)
        ttk.Spinbox(win, from_=0, to=5, textvariable=self.global_line_width, width=5).grid(row=2, column=1, padx=8)
        # 全域模糊
        ttk.Label(win, text="全域模糊 (0=沿用,0~6)：").grid(row=3, column=0, sticky='w', padx=8, pady=8)
        ttk.Spinbox(win, from_=0, to=6, textvariable=self.global_blur, width=5).grid(row=3, column=1, padx=8)
        ttk.Button(win, text="套用", command=_apply_global).grid(row=4, column=0, columnspan=2, pady=10)

    def open_field_settings(self, key):
        win = tk.Toplevel(self)
        win.title(f"欄位設定 - {key}")
        win.rowconfigure(0, weight=1)
        win.columnconfigure(0, weight=1)
        ov = self.field_overrides.get(key, {}).copy()
        # 字型選擇
        ttk.Label(win, text="字型 (可選)：").grid(row=0, column=0, sticky='w', padx=8, pady=6)
        font_var = tk.StringVar(value=ov.get('font', ''))
        values = [''] + self.fonts_list if self.fonts_list else ['']
        font_cb = ttk.Combobox(win, textvariable=font_var, values=values, state='readonly')
        font_cb.grid(row=0, column=1, padx=8, pady=6)
        # 縮放
        ttk.Label(win, text="額外縮放 (50%~150%)：").grid(row=1, column=0, sticky='w', padx=8, pady=6)
        scale_var = tk.DoubleVar(value=(ov.get('scale', 1.0) * 100))
        ttk.Spinbox(win, from_=50, to=150, textvariable=scale_var, width=6).grid(row=1, column=1, padx=8)
        # 細化
        ttk.Label(win, text="線條細化 (0~3)：").grid(row=2, column=0, sticky='w', padx=8, pady=6)
        thin_var = tk.IntVar(value=ov.get('thin', 0))
        ttk.Spinbox(win, from_=0, to=3, textvariable=thin_var, width=5).grid(row=2, column=1, padx=8)
        # 線寬（直接影響描邊寬度）
        ttk.Label(win, text="線寬 (1~5)：").grid(row=3, column=0, sticky='w', padx=8, pady=6)
        lw_var = tk.IntVar(value=ov.get('line_width', 0) or 0)
        ttk.Spinbox(win, from_=0, to=5, textvariable=lw_var, width=5).grid(row=3, column=1, padx=8)
        ttk.Label(win, text="(0 表示沿用全域/預設)").grid(row=3, column=2, sticky='w')
        # 模糊（影響整體柔化程度）
        ttk.Label(win, text="模糊 (0~6)：").grid(row=4, column=0, sticky='w', padx=8, pady=6)
        blur_var = tk.IntVar(value=ov.get('blur', 0) or 0)
        ttk.Spinbox(win, from_=0, to=6, textvariable=blur_var, width=5).grid(row=4, column=1, padx=8)
        # 隨機
        ttk.Label(win, text="手寫隨機化覆寫：").grid(row=5, column=0, sticky='w', padx=8, pady=6)
        rand_state = tk.StringVar(value={True: 'on', False: 'off', None: 'inherit'}.get(ov.get('random', None), 'inherit'))
        ttk.Combobox(win, textvariable=rand_state, values=['inherit', 'on', 'off'], state='readonly').grid(row=5, column=1, padx=8)
        # 進階設定（完整 config 覆寫）
        ttk.Button(win, text="進階…", command=lambda: self.open_advanced_field(key, parent=win)).grid(row=6, column=0, padx=8, pady=8, sticky='w')

        def _save():
            new_ov = {}
            fv = font_var.get().strip()
            if fv:
                new_ov['font'] = os.path.join(self.fonts_dir, fv) if self.fonts_dir else fv
            sv = max(50, min(150, scale_var.get()))/100.0
            if abs(sv-1.0) > 1e-6:
                new_ov['scale'] = sv
            tv = max(0, min(3, thin_var.get()))
            if tv:
                new_ov['thin'] = tv
            lw = max(0, min(5, int(lw_var.get())))
            if lw:
                new_ov['line_width'] = lw
            bl = max(0, min(6, int(blur_var.get())))
            if bl:
                new_ov['blur'] = bl
            rv = rand_state.get()
            if rv != 'inherit':
                new_ov['random'] = (rv == 'on')
            # 保留既有的進階覆寫
            if 'config_overrides' in ov and isinstance(ov['config_overrides'], dict):
                new_ov['config_overrides'] = ov['config_overrides']
            self.field_overrides[key] = new_ov
            win.destroy()
        ttk.Button(win, text="儲存", command=_save).grid(row=7, column=0, columnspan=2, pady=10)

    # ====== 內部工具 ======
    def _apply_thinning_if_needed(self, key, img):
        steps = self.global_thin_steps.get() + int(self.field_overrides.get(key, {}).get('thin', 0))
        if steps <= 0:
            return img
        steps = min(3, max(0, steps))
        r, g, b, a = img.split()
        for _ in range(steps):
            a = a.filter(ImageFilter.MinFilter(3))
        out = Image.merge('RGBA', (r, g, b, a))
        return out

    def _generate_image_with_overrides(self, key, text):
        ov = self.field_overrides.get(key, {})
        font_path = ov.get('font', None)
        rnd = ov.get('random', None)
        use_random = self.random_flag.get() if rnd is None else rnd
        overrides = {}
        # 先套用全域覆寫
        if int(self.global_line_width.get()) > 0:
            overrides['LINE_WIDTH'] = int(self.global_line_width.get())
        if int(self.global_blur.get()) > 0:
            overrides['BLUR_AMOUNT'] = int(self.global_blur.get())
        # 全域進階覆寫（完整集）
        if self.global_config_overrides:
            overrides.update(self.global_config_overrides)
        # 欄位覆寫優先於全域覆寫
        if ov.get('line_width'):
            overrides['LINE_WIDTH'] = int(ov['line_width'])
        if ov.get('blur') is not None and ov.get('blur') != 0:
            overrides['BLUR_AMOUNT'] = int(ov['blur'])
        # 欄位進階覆寫（完整集）
        if ov.get('config_overrides'):
            overrides.update(ov['config_overrides'])
        img = generate_text_image(text, font_path=font_path, random=use_random, overrides=overrides or None)
        return img

    # ====== 高階設定視窗 ======
    def open_advanced_global(self):
        if not hasattr(self, '_adv_global_win') or not self._adv_global_win.winfo_exists():
            win = tk.Toplevel(self)
            win.title("進階設定（全域）")
            win.rowconfigure(0, weight=1)
            win.columnconfigure(0, weight=1)
            # 預設以目前 config 內容為起點
            panel = ConfigPanel(win, start_values=None, on_apply=lambda vals: self._on_global_advanced_apply(vals))
            panel.grid(row=0, column=0, sticky='nsew')
            self._adv_global_win = win
        else:
            self._adv_global_win.lift()

    def _on_global_advanced_apply(self, values: dict):
        # 將整包參數記為全域進階覆寫；字型也能被覆寫
        self.global_config_overrides = dict(values)
        # 立即更新預覽
        self.update_preview()

    def open_advanced_field(self, key, parent=None):
        win = tk.Toplevel(parent or self)
        win.title(f"進階設定（欄位：{key}）")
        win.rowconfigure(0, weight=1)
        win.columnconfigure(0, weight=1)
        # 用目前全域覆寫或現行 config 作為起點（優先使用欄位現有覆寫）
        start = self.field_overrides.get(key, {}).get('config_overrides') or self.global_config_overrides or None
        def _apply(vals):
            ov = self.field_overrides.get(key, {})
            ov['config_overrides'] = dict(vals)
            self.field_overrides[key] = ov
            # 不關閉也可以立刻預覽
            self.update_preview()
        panel = ConfigPanel(win, start_values=start, on_apply=_apply)
        panel.grid(row=0, column=0, sticky='nsew')

    def _paste_image_scaled(self, page, rect, img, scale_mult=1.0):
        # 根據 rect 計算等比縮放，套用 scale_mult 後置中貼入
        img_w, img_h = img.size
        if img_w == 0 or img_h == 0:
            return
        rect_w, rect_h = rect.width, rect.height
        scale = min(rect_w / img_w, rect_h / img_h) * max(0.5, min(1.5, scale_mult))
        w = max(1, int(img_w * scale))
        h = max(1, int(img_h * scale))
        x0 = rect.x0 + (rect_w - w) / 2
        y0 = rect.y0 + (rect_h - h) / 2
        x1, y1 = x0 + w, y0 + h
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        page.insert_image(fitz.Rect(x0, y0, x1, y1), stream=buf.getvalue())

    def _render_preview_with_overrides(self, values, zoom=1.5):
        # 產生底圖
        doc = fitz.open(self.pdf_path)
        page = doc[0]
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        base = Image.frombytes("RGB", [pix.width, pix.height], pix.samples).convert('RGBA')
        # 疊各欄位
        for key, text in values.items():
            # 找 rect
            rect = None
            for annot in page.annots() or []:
                if annot.type[1] == "FreeText":
                    content = annot.info.get("content", "").strip()
                    if content == key:
                        rect = fitz.Rect(annot.rect)
                        break
            if rect is None:
                rect = self.pos_map.get(key)
            if rect is None:
                continue
            img = self._generate_image_with_overrides(key, str(text))
            if not img:
                continue
            # 細化與縮放
            img = self._apply_thinning_if_needed(key, img)
            scale_mult = self.field_overrides.get(key, {}).get('scale', 1.0) * self.global_scale.get()
            img_w, img_h = img.size
            rect_w = rect.width * zoom
            rect_h = rect.height * zoom
            scale = min(rect_w / img_w, rect_h / img_h) * max(0.5, min(1.5, scale_mult))
            w = max(1, int(img_w * scale))
            h = max(1, int(img_h * scale))
            imgr = img.resize((w, h), Image.LANCZOS)
            x0 = int(rect.x0 * zoom + (rect_w - w) / 2)
            y0 = int(rect.y0 * zoom + (rect_h - h) / 2)
            base.alpha_composite(imgr, dest=(x0, y0))
        doc.close()
        return base


def main():
    app = PDFFillGUI()
    app.mainloop()
