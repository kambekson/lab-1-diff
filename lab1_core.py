# -*- coding: utf-8 -*-
"""
lab1_core.py — общая логика учебного DES.
Импортируется и студенческой, и преподавательской версиями программы.
Гарантирует идентичность вариантов: одни и те же FIO+группа дают
одни и те же S-блоки, ключ и открытые тексты в обеих программах.
"""

import hashlib
import random


# ─────────────────────────────────────────────
#  Шифр: 3-раундовый Фейстель, блок 16 бит
# ─────────────────────────────────────────────

class TeachingDES:
    """
    Структура:
        блок 16 бит  (L=8 бит, R=8 бит)
        3 раунда Фейстеля
        F(R, K):
            1. EP: 8 → 12 бит
            2. XOR с 12-битным ключом раунда
            3. S1(4→3) | S2(4→3) | S3(4→2)  = 8 бит
            4. Перестановка P (8→8)
    """

    def __init__(self, s1, s2, s3, p_table, ep_table, round_keys):
        self.s1 = s1           # list[2][8], значения 0–7
        self.s2 = s2           # list[2][8], значения 0–7
        self.s3 = s3           # list[4][4], значения 0–3
        self.p  = p_table      # list[8], 1-based
        self.ep = ep_table     # list[12], 1-based
        self.rk = round_keys   # list[3] из 12-битных int

    # ── Внутренние операции ──────────────────────────
    def _expand(self, r8: int) -> int:
        bits = [(r8 >> (7 - i)) & 1 for i in range(8)]
        out  = [bits[pos - 1] for pos in self.ep]
        v = 0
        for b in out:
            v = (v << 1) | b
        return v

    def _sub(self, v12: int):
        g0 = (v12 >> 8) & 0xF
        g1 = (v12 >> 4) & 0xF
        g2 =  v12       & 0xF
        r0, c0 = (g0 >> 3) & 1, g0 & 0x7
        r1, c1 = (g1 >> 3) & 1, g1 & 0x7
        r2, c2 = (g2 >> 2) & 3, g2 & 0x3
        return self.s1[r0][c0], self.s2[r1][c1], self.s3[r2][c2]

    def _permute(self, v8: int) -> int:
        bits = [(v8 >> (7 - i)) & 1 for i in range(8)]
        out  = [bits[pos - 1] for pos in self.p]
        v = 0
        for b in out:
            v = (v << 1) | b
        return v

    # ── Функция раунда (возвращает значение + детали для трассировки) ──
    def F(self, r8: int, k12: int):
        exp    = self._expand(r8)
        xored  = exp ^ k12
        o1, o2, o3 = self._sub(xored)
        combined   = (o1 << 5) | (o2 << 2) | o3
        fout   = self._permute(combined)
        detail = (exp, xored, o1, o2, o3, combined)
        return fout, detail

    # ── Шифрование ───────────────────────────────────
    def encrypt(self, pt16: int):
        """Возвращает (ciphertext, trace).
        trace — список из 4 словарей (исходное состояние + 3 раунда)."""
        L = (pt16 >> 8) & 0xFF
        R =  pt16       & 0xFF
        trace = [{'L': L, 'R': R}]
        for i in range(3):
            fval, fdetail = self.F(R, self.rk[i])
            nL = R
            nR = L ^ fval
            trace.append({
                'L': nL, 'R': nR,
                'F_in': R, 'K': self.rk[i],
                'expanded': fdetail[0], 'xored': fdetail[1],
                's1_in': (fdetail[1] >> 8) & 0xF,
                's2_in': (fdetail[1] >> 4) & 0xF,
                's3_in':  fdetail[1]        & 0xF,
                's1_out': fdetail[2], 's2_out': fdetail[3],
                's3_out': fdetail[4],
                'F_out': fval,
            })
            L, R = nL, nR
        return (L << 8) | R, trace

    # ── Расшифрование ─────────────────────────────────
    def decrypt(self, ct16: int) -> int:
        L = (ct16 >> 8) & 0xFF
        R =  ct16       & 0xFF
        for i in range(2, -1, -1):
            fval, _ = self.F(L, self.rk[i])
            nR = L
            nL = R ^ fval
            L, R = nL, nR
        return (L << 8) | R


