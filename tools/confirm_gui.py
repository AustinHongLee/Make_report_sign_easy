import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

# src layout優先
import sys
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
src_root = os.path.join(repo_root, "src")
if os.path.isdir(src_root):
    sys.path.insert(0, src_root)
sys.path.insert(0, repo_root)

from Make_report_sign_easy.builder import generate_text_image
from Make_report_sign_easy import config
from Make_report_sign_easy.utils import sanitize_filename_char
from Make_report_sign_easy.safe_char_map import REVERSE_SAFE_CHAR_MAP


class ConfirmManager(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.confirm_dir = os.path.join(config.BASE_DIR, "confirm")
        os.makedirs(self.confirm_dir, exist_ok=True)
        self.font_dir = config.FONTS_DIR or os.path.join(config.BASE_DIR, "fonts")

        self._thumb_cache = {}  # (char,font)->PhotoImage
        self._candidates = []   # [(font_file, image)] for current char
        self._var_checks = {}   # font_file -> tk.BooleanVar
        self._current_char = None

        self._build_ui()

    def _build_ui(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        # Tab 1: 挑選
        pick_tab = ttk.Frame(nb)
        nb.add(pick_tab, text="挑選")

        top = ttk.Frame(pick_tab)
        top.pack(side="top", fill="x", padx=8, pady=8)
        ttk.Label(top, text="字元：").pack(side="left")
        self.char_var = tk.StringVar(value="7")
        ttk.Entry(top, textvariable=self.char_var, width=6).pack(side="left")
        ttk.Button(top, text="生成候選", command=self.load_candidates).pack(side="left", padx=6)
        ttk.Button(top, text="全選", command=lambda: self._set_all_checks(True)).pack(side="left")
        ttk.Button(top, text="全不選", command=lambda: self._set_all_checks(False)).pack(side="left")
        ttk.Button(top, text="匯入所選", command=self.import_selected).pack(side="left", padx=6)
        ttk.Button(top, text="更新路由", command=self.update_router_from_confirm).pack(side="left")
        ttk.Button(top, text="屬性", command=self.open_char_attributes).pack(side="left", padx=6)
        ttk.Button(top, text="說明", command=self.show_help).pack(side="left", padx=6)

        self.cand_canvas = tk.Canvas(pick_tab, borderwidth=0, highlightthickness=0)
        self.cand_scroll = ttk.Scrollbar(pick_tab, orient="vertical", command=self.cand_canvas.yview)
        self.cand_inner = ttk.Frame(self.cand_canvas)
        self.cand_inner.bind("<Configure>", lambda e: self.cand_canvas.configure(scrollregion=self.cand_canvas.bbox("all")))
        self.cand_canvas.create_window((0, 0), window=self.cand_inner, anchor="nw")
        self.cand_canvas.configure(yscrollcommand=self.cand_scroll.set)
        self.cand_canvas.pack(side="left", fill="both", expand=True)
        self.cand_scroll.pack(side="right", fill="y")

        # Tab 2: 已確認
        confirmed_tab = ttk.Frame(nb)
        nb.add(confirmed_tab, text="已確認")

        ctop = ttk.Frame(confirmed_tab)
        ctop.pack(side="top", fill="x", padx=8, pady=8)
        ttk.Button(ctop, text="重新整理", command=self.refresh_confirmed).pack(side="left")
        ttk.Button(ctop, text="移除所選", command=self.remove_selected_confirm).pack(side="left", padx=6)

        self.confirm_canvas = tk.Canvas(confirmed_tab, borderwidth=0, highlightthickness=0)
        self.confirm_scroll = ttk.Scrollbar(confirmed_tab, orient="vertical", command=self.confirm_canvas.yview)
        self.confirm_inner = ttk.Frame(self.confirm_canvas)
        self.confirm_inner.bind("<Configure>", lambda e: self.confirm_canvas.configure(scrollregion=self.confirm_canvas.bbox("all")))
        self.confirm_canvas.create_window((0, 0), window=self.confirm_inner, anchor="nw")
        self.confirm_canvas.configure(yscrollcommand=self.confirm_scroll.set)
        self.confirm_canvas.pack(side="left", fill="both", expand=True)
        self.confirm_scroll.pack(side="right", fill="y")

        self.refresh_confirmed()

        # Tab 3: 句子預設（持久化的句子級風格）
        preset_tab = ttk.Frame(nb)
        nb.add(preset_tab, text="句子預設")
        self._build_sentence_preset_tab(preset_tab)

    def load_candidates(self):
        text = self.char_var.get().strip()
        if not text:
            messagebox.showwarning("提示", "請輸入要預覽的字元（建議單一字元）")
            return
        if len(text) != 1:
            messagebox.showwarning("提示", "目前建議一次挑選一個字元。請輸入單一字元。")
            return
        ch = text
        self._current_char = ch
        for w in self.cand_inner.winfo_children():
            w.destroy()
        self._var_checks.clear()
        self._candidates.clear()

        # 產生每個字型的縮圖
        fonts = []
        try:
            fonts = [f for f in os.listdir(self.font_dir) if f.lower().endswith(".ttf")]
        except Exception:
            pass
        fonts.sort()
        row = 0
        col = 0
        max_cols = 3
        thumbs = []
        for f in fonts:
            font_path = os.path.join(self.font_dir, f)
            try:
                img = generate_text_image(ch, font_path=font_path, random=True)
            except Exception:
                img = None
            if not img:
                continue
            # 縮成縮圖
            scale = 180 / max(img.width, img.height)
            scale = max(0.1, min(1.0, scale))
            thumb = img.resize((int(img.width * scale), int(img.height * scale)))
            ph = ImageTk.PhotoImage(thumb)
            thumbs.append(ph)  # keep ref

            frame = ttk.Frame(self.cand_inner, padding=6)
            frame.grid(row=row, column=col, sticky="nw")
            ttk.Label(frame, image=ph).pack()
            ttk.Label(frame, text=f, width=36).pack(anchor="w")
            var = tk.BooleanVar(value=False)
            self._var_checks[f] = var
            ttk.Checkbutton(frame, text="選取", variable=var).pack(anchor="w")

            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        # 保存對象避免被回收
        self._thumb_cache[(ch, "batch")] = thumbs

    def _set_all_checks(self, val: bool):
        for v in self._var_checks.values():
            v.set(val)

    def import_selected(self):
        if not self._current_char:
            messagebox.showwarning("提示", "請先生成候選並選字")
            return
        ch = self._current_char
        safe = sanitize_filename_char(ch)
        count = 0
        for font_file, var in self._var_checks.items():
            if not var.get():
                continue
            # 建立一個佔位 png（實際上 import 腳本只看檔名即可）
            name = f"{safe}_{font_file}.png"
            dest = os.path.join(self.confirm_dir, name)
            try:
                if not os.path.exists(dest):
                    # 生成縮圖存進去，方便人眼檢查
                    img = generate_text_image(ch, font_path=os.path.join(self.font_dir, font_file), random=False)
                    if img:
                        img.save(dest)
                    else:
                        # fallback 空白檔
                        open(dest, 'wb').close()
                count += 1
            except Exception as e:
                messagebox.showerror("錯誤", f"匯入 {font_file} 失敗：{e}")
                return
        if count:
            messagebox.showinfo("完成", f"已寫入 {count} 筆到 confirm/，請點『更新路由』套用。")
            self.refresh_confirmed()
        else:
            messagebox.showinfo("提示", "沒有選取任何候選。")

    def update_router_from_confirm(self):
        # 依 import_confirmed_previews.py 的邏輯，掃描 confirm 檔名回寫 router JSON
        router_path = os.path.join(config.BASE_DIR, "configs", "font_routes_template.json")
        try:
            if os.path.exists(router_path):
                import json
                with open(router_path, 'r', encoding='utf-8') as f:
                    router = json.load(f)
            else:
                router = {}
            added = 0
            for file in os.listdir(self.confirm_dir):
                if not file.endswith(".ttf.png"):
                    continue
                try:
                    safe_char, font_with_ext = file.split("_", 1)
                    ch = REVERSE_SAFE_CHAR_MAP.get(safe_char, None)
                    if ch is None and safe_char.startswith("U") and len(safe_char) == 5:
                        try:
                            ch = chr(int(safe_char[1:], 16))
                        except Exception:
                            ch = safe_char
                    font_name = font_with_ext.replace(".png", "")
                    router[ch] = os.path.join("fonts", font_name).replace("\\", "/")
                    added += 1
                except Exception:
                    pass
            with open(router_path, 'w', encoding='utf-8') as f:
                import json
                json.dump(router, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("完成", f"已更新路由，共 {added} 筆。重新預覽即可生效。")
        except Exception as e:
            messagebox.showerror("錯誤", str(e))

    def refresh_confirmed(self):
        for w in self.confirm_inner.winfo_children():
            w.destroy()
        files = []
        try:
            files = [f for f in os.listdir(self.confirm_dir) if f.endswith('.png')]
        except Exception:
            pass
        files.sort()
        self._confirmed_checks = {}
        row = 0
        col = 0
        max_cols = 3
        thumbs = []
        for f in files:
            p = os.path.join(self.confirm_dir, f)
            try:
                img = Image.open(p).convert('RGBA')
                scale = 160 / max(img.width, img.height)
                scale = max(0.1, min(1.0, scale))
                thumb = img.resize((int(img.width * scale), int(img.height * scale)))
                ph = ImageTk.PhotoImage(thumb)
                thumbs.append(ph)
            except Exception:
                ph = None
            frame = ttk.Frame(self.confirm_inner, padding=6)
            frame.grid(row=row, column=col, sticky="nw")
            if ph:
                ttk.Label(frame, image=ph).pack()
            ttk.Label(frame, text=f, width=40).pack(anchor='w')
            var = tk.BooleanVar(value=False)
            self._confirmed_checks[f] = var
            ttk.Checkbutton(frame, text="選取", variable=var).pack(anchor='w')
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        self._thumb_cache[("confirmed", "batch")] = thumbs

    def remove_selected_confirm(self):
        to_remove = [fn for fn, var in self._confirmed_checks.items() if var.get()]
        if not to_remove:
            messagebox.showinfo("提示", "未選取任何檔案")
            return
        # 移除檔案並同步移除 router 內對應 mapping（如果目前正好指向該字型）
        router_path = os.path.join(config.BASE_DIR, "configs", "font_routes_template.json")
        import json
        if os.path.exists(router_path):
            with open(router_path, 'r', encoding='utf-8') as f:
                router = json.load(f)
        else:
            router = {}
        removed = 0
        for fn in to_remove:
            try:
                safe_char, font_with_ext = fn.split("_", 1)
                ch = REVERSE_SAFE_CHAR_MAP.get(safe_char, None)
                if ch is None and safe_char.startswith("U") and len(safe_char) == 5:
                    try:
                        ch = chr(int(safe_char[1:], 16))
                    except Exception:
                        ch = safe_char
                font_name = font_with_ext.replace('.png', '')
                # 若 router 對該字元的 mapping 正好等於此字型，就刪除
                target = os.path.join('fonts', font_name).replace("\\", "/")
                if router.get(ch) == target:
                    router.pop(ch, None)
                # 刪除檔案
                os.remove(os.path.join(self.confirm_dir, fn))
                removed += 1
            except Exception:
                pass
        with open(router_path, 'w', encoding='utf-8') as f:
            json.dump(router, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("完成", f"已移除 {removed} 筆並更新路由")
        self.refresh_confirmed()

    # ====== 句子預設 CRUD ======
    def _build_sentence_preset_tab(self, tab):
        top = ttk.Frame(tab)
        top.pack(side='top', fill='x', padx=8, pady=8)
        ttk.Label(top, text='名稱：').pack(side='left')
        self.preset_name = tk.StringVar()
        ttk.Entry(top, textvariable=self.preset_name, width=24).pack(side='left', padx=6)
        ttk.Button(top, text='新增/更新', command=self._save_sentence_preset).pack(side='left', padx=4)
        ttk.Button(top, text='刪除', command=self._delete_sentence_preset).pack(side='left', padx=4)
        ttk.Button(top, text='重新整理', command=self._refresh_sentence_presets).pack(side='left', padx=4)

        # 句子候選（與『挑選』概念相同，僅對整句）
        row_sentence = ttk.Frame(tab)
        row_sentence.pack(side='top', fill='x', padx=8)
        ttk.Label(row_sentence, text='句子：').pack(side='left')
        self.sent_text = tk.StringVar()
        ttk.Entry(row_sentence, textvariable=self.sent_text, width=40).pack(side='left', padx=6)
        ttk.Button(row_sentence, text='生成候選', command=self._load_sentence_candidates).pack(side='left')

        body = ttk.Frame(tab)
        body.pack(fill='both', expand=True, padx=8, pady=8)
        # 左側清單
        left = ttk.Frame(body)
        left.pack(side='left', fill='y')
        self.preset_list = tk.Listbox(left, height=16)
        self.preset_list.pack(side='left', fill='y')
        self.preset_list.bind('<<ListboxSelect>>', self._on_select_preset)
        sb = ttk.Scrollbar(left, orient='vertical', command=self.preset_list.yview)
        self.preset_list.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        # 右側編輯
        right = ttk.Frame(body)
        right.pack(side='left', fill='both', expand=True, padx=12)
        # 欄位集合
        self.sp_scale = tk.StringVar()
        self.sp_offy = tk.StringVar()
        self.sp_alpha = tk.StringVar()
        self.sp_spacing = tk.StringVar()
        self.sp_lw = tk.StringVar()
        self.sp_blur = tk.StringVar()
        self.sp_perturb = tk.StringVar()
        self.sp_shear = tk.StringVar()
        self.sp_color = tk.StringVar()
        self.sp_font = tk.StringVar()

        def row(r, label, var, width=12):
            ttk.Label(right, text=label, width=12).grid(row=r, column=0, sticky='e', pady=3)
            ttk.Entry(right, textvariable=var, width=width).grid(row=r, column=1, sticky='w')

        row(0, 'scale', self.sp_scale)
        row(1, 'offset_y', self.sp_offy)
        row(2, 'alpha', self.sp_alpha)
        row(3, 'spacing', self.sp_spacing)
        row(4, 'line_width', self.sp_lw)
        row(5, 'blur', self.sp_blur)
        row(6, 'perturb', self.sp_perturb)
        row(7, 'shear', self.sp_shear)
        row(8, 'color(r,g,b)', self.sp_color)
        # 字型用 combobox（若可列出 fonts）
        ttk.Label(right, text='font').grid(row=9, column=0, sticky='e', pady=3)
        fonts = []
        try:
            fonts = [f for f in os.listdir(self.font_dir) if f.lower().endswith('.ttf')]
        except Exception:
            pass
        self.sp_font_combo = ttk.Combobox(right, textvariable=self.sp_font, values=[''] + fonts, width=30, state='readonly')
        self.sp_font_combo.grid(row=9, column=1, sticky='w')

        self._refresh_sentence_presets()

        # 候選清單（句子 × 字型）
        cand = ttk.LabelFrame(tab, text='候選（句子 × 字型）')
        cand.pack(fill='both', expand=True, padx=8, pady=(6, 8))
        self.sent_canvas = tk.Canvas(cand, borderwidth=0, highlightthickness=0)
        self.sent_scroll = ttk.Scrollbar(cand, orient='vertical', command=self.sent_canvas.yview)
        self.sent_inner = ttk.Frame(self.sent_canvas)
        self.sent_inner.bind(
            '<Configure>',
            lambda e: self.sent_canvas.configure(scrollregion=self.sent_canvas.bbox('all')),
        )
        self.sent_canvas.create_window((0, 0), window=self.sent_inner, anchor='nw')
        self.sent_canvas.configure(yscrollcommand=self.sent_scroll.set)
        self.sent_canvas.pack(side='left', fill='both', expand=True)
        self.sent_scroll.pack(side='right', fill='y')
        self._sent_thumbs = []

    def _load_sentence_candidates(self):
        txt = (self.sent_text.get() or '').strip()
        if not txt:
            messagebox.showinfo('提示', '請先輸入句子內容')
            return
        for w in self.sent_inner.winfo_children():
            w.destroy()
        self._sent_thumbs.clear()
        # 掃描字型並產生縮圖
        try:
            fonts = [f for f in os.listdir(self.font_dir) if f.lower().endswith('.ttf')]
        except Exception:
            fonts = []
        fonts.sort()
        row = 0
        col = 0
        max_cols = 2
        for f in fonts:
            font_path = os.path.join(self.font_dir, f)
            try:
                img = generate_text_image(txt, font_path=font_path, random=False)
            except Exception:
                img = None
            if not img:
                continue
            # 產生較寬的縮圖
            max_side = 320
            scale = min(max_side / max(1, img.width), 180 / max(1, img.height))
            scale = max(0.1, min(1.0, scale))
            thumb = img.resize((int(img.width * scale), int(img.height * scale)))
            ph = ImageTk.PhotoImage(thumb)
            self._sent_thumbs.append(ph)

            frame = ttk.Frame(self.sent_inner, padding=6)
            frame.grid(row=row, column=col, sticky='nw')
            ttk.Label(frame, image=ph).pack()
            ttk.Label(frame, text=f, width=40).pack(anchor='w')
            ttk.Button(
                frame,
                text='選用此字型',
                command=lambda name=f: self.sp_font.set(name),
            ).pack(anchor='w', pady=(4, 0))

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def _sentence_presets_path(self):
        return os.path.join(config.BASE_DIR, 'configs', 'sentence_presets.json')

    def _read_sentence_presets(self):
        path = self._sentence_presets_path()
        if not os.path.exists(path):
            return {}
        try:
            import json
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f) or {}
        except Exception:
            return {}

    def _write_sentence_presets(self, data: dict):
        os.makedirs(os.path.join(config.BASE_DIR, 'configs'), exist_ok=True)
        import json
        with open(self._sentence_presets_path(), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _refresh_sentence_presets(self):
        self._sp_data = self._read_sentence_presets()
        self.preset_list.delete(0, tk.END)
        for name in sorted(self._sp_data.keys()):
            self.preset_list.insert(tk.END, name)

    def _on_select_preset(self, event=None):
        sel = self.preset_list.curselection()
        if not sel:
            return
        name = self.preset_list.get(sel[0])
        self.preset_name.set(name)
        data = self._sp_data.get(name, {})
        self.sp_scale.set(str(data.get('scale', '')))
        self.sp_offy.set(str(data.get('offset_y', '')))
        self.sp_alpha.set(str(data.get('alpha', '')))
        self.sp_spacing.set(str(data.get('spacing', '')))
        self.sp_lw.set(str(data.get('line_width', '')))
        self.sp_blur.set(str(data.get('blur', '')))
        self.sp_perturb.set(str(data.get('perturb', '')))
        self.sp_shear.set(str(data.get('shear', '')))
        self.sp_color.set(str(tuple(data.get('color', ())) if data.get('color') else ''))
        self.sp_font.set(os.path.basename(data.get('font_path', '')) if data.get('font_path') else '')

    def _save_sentence_preset(self):
        name = (self.preset_name.get() or '').strip()
        if not name:
            messagebox.showwarning('提示', '請輸入名稱')
            return
        def _float(s):
            try:
                return float(s)
            except Exception:
                return None
        def _int(s):
            try:
                return int(float(s))
            except Exception:
                return None
        data = self._read_sentence_presets()
        entry = {}
        v = _float(self.sp_scale.get());
        if v is not None: entry['scale'] = v
        v = _float(self.sp_offy.get());
        if v is not None: entry['offset_y'] = v
        v = _int(self.sp_alpha.get());
        if v is not None: entry['alpha'] = max(0, min(255, v))
        v = _int(self.sp_spacing.get());
        if v is not None: entry['spacing'] = v
        v = _int(self.sp_lw.get());
        if v is not None: entry['line_width'] = max(1, min(10, v))
        v = _float(self.sp_blur.get());
        if v is not None: entry['blur'] = max(0.0, min(10.0, v))
        v = _int(self.sp_perturb.get());
        if v is not None: entry['perturb'] = max(0, min(30, v))
        v = _int(self.sp_shear.get());
        if v is not None: entry['shear'] = max(-45, min(45, v))
        # 顏色
        try:
            c = eval(self.sp_color.get()) if self.sp_color.get().strip() else None
            if isinstance(c, (list, tuple)) and len(c) == 3:
                entry['color'] = [int(max(0, min(255, int(x)))) for x in c]
        except Exception:
            pass
        # 字型路徑
        font_name = (self.sp_font.get() or '').strip()
        if font_name:
            entry['font_path'] = os.path.join(self.font_dir, font_name)
        data[name] = entry
        try:
            self._write_sentence_presets(data)
            self._refresh_sentence_presets()
            messagebox.showinfo('完成', '已儲存句子預設')
        except Exception as e:
            messagebox.showerror('錯誤', f'寫入失敗：{e}')

    def _delete_sentence_preset(self):
        name = (self.preset_name.get() or '').strip()
        if not name:
            messagebox.showinfo('提示', '請選擇要刪除的預設')
            return
        data = self._read_sentence_presets()
        if name in data:
            data.pop(name, None)
            try:
                self._write_sentence_presets(data)
                self._refresh_sentence_presets()
                messagebox.showinfo('完成', '已刪除')
            except Exception as e:
                messagebox.showerror('錯誤', f'刪除失敗：{e}')

    # ====== 單字屬性覆寫（使用 config.SPECIAL_RENDER_OVERRIDES）======
    def open_char_attributes(self):
        if not self._current_char:
            messagebox.showinfo("提示", "請先輸入字元並按『生成候選』")
            return
        ch = self._current_char
        ov = dict(config.SPECIAL_RENDER_OVERRIDES.get(ch, {}))
        # 初值
        scale_v = tk.StringVar(value=str(ov.get('scale', '')))
        offy_v = tk.StringVar(value=str(ov.get('offset_y', '')))
        alpha_v = tk.StringVar(value=str(ov.get('alpha', '')))
        spacing_v = tk.StringVar(value=str(ov.get('spacing', '')))

        win = tk.Toplevel(self)
        win.title(f"單字屬性：{ch}")
        win.geometry("360x220")
        body = ttk.Frame(win, padding=12)
        body.pack(fill="both", expand=True)
        # 說明
        ttk.Label(body, text="以下屬性只影響此單一字元的渲染（覆寫全域設定）").pack(anchor='w')
        frm = ttk.Frame(body)
        frm.pack(fill='x', pady=8)
        # 欄位
        row = 0
        def add_row(lbl, var):
            nonlocal row
            r = ttk.Frame(frm)
            r.grid(row=row, column=0, sticky='ew', pady=2)
            ttk.Label(r, text=lbl, width=12).pack(side='left')
            ttk.Entry(r, textvariable=var, width=12).pack(side='left')
            row += 1

        add_row('scale', scale_v)
        add_row('offset_y', offy_v)
        add_row('alpha', alpha_v)
        add_row('spacing', spacing_v)

        btns = ttk.Frame(body)
        btns.pack(fill='x', pady=8)
        ttk.Button(btns, text='儲存', command=lambda: self._save_char_attributes(win, ch, scale_v.get(), offy_v.get(), alpha_v.get(), spacing_v.get())).pack(side='left')
        ttk.Button(btns, text='重設(清空)', command=lambda: self._save_char_attributes(win, ch, '', '', '', '')).pack(side='left', padx=8)

    def _save_char_attributes(self, win, ch, scale_s, offy_s, alpha_s, spacing_s):
        # 將輸入轉型（空字串代表移除該鍵）
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
        newv = {}
        sv = _parse_float(scale_s)
        if sv is not None:
            newv['scale'] = sv
        oy = _parse_float(offy_s)
        if oy is not None:
            newv['offset_y'] = oy
        al = _parse_int(alpha_s)
        if al is not None:
            newv['alpha'] = max(0, min(255, al))
        sp = _parse_int(spacing_s)
        if sp is not None:
            newv['spacing'] = sp

        # 更新記憶體中的覆寫
        if newv:
            config.SPECIAL_RENDER_OVERRIDES[ch] = newv
        else:
            # 清空：移除該字元的覆寫
            if ch in config.SPECIAL_RENDER_OVERRIDES:
                config.SPECIAL_RENDER_OVERRIDES.pop(ch, None)

        # 永久寫入 configs/custom_config.json
        try:
            cpath = config.CUSTOM_CONFIG_PATH
            data = {}
            if os.path.exists(cpath):
                import json
                with open(cpath, 'r', encoding='utf-8') as f:
                    data = json.load(f) or {}
            sro = data.get('SPECIAL_RENDER_OVERRIDES') or {}
            # 以目前 config 內的完整 dict 為真實來源，避免局部覆蓋遺失
            sro.update(config.SPECIAL_RENDER_OVERRIDES)
            # 若此字被清空，要確保也從檔案移除
            if ch not in config.SPECIAL_RENDER_OVERRIDES and ch in sro:
                sro.pop(ch, None)
            data['SPECIAL_RENDER_OVERRIDES'] = sro
            with open(cpath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            messagebox.showinfo('完成', '已儲存單字屬性到 custom_config.json\n重新預覽即可生效（視 GUI 狀態可能需刷新）')
            if win:
                win.destroy()
        except Exception as e:
            messagebox.showerror('錯誤', f'寫入 custom_config.json 失敗：{e}')

    def show_help(self):
        lines = [
            "使用說明",
            "",
            "挑選 分頁：",
            "1) 在『字元』輸入框輸入單一字元（建議一次一個）。",
            "2) 按『生成候選』：系統會掃描 fonts/ 內的 .ttf，為此字元產生各字型的縮圖。",
            "3) 勾選想要採用的候選（可用『全選／全不選』快速切換）。",
            "4) 按『匯入所選』：會把檔案以 safe 檔名寫到 confirm/，供檢視與後續路由更新。",
            "5) 按『更新路由』：掃描 confirm/，依檔名回寫 configs/font_routes_template.json，",
            "   之後渲染同一字元時會優先採用對應字型。",
            "",
            "已確認 分頁：",
            "- 顯示 confirm/ 中已存在的縮圖。可勾選並『移除所選』；",
            "  若路由目前指向要移除的同一個字型，會一併清除其對應 mapping。",
            "- 『重新整理』可更新列表。",
            "",
            "注意事項：",
            "- 目前建議一次處理單一字元；輸入多字元會提示。",
            "- 路由更新寫入 font_routes_template.json；若另一個 GUI 已開啟預覽，",
            "  可能需要重新預覽／刷新，才能載入新的路由。",
            "- 只列出 .ttf 字型；若某些字在特定字型無法渲染，會略過該縮圖。",
        ]
        message = "\n".join(lines)
        messagebox.showinfo("字型挑選 / confirm - 說明", message)


def main():
    root = tk.Tk()
    root.title("字型挑選 / confirm 管理")
    root.geometry("1000x720")
    app = ConfirmManager(root)
    app.pack(fill="both", expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()
