# -*- coding: utf-8 -*-
"""
lab1_des.py — ВЕРСИЯ ДЛЯ СТУДЕНТА
Ключ не отображается. Студент должен найти ключ методом дифференциального анализа
и ввести его на вкладке «Проверка».
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from lab1_base import BaseApp, BLUE, WHITE, LGRAY, DGRAY, RED, GREEN
from lab1_core import bits_str, VariantGen


class StudentApp(BaseApp):
    TITLE = "Лабораторная работа №1  [Студент]"

    def __init__(self):
        self._pairs_data = []   # список (pt, ptp, ct, ctp, dxl, dxr, dyl, dyr)
        super().__init__()

    # ───────────────────────────────────────────────────────────────────────
    #  Вкладка 2 — Таблица XL | XR | YL | YR
    # ───────────────────────────────────────────────────────────────────────
    def _build_tab2(self):
        t = self.tab2

        tk.Label(t, text=(
            "Таблица пар открытых текстов (X) и шифртекстов (Y).\n"
            "Используйте дифференциальный анализ для нахождения ключа."),
            bg=LGRAY, font=('Arial', 9), justify='left'
        ).pack(padx=8, pady=(6, 2), anchor='w')

        # Легенда
        leg = tk.Frame(t, bg=LGRAY)
        leg.pack(padx=8, pady=(0, 4), anchor='w')
        for color, label in [('#E3F2FD', 'P  — открытый текст'),
                              ('#E8F5E9', "P' — парный открытый текст"),
                              ('#F3E5F5', 'ΔX/ΔY — разность')]:
            f = tk.Frame(leg, bg=color, relief='solid', bd=1,
                         width=14, height=14)
            f.grid_propagate(False)
            f.pack(side='left', padx=(0, 2))
            tk.Label(leg, text=label, bg=LGRAY,
                     font=('Arial', 8)).pack(side='left', padx=(0, 10))

        # Treeview
        cols = ('XL', 'XR', 'YL', 'YR')
        frame = tk.Frame(t, bg=LGRAY)
        frame.pack(fill='both', expand=True, padx=8, pady=4)

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
                  ).pack(pady=8)

    # ───────────────────────────────────────────────────────────────────────
    #  Вкладка 3 — Ввод найденного ключа K1…K24
    # ───────────────────────────────────────────────────────────────────────
    def _build_tab3(self):
        t = self.tab3

        tk.Label(t, text="Искомый ключ",
                 bg=LGRAY, font=('Arial', 11, 'bold')
                 ).pack(pady=(20, 6))

        grid_frame = tk.Frame(t, bg=LGRAY, relief='groove', bd=1)
        grid_frame.pack(padx=20, pady=4)

        self._key_entries = []
        for i in range(24):
            tk.Label(grid_frame, text=f"K{i+1}", font=('Consolas', 8),
                     bg=LGRAY, width=3, anchor='center'
                     ).grid(row=0, column=i, padx=1, pady=(4, 0))
            e = tk.Entry(grid_frame, width=3, justify='center',
                         font=('Consolas', 10), relief='solid', bd=1)
            e.insert(0, 'x')
            e.bind('<FocusIn>',  lambda ev, ent=e: self._clear_x(ent))
            e.bind('<FocusOut>', lambda ev, ent=e: self._restore_x(ent))
            e.grid(row=1, column=i, padx=1, pady=(0, 4))
            self._key_entries.append(e)

        tk.Label(t, text="Введите найденные биты ключа (0 или 1) в каждую ячейку.",
                 bg=LGRAY, font=('Arial', 9), fg='#555555'
                 ).pack(pady=(4, 8))

        tk.Button(t, text="  Проверка  ",
                  font=('Arial', 11), width=18,
                  command=self._check_key
                  ).pack(pady=6)

        self._check_result_lbl = tk.Label(t, text="", bg=LGRAY,
                                          font=('Arial', 11, 'bold'))
        self._check_result_lbl.pack(pady=4)

        tk.Button(t, text="Сбросить",
                  font=('Arial', 9), fg='#555555',
                  command=self._reset_key_entries
                  ).pack(pady=(0, 6))

    # ───────────────────────────────────────────────────────────────────────
    #  Хуки BaseApp
    # ───────────────────────────────────────────────────────────────────────
    def _on_variant_generated(self):
        for item in self._tree.get_children():
            self._tree.delete(item)
        self._pairs_data.clear()
        self._check_result_lbl.config(text="")
        self._reset_key_entries()

    def _on_encrypt_done(self, delta_x, delta_y, pt, ptp, ct, ctp):
        for item in self._tree.get_children():
            self._tree.delete(item)
        self._pairs_data.clear()

        dxl = (delta_x >> 8) & 0xFF
        dxr =  delta_x       & 0xFF

        for i, (plain, cipher_t) in enumerate(
                zip(self.plaintexts, self.ciphertexts)):
            pl  = (plain    >> 8) & 0xFF
            pr  =  plain         & 0xFF
            cl  = (cipher_t >> 8) & 0xFF
            cr  =  cipher_t      & 0xFF

            ptp_i = plain ^ delta_x
            plp = (ptp_i >> 8) & 0xFF
            prp =  ptp_i       & 0xFF
            ctp_i, _ = self.cipher.encrypt(ptp_i)
            clp = (ctp_i >> 8) & 0xFF
            crp =  ctp_i       & 0xFF
            dyl_i = cl ^ clp
            dyr_i = cr ^ crp

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
    #  Проверка ключа
    # ───────────────────────────────────────────────────────────────────────
    def _check_key(self):
        if not self.round_keys:
            messagebox.showinfo("Нет данных", "Сначала сформируйте вариант.")
            return
        bits = []
        for i, e in enumerate(self._key_entries):
            v = e.get().strip()
            if v not in ('0', '1'):
                messagebox.showerror("Ошибка", f"Ячейка K{i+1}: введите 0 или 1.")
                return
            bits.append(int(v))

        guess   = int("".join(map(str, bits)), 2)
        correct = self.master_key
        correct_bits = [int(b) for b in bits_str(correct, 24)]

        all_ok = True
        for e, cb, gb in zip(self._key_entries, correct_bits, bits):
            e.config(bg='#C8E6C9' if gb == cb else '#FFCDD2')
            if gb != cb:
                all_ok = False

        if all_ok:
            self._check_result_lbl.config(
                text=f"✓ Верно!  Ключ = 0x{correct:06X}",
                fg=GREEN)
        else:
            wrong = sum(cb != gb for cb, gb in zip(correct_bits, bits))
            self._check_result_lbl.config(
                text=f"✗ Неверно. Ошибочных бит: {wrong}",
                fg=RED)

    def _reset_key_entries(self):
        for e in self._key_entries:
            e.config(bg=WHITE)
            e.delete(0, 'end')
            e.insert(0, 'x')
        self._check_result_lbl.config(text="")

    def _clear_x(self, entry):
        if entry.get() == 'x':
            entry.delete(0, 'end')
            entry.config(bg=WHITE)

    def _restore_x(self, entry):
        if entry.get().strip() == '':
            entry.insert(0, 'x')

    # ───────────────────────────────────────────────────────────────────────
    #  Сохранение в файл
    # ───────────────────────────────────────────────────────────────────────
    def _save_to_file(self):
        if not self._pairs_data:
            messagebox.showinfo("Нет данных", "Сначала выполните шифрование.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension='.txt',
            filetypes=[('Text files', '*.txt'), ('All files', '*.*')],
            title="Сохранить результаты")
        if not path:
            return
        lines = [
            "Лабораторная работа №1 — Учебный шифр",
            f"ФИО: {self.e_fio.get().strip()}",
            f"Группа: {self.e_group.get().strip()}",
            "",
            f"{'XL':^10}  {'XR':^10}  {'YL':^10}  {'YR':^10}  Тип",
            "-" * 58,
        ]
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
    app = StudentApp()
    app.mainloop()