# ─────────────────────────────────────────────
#  DDT (Differential Distribution Table)
# ─────────────────────────────────────────────

def compute_ddt_s1s2(sbox_2x8):
    """DDT для S1/S2: вход 4 бит → выход 3 бита; таблица 16×8."""
    ddt = [[0] * 8 for _ in range(16)]
    for dx in range(16):
        for x in range(16):
            xp         = x ^ dx
            row_x,  col_x  = (x  >> 3) & 1, x  & 7
            row_xp, col_xp = (xp >> 3) & 1, xp & 7
            y  = sbox_2x8[row_x ][col_x ]
            yp = sbox_2x8[row_xp][col_xp]
            ddt[dx][y ^ yp] += 1
    return ddt


def compute_ddt_s3(sbox_4x4):
    """DDT для S3: вход 4 бита → выход 2 бита; таблица 16×4."""
    ddt = [[0] * 4 for _ in range(16)]
    for dx in range(16):
        for x in range(16):
            xp         = x ^ dx
            row_x,  col_x  = (x  >> 2) & 3, x  & 3
            row_xp, col_xp = (xp >> 2) & 3, xp & 3
            y  = sbox_4x4[row_x ][col_x ]
            yp = sbox_4x4[row_xp][col_xp]
            ddt[dx][y ^ yp] += 1
    return ddt


def best_differentials(ddt, skip_dx0=True):
    """Список (dx, dy, count) по убыванию count."""
    result = []
    for dx, row in enumerate(ddt):
        if skip_dx0 and dx == 0:
            continue
        for dy, cnt in enumerate(row):
            if cnt > 0:
                result.append((dx, dy, cnt))
    result.sort(key=lambda x: -x[2])
    return result


# ─────────────────────────────────────────────
#  Поиск лучшей 1-раундовой характеристики F
# ─────────────────────────────────────────────

def find_best_f_differential(s1, s2, s3, ep):
    """
    Перебирает все ΔR (1…255) и вычисляет точную вероятность
    P(ΔF = 0 | ΔR = α) = DDT_S1[δ1][0]/16 · DDT_S2[δ2][0]/16 · DDT_S3[δ3][0]/16,
    где δ = EP(α) не зависит от R и K (EP линейна).

    Возвращает (alpha, prob, ep_val, d1, d2, d3).
    """
    ddt1 = compute_ddt_s1s2(s1)
    ddt2 = compute_ddt_s1s2(s2)
    ddt3 = compute_ddt_s3(s3)

    best = (0, 0.0, 0, 0, 0, 0)
    for alpha in range(1, 256):
        bits    = [(alpha >> (7 - i)) & 1 for i in range(8)]
        ep_bits = [bits[pos - 1] for pos in ep]
        ep_val  = 0
        for b in ep_bits:
            ep_val = (ep_val << 1) | b
        d1 = (ep_val >> 8) & 0xF
        d2 = (ep_val >> 4) & 0xF
        d3 =  ep_val       & 0xF
        p  = (ddt1[d1][0] / 16.0) * (ddt2[d2][0] / 16.0) * (ddt3[d3][0] / 16.0)
        if p > best[1]:
            best = (alpha, p, ep_val, d1, d2, d3)
    return best


def characteristic_strength(prob: float) -> str:
    if prob >= 0.5:   return "Отличная (p ≥ 1/2)"
    if prob >= 0.25:  return "Хорошая (p ≥ 1/4)"
    if prob >= 0.125: return "Удовлетворительная (p ≥ 1/8)"
    if prob >= 0.0625:return "Слабая (p ≥ 1/16) — увеличьте кол-во текстов"
    return "Неудовлетворительная — вариант не подходит для анализа"


# ─────────────────────────────────────────────
#  Генерация варианта (детерминированная по FIO+группа)
# ─────────────────────────────────────────────

