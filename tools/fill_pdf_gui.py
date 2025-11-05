import os
import sys
import io
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import customtkinter as ctk

import fitz  # PyMuPDF
from PIL import Image, ImageTk, ImageFilter

if __name__ == "__main__" and __package__ is None:
    # 允許直接以腳本執行；優先使用 src 佈局（若存在），再回退到專案根
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    src_root = os.path.join(repo_root, "src")
    if os.path.isdir(src_root):
        sys.path.insert(0, src_root)
    sys.path.insert(0, repo_root)

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


def render_page_preview(pdf_path, values, random_flag=False, zoom=2.0):
    doc = fitz.open(pdf_path)
    page = doc[0]
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    base = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    base = base.convert("RGBA")

    # 疊上預覽的文字圖片
    for key, text in values.items():
        rect = None
        for annot in page.annots() or []:
            if annot.type[1] == "FreeText":
                content = annot.info.get("content", "").strip()
                if content == key:
                    rect = fitz.Rect(annot.rect)
                    break
        if rect is None:
            continue
        # 產圖並等比放入
        img = generate_text_image(str(text), random=random_flag)
        if not img:
            continue
        img_w, img_h = img.size
        rect_w = rect.width * zoom
        rect_h = rect.height * zoom
        if img_w == 0 or img_h == 0:
            continue
        scale = min(rect_w / img_w, rect_h / img_h)
        w = max(1, int(img_w * scale))
        h = max(1, int(img_h * scale))
        imgr = img.resize((w, h), Image.LANCZOS)
        # 置中位置
        x0 = int(rect.x0 * zoom + (rect_w - w) / 2)
        y0 = int(rect.y0 * zoom + (rect_h - h) / 2)
        base.alpha_composite(imgr, dest=(x0, y0))

    doc.close()
    return base


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
        self.show_boxes = tk.BooleanVar(value=False)  # 是否在預覽上顯示紅框
        self.edit_boxes = tk.BooleanVar(value=False)  # 編輯紅框模式（允許點選/拖曳）
        self.global_thin_steps = tk.IntVar(value=0)   # 全域細化次數 0~3
        self.global_thick_steps = tk.IntVar(value=0)  # 全域加粗次數 0~3
        self.global_scale = tk.DoubleVar(value=1.0)   # 全域額外縮放 0.5~1.5
        self.global_line_width = tk.IntVar(value=0)   # 全域線寬 0 表示沿用
        self.global_blur = tk.IntVar(value=0)         # 全域模糊 0 表示沿用
        self.global_config_overrides = {}             # 全域進階設定（完整 config 覆寫）
        self.nudge_step = tk.IntVar(value=2)          # 紅框微調步長（pt）
        # 本次（會話層）單字視覺覆寫：{'scale':float,'offset_y':float,'alpha':int,'spacing':int}
        self.session_char_overrides = {}
        # 篩選器（層級開關）：單字 / 句子 / 欄位 / 報告
        self.use_char_filter = tk.BooleanVar(value=True)
        self.use_sentence_filter = tk.BooleanVar(value=True)
        self.use_field_filter = tk.BooleanVar(value=True)
        self.use_report_filter = tk.BooleanVar(value=True)
        # {key: {font, scale, thin, thick, random, random_per, line_width, blur, color, config_overrides}}
        self.field_overrides = {}
        # 欄位紅框尺寸覆寫：{ key: {left:int, right:int, top:int, bottom:int} }，單位：PDF 點數
        self.rect_overrides = {}
        # 互動編輯狀態
        self.active_field = None
        self._preview_zoom = 1.5
        self._screen_rects = {}  # {key: (x0,y0,x1,y1) in px at current zoom}
        self._drag_state = None  # {'key','mode','start_mouse',(x,y),'start_rect','base_rect'}
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

        # 左：欄位區；右：預覽（使用可拖曳分隔的 PanedWindow）
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # 頂部工具列（極簡 + 進階選單）
        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, sticky="we", padx=8, pady=8)
        ttk.Button(toolbar, text="選擇 PDF", command=self.pick_pdf).pack(side="left")
        ttk.Button(toolbar, text="讀取欄位", command=self.load_fields).pack(side="left", padx=6)
        ttk.Button(toolbar, text="載入 JSON", command=self.load_values).pack(side="left")
        ttk.Button(toolbar, text="儲存 JSON", command=self.save_values).pack(side="left", padx=6)
        ttk.Checkbutton(toolbar, text="手寫隨機化", variable=self.random_flag).pack(side="left", padx=12)
        ttk.Checkbutton(toolbar, text="顯示紅框", variable=self.show_boxes, command=self.update_preview).pack(side="left")
        ttk.Label(toolbar, text="步長(pt)").pack(side="left", padx=(12, 4))
        ttk.Spinbox(toolbar, from_=1, to=20, textvariable=self.nudge_step, width=4).pack(side="left")
        # 極簡：將進階動作收入彈出選單
        ttk.Button(toolbar, text="簡易模式", command=self.open_quick_adjust).pack(side="left")
        adv_btn = tk.Menubutton(toolbar, text="進階", relief="raised")
        adv_menu = tk.Menu(adv_btn, tearoff=False)
        adv_menu.add_command(label="本次微調（詳細）", command=self.open_session_overrides)
        adv_menu.add_command(label="篩選器（層級開關）", command=self.open_filter_pipeline)
        adv_menu.add_separator()
        adv_menu.add_command(label="全域設定（快速）", command=self.open_global_settings)
        adv_menu.add_command(label="進階設定（全域）", command=self.open_advanced_global)
        adv_menu.add_separator()
        adv_menu.add_checkbutton(label="編輯紅框（互動）", variable=self.edit_boxes, command=self._toggle_edit_mode)
        adv_btn.configure(menu=adv_menu)
        adv_btn.pack(side="left", padx=(6, 0))
        ttk.Button(toolbar, text="預覽", command=self.update_preview).pack(side="left", padx=6)
        ttk.Button(toolbar, text="輸出 PDF", command=self.export_pdf).pack(side="left")

        # 可調整寬度的分割視窗
        self.panes = tk.PanedWindow(self, orient="horizontal")
        self.panes.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        # 左側：欄位輸入
        left = ttk.LabelFrame(self.panes, text="欄位與文字")
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)
        self.fields_panel = ScrollableFields(left)
        self.fields_panel.grid(row=0, column=0, sticky="nswe")

        # 右側：預覽
        right = ttk.LabelFrame(self.panes, text="預覽（第一頁）")
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)
        self.preview_canvas = tk.Canvas(right, bg="#f3f3f3", highlightthickness=0)
        self.preview_canvas.grid(row=0, column=0, sticky="nsew")
        # 畫布項目與比例
        self._canvas_image_id = None
        self._canvas_rect_items = {}
        self._display_scale = 1.0
        # 綁定互動事件（在編輯模式時才會生效）
        self.preview_canvas.bind('<Button-1>', self._on_preview_click)
        self.preview_canvas.bind('<B1-Motion>', self._on_preview_drag)
        self.preview_canvas.bind('<ButtonRelease-1>', self._on_preview_release)
        self.bind('<KeyPress>', self._on_key_press)

        # 啟動時預設開啟簡易模式（可在此改為條件控制）
        self.after(300, self.open_quick_adjust)

        # 將左右加入 Pane，並設定最小寬度，預設給左側較寬以避免按鈕被擠掉
        self.panes.add(left, minsize=380)
        self.panes.add(right, minsize=480)
        self.after(150, self._init_sash_position)

    def _init_sash_position(self):
        # 設定初始分隔線位置（左側約 420px），使用 try 以避免平台差異
        try:
            self.panes.sash_place(0, 420, 1)
        except Exception:
            pass

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
            ttk.Button(self.fields_panel.interior, text="框", command=lambda k=key: self.open_rect_adjust(k)).grid(
                row=r, column=3, padx=2
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
            zoom = 1.5
            self._preview_zoom = zoom
            # 一律渲染完整預覽作為底圖（拖曳期間不會重算，只更新 Canvas 上的紅框）
            img = self._render_preview_with_overrides(values, zoom=zoom)
            # 將圖縮到視窗適配
            max_w, max_h = 800, 1000
            disp_scale = min(max_w / img.width, max_h / img.height, 1.0)
            self._display_scale = disp_scale
            if disp_scale < 1.0:
                img = img.resize((int(img.width * disp_scale), int(img.height * disp_scale)), Image.LANCZOS)
            self._tk_img = ImageTk.PhotoImage(img)
            if self._canvas_image_id is None:
                self._canvas_image_id = self.preview_canvas.create_image(0, 0, anchor='nw', image=self._tk_img)
            else:
                self.preview_canvas.itemconfig(self._canvas_image_id, image=self._tk_img)
            # 調整畫布大小
            self.preview_canvas.configure(width=img.width, height=img.height)
            # 更新螢幕座標並重畫紅框
            self._recompute_screen_rects()
            self._redraw_canvas_rectangles()
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
                # 套用紅框覆寫
                rect = self._apply_rect_override(key, rect)
                img = self._generate_image_with_overrides(key, str(text))
                if img:
                    # 套用欄位/全域縮放
                    scale_mult = self.field_overrides.get(key, {}).get('scale', 1.0) * self.global_scale.get()
                    img = self._apply_thickness_if_needed(key, img)
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
        ttk.Label(win, text="線條加粗 (0~3)：").grid(row=1, column=0, sticky='w', padx=8, pady=8)
        ttk.Spinbox(win, from_=0, to=3, textvariable=self.global_thick_steps, width=5).grid(row=1, column=1, padx=8)
        ttk.Label(win, text="額外縮放 (50%~150%)：").grid(row=2, column=0, sticky='w', padx=8, pady=8)
        scale_var = tk.DoubleVar(value=self.global_scale.get() * 100)
        def _apply_global():
            self.global_scale.set(max(0.5, min(1.5, scale_var.get()/100)))
            # 全域線寬/模糊無需轉換，直接保留 IntVar 值（0=沿用）
            win.destroy()
        ttk.Spinbox(win, from_=50, to=150, textvariable=scale_var, width=6).grid(row=2, column=1, padx=8)
        # 全域線寬
        ttk.Label(win, text="全域線寬 (0=沿用,1~5)：").grid(row=3, column=0, sticky='w', padx=8, pady=8)
        ttk.Spinbox(win, from_=0, to=5, textvariable=self.global_line_width, width=5).grid(row=3, column=1, padx=8)
        # 全域模糊
        ttk.Label(win, text="全域模糊 (0=沿用,0~6)：").grid(row=4, column=0, sticky='w', padx=8, pady=8)
        ttk.Spinbox(win, from_=0, to=6, textvariable=self.global_blur, width=5).grid(row=4, column=1, padx=8)
        ttk.Button(win, text="套用", command=_apply_global).grid(row=5, column=0, columnspan=2, pady=10)

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
        ttk.Combobox(win, textvariable=font_var, values=values, state='readonly').grid(row=0, column=1, padx=8, pady=6)
        # 縮放
        ttk.Label(win, text="額外縮放 (50%~150%)：").grid(row=1, column=0, sticky='w', padx=8, pady=6)
        scale_var = tk.DoubleVar(value=(ov.get('scale', 1.0) * 100))
        ttk.Spinbox(win, from_=50, to=150, textvariable=scale_var, width=6).grid(row=1, column=1, padx=8)
        # 細化/加粗
        ttk.Label(win, text="線條細化 (0~3)：").grid(row=2, column=0, sticky='w', padx=8, pady=6)
        thin_var = tk.IntVar(value=ov.get('thin', 0))
        ttk.Spinbox(win, from_=0, to=3, textvariable=thin_var, width=5).grid(row=2, column=1, padx=8)
        ttk.Label(win, text="線條加粗 (0~3)：").grid(row=3, column=0, sticky='w', padx=8, pady=6)
        thick_var = tk.IntVar(value=ov.get('thick', 0))
        ttk.Spinbox(win, from_=0, to=3, textvariable=thick_var, width=5).grid(row=3, column=1, padx=8)
        # 線寬（直接影響描邊寬度）
        ttk.Label(win, text="線寬 (1~5)：").grid(row=4, column=0, sticky='w', padx=8, pady=6)
        lw_var = tk.IntVar(value=ov.get('line_width', 0) or 0)
        ttk.Spinbox(win, from_=0, to=5, textvariable=lw_var, width=5).grid(row=4, column=1, padx=8)
        ttk.Label(win, text="(0 表示沿用全域/預設)").grid(row=4, column=2, sticky='w')
        # 模糊（影響整體柔化程度）
        ttk.Label(win, text="模糊 (0~6)：").grid(row=5, column=0, sticky='w', padx=8, pady=6)
        blur_var = tk.IntVar(value=ov.get('blur', 0) or 0)
        ttk.Spinbox(win, from_=0, to=6, textvariable=blur_var, width=5).grid(row=5, column=1, padx=8)
        # 顫抖/傾斜/隨機幅度
        ttk.Label(win, text="顫抖(0~15)：").grid(row=6, column=0, sticky='w', padx=8, pady=6)
        perturb_var = tk.IntVar(value=ov.get('perturb', 0))
        ttk.Spinbox(win, from_=0, to=15, textvariable=perturb_var, width=5).grid(row=6, column=1, padx=8)
        ttk.Label(win, text="傾斜角(-20~20)：").grid(row=7, column=0, sticky='w', padx=8, pady=6)
        shear_var = tk.IntVar(value=ov.get('shear', 0))
        ttk.Spinbox(win, from_=-20, to=20, textvariable=shear_var, width=6).grid(row=7, column=1, padx=8)
        ttk.Label(win, text="隨機幅度%(0~30)：").grid(row=8, column=0, sticky='w', padx=8, pady=6)
        randper_var = tk.IntVar(value=ov.get('random_per', 10))
        ttk.Spinbox(win, from_=0, to=30, textvariable=randper_var, width=6).grid(row=8, column=1, padx=8)
        # 隨機開關
        ttk.Label(win, text="手寫隨機化覆寫：").grid(row=9, column=0, sticky='w', padx=8, pady=6)
        rand_state = tk.StringVar(value={True: 'on', False: 'off', None: 'inherit'}.get(ov.get('random', None), 'inherit'))
        ttk.Combobox(win, textvariable=rand_state, values=['inherit', 'on', 'off'], state='readonly').grid(row=9, column=1, padx=8)
        # 顏色
        ttk.Label(win, text="筆跡顏色(RGB)：").grid(row=10, column=0, sticky='w', padx=8, pady=6)
        color_preview = tk.Label(win, text=str(ov.get('color') or ''), width=16, anchor='w')
        color_preview.grid(row=10, column=1, sticky='w', padx=8)
        def _pick_color():
            init = '#4169e1'
            if isinstance(ov.get('color'), (list, tuple)) and len(ov.get('color'))==3:
                init = '#%02x%02x%02x' % tuple(max(0,min(255,int(x))) for x in ov['color'])
            c = colorchooser.askcolor(color=init, title='選擇筆跡顏色')
            if c and c[0]:
                rgb = tuple(int(round(x)) for x in c[0])
                color_preview.config(text=str(rgb))
        ttk.Button(win, text="選色…", command=_pick_color).grid(row=10, column=2, padx=6)
        # 樣式預設
        ttk.Label(win, text="樣式預設：").grid(row=11, column=0, sticky='w', padx=8, pady=6)
        preset_var = tk.StringVar(value='inherit')
        ttk.Combobox(win, textvariable=preset_var, values=['inherit','工整細緻','日常手寫','粗獷隨性'], state='readonly').grid(row=11, column=1, padx=8)
        # 進階設定（完整 config 覆寫）
        ttk.Button(win, text="進階…", command=lambda: self.open_advanced_field(key, parent=win)).grid(row=12, column=0, padx=8, pady=8, sticky='w')

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
            thv = max(0, min(3, thick_var.get()))
            if thv:
                new_ov['thick'] = thv
            lw = max(0, min(5, int(lw_var.get())))
            if lw:
                new_ov['line_width'] = lw
            bl = max(0, min(6, int(blur_var.get())))
            if bl:
                new_ov['blur'] = bl
            pv = max(0, min(15, int(perturb_var.get())))
            if pv:
                new_ov['perturb'] = pv
            sh = max(-20, min(20, int(shear_var.get())))
            if sh:
                new_ov['shear'] = sh
            rp = max(0, min(30, int(randper_var.get())))
            if rp != 10:
                new_ov['random_per'] = rp
            rv = rand_state.get()
            if rv != 'inherit':
                new_ov['random'] = (rv == 'on')
            # 顏色
            if color_preview.cget('text'):
                try:
                    t = eval(color_preview.cget('text'))
                    if isinstance(t, (list, tuple)) and len(t)==3:
                        new_ov['color'] = tuple(int(max(0,min(255,int(x)))) for x in t)
                except Exception:
                    pass
            # 樣式預設合併
            def _preset_overrides(name:str):
                if name=='工整細緻':
                    return {'PERTURB':6,'SHEAR_ANGLE':10,'BLUR_AMOUNT':1.5,'LINE_WIDTH':1,'COLOR_VARIATION':10}
                if name=='日常手寫':
                    return {'PERTURB':12,'SHEAR_ANGLE':20,'BLUR_AMOUNT':1.8,'LINE_WIDTH':1,'COLOR_VARIATION':20}
                if name=='粗獷隨性':
                    return {'PERTURB':15,'SHEAR_ANGLE':22,'BLUR_AMOUNT':2.5,'LINE_WIDTH':2,'COLOR_VARIATION':40}
                return {}
            preset_name = preset_var.get()
            if preset_name and preset_name!='inherit':
                new_ov.setdefault('config_overrides', {})
                new_ov['config_overrides'].update(_preset_overrides(preset_name))
            # 保留既有的進階覆寫
            if 'config_overrides' in ov and isinstance(ov['config_overrides'], dict):
                new_ov['config_overrides'] = {**ov['config_overrides'], **new_ov.get('config_overrides', {})}
            self.field_overrides[key] = new_ov
            win.destroy()
        ttk.Button(win, text="儲存", command=_save).grid(row=13, column=0, columnspan=2, pady=10)

    # ====== 內部工具 ======
    def _apply_thickness_if_needed(self, key, img):
        thin = self.global_thin_steps.get() + int(self.field_overrides.get(key, {}).get('thin', 0))
        thick = self.global_thick_steps.get() + int(self.field_overrides.get(key, {}).get('thick', 0))
        net = max(-3, min(3, int(thick) - int(thin)))
        if net == 0:
            return img
        r, g, b, a = img.split()
        if net > 0:
            for _ in range(net):
                a = a.filter(ImageFilter.MaxFilter(3))
        else:
            for _ in range(-net):
                a = a.filter(ImageFilter.MinFilter(3))
        return Image.merge('RGBA', (r, g, b, a))

    def _generate_image_with_overrides(self, key, text):
        ov = self.field_overrides.get(key, {})
        # 欄位字型（當欄位層啟用時才採用）
        field_font = ov.get('font', None) if self.use_field_filter.get() else None
        font_path = field_font
        # 隨機化（欄位層啟用且有覆寫時採用，否則用全域勾選）
        rnd = ov.get('random', None) if self.use_field_filter.get() else None
        use_random = self.random_flag.get() if rnd is None else rnd
        overrides = {}
        # 先套用「報告層」覆寫（若啟用）
        if self.use_report_filter.get():
            if int(self.global_line_width.get()) > 0:
                overrides['LINE_WIDTH'] = int(self.global_line_width.get())
            if int(self.global_blur.get()) > 0:
                overrides['BLUR_AMOUNT'] = int(self.global_blur.get())
            if self.global_config_overrides:
                overrides.update(self.global_config_overrides)
        # 欄位覆寫（若啟用）優先於報告層
        if self.use_field_filter.get():
            if ov.get('line_width'):
                overrides['LINE_WIDTH'] = int(ov['line_width'])
            if ov.get('blur') is not None and ov.get('blur') != 0:
                overrides['BLUR_AMOUNT'] = int(ov['blur'])
            if ov.get('perturb') is not None and ov.get('perturb') != 0:
                overrides['PERTURB'] = int(ov['perturb'])
            if ov.get('shear') is not None and ov.get('shear') != 0:
                overrides['SHEAR_ANGLE'] = int(ov['shear'])
            if ov.get('color'):
                c = ov['color']
                if isinstance(c, (list, tuple)) and len(c) == 3:
                    overrides['COLOR_BASE'] = tuple(int(max(0, min(255, int(x)))) for x in c)
            if ov.get('config_overrides'):
                overrides.update(ov['config_overrides'])
        # 句子層：以 config.SESSION_RENDER_OVERRIDES 臨時覆寫（只在本次有效；若啟用）
        if self.use_sentence_filter.get() and getattr(self, 'session_char_overrides', None):
            overrides['SESSION_RENDER_OVERRIDES'] = dict(self.session_char_overrides)
        # 若停用單字層，則清空 SPECIAL_RENDER_OVERRIDES；若啟用則沿用
        if not self.use_char_filter.get():
            overrides['SPECIAL_RENDER_OVERRIDES'] = {}
        # 隨機化幅度（欄位覆寫若停用則以預設 10）
        rp = 10
        if self.use_field_filter.get() and ov.get('random_per') is not None:
            try:
                rp = int(ov.get('random_per', 10))
            except Exception:
                rp = 10
        # 字元路由：若欄位有指定字型，則忽略路由；若停用單字層，忽略路由；否則允許路由
        ignore_router_flag = False
        if field_font:
            ignore_router_flag = True
        if not self.use_char_filter.get():
            ignore_router_flag = True
        img = generate_text_image(
            text,
            font_path=font_path,
            ignore_router=ignore_router_flag,
            random=use_random,
            random_per=rp,
            overrides=overrides or None,
        )
        return img

    # ====== 句子層（本次渲染）覆寫 ======
    def open_session_overrides(self):
        # 只在記憶體中生效，不寫檔；支援四鍵：scale/offset_y/alpha/spacing（CTK 版）
        try:
            ctk.set_appearance_mode("dark")
        except Exception:
            pass
        win = ctk.CTkToplevel(self)
        win.title("本次覆寫（僅此回合）")
        frm = ctk.CTkFrame(win)
        frm.pack(fill='both', expand=True, padx=10, pady=10)
        # 預設清單（句子預設）
        presets = {}
        try:
            import Make_report_sign_easy.config as cfg
            p = os.path.join(cfg.BASE_DIR, 'configs', 'sentence_presets.json')
            if os.path.exists(p):
                with open(p, 'r', encoding='utf-8') as f:
                    presets = json.load(f) or {}
        except Exception:
            presets = {}
        row0 = ctk.CTkFrame(frm)
        row0.grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 8))
        ctk.CTkLabel(row0, text='載入句子預設：').pack(side='left')
        names = sorted(list(presets.keys())) if isinstance(presets, dict) else []
        preset_cb = ctk.CTkComboBox(row0, values=['']+names, width=220)
        preset_cb.pack(side='left', padx=6)

        # 現值（從 config 會話層讀不到，因為尚未套用；用自家暫存）
        cur = getattr(self, 'session_char_overrides', {}) if hasattr(self, 'session_char_overrides') else {}
        scale_v = tk.StringVar(value=str(cur.get('scale', '')))
        offy_v = tk.StringVar(value=str(cur.get('offset_y', '')))
        alpha_v = tk.StringVar(value=str(cur.get('alpha', '')))
        spacing_v = tk.StringVar(value=str(cur.get('spacing', '')))

        def add_row(r, label, var):
            ctk.CTkLabel(frm, text=label, width=80, anchor='e').grid(row=r, column=0, sticky='e', padx=6, pady=4)
            ctk.CTkEntry(frm, textvariable=var, width=120).grid(row=r, column=1, sticky='w')

        add_row(1, 'scale', scale_v)
        add_row(2, 'offset_y', offy_v)
        add_row(3, 'alpha', alpha_v)
        add_row(4, 'spacing', spacing_v)

        def _load_from_preset():
            name = (preset_cb.get() or '').strip()
            if not name or name not in presets:
                return
            d = presets.get(name) or {}

            def _get(k):
                v = d.get(k, '')
                return '' if v is None else str(v)
            scale_v.set(_get('scale'))
            offy_v.set(_get('offset_y'))
            alpha_v.set(_get('alpha'))
            spacing_v.set(_get('spacing'))

        ctk.CTkButton(row0, text='載入', command=_load_from_preset).pack(side='left')

        btns = ctk.CTkFrame(frm)
        btns.grid(row=5, column=0, columnspan=2, pady=8)

        def _parse_float(s):
            try:
                return float(s)
            except Exception:
                return None

        def _parse_int(s):
            try:
                return int(float(s))
            except Exception:
                return None

        def _apply():
            newv = {}
            sv = _parse_float(scale_v.get().strip())
            if sv is not None:
                newv['scale'] = sv
            oy = _parse_float(offy_v.get().strip())
            if oy is not None:
                newv['offset_y'] = oy
            al = _parse_int(alpha_v.get().strip())
            if al is not None:
                newv['alpha'] = max(0, min(255, al))
            sp = _parse_int(spacing_v.get().strip())
            if sp is not None:
                newv['spacing'] = sp
            self.session_char_overrides = newv
            win.destroy()
            self.update_preview()

        def _clear():
            self.session_char_overrides = {}
            win.destroy()
            self.update_preview()

        ctk.CTkButton(btns, text='套用', command=_apply).pack(side='left', padx=6)
        ctk.CTkButton(btns, text='清除', command=_clear).pack(side='left', padx=6)

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

    # ====== 簡易模式（快速調整） ======
    def open_quick_adjust(self):
        # 以 CTK 風格開啟「簡易模式」視窗
        try:
            ctk.set_appearance_mode("dark")
        except Exception:
            pass
        win = ctk.CTkToplevel(self)
        win.title("簡易模式：快速調整")
        frm = ctk.CTkFrame(win)
        frm.pack(fill='both', expand=True, padx=10, pady=10)
        # 預設清單
        presets = {}
        try:
            import Make_report_sign_easy.config as cfg
            p = os.path.join(cfg.BASE_DIR, 'configs', 'sentence_presets.json')
            if os.path.exists(p):
                with open(p, 'r', encoding='utf-8') as f:
                    presets = json.load(f) or {}
        except Exception:
            presets = {}
        ctk.CTkLabel(frm, text='預設：').grid(row=0, column=0, sticky='e', padx=4, pady=4)
        names = sorted(list(presets.keys())) if isinstance(presets, dict) else []
        preset_cb = ctk.CTkComboBox(frm, values=[''] + names, width=220)
        preset_cb.grid(row=0, column=1, sticky='w')
        def _load():
            name = (preset_cb.get() or '').strip()
            if not name or name not in presets:
                return
            d = presets.get(name) or {}
            sv = d.get('scale', None)
            if sv is not None:
                scale_v.set(float(sv))
            spv = d.get('spacing', None)
            if spv is not None:
                spacing_v.set(int(spv))
            _apply(live=True)
        ctk.CTkButton(frm, text='載入', command=_load).grid(row=0, column=2, sticky='w', padx=6)

        # 分隔線
        sep = ctk.CTkFrame(frm, height=1)
        sep.grid(row=1, column=0, columnspan=3, sticky='ew', pady=(6, 8))
        frm.grid_columnconfigure(1, weight=1)

        scale_v = tk.DoubleVar(value=float(self.session_char_overrides.get('scale', 1.0)))
        spacing_v = tk.IntVar(value=int(self.session_char_overrides.get('spacing', 0)))
        live_v = tk.BooleanVar(value=True)

        ctk.CTkLabel(frm, text='scale').grid(row=2, column=0, sticky='e', padx=4, pady=6)
        s1 = ctk.CTkSlider(frm, from_=0.5, to=1.5, number_of_steps=100)
        s1.set(scale_v.get())
        s1.grid(row=2, column=1, sticky='we', padx=4)
        ctk.CTkLabel(frm, text='').grid(row=2, column=2)  # 占位

        ctk.CTkLabel(frm, text='spacing').grid(row=3, column=0, sticky='e', padx=4, pady=6)
        s2 = ctk.CTkSlider(frm, from_=-20, to=40, number_of_steps=60)
        s2.set(spacing_v.get())
        s2.grid(row=3, column=1, sticky='we', padx=4)
        ctk.CTkCheckBox(frm, text='即時預覽', variable=live_v).grid(row=3, column=2, sticky='w')

        def _apply(live=False):
            vals = {}
            sv = float(s1.get())
            if abs(sv - 1.0) > 1e-6:
                vals['scale'] = sv
            sp = int(round(float(s2.get())))
            if sp != 0:
                vals['spacing'] = sp
            self.session_char_overrides = vals
            if live or live_v.get():
                self.update_preview()

        s1.configure(command=lambda v: _apply(live=True))
        s2.configure(command=lambda v: _apply(live=True))

        btns = ctk.CTkFrame(frm)
        btns.grid(row=4, column=0, columnspan=3, pady=(8, 0))
        ctk.CTkButton(btns, text='套用', command=_apply).pack(side='left', padx=6)
        ctk.CTkButton(btns, text='關閉', command=win.destroy).pack(side='left', padx=6)

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

    # ====== 篩選器（層級開關） ======
    def open_filter_pipeline(self):
        try:
            ctk.set_appearance_mode("dark")
        except Exception:
            pass
        win = ctk.CTkToplevel(self)
        win.title("篩選器：層級開關")
        frm = ctk.CTkFrame(win)
        frm.pack(fill='both', expand=True, padx=10, pady=10)
        ctk.CTkLabel(
            frm,
            text='渲染流程依優先序套用下列層級，未命中則自動回退到下一層：',
            anchor='w',
        ).grid(row=0, column=0, columnspan=2, sticky='w')
        ctk.CTkCheckBox(
            frm,
            text='單字篩選器（字路由／單字屬性）',
            variable=self.use_char_filter,
        ).grid(row=1, column=0, sticky='w', pady=2)
        ctk.CTkCheckBox(
            frm,
            text='句子篩選器（本次覆寫）',
            variable=self.use_sentence_filter,
        ).grid(row=2, column=0, sticky='w', pady=2)
        ctk.CTkCheckBox(
            frm,
            text='欄位篩選器（欄位覆寫）',
            variable=self.use_field_filter,
        ).grid(row=3, column=0, sticky='w', pady=2)
        ctk.CTkCheckBox(
            frm,
            text='報告篩選器（全域/進階）',
            variable=self.use_report_filter,
        ).grid(row=4, column=0, sticky='w', pady=2)
        hint = (
            """說明:
 - 單字: 使用字路由(font_routes)與 SPECIAL_RENDER_OVERRIDES。
 - 句子: 使用「本次覆寫」的四鍵(scale/offset_y/alpha/spacing)。
 - 欄位: 使用每個欄位的字型/線寬/模糊/顏色/進階覆寫與 scale。
 - 報告: 使用全域線寬/模糊以及「進階設定(全域)」。
 未命中時會自動落回下一層，最後落到全域預設。"""
        )
        ctk.CTkLabel(frm, text=hint, justify='left', anchor='w').grid(row=5, column=0, sticky='w', pady=(6, 8))
        btns = ctk.CTkFrame(frm)
        btns.grid(row=6, column=0, sticky='w')
        ctk.CTkButton(btns, text='套用', command=lambda: (win.destroy(), self.update_preview())).pack(side='left', padx=4)
        ctk.CTkButton(btns, text='關閉', command=win.destroy).pack(side='left', padx=4)

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
        self._screen_rects = {}
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
            rect = self._apply_rect_override(key, rect)
            img = self._generate_image_with_overrides(key, str(text))
            if not img:
                continue
            # 細化與縮放
            img = self._apply_thickness_if_needed(key, img)
            # 欄位 scale 僅在欄位篩選器啟用時生效
            field_scale = self.field_overrides.get(key, {}).get('scale', 1.0) if self.use_field_filter.get() else 1.0
            scale_mult = field_scale * self.global_scale.get()
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

    def _render_base_page(self, zoom=1.5):
        doc = fitz.open(self.pdf_path)
        page = doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        base = Image.frombytes("RGB", [pix.width, pix.height], pix.samples).convert('RGBA')
        doc.close()
        return base

    def _recompute_screen_rects(self):
        # 根據 pos_map 與覆寫，計算目前畫面座標（考慮 zoom 與 display_scale）
        z = self._preview_zoom or 1.5
        s = self._display_scale or 1.0
        rects = {}
        for key, rect in self.pos_map.items():
            if rect is None:
                continue
            r = self._apply_rect_override(key, rect)
            x0 = int(r.x0 * z * s)
            y0 = int(r.y0 * z * s)
            x1 = int(r.x1 * z * s)
            y1 = int(r.y1 * z * s)
            rects[key] = (x0, y0, x1, y1)
        self._screen_rects = rects

    def _redraw_canvas_rectangles(self):
        # 無需顯示時清空
        if not (self.show_boxes.get() or self.edit_boxes.get()):
            self._clear_canvas_rectangles()
            return
        # 更新或建立每個矩形
        existing_keys = set(self._canvas_rect_items.keys())
        for key, coords in self._screen_rects.items():
            color = '#ff4040' if key == self.active_field else '#ff0000'
            width = 3 if key == self.active_field else 2
            if key in self._canvas_rect_items:
                rid = self._canvas_rect_items[key]
                self.preview_canvas.coords(rid, *coords)
                self.preview_canvas.itemconfig(rid, outline=color, width=width)
            else:
                rid = self.preview_canvas.create_rectangle(*coords, outline=color, width=width)
                self._canvas_rect_items[key] = rid
        # 刪除多餘項
        for k in list(existing_keys - set(self._screen_rects.keys())):
            try:
                self.preview_canvas.delete(self._canvas_rect_items[k])
            except Exception:
                pass
            self._canvas_rect_items.pop(k, None)

    def _clear_canvas_rectangles(self):
        for rid in self._canvas_rect_items.values():
            try:
                self.preview_canvas.delete(rid)
            except Exception:
                pass
        self._canvas_rect_items.clear()

    def _get_screen_rect_for_key(self, key):
        z = self._preview_zoom or 1.5
        s = self._display_scale or 1.0
        base_rect = self._get_base_rect_for_key(key) or self.pos_map.get(key)
        if base_rect is None:
            return None
        r = self._apply_rect_override(key, base_rect)
        return (int(r.x0 * z * s), int(r.y0 * z * s), int(r.x1 * z * s), int(r.y1 * z * s))

    def _update_canvas_rect_for_key(self, key):
        coords = self._get_screen_rect_for_key(key)
        if not coords:
            return
        self._screen_rects[key] = coords
        color = '#ff4040' if key == self.active_field else '#ff0000'
        width = 3 if key == self.active_field else 2
        if key in self._canvas_rect_items:
            rid = self._canvas_rect_items[key]
            self.preview_canvas.coords(rid, *coords)
            self.preview_canvas.itemconfig(rid, outline=color, width=width)
        else:
            rid = self.preview_canvas.create_rectangle(*coords, outline=color, width=width)
            self._canvas_rect_items[key] = rid

    # ====== 預覽互動：選取/拖曳/鍵盤微調 ======
    def _toggle_edit_mode(self):
        # 清理拖曳狀態並更新預覽
        self._drag_state = None
        self.update_preview()

    def _hit_test(self, x, y):
        # 回傳 (key, mode, edges)；mode 為 'move' 或 'resize'，edges 例如 ('left','top')
        # 優先檢測邊/角，再檢測內部
        threshold = 8
        for key, (x0, y0, x1, y1) in self._screen_rects.items():
            # 邊界檢測
            near_left = abs(x - x0) <= threshold and y0 - threshold <= y <= y1 + threshold
            near_right = abs(x - x1) <= threshold and y0 - threshold <= y <= y1 + threshold
            near_top = abs(y - y0) <= threshold and x0 - threshold <= x <= x1 + threshold
            near_bottom = abs(y - y1) <= threshold and x0 - threshold <= x <= x1 + threshold
            edges = []
            if near_left:
                edges.append('left')
            if near_right:
                edges.append('right')
            if near_top:
                edges.append('top')
            if near_bottom:
                edges.append('bottom')
            if edges:
                return key, 'resize', tuple(edges)
            # 內部
            if x0 <= x <= x1 and y0 <= y <= y1:
                return key, 'move', ()
        return None, None, None

    def _on_preview_click(self, event):
        if not self.edit_boxes.get():
            return
        key, mode, edges = self._hit_test(event.x, event.y)
        if not key:
            self.active_field = None
            self._drag_state = None
            self._redraw_canvas_rectangles()
            return
        self.active_field = key
        # 記錄起始狀態
        base_rect = self._get_base_rect_for_key(key)
        start_rect = self._apply_rect_override(key, base_rect)
        self._drag_state = {
            'key': key,
            'mode': mode or 'move',
            'edges': edges or (),
            'start_mouse': (event.x, event.y),
            'start_rect': start_rect,
            'base_rect': base_rect,
        }
        self._redraw_canvas_rectangles()

    def _on_preview_drag(self, event):
        if not self.edit_boxes.get() or not self._drag_state:
            return
        ds = self._drag_state
        key = ds['key']
        zoom = self._preview_zoom or 1.5
        disp = self._display_scale or 1.0
        dx_px = event.x - ds['start_mouse'][0]
        dy_px = event.y - ds['start_mouse'][1]
        dx = dx_px / (zoom * disp)
        dy = dy_px / (zoom * disp)
        new_rect = fitz.Rect(ds['start_rect'])
        if ds['mode'] == 'move':
            new_rect.x0 += dx
            new_rect.x1 += dx
            new_rect.y0 += dy
            new_rect.y1 += dy
        else:
            # resize by edges
            if 'left' in ds['edges']:
                new_rect.x0 += dx
            if 'right' in ds['edges']:
                new_rect.x1 += dx
            if 'top' in ds['edges']:
                new_rect.y0 += dy
            if 'bottom' in ds['edges']:
                new_rect.y1 += dy
        # 轉成 overrides 並套用，並更新單一矩形外觀
        ov = self._overrides_from_rect(ds['base_rect'], new_rect)
        self.rect_overrides[key] = ov
        self._update_canvas_rect_for_key(key)

    def _on_preview_release(self, event):
        if not self.edit_boxes.get():
            return
        self._drag_state = None

    def _on_key_press(self, event):
        if not self.edit_boxes.get() or not self.active_field:
            return
        step = int(self.nudge_step.get() or 2)  # 預設每次 2pt，可在工具列調整
        key = self.active_field
        base_rect = self._get_base_rect_for_key(key)
        cur_rect = self._apply_rect_override(key, base_rect)
        resize = (event.state & 0x0004) != 0  # Ctrl 進行 resize，否則 move
        if event.keysym in ('Left', 'Right', 'Up', 'Down'):
            dx = (-step if event.keysym == 'Left' else step if event.keysym == 'Right' else 0)
            dy = (-step if event.keysym == 'Up' else step if event.keysym == 'Down' else 0)
            new_rect = fitz.Rect(cur_rect)
            if not resize:
                new_rect.x0 += dx
                new_rect.x1 += dx
                new_rect.y0 += dy
                new_rect.y1 += dy
            else:
                # Ctrl+Arrow：只改一個對應邊
                if event.keysym == 'Left':
                    new_rect.x0 += dx
                elif event.keysym == 'Right':
                    new_rect.x1 += dx
                elif event.keysym == 'Up':
                    new_rect.y0 += dy
                elif event.keysym == 'Down':
                    new_rect.y1 += dy
            self.rect_overrides[key] = self._overrides_from_rect(base_rect, new_rect)
            self._update_canvas_rect_for_key(key)

    def _get_base_rect_for_key(self, key):
        # 從 PDF 註解或 pos_map 取得原始 rect
        if self.pdf_path:
            try:
                doc = fitz.open(self.pdf_path)
                page = doc[0]
                for annot in page.annots() or []:
                    if annot.type[1] == "FreeText" and annot.info.get("content", "").strip() == key:
                        r = fitz.Rect(annot.rect)
                        doc.close()
                        return r
                doc.close()
            except Exception:
                pass
        return self.pos_map.get(key)

    def _overrides_from_rect(self, base_rect, new_rect):
        # 根據 base_rect 與 new_rect 計算四邊覆寫值（對應 _apply_rect_override 的反向）
        if base_rect is None or new_rect is None:
            return {'left': 0, 'right': 0, 'top': 0, 'bottom': 0}
        left = base_rect.x0 - new_rect.x0
        right = new_rect.x1 - base_rect.x1
        top = base_rect.y0 - new_rect.y0
        bottom = new_rect.y1 - base_rect.y1
        return {
            'left': int(round(left)),
            'right': int(round(right)),
            'top': int(round(top)),
            'bottom': int(round(bottom)),
        }

    # ====== 紅框覆寫 ======
    def open_rect_adjust(self, key):
        # 提供以 PDF 點數調整四邊的對話框
        win = tk.Toplevel(self)
        win.title(f"調整紅框 - {key}")
        # 取得原始 rect
        base_rect = self.pos_map.get(key)
        if base_rect is None:
            # 嘗試從 PDF 中再找一次（避免使用者先載入後動過）
            try:
                if self.pdf_path:
                    doc = fitz.open(self.pdf_path)
                    page = doc[0]
                    for annot in page.annots() or []:
                        if annot.type[1] == "FreeText" and annot.info.get("content", "").strip() == key:
                            base_rect = fitz.Rect(annot.rect)
                            break
                    doc.close()
            except Exception:
                base_rect = None
        if base_rect is None:
            ttk.Label(win, text="找不到原始紅框，請先讀取欄位").grid(row=0, column=0, padx=10, pady=10)
            return

        ov = self.rect_overrides.get(key, {})
        left_var = tk.IntVar(value=int(ov.get('left', 0)))
        right_var = tk.IntVar(value=int(ov.get('right', 0)))
        top_var = tk.IntVar(value=int(ov.get('top', 0)))
        bottom_var = tk.IntVar(value=int(ov.get('bottom', 0)))

        # 顯示目前尺寸資訊
        info = ttk.Label(win, text=f"原始尺寸: {int(base_rect.width)}x{int(base_rect.height)} pt")
        info.grid(row=0, column=0, columnspan=3, sticky='w', padx=10, pady=8)

        ttk.Label(win, text="左(+擴大/−縮小)").grid(row=1, column=0, sticky='e', padx=8, pady=6)
        ttk.Spinbox(win, from_=-100, to=100, textvariable=left_var, width=6).grid(row=1, column=1, padx=8)
        ttk.Label(win, text="pt").grid(row=1, column=2, sticky='w')

        ttk.Label(win, text="右(+擴大/−縮小)").grid(row=2, column=0, sticky='e', padx=8, pady=6)
        ttk.Spinbox(win, from_=-100, to=100, textvariable=right_var, width=6).grid(row=2, column=1, padx=8)
        ttk.Label(win, text="pt").grid(row=2, column=2, sticky='w')

        ttk.Label(win, text="上(+擴大/−縮小)").grid(row=3, column=0, sticky='e', padx=8, pady=6)
        ttk.Spinbox(win, from_=-100, to=100, textvariable=top_var, width=6).grid(row=3, column=1, padx=8)
        ttk.Label(win, text="pt").grid(row=3, column=2, sticky='w')

        ttk.Label(win, text="下(+擴大/−縮小)").grid(row=4, column=0, sticky='e', padx=8, pady=6)
        ttk.Spinbox(win, from_=-100, to=100, textvariable=bottom_var, width=6).grid(row=4, column=1, padx=8)
        ttk.Label(win, text="pt").grid(row=4, column=2, sticky='w')

        def _apply():
            ov = {
                'left': int(left_var.get()),
                'right': int(right_var.get()),
                'top': int(top_var.get()),
                'bottom': int(bottom_var.get()),
            }
            self.rect_overrides[key] = ov
            self.update_preview()
            win.destroy()

        def _reset():
            if key in self.rect_overrides:
                del self.rect_overrides[key]
            self.update_preview()
            win.destroy()

        btns = ttk.Frame(win)
        btns.grid(row=5, column=0, columnspan=3, pady=10)
        ttk.Button(btns, text="套用", command=_apply).pack(side='left', padx=6)
        ttk.Button(btns, text="重設", command=_reset).pack(side='left', padx=6)
        ttk.Button(btns, text="關閉", command=win.destroy).pack(side='left', padx=6)

    def _apply_rect_override(self, key, rect):
        """將 rect 依欄位的覆寫（左右上下延伸/縮小，單位 pt）調整後回傳新 rect。"""
        if rect is None:
            return None
        ov = self.rect_overrides.get(key)
        if not ov:
            return rect
        try:
            left = int(ov.get('left', 0))
            right = int(ov.get('right', 0))
            top = int(ov.get('top', 0))
            bottom = int(ov.get('bottom', 0))
        except Exception:
            return rect
        # 注意：左/上為負向座標方向（向左/上擴大），因此 x0 減 left, y0 減 top
        new_rect = fitz.Rect(rect.x0 - left, rect.y0 - top, rect.x1 + right, rect.y1 + bottom)
        # 確保最小尺寸
        min_size = 1.0
        if new_rect.width < min_size:
            cx = (rect.x0 + rect.x1) / 2.0
            new_rect.x0 = cx - min_size / 2.0
            new_rect.x1 = cx + min_size / 2.0
        if new_rect.height < min_size:
            cy = (rect.y0 + rect.y1) / 2.0
            new_rect.y0 = cy - min_size / 2.0
            new_rect.y1 = cy + min_size / 2.0
        return new_rect


def main():
    app = PDFFillGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
