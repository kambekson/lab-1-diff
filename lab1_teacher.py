# -*- coding: utf-8 -*-
"""
lab1_teacher.py — ВЕРСИЯ ДЛЯ ПРЕПОДАВАТЕЛЯ
Отображает ключ открыто для проверки работ студентов.
Генерация варианта ИДЕНТИЧНА студенческой версии (используется
тот же модуль lab1_core.VariantGen.generate).
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from lab1_base import BaseApp, BLUE, WHITE, LGRAY, DGRAY, RED, GREEN
from lab1_core import bits_str, VariantGen, compute_ddt_s1s2, compute_ddt_s3


class TeacherApp(BaseApp):
    TITLE = "Лабораторная работа №1  [ПРЕПОДАВАТЕЛЬ]"

    def __init__(self):
        self._pairs_data = []
        super().__init__()
        # Красная полоска — визуальный маркер преподавательской версии
        banner = tk.Label(self, text="  ★  РЕЖИМ ПРЕПОДАВАТЕЛЯ  ★  ",
                          bg='#B71C1C', fg=WHITE,
                          font=('Arial', 9, 'bold'))
        banner.pack(side='bottom', fill='x')

    # ───────────────────────────────────────────────────────────────────────
    #  Вкладка 2 — Ключи + таблица пар
    # ───────────────────────────────────────────────────────────────────────
    def _build_tab2(self):
        t = self.tab2

        # ── Блок ключей (всегда виден) ──────────────────────────────────────
        kf = tk.LabelFrame(t, text="  Ключи  ", bg='#FFF3E0',
                           font=('Arial', 9, 'bold'), fg='#BF360C')
        kf.pack(fill='x', padx=8, pady=(6, 4))

        # Мастер-ключ
        mk_row = tk.Frame(kf, bg='#FFF3E0')
        mk_row.pack(fill='x', padx=6, pady=(4, 2))
        tk.Label(mk_row, text="Мастер-ключ (24 бит):", bg='#FFF3E0',
                 font=('Consolas', 9, 'bold'), fg='#BF360C', width=22,
                 anchor='w').pack(side='left')
        self._mk_lbl = tk.Label(mk_row, text="—", bg=WHITE, relief='sunken',
                                 font=('Consolas', 10), fg='#B71C1C',
                                 width=38, anchor='w')
        self._mk_lbl.pack(side='left', padx=4)

        # Строки раундовых ключей
        self._rk_lbls = []
        rk_frame = tk.Frame(kf, bg='#FFF3E0')
        rk_frame.pack(fill='x', padx=6, pady=(0, 6))
        for i in range(3):
            tk.Label(rk_frame, text=f"K{i+1} (12 бит):", bg='#FFF3E0',
                     font=('Consolas', 9), width=14, anchor='w'
                     ).grid(row=i, column=0, padx=(0, 4), pady=1)
            lbl = tk.Label(rk_frame, text="—", bg=WHITE, relief='sunken',
                           font=('Consolas', 9), width=30, anchor='w')
            lbl.grid(row=i, column=1, sticky='w', pady=1)
            self._rk_lbls.append(lbl)

        # ── Легенда ─────────────────────────────────────────────────────────
        leg = tk.Frame(t, bg=LGRAY)
        leg.pack(padx=8, pady=(0, 2), anchor='w')
        for color, label in [('#E3F2FD', 'P'), ('#E8F5E9', "P'"),
                              ('#F3E5F5', 'ΔX/ΔY')]:
            f = tk.Frame(leg, bg=color, relief='solid', bd=1,
                         width=14, height=14)
            f.grid_propagate(False)
            f.pack(side='left', padx=(0, 2))
            tk.Label(leg, text=label, bg=LGRAY,
                     font=('Arial', 8)).pack(side='left', padx=(0, 8))

        # ── Таблица XL|XR|YL|YR ─────────────────────────────────────────────
        cols = ('XL', 'XR', 'YL', 'YR')
        frame = tk.Frame(t, bg=LGRAY)
        frame.pack(fill='both', expand=True, padx=8, pady=2)

        self._tree = ttk.Treeview(frame, columns=cols, show='headings',
                                  selectmode='browse')
        col_w = 130
        for c in cols:
            self._tree.heading(c, text=c)
            self._tree.column(c, width=col_w, anchor='center',
                              minwidth=col_w, stretch=False)

        vsb = ttk.Scrollbar(frame, orient='vertical',
                            command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        self._tree.tag_configure('p',     background='#E3F2FD')
        self._tree.tag_configure('pp',    background='#E8F5E9')
        self._tree.tag_configure('delta', background='#F3E5F5')
        self._tree.tag_configure('sep',   background='#EEEEEE')

        tk.Button(t, text="  Сохранить в файл  ",
                  font=('Arial', 10), width=20,
                  command=self._save_to_file
                  ).pack(pady=4)

    # ───────────────────────────────────────────────────────────────────────
    #  Вкладка 3 — Правильный ключ + DDT + трассировка
    # ───────────────────────────────────────────────────────────────────────
    def _build_tab3(self):
        t = self.tab3

        tk.Label(t, text="Правильный ключ (ответ)",
                 bg=LGRAY, font=('Arial', 11, 'bold')
                 ).pack(pady=(16, 4))

        # Сетка K1…K24 (readonly, автозаполняется)
        grid_frame = tk.Frame(t, bg=LGRAY, relief='groove', bd=1)
        grid_frame.pack(padx=20, pady=4)

        self._key_display = []
        for i in range(24):
            tk.Label(grid_frame, text=f"K{i+1}", font=('Consolas', 8),
                     bg=LGRAY, width=3, anchor='center'
                     ).grid(row=0, column=i, padx=1, pady=(4, 0))
            e = tk.Entry(grid_frame, width=3, justify='center',
                         font=('Consolas', 10), relief='solid', bd=1,
                         state='disabled',
                         disabledbackground='#FFF9C4',
                         disabledforeground='#B71C1C')
            e.grid(row=1, column=i, padx=1, pady=(0, 4))
            self._key_display.append(e)

        # Hex-представление ключа
        self._key_hex_lbl = tk.Label(t, text="",
                                     bg=LGRAY, font=('Consolas', 10, 'bold'),
                                     fg='#B71C1C')
        self._key_hex_lbl.pack(pady=(4, 8))

        # Раундовые ключи
        rk_f = tk.LabelFrame(t, text=" Раундовые ключи ", bg=LGRAY,
                              font=('Arial', 9))
        rk_f.pack(padx=20, fill='x', pady=(0, 6))
        self._rk3_lbls = []
        for i in range(3):
            tk.Label(rk_f, text=f"K{i+1}:", bg=LGRAY,
                     font=('Consolas', 9), width=4
                     ).grid(row=i, column=0, padx=4, pady=1, sticky='e')
            lbl = tk.Label(rk_f, text="—", bg=WHITE, relief='sunken',
                           font=('Consolas', 9), width=32, anchor='w')
            lbl.grid(row=i, column=1, pady=1, sticky='w')
            self._rk3_lbls.append(lbl)

        # Трассировка (прокручиваемый текст)
        sep = ttk.Separator(t, orient='horizontal')
        sep.pack(fill='x', padx=8, pady=4)
        tk.Label(t, text="Трассировка 1-го блока (раунд 1)",
                 bg=LGRAY, font=('Arial', 9, 'italic')
                 ).pack(anchor='w', padx=12)
        tf = tk.Frame(t, bg=LGRAY)
        tf.pack(fill='both', expand=True, padx=8, pady=(2, 6))
        self._trace_text = tk.Text(tf, height=8, font=('Consolas', 8),
                                   bg='#1E1E1E', fg='#D4D4D4',
                                   relief='flat', wrap='none',
                                   state='disabled')
        sc = tk.Scrollbar(tf, command=self._trace_text.yview)
        self._trace_text.configure(yscrollcommand=sc.set)
        sc.pack(side='right', fill='y')
        self._trace_text.pack(fill='both', expand=True)

    # ───────────────────────────────────────────────────────────────────────
    #  Хуки BaseApp
    # ───────────────────────────────────────────────────────────────────────
    def _on_variant_generated(self):
        # Обновить блок ключей на Tab2 сразу после генерации
        self._refresh_key_display()
        for item in self._tree.get_children():
            self._tree.delete(item)
        self._pairs_data.clear()

    def _on_encrypt_done(self, delta_x, delta_y, pt, ptp, ct, ctp):
        self._refresh_key_display()
        self._fill_table(delta_x)
        self._fill_trace()

    # ───────────────────────────────────────────────────────────────────────
    #  Обновление ключа
    # ───────────────────────────────────────────────────────────────────────
    def _refresh_key_display(self):
        if self.master_key is None:
            return
        mk = self.master_key
        rks = self.round_keys

        # Tab2 — блок ключей
        self._mk_lbl.config(
            text=f"{bits_str(mk, 24)}   (0x{mk:06X})")
        for i, lbl in enumerate(self._rk_lbls):
            lbl.config(text=f"{bits_str(rks[i], 12)}   (0x{rks[i]:03X})")

        # Tab3 — ячейки K1-K24
        key_bits = [int(b) for b in bits_str(mk, 24)]
        for e, b in zip(self._key_display, key_bits):
            e.config(state='normal')
            e.delete(0, 'end')
            e.insert(0, str(b))
            e.config(state='disabled')
        self._key_hex_lbl.config(
            text=f"0x{mk:06X}  ({bits_str(mk, 24)})")
        for i, lbl in enumerate(self._rk3_lbls):
            lbl.config(text=f"{bits_str(rks[i], 12)}   (0x{rks[i]:03X})")

    # ───────────────────────────────────────────────────────────────────────
    #  Таблица пар
    # ───────────────────────────────────────────────────────────────────────
    def _fill_table(self, delta_x):
        for item in self._tree.get_children():
            self._tree.delete(item)
        self._pairs_data.clear()

        dxl = (delta_x >> 8) & 0xFF
        dxr =  delta_x       & 0xFF

        for i, (plain, cipher_t) in enumerate(
                zip(self.plaintexts, self.ciphertexts)):
            pl  = (plain    >> 8) & 0xFF;  pr  = plain    & 0xFF
            cl  = (cipher_t >> 8) & 0xFF;  cr  = cipher_t & 0xFF

            ptp_i = plain ^ delta_x
            plp = (ptp_i >> 8) & 0xFF;  prp = ptp_i & 0xFF
            ctp_i, _ = self.cipher.encrypt(ptp_i)
            clp = (ctp_i >> 8) & 0xFF;  crp = ctp_i & 0xFF
            dyl_i = cl ^ clp;  dyr_i = cr ^ crp

            self._pairs_data.append(
                (plain, ptp_i, cipher_t, ctp_i, dxl, dxr, dyl_i, dyr_i))

            self._tree.insert('', 'end', tags=('p',),
                              values=(bits_str(pl,  8), bits_str(pr,  8),
                                      bits_str(cl,  8), bits_str(cr,  8)))
            self._tree.insert('', 'end', tags=('pp',),
                              values=(bits_str(plp, 8), bits_str(prp, 8),
                                      bits_str(clp, 8), bits_str(crp, 8)))
            self._tree.insert('', 'end', tags=('delta',),
                              values=(bits_str(dxl,   8), bits_str(dxr,   8),
                                      bits_str(dyl_i, 8), bits_str(dyr_i, 8)))
            if i < len(self.plaintexts) - 1:
                self._tree.insert('', 'end', tags=('sep',),
                                  values=('', '', '', ''))

    # ───────────────────────────────────────────────────────────────────────
    #  Трассировка раунда 1 для блока 1
    # ───────────────────────────────────────────────────────────────────────
    def _fill_trace(self):
        if not self.traces:
            return
        tr = self.traces[0]   # первый блок
        rk = self.round_keys
        lines = []
        lines.append(f"Блок 1:  P = {self.plaintexts[0]:04X}h  "
                     f"({bits_str(self.plaintexts[0], 16)})")
        lines.append(f"Мастер-ключ: 0x{self.master_key:06X}  "
                     f"({bits_str(self.master_key, 24)})")
        lines.append("")
        for rnd in range(1, 4):
            r = tr[rnd]
            if 'F_in' not in r:
                continue
            lines.append(f"── Раунд {rnd} ──────────────────────────────────")
            lines.append(
                f"  Вход L={r['L']:02X}h R={r['R']:02X}h  "
                f"({bits_str(r['L'],8)} {bits_str(r['R'],8)})")
            lines.append(
                f"  F вход  : {r['F_in']:02X}h  ({bits_str(r['F_in'], 8)})")
            lines.append(
                f"  Расшир. : {r['expanded']:03X}h ({bits_str(r['expanded'], 12)})")
            lines.append(
                f"  K{rnd}      : {rk[rnd-1]:03X}h  ({bits_str(rk[rnd-1], 12)})")
            lines.append(
                f"  XOR     : {r['xored']:03X}h  ({bits_str(r['xored'], 12)})")
            lines.append(
                f"  S1 {r['s1_in']:X}→{r['s1_out']}  "
                f"S2 {r['s2_in']:X}→{r['s2_out']}  "
                f"S3 {r['s3_in']:X}→{r['s3_out']}")
            lines.append(
                f"  F вых.  : {r['F_out']:02X}h  ({bits_str(r['F_out'], 8)})")
        lines.append("")
        lines.append(f"Шифртекст: {self.ciphertexts[0]:04X}h  "
                     f"({bits_str(self.ciphertexts[0], 16)})")

        self._trace_text.config(state='normal')
        self._trace_text.delete('1.0', 'end')
        self._trace_text.insert('end', "\n".join(lines))
        self._trace_text.config(state='disabled')

    # ───────────────────────────────────────────────────────────────────────
    #  Сохранение в файл (с ключом)
    # ───────────────────────────────────────────────────────────────────────
    def _save_to_file(self):
        if not self._pairs_data:
            messagebox.showinfo("Нет данных", "Сначала выполните шифрование.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension='.txt',
            filetypes=[('Text files', '*.txt'), ('All files', '*.*')],
            title="Сохранить результаты (преподаватель)")
        if not path:
            return
        lines = [
            "Лабораторная работа №1 — Ответы преподавателя",
            f"ФИО: {self.e_fio.get().strip()}",
            f"Группа: {self.e_group.get().strip()}",
            "",
            f"=== КЛЮЧ ===",
            f"Мастер-ключ : 0x{self.master_key:06X}  "
            f"({bits_str(self.master_key, 24)})",
        ]
        for i, rk in enumerate(self.round_keys):
            lines.append(f"K{i+1}          : 0x{rk:03X}  ({bits_str(rk, 12)})")
        lines += ["", f"{'XL':^10}  {'XR':^10}  {'YL':^10}  {'YR':^10}  Тип",
                  "-" * 58]
        for pt, ptp, ct, ctp, dxl, dxr, dyl, dyr in self._pairs_data:
            pl  = (pt  >> 8) & 0xFF;  pr  = pt  & 0xFF
            cl  = (ct  >> 8) & 0xFF;  cr  = ct  & 0xFF
            plp = (ptp >> 8) & 0xFF;  prp = ptp & 0xFF
            clp = (ctp >> 8) & 0xFF;  crp = ctp & 0xFF
            lines += [
                f"{bits_str(pl, 8):^10}  {bits_str(pr, 8):^10}  "
                f"{bits_str(cl, 8):^10}  {bits_str(cr, 8):^10}  P",
                f"{bits_str(plp,8):^10}  {bits_str(prp,8):^10}  "
                f"{bits_str(clp,8):^10}  {bits_str(crp,8):^10}  P'",
                f"{bits_str(dxl,8):^10}  {bits_str(dxr,8):^10}  "
                f"{bits_str(dyl,8):^10}  {bits_str(dyr,8):^10}  ΔX/ΔY",
                "",
            ]
        with open(path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        messagebox.showinfo("Готово", f"Файл сохранён:\n{path}")


# ────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app = TeacherApp()
    app.mainloop()