class VariantGen:
    MIN_CHAR_PROB = 0.125  # минимальная вероятность характеристики

    @staticmethod
    def generate(fio: str, group: str):
        """
        Генерирует вариант: S1, S2, S3, P, EP, master_key, round_keys.
        Гарантирует вероятность лучшей 1-раундовой характеристики ≥ MIN_CHAR_PROB
        (до 30 попыток; при неудаче берёт наилучший найденный).
        """
        raw  = (fio.strip().lower() + "|" + group.strip().lower()).encode()
        seed = int.from_bytes(hashlib.sha256(raw).digest()[:8], 'big')
        rng  = random.Random(seed)

        best_result, best_prob = None, -1.0
        for _ in range(30):
            s1 = VariantGen._sbox_2x8(rng)
            s2 = VariantGen._sbox_2x8(rng)
            s3 = VariantGen._sbox_4x4(rng)
            p  = VariantGen._perm(rng, 8)
            ep = VariantGen._ep(rng)
            mk = rng.randint(0, 0xFFFFFF)
            rk0 = (mk >> 12) & 0xFFF
            rk1 = ((mk ^ (mk >> 6)) >> 6) & 0xFFF
            rk2 =  mk & 0xFFF
            result = (s1, s2, s3, p, ep, mk, [rk0, rk1, rk2])
            _, prob, *_ = find_best_f_differential(s1, s2, s3, ep)
            if prob > best_prob:
                best_prob, best_result = prob, result
            if prob >= VariantGen.MIN_CHAR_PROB:
                break
        return best_result

    # ── Внутренние генераторы S-блоков ─────────────────────────────────────

    @staticmethod
    def _sbox_2x8(rng):
        """
        2×8, значения 0–7.
        row1 = row0 с 1–2 swap-ами → 4–6 совпадающих позиций
        → DDT[8][0] ∈ {4,6,8} → вероятность нулевого выхода при ΔR=α ≥ 1/4.
        """
        row0 = list(range(8))
        rng.shuffle(row0)
        row1 = row0[:]
        n_swaps = rng.choice([1, 2])
        positions = list(range(8))
        rng.shuffle(positions)
        for i in range(n_swaps):
            a, b = positions[i * 2], positions[i * 2 + 1]
            row1[a], row1[b] = row1[b], row1[a]
        return [row0, row1]

    @staticmethod
    def _sbox_4x4(rng):
        """
        4×4, значения 0–3.
        row2 ≈ row0 (1 отличие), row3 ≈ row1 (1 отличие)
        → DDT_S3[8][0] ≥ 6.
        """
        row0 = [rng.randint(0, 3) for _ in range(4)]
        row2 = row0[:]
        row1 = [rng.randint(0, 3) for _ in range(4)]
        row3 = row1[:]
        pos2 = rng.randint(0, 3)
        row2[pos2] = (row0[pos2] + 1 + rng.randint(0, 1)) & 3
        pos3 = rng.randint(0, 3)
        row3[pos3] = (row1[pos3] + 1 + rng.randint(0, 1)) & 3
        return [row0, row1, row2, row3]

    @staticmethod
    def _perm(rng, n):
        p = list(range(1, n + 1))
        rng.shuffle(p)
        return p

    @staticmethod
    def _ep(rng):
        base  = list(range(1, 9))
        extra = [rng.choice([1, 2, 4, 5, 6, 8]) for _ in range(4)]
        ep    = base + extra
        rng.shuffle(ep)
        return ep

    @staticmethod
    def random_plaintexts(fio: str, group: str, count: int):
        """Детерминированная по FIO+группа последовательность открытых текстов."""
        raw  = (fio.strip().lower() + "|" + group.strip().lower() + "|pts").encode()
        seed = int.from_bytes(hashlib.sha256(raw).digest()[:8], 'big')
        rng  = random.Random(seed)
        return [rng.randint(0, 0xFFFF) for _ in range(count)]


# ─────────────────────────────────────────────
#  Вспомогательные функции (биты, строки)
# ─────────────────────────────────────────────

def bits_str(val: int, n: int) -> str:
    return format(val, f'0{n}b')
