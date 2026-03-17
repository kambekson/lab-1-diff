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
    """Создаёт редактируемую сетку Entry для S-блока. Возвращает cells2d."""
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
                         bg=bg, fg=fg,
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
            c.config(bg=bg, fg=fg)
            c.delete(0, 'end')
            c.insert(0, str(val))


def set_ro_cells(cells, values):
    """Записать значения в ряд ячеек."""
    for c, v in zip(cells, values):
        c.delete(0, 'end')
        c.insert(0, str(v))


def make_bit_row(parent, n, color=BLUE):
    """Ряд из n редактируемых Entry (для P, EP)."""
    cells = []
    for i in range(n):
        bg = color if i == 0 else WHITE
        fg = WHITE if i == 0 else "black"
        e = tk.Entry(parent, width=3, justify='center',
                     relief='solid', bd=1,
                     bg=bg, fg=fg,
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

    TITLE     = "Лабораторная работа №1"
    GEOMETRY  = "1440x900"  # ширина × высота по умолчанию
    SHOW_HINT = False        # True только в TeacherApp

    def __init__(self):
        super().__init__()
        self.title(self.TITLE)
        self.resizable(True, True)
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

        self.tab1    = tk.Frame(nb, bg=LGRAY)
        self.tab2    = tk.Frame(nb, bg=LGRAY)
        self.tab3    = tk.Frame(nb, bg=LGRAY)
        self.tab_ddt = tk.Frame(nb, bg=LGRAY)

        nb.add(self.tab1,    text="  Исходные данные  ")
        nb.add(self.tab2,    text="  Результат шифрования  ")
        nb.add(self.tab3,    text="  Проверка  ")
        nb.add(self.tab_ddt, text="  DDT S-блоков  ")

        self._build_tab1()
        self._build_tab2()      # реализуется в подклассе
        self._build_tab3()      # реализуется в подклассе
        self._build_tab_ddt()

    # ── Вкладка DDT ────────────────────────────────────────────────────────────
    @staticmethod
    def _fmt_frac(count, denom=16):
        """Вернуть строку вида '3/8', '1/2', '1', '0' для count/denom."""
        from math import gcd
        if count == 0:
            return '0'
        g = gcd(count, denom)
        n, d = count // g, denom // g
        return str(n) if d == 1 else f'{n}/{d}'

    def _build_tab_ddt(self):
        t = self.tab_ddt

        tk.Label(t,
            text=("Вероятностная таблица дифференциального анализа.\n"
                  "Ячейка [ΔA][ΔC] = #{x : S(x)⊕S(x⊕ΔA)=ΔC} / 16.  "
                  "Столбец ΔC=0 — вероятность сохранения разности; "
                  "голубым выделена строка с наилучшей характеристикой."),
            bg=LGRAY, font=('Arial', 10), justify='left', wraplength=900
        ).pack(padx=10, pady=(8, 4), anchor='w')

        leg = tk.Frame(t, bg=LGRAY)
        leg.pack(padx=10, pady=(0, 8), anchor='w')
        for clr, lbl in [
                ('#C8E6C9', 'ΔC=0, p ≥ 1/2'),
                ('#FFF9C4', 'ΔC=0, p = 1/4–7/16'),
                ('#FFCDD2', 'ΔC=0, p < 1/4'),
                ('#E0E0E0', '0'),
                ('#B3E5FC', 'Лучшая строка для атаки'),
        ]:
            f = tk.Frame(leg, bg=clr, relief='solid', bd=1, width=18, height=18)
            f.grid_propagate(False)
            f.pack(side='left', padx=(0, 3))
            tk.Label(leg, text=lbl, bg=LGRAY, font=('Arial', 10)
                     ).pack(side='left', padx=(0, 14))

        tk.Button(
            t,
            text='Сделать анализ',
            font=('Arial', 10, 'bold'),
            command=self._update_ddt
        ).pack(padx=10, pady=(0, 8), anchor='w')

        sb_y = ttk.Scrollbar(t, orient='vertical')
        sb_y.pack(side='right', fill='y')
        sb_x = ttk.Scrollbar(t, orient='horizontal')
        sb_x.pack(side='bottom', fill='x')
        sc = tk.Canvas(t, bg=LGRAY, highlightthickness=0,
                       yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        sc.pack(side='left', fill='both', expand=True, padx=(10, 0))
        sb_y.config(command=sc.yview)
        sb_x.config(command=sc.xview)

        inner = tk.Frame(sc, bg=LGRAY)
        sc.create_window((0, 0), window=inner, anchor='nw')
        inner.bind('<Configure>',
                   lambda e: sc.configure(scrollregion=sc.bbox('all')))

        PURPLE  = '#CE93D8'   # фон заголовков ΔC / ΔA
        PRP_FG  = '#4A148C'   # текст заголовков
        HDR_FNT = ('Arial', 11, 'bold')
        ROW_FNT = ('Consolas', 11, 'bold')
        CEL_FNT = ('Consolas', 11)
        CEL_W   = 6   # ширина ячейки данных
        ROW_W   = 6   # ширина заголовка строки (binary)

        # S1/S2 — 3-битный выход (8 колонок), S3 — 2-битный (4 колонки)
        specs = [('S1', 8, 3, '₁'), ('S2', 8, 3, '₂'), ('S3', 4, 2, '₃')]

        self._ddt_tables = {}
        for col_offset, (name, n_out, out_bits, sub) in enumerate(specs):
            frame = tk.Frame(inner, bg=LGRAY, relief='groove', bd=2)
            frame.grid(row=0, column=col_offset, padx=12, pady=8, sticky='n')

            # ── Заголовок таблицы ──────────────────────────────────────────
            tk.Label(frame,
                     text=f'Вероятностная таблица анализа\nдля блока замены {name}',
                     bg=LGRAY, font=('Arial', 11, 'bold'), justify='center'
                     ).grid(row=0, column=0, columnspan=n_out+1,
                            pady=(6, 4), padx=4)

            # ── Строка 1: угол пустой + ΔC{sub} spanning n_out столбцов ───
            tk.Label(frame, text='', bg=PURPLE,
                     relief='solid', bd=1, width=ROW_W
                     ).grid(row=1, column=0, padx=1, pady=1, ipady=4)
            tk.Label(frame, text=f'ΔC{sub}',
                     bg=PURPLE, fg=PRP_FG, font=HDR_FNT,
                     relief='solid', bd=1
                     ).grid(row=1, column=1, columnspan=n_out,
                            sticky='ew', padx=1, pady=1, ipady=4)

            # ── Строка 2: ΔA{sub} + бинарные значения выхода ───────────────
            tk.Label(frame, text=f'ΔA{sub}',
                     bg=PURPLE, fg=PRP_FG, font=HDR_FNT,
                     relief='solid', bd=1, width=ROW_W
                     ).grid(row=2, column=0, padx=1, pady=1, ipady=3)
            for j in range(n_out):
                hdr_bg = '#1565C0' if j == 0 else PURPLE
                hdr_fg = WHITE     if j == 0 else PRP_FG
                tk.Label(frame,
                         text=format(j, f'0{out_bits}b'),
                         bg=hdr_bg, fg=hdr_fg, font=HDR_FNT,
                         relief='solid', bd=1, width=CEL_W
                         ).grid(row=2, column=j+1, padx=1, pady=1, ipady=3)

            # ── Строки данных ──────────────────────────────────────────────
            rows_labels = []
            for i in range(16):
                tk.Label(frame,
                         text=format(i, '04b'),
                         bg=PURPLE, fg=PRP_FG, font=ROW_FNT,
                         relief='solid', bd=1, width=ROW_W
                         ).grid(row=i+3, column=0, padx=1, pady=1, ipady=2)
                row_lbls = []
                for j in range(n_out):
                    lbl = tk.Label(frame, text='-', bg=WHITE,
                                   font=CEL_FNT, width=CEL_W,
                                   relief='solid', bd=1)
                    lbl.grid(row=i+3, column=j+1, padx=1, pady=1, ipady=2)
                    row_lbls.append(lbl)
                rows_labels.append(row_lbls)

            self._ddt_tables[name] = rows_labels

    def _clear_ddt(self):
        """Очистить DDT-таблицы до запуска анализа."""
        for rows in self._ddt_tables.values():
            for row_lbls in rows:
                for lbl in row_lbls:
                    lbl.config(text='-', bg=WHITE, font=('Consolas', 11, 'normal'))

    def _update_ddt(self):
        """Заполнить DDT-таблицы по текущим s1, s2, s3."""
        ddt1 = compute_ddt_s1s2(self.s1)
        ddt2 = compute_ddt_s1s2(self.s2)
        ddt3 = compute_ddt_s3(self.s3)

        def _fill(name, ddt, n_out):
            rows  = self._ddt_tables[name]
            best_row = max(range(1, 16), key=lambda i: ddt[i][0])
            for i, row_lbls in enumerate(rows):
                for j, lbl in enumerate(row_lbls):
                    val  = ddt[i][j]
                    text = self._fmt_frac(val)
                    # цвет фона
                    if val == 0:
                        bg = '#E0E0E0'
                    elif j == 0 and i > 0:
                        if   val >= 8: bg = '#C8E6C9'
                        elif val >= 4: bg = '#FFF9C4'
                        else:          bg = '#FFCDD2'
                    else:
                        bg = WHITE
                    if i == best_row and i > 0:
                        bg = '#B3E5FC'
                    bold = (j == 0 and i > 0)
                    lbl.config(text=text, bg=bg,
                               font=('Consolas', 11,
                                     'bold' if bold else 'normal'))

        _fill('S1', ddt1, 8)
        _fill('S2', ddt2, 8)
        _fill('S3', ddt3, 4)

    # ── \u0412\u043a\u043b\u0430\u0434\u043a\u0430 1 \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    def _build_tab1(self):
        t = self.tab1

        # ---- Левая колонка ----
        left = tk.Frame(t, bg=LGRAY)
        left.grid(row=0, column=0, sticky='nw', padx=8, pady=8)

        tk.Label(left, text="ФИО студента:", bg=LGRAY,
                 font=('Arial', 9)).grid(row=0, column=0, sticky='w')
        self.e_fio = tk.Entry(left, width=30, font=('Arial', 9))
        self.e_fio.insert(0, "Иванов Иван Иванович")
        self.e_fio.grid(row=1, column=0, pady=2, sticky='w')

        tk.Label(left, text="Номер группы:", bg=LGRAY,
                 font=('Arial', 9)).grid(row=2, column=0, sticky='w', pady=(6, 0))
        self.e_group = tk.Entry(left, width=30, font=('Arial', 9))
        self.e_group.insert(0, "И-18")
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
        set_ro_cells(self._p_cells, [8, 7, 3, 2, 5, 4, 1, 6])

        # Таблица EP
        tk.Label(left, text="Таблица перестановки с расширением", bg=LGRAY,
                 font=('Arial', 9)).grid(row=8, column=0, sticky='w', pady=(6, 0))
        epf = tk.Frame(left, bg=LGRAY)
        epf.grid(row=9, column=0, sticky='w')
        self._ep_cells = make_bit_row(epf, 12, BLUE)
        set_ro_cells(self._ep_cells, [4, 6, 3, 2, 1, 5, 8, 7, 4, 1, 6, 3])

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

        init_s1 = [[4, 6, 6, 3, 1, 3, 7, 4], [5, 1, 5, 7, 2, 0, 0, 2]]
        init_s2 = [[6, 3, 6, 0, 4, 1, 7, 2], [3, 5, 1, 7, 2, 4, 0, 5]]
        init_s3 = [[0, 0, 0, 2], [1, 1, 2, 2], [2, 0, 3, 3], [1, 1, 3, 3]]

        # S1, S2, S3 — общий конструктор
        self._s1_cells = self._sbox_panel(right, "Таблица S1", init_s1, row=0, col=0)
        self._s2_cells = self._sbox_panel(right, "Таблица S2", init_s2, row=2, col=0)
        self._s3_cells = self._sbox_panel(right, "Таблица S3", init_s3, row=4, col=0)

        # Инициализировать шифр значениями по умолчанию
        self._init_default_cipher(init_s1, init_s2, init_s3,
                                   [8, 7, 3, 2, 5, 4, 1, 6],
                                   [4, 6, 3, 2, 1, 5, 8, 7, 4, 1, 6, 3])

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

    def _sbox_panel(self, parent, title, init_data, row, col):
        """Создаёт панель: заголовок + сетка S-блока."""
        tk.Label(parent, text=title, bg=LGRAY,
                 font=('Arial', 9, 'bold')).grid(row=row, column=col,
                                                  sticky='w', pady=(8, 0))
        sf = tk.Frame(parent, bg=LGRAY)
        sf.grid(row=row + 1, column=col, sticky='w')
        return make_sbox_grid(sf, init_data)

    def _init_default_cipher(self, s1, s2, s3, p_table, ep_table):
        """Инициализировать шифр значениями по умолчанию (без генерации варианта)."""
        fio   = self.e_fio.get().strip()
        group = self.e_group.get().strip()
        try:
            (_, _, _,
             _, _,
             self.master_key, self.round_keys) = VariantGen.generate(fio, group)
        except Exception:
            self.master_key = self.round_keys = None
        self.s1, self.s2, self.s3 = s1, s2, s3
        self.p_table, self.ep_table = p_table, ep_table
        self.plaintexts  = VariantGen.random_plaintexts(fio, group, 1) if self.master_key else []
        self.ciphertexts = []
        self.traces      = []
        if self.round_keys is not None:
            self.cipher = TeachingDES(s1, s2, s3, p_table, ep_table, self.round_keys)
        # Обновить рекомендуемую характеристику
        from lab1_core import find_best_f_differential, bits_str, characteristic_strength
        from lab1_core import compute_ddt_s1s2, compute_ddt_s3
        alpha, prob, ep_val, d1, d2, d3 = find_best_f_differential(
            s1, s2, s3, ep_table)
        self._best_alpha = alpha
        if self.SHOW_HINT:
            ddt1 = compute_ddt_s1s2(s1)
            ddt2 = compute_ddt_s1s2(s2)
            ddt3 = compute_ddt_s3(s3)
            p1, p2, p3 = ddt1[d1][0], ddt2[d2][0], ddt3[d3][0]
            char_text = (
                f"Лучшая 1-раундовая харак. (ΔF=0):\n"
                f"  ΔXR = 0x{alpha:02X}  ({bits_str(alpha, 8)})\n"
                f"  EP(ΔXR) = 0x{ep_val:03X}  → δ1={d1:X} δ2={d2:X} δ3={d3:X}\n"
                f"  p = ({p1}/16)×({p2}/16)×({p3}/16) = {prob:.4f}  "
                f"[{characteristic_strength(prob)}]"
            )
            self._char_lbl.config(text=char_text)
            set_edit_cells(self._dxl_cells, [0] * 8)
            set_edit_cells(self._dxr_cells, [int(b) for b in bits_str(alpha, 8)])

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

        if self.SHOW_HINT:
            char_text = (
                f"Лучшая 1-раундовая харак. (ΔF=0):\n"
                f"  ΔXR = 0x{alpha:02X}  ({bits_str(alpha, 8)})\n"
                f"  EP(ΔXR) = 0x{ep_val:03X}  → δ1={d1:X} δ2={d2:X} δ3={d3:X}\n"
                f"  p = ({p1}/16)×({p2}/16)×({p3}/16) = {prob:.4f}  "
                f"[{characteristic_strength(prob)}]"
            )
            self._char_lbl.config(text=char_text)
            # Преподавательская версия: автоподставляем рекомендуемый ΔXR
            set_edit_cells(self._dxl_cells, [0] * 8)
            set_edit_cells(self._dxr_cells, [int(b) for b in bits_str(alpha, 8)])
        else:
            self._char_lbl.config(text="")
            # Студент находит дельты самостоятельно
            set_edit_cells(self._dxl_cells, [0] * 8)
            set_edit_cells(self._dxr_cells, [0] * 8)

        if prob < VariantGen.MIN_CHAR_PROB:
            self._warn_lbl.config(
                text=f"⚠ Слабая характеристика (p={prob:.4f}). "
                     "Рекомендуется увеличить кол-во текстов.")
        else:
            self._warn_lbl.config(text="")

        set_edit_cells(self._dyl_cells, [0] * 8)
        set_edit_cells(self._dyr_cells, [0] * 8)

        # Кнопка активна только когда все 4 дельты заполнены студентом
        self._btn_encrypt.config(state='disabled')
        self._clear_ddt()
        self._on_variant_generated()   # хук для подкласса

    def _on_variant_generated(self):
        """Хук — вызывается после генерации варианта. Подкласс может переопределить."""
        pass

    def _do_encrypt(self):
        if not self.cipher:
            return
        # Читаем таблицы из UI и пересоздаём шифр с актуальными значениями
        try:
            p_table  = [int(c.get()) for c in self._p_cells]
            ep_table = [int(c.get()) for c in self._ep_cells]
            s1 = [[int(c.get()) for c in row] for row in self._s1_cells]
            s2 = [[int(c.get()) for c in row] for row in self._s2_cells]
            s3 = [[int(c.get()) for c in row] for row in self._s3_cells]
        except ValueError:
            messagebox.showerror("Ошибка",
                                 "Таблицы содержат некорректные значения.")
            return
        self.p_table  = p_table
        self.ep_table = ep_table
        self.s1 = s1;  self.s2 = s2;  self.s3 = s3
        self.cipher = TeachingDES(self.s1, self.s2, self.s3,
                                   self.p_table, self.ep_table,
                                   self.round_keys)
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
        """Подсветить активную ячейку S-блоков для первого блока."""
        if not self.cipher or not self.traces:
            return
        idx = 0
        if 0 <= idx < len(self.traces):
            tr = self.traces[idx]
            for rnd in range(1, 4):
                if 's1_in' in tr[rnd]:
                    self._hl_s1s2(self._s1_cells, tr[rnd]['s1_in'])
                    self._hl_s1s2(self._s2_cells, tr[rnd]['s2_in'])
                    self._hl_s3(self._s3_cells,   tr[rnd]['s3_in'])
                    break  # показываем только раунд 1 для данного блока

    def _hl_s1s2(self, cells2d, inp4):
        for row in cells2d:
            for c in row:
                c.config(bg=WHITE, fg='black')
        r, col = (inp4 >> 3) & 1, inp4 & 7
        if 0 <= r < len(cells2d) and 0 <= col < len(cells2d[0]):
            cells2d[r][col].config(bg=BLUE, fg=WHITE)

    def _hl_s3(self, cells2d, inp4):
        for row in cells2d:
            for c in row:
                c.config(bg=WHITE, fg='black')
        r, col = (inp4 >> 2) & 3, inp4 & 3
        if 0 <= r < len(cells2d) and 0 <= col < len(cells2d[0]):
            cells2d[r][col].config(bg=BLUE, fg=WHITE)

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
