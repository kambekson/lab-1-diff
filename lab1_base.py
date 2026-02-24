# -*- coding: utf-8 -*-
"""
lab1_base.py — базовый класс UI (вкладка 1 + вся логика кнопок).
Наследуется студенческой и преподавательской версиями.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from lab1_core import (
    TeachingDES, VariantGen,
    find_best_f_differential, characteristic_strength,
    compute_ddt_s1s2, compute_ddt_s3, best_differentials,
    bits_str,
)

# ── Цвета ───────────────────────────────────────────────────────────────────
BLUE  = "#1565C0"
WHITE = "#FFFFFF"
LGRAY = "#F0F0F0"
DGRAY = "#9E9E9E"
RED   = "#C62828"
GREEN = "#1B5E20"


# ── Вспомогательные виджеты ─────────────────────────────────────────────────

def make_sbox_grid(parent, rows_data):
    """Создаёт сетку Entry (readonly) для S-блока. Возвращает cells2d."""
    cells2d = []
    n_cols = len(rows_data[0])
    for j in range(n_cols):
        tk.Label(parent, text=str(j), width=3,
                 font=('Consolas', 8), fg=DGRAY).grid(row=0, column=j + 1)
    for i, row in enumerate(rows_data):
        tk.Label(parent, text=str(i), width=2,
                 font=('Consolas', 8), fg=DGRAY).grid(row=i + 1, column=0)
        row_cells = []
        for j, val in enumerate(row):
            bg = BLUE if (i == 0 and j == 0) else WHITE
            fg = WHITE if (i == 0 and j == 0) else "black"
            e = tk.Entry(parent, width=3, justify='center',
                         relief='solid', bd=1,
                         bg=bg, fg=fg, disabledbackground=bg,
                         disabledforeground=fg, state='disabled',
                         font=('Consolas', 9))
            e.insert(0, str(val))
            e.grid(row=i + 1, column=j + 1, padx=1, pady=1)
            row_cells.append(e)
        cells2d.append(row_cells)
    return cells2d


def update_sbox_grid(cells2d, rows_data):
    for i, row in enumerate(rows_data):
        for j, val in enumerate(row):
            bg = BLUE if (i == 0 and j == 0) else WHITE
            fg = WHITE if (i == 0 and j == 0) else "black"
            c = cells2d[i][j]
            c.config(state='normal', bg=bg, fg=fg,
                     disabledbackground=bg, disabledforeground=fg)
            c.delete(0, 'end')
            c.insert(0, str(val))
            c.config(state='disabled')


def set_ro_cells(cells, values):
    """Записать значения в readonly-ряд ячеек."""
    for c, v in zip(cells, values):
        c.config(state='normal')
        c.delete(0, 'end')
        c.insert(0, str(v))
        c.config(state='disabled')


def make_bit_row(parent, n, color=BLUE):
    """Ряд из n readonly Entry (для Дельта YL/YR, P, EP)."""
    cells = []
    for i in range(n):
        bg = color if i == 0 else WHITE
        fg = WHITE if i == 0 else "black"
        e = tk.Entry(parent, width=3, justify='center',
                     relief='solid', bd=1,
                     bg=bg, fg=fg, disabledbackground=bg,
                     disabledforeground=fg, state='disabled',
                     font=('Consolas', 9))
        e.grid(row=0, column=i, padx=1, pady=1)
        cells.append(e)
    return cells


def make_editable_bit_row(parent, n, on_change=None):
    """
    Ряд из n редактируемых Entry для ввода бит (только 0 или 1).
    Первая ячейка — синяя (маркер), остальные — белые.
    После ввода 0 или 1 фокус автоматически переходит в следующую ячейку.
    on_change() вызывается при любом изменении.
    """
    cells = []
    for i in range(n):
        bg = BLUE if i == 0 else WHITE
        fg = WHITE if i == 0 else 'black'
        ins = WHITE if i == 0 else 'black'
        e = tk.Entry(parent, width=3, justify='center',
                     relief='solid', bd=1,
                     bg=bg, fg=fg,
                     insertbackground=ins,
                     selectbackground='#90CAF9',
                     font=('Consolas', 9, 'bold'))
        e.grid(row=0, column=i, padx=1, pady=1)
        cells.append(e)

    def _on_key(event, idx):
        entry = cells[idx]
        # Удалить всё лишнее — оставить только 0 или 1
        raw = entry.get().strip()
        if raw not in ('0', '1', ''):
            # Оставляем только последний введённый символ, если он допустим
            last = event.char if event.char in ('0', '1') else ''
            entry.delete(0, 'end')
            entry.insert(0, last)
            raw = last
        # Автопереход вправо
        if raw in ('0', '1') and idx + 1 < len(cells):
            cells[idx + 1].focus_set()
            cells[idx + 1].select_range(0, 'end')
        if on_change:
            on_change()

    def _on_backspace(event, idx):
        """Backspace в пустой ячейке — перейти влево."""
        entry = cells[idx]
        if entry.get() == '' and idx > 0:
            cells[idx - 1].focus_set()
            cells[idx - 1].delete(0, 'end')
        if on_change:
            on_change()

    for i, e in enumerate(cells):
        e.bind('<KeyRelease>',   lambda ev, idx=i: _on_key(ev, idx))
        e.bind('<BackSpace>',    lambda ev, idx=i: _on_backspace(ev, idx))
        # Блокируем вставку нецифровых данных
        e.bind('<Control-v>',    lambda ev: 'break')
        e.bind('<Control-V>',    lambda ev: 'break')

    return cells


def set_edit_cells(cells, values):
    """Записать значения в редактируемый ряд ячеек."""
    for c, v in zip(cells, values):
        c.delete(0, 'end')
        c.insert(0, str(v))


# ── Базовый класс приложения ─────────────────────────────────────────────────

class BaseApp(tk.Tk):
    """Общие поля и вкладка 1. Подклассы реализуют _build_tab2() и _build_tab3()."""

    TITLE = "Лабораторная работа №1"
    GEOMETRY = None  # None = авто

    def __init__(self):
        super().__init__()
        self.title(self.TITLE)
        self.resizable(False, False)
        self.configure(bg=LGRAY)
        if self.GEOMETRY:
            self.geometry(self.GEOMETRY)

        # Состояние
        self.cipher      = None
        self.s1 = self.s2 = self.s3 = None
        self.p_table = self.ep_table = None
        self.master_key  = None
        self.round_keys  = None
        self.plaintexts  = []
        self.ciphertexts = []
        self.traces      = []
        self._best_alpha = 0   # рекомендуемый ΔXR

        self._build_ui()

    # ──────────────────────────────────────────────────────────────────────────
    #  Построение интерфейса
    # ──────────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        nb = ttk.Notebook(self)
        nb.pack(fill='both', expand=True, padx=4, pady=4)

        self.tab1 = tk.Frame(nb, bg=LGRAY)
        self.tab2 = tk.Frame(nb, bg=LGRAY)
        self.tab3 = tk.Frame(nb, bg=LGRAY)

        nb.add(self.tab1, text="  Исходные данные  ")
        nb.add(self.tab2, text="  Результат шифрования  ")
        nb.add(self.tab3, text="  Проверка  ")

        self._build_tab1()
        self._build_tab2()   # реализуется в подклассе
        self._build_tab3()   # реализуется в подклассе

    # ── Вкладка 1 ─────────────────────────────────────────────────────────────
    def _build_tab1(self):
        t = self.tab1

        # ---- Левая колонка ----
        left = tk.Frame(t, bg=LGRAY)
        left.grid(row=0, column=0, sticky='nw', padx=8, pady=8)

        tk.Label(left, text="ФИО студента:", bg=LGRAY,
                 font=('Arial', 9)).grid(row=0, column=0, sticky='w')
        self.e_fio = tk.Entry(left, width=30, font=('Arial', 9))
        self.e_fio.grid(row=1, column=0, pady=2, sticky='w')

        tk.Label(left, text="Номер группы:", bg=LGRAY,
                 font=('Arial', 9)).grid(row=2, column=0, sticky='w', pady=(6, 0))
        self.e_group = tk.Entry(left, width=30, font=('Arial', 9))
        self.e_group.grid(row=3, column=0, pady=2, sticky='w')

        tk.Label(left, text="Количество исходных текстов\n(от 1 до 5000):",
                 bg=LGRAY, font=('Arial', 9), justify='left'
                 ).grid(row=4, column=0, sticky='w', pady=(10, 0))
        self.e_count = tk.Entry(left, width=8, font=('Arial', 9))
        self.e_count.insert(0, "1")
        self.e_count.grid(row=5, column=0, sticky='w')

        # Таблица P
        tk.Label(left, text="Таблица перестановки", bg=LGRAY,
                 font=('Arial', 9)).grid(row=6, column=0, sticky='w', pady=(10, 0))
        pf = tk.Frame(left, bg=LGRAY)
        pf.grid(row=7, column=0, sticky='w')
        self._p_cells = make_bit_row(pf, 8, BLUE)

        # Таблица EP
        tk.Label(left, text="Таблица перестановки с расширением", bg=LGRAY,
                 font=('Arial', 9)).grid(row=8, column=0, sticky='w', pady=(6, 0))
        epf = tk.Frame(left, bg=LGRAY)
        epf.grid(row=9, column=0, sticky='w')
        self._ep_cells = make_bit_row(epf, 12, BLUE)

        # Дельта XL — редактируемая
        tk.Label(left, text="Дельта XL", bg=LGRAY,
                 font=('Arial', 9)).grid(row=10, column=0,
                                         sticky='w', pady=(6, 0))
        f_dxl = tk.Frame(left, bg=LGRAY)
        f_dxl.grid(row=11, column=0, sticky='w')
        self._dxl_cells = make_editable_bit_row(
            f_dxl, 8, on_change=self._on_delta_changed)
        set_edit_cells(self._dxl_cells, [0] * 8)

        # Дельта XR — редактируемая
        tk.Label(left, text="Дельта XR", bg=LGRAY,
                 font=('Arial', 9)).grid(row=12, column=0,
                                         sticky='w', pady=(6, 0))
        f_dxr = tk.Frame(left, bg=LGRAY)
        f_dxr.grid(row=13, column=0, sticky='w')
        self._dxr_cells = make_editable_bit_row(
            f_dxr, 8, on_change=self._on_delta_changed)
        set_edit_cells(self._dxr_cells, [0] * 8)

        # Дельта YL / YR — редактируемые (студент вводит вручную)
        for lbl, attr, row_i in [
                ("Дельта YL:", '_dyl_cells', 14),
                ("Дельта YR:", '_dyr_cells', 16),
        ]:
            tk.Label(left, text=lbl, bg=LGRAY,
                     font=('Arial', 9)).grid(row=row_i, column=0,
                                             sticky='w', pady=(6, 0))
            f = tk.Frame(left, bg=LGRAY)
            f.grid(row=row_i + 1, column=0, sticky='w')
            cells = make_editable_bit_row(f, 8, on_change=self._on_delta_changed)
            set_edit_cells(cells, [0] * 8)
            setattr(self, attr, cells)

        # Лейбл рекомендуемой характеристики
        self._char_lbl = tk.Label(left, text="", bg=LGRAY,
                                  font=('Arial', 8), justify='left',
                                  wraplength=315, fg='#1A237E')
        self._char_lbl.grid(row=18, column=0, sticky='w', pady=(4, 0))

        # ---- Правая колонка: S-блоки ----
        right = tk.Frame(t, bg=LGRAY)
        right.grid(row=0, column=1, sticky='nw', padx=8, pady=8)

        init_s1 = [[6, 7, 6, 7, 5, 3, 3, 2], [0, 1, 2, 0, 1, 4, 5, 4]]
        init_s2 = [[0, 2, 3, 3, 0, 1, 6, 1], [7, 7, 4, 6, 2, 5, 5, 4]]
        init_s3 = [[1, 2, 1, 2], [3, 0, 0, 3], [1, 0, 2, 1], [0, 3, 3, 2]]

        # S1, S2, S3 — общий конструктор
        self._s1_cells = self._sbox_panel(right, "Таблица S1", init_s1,
                                          row=0, col=0, spin_attr='_s1_block')
        self._s2_cells = self._sbox_panel(right, "Таблица S2", init_s2,
                                          row=2, col=0, spin_attr='_s2_block')
        self._s3_cells = self._sbox_panel(right, "Таблица S3", init_s3,
                                          row=4, col=0, spin_attr='_s3_block')

        # Кнопки
        btn_frame = tk.Frame(right, bg=LGRAY)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=12, sticky='e')
        tk.Button(btn_frame, text="  Сформировать вариант  ",
                  font=('Arial', 10), width=22,
                  command=self._generate_variant
                  ).grid(row=0, column=0, pady=4)
        self._btn_encrypt = tk.Button(btn_frame, text="  Начать шифрование  ",
                                      font=('Arial', 10), width=22,
                                      state='disabled', command=self._do_encrypt)
        self._btn_encrypt.grid(row=1, column=0, pady=4)
        self._warn_lbl = tk.Label(btn_frame, text="", bg=LGRAY,
                                  font=('Arial', 8), fg=RED,
                                  wraplength=240, justify='center')
        self._warn_lbl.grid(row=2, column=0)

    def _on_delta_changed(self):
        """Разблокирует кнопку шифрования когда все 4 дельты полностью заполнены."""
        if not self.cipher:
            return
        all_filled = all(
            c.get() in ('0', '1')
            for cells in [self._dxl_cells, self._dxr_cells,
                          self._dyl_cells, self._dyr_cells]
            for c in cells
        )
        self._btn_encrypt.config(
            state='normal' if all_filled else 'disabled')

    def _sbox_panel(self, parent, title, init_data, row, col, spin_attr):
        """Создаёт панель: заголовок + сетка S-блока + спиннер 'Номер блока'."""
        tk.Label(parent, text=title, bg=LGRAY,
                 font=('Arial', 9, 'bold')).grid(row=row, column=col,
                                                  columnspan=2, sticky='w',
                                                  pady=(8, 0))
        sf = tk.Frame(parent, bg=LGRAY)
        sf.grid(row=row + 1, column=col, sticky='w')
        cells2d = make_sbox_grid(sf, init_data)

        ctrl = tk.Frame(parent, bg=LGRAY)
        ctrl.grid(row=row + 1, column=col + 1, padx=6, sticky='n')
        tk.Label(ctrl, text="Номер\nблока", bg=LGRAY, font=('Arial', 8)
                 ).grid(row=0, column=0)
        var = tk.IntVar(value=1)
        setattr(self, spin_attr, var)
        tk.Spinbox(ctrl, from_=1, to=5000, textvariable=var,
                   width=5, command=self._on_block_change
                   ).grid(row=1, column=0)
        return cells2d

    # ──────────────────────────────────────────────────────────────────────────
    #  Вкладка 2 и 3 — переопределяются в подклассах
    # ──────────────────────────────────────────────────────────────────────────
    def _build_tab2(self):
        raise NotImplementedError

    def _build_tab3(self):
        raise NotImplementedError

    # ──────────────────────────────────────────────────────────────────────────
    #  Логика кнопок (общая)
    # ──────────────────────────────────────────────────────────────────────────
    def _generate_variant(self):
        fio   = self.e_fio.get().strip()
        group = self.e_group.get().strip()
        if not fio or not group:
            messagebox.showwarning("Внимание", "Введите ФИО и номер группы.")
            return
        try:
            count = int(self.e_count.get())
            if not (1 <= count <= 5000):
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Количество текстов: от 1 до 5000.")
            return

        (self.s1, self.s2, self.s3,
         self.p_table, self.ep_table,
         self.master_key, self.round_keys) = VariantGen.generate(fio, group)
        self.plaintexts  = VariantGen.random_plaintexts(fio, group, count)
        self.ciphertexts = []
        self.traces      = []

        self.cipher = TeachingDES(self.s1, self.s2, self.s3,
                                   self.p_table, self.ep_table,
                                   self.round_keys)

        # Обновить S-сетки
        update_sbox_grid(self._s1_cells, self.s1)
        update_sbox_grid(self._s2_cells, self.s2)
        update_sbox_grid(self._s3_cells, self.s3)

        # P и EP
        set_ro_cells(self._p_cells,  self.p_table)
        set_ro_cells(self._ep_cells, self.ep_table)

        # Найти лучшую характеристику и подставить ΔXR
        alpha, prob, ep_val, d1, d2, d3 = find_best_f_differential(
            self.s1, self.s2, self.s3, self.ep_table)
        self._best_alpha = alpha

        ddt1 = compute_ddt_s1s2(self.s1)
        ddt2 = compute_ddt_s1s2(self.s2)
        ddt3 = compute_ddt_s3(self.s3)
        p1, p2, p3 = ddt1[d1][0], ddt2[d2][0], ddt3[d3][0]

        char_text = (
            f"Лучшая 1-раундовая харак. (ΔF=0):\n"
            f"  ΔXR = 0x{alpha:02X}  ({bits_str(alpha, 8)})\n"
            f"  EP(ΔXR) = 0x{ep_val:03X}  → δ1={d1:X} δ2={d2:X} δ3={d3:X}\n"
            f"  p = ({p1}/16)×({p2}/16)×({p3}/16) = {prob:.4f}  "
            f"[{characteristic_strength(prob)}]"
        )
        self._char_lbl.config(text=char_text)

        if prob < VariantGen.MIN_CHAR_PROB:
            self._warn_lbl.config(
                text=f"⚠ Слабая характеристика (p={prob:.4f}). "
                     "Рекомендуется увеличить кол-во текстов.")
        else:
            self._warn_lbl.config(text="")

        # Автоматически подставить рекомендуемый ΔXR; YL/YR студент вводит сам
        set_edit_cells(self._dxl_cells, [0] * 8)
        set_edit_cells(self._dxr_cells, [int(b) for b in bits_str(alpha, 8)])
        set_edit_cells(self._dyl_cells, [0] * 8)
        set_edit_cells(self._dyr_cells, [0] * 8)

        # Кнопка активна только когда все 4 дельты заполнены студентом
        self._btn_encrypt.config(state='disabled')
        self._on_variant_generated()   # хук для подкласса

    def _on_variant_generated(self):
        """Хук — вызывается после генерации варианта. Подкласс может переопределить."""
        pass

    def _do_encrypt(self):
        if not self.cipher:
            return
        # Читаем дельты — пустая ячейка считается за 0
        try:
            dxl_bits = [int(c.get()) if c.get() in ('0','1') else 0
                        for c in self._dxl_cells]
            dxr_bits = [int(c.get()) if c.get() in ('0','1') else 0
                        for c in self._dxr_cells]
        except ValueError:
            messagebox.showerror("Ошибка",
                                 "Дельты XL и XR должны содержать только 0 и 1.")
            return
        dxl = int("".join(map(str, dxl_bits)), 2)
        dxr = int("".join(map(str, dxr_bits)), 2)
        delta_x = (dxl << 8) | dxr

        # Шифруем все тексты
        self.ciphertexts, self.traces = [], []
        for pt in self.plaintexts:
            ct, trace = self.cipher.encrypt(pt)
            self.ciphertexts.append(ct)
            self.traces.append(trace)

        # Пара для первого блока
        pt  = self.plaintexts[0]
        ptp = pt ^ delta_x
        ct  = self.ciphertexts[0]
        ctp, _ = self.cipher.encrypt(ptp)
        delta_y = ct ^ ctp
        dyl = (delta_y >> 8) & 0xFF
        dyr =  delta_y       & 0xFF

        set_edit_cells(self._dyl_cells, [int(b) for b in bits_str(dyl, 8)])
        set_edit_cells(self._dyr_cells, [int(b) for b in bits_str(dyr, 8)])

        self._on_encrypt_done(delta_x, delta_y, pt, ptp, ct, ctp)
        self._on_block_change()

    def _on_encrypt_done(self, delta_x, delta_y, pt, ptp, ct, ctp):
        """Хук — вызывается после шифрования. Подкласс обновляет Tab2."""
        pass

    def _on_block_change(self):
        """Подсветить активную ячейку S-блоков для выбранного блока."""
        if not self.cipher or not self.traces:
            return
        idx = self._s1_block.get() - 1
        if 0 <= idx < len(self.traces):
            tr = self.traces[idx]
            for rnd in range(1, 4):
                if 's1_in' in tr[rnd]:
                    self._hl_s1s2(self._s1_cells, tr[rnd]['s1_in'])
                    self._hl_s1s2(self._s2_cells, tr[rnd]['s2_in'])
                    self._hl_s3(self._s3_cells,   tr[rnd]['s3_in'])
                    break  # показываем только раунд 1 для данного блока

    def _hl_s1s2(self, cells2d, inp4):
        for i, row in enumerate(cells2d):
            for j, c in enumerate(row):
                c.config(state='normal', bg=WHITE, fg='black',
                         disabledbackground=WHITE, disabledforeground='black')
                c.config(state='disabled')
        r, col = (inp4 >> 3) & 1, inp4 & 7
        if 0 <= r < len(cells2d) and 0 <= col < len(cells2d[0]):
            c = cells2d[r][col]
            c.config(state='normal', bg=BLUE, fg=WHITE,
                     disabledbackground=BLUE, disabledforeground=WHITE)
            c.config(state='disabled')

    def _hl_s3(self, cells2d, inp4):
        for i, row in enumerate(cells2d):
            for j, c in enumerate(row):
                c.config(state='normal', bg=WHITE, fg='black',
                         disabledbackground=WHITE, disabledforeground='black')
                c.config(state='disabled')
        r, col = (inp4 >> 2) & 3, inp4 & 3
        if 0 <= r < len(cells2d) and 0 <= col < len(cells2d[0]):
            c = cells2d[r][col]
            c.config(state='normal', bg=BLUE, fg=WHITE,
                     disabledbackground=BLUE, disabledforeground=WHITE)
            c.config(state='disabled')

    def _dialog_delta(self):
        """Вспомогательный диалог: задать ΔXL/ΔXR в шестнадцатеричном формате."""
        d = tk.Toplevel(self)
        d.title("Задать ΔXL / ΔXR (hex)")
        d.resizable(False, False)
        d.grab_set()
        tk.Label(d, text="ΔXL (hex):", font=('Arial', 9)
                 ).grid(row=0, column=0, padx=8, pady=4, sticky='e')
        e_xl = tk.Entry(d, width=6, font=('Consolas', 9))
        e_xl.insert(0, "00")
        e_xl.grid(row=0, column=1, padx=4)
        tk.Label(d, text="ΔXR (hex):", font=('Arial', 9)
                 ).grid(row=1, column=0, padx=8, pady=4, sticky='e')
        e_xr = tk.Entry(d, width=6, font=('Consolas', 9))
        e_xr.insert(0, f"{self._best_alpha:02X}")
        e_xr.grid(row=1, column=1, padx=4)

        def apply():
            try:
                xl = int(e_xl.get().strip(), 16) & 0xFF
                xr = int(e_xr.get().strip(), 16) & 0xFF
            except ValueError:
                messagebox.showerror("Ошибка", "Введите корректные hex-значения.",
                                     parent=d)
                return
            set_edit_cells(self._dxl_cells, [int(b) for b in bits_str(xl, 8)])
            set_edit_cells(self._dxr_cells, [int(b) for b in bits_str(xr, 8)])
            self._on_delta_changed()
            d.destroy()

        tk.Button(d, text="Применить", command=apply,
                  font=('Arial', 9)).grid(row=2, column=0, columnspan=2, pady=6)
