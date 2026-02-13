from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .schema import COL_GRUPO, COL_COTA

# indexer.py
import re

def _norm_num_str(v: object) -> str:
    s = str(v).strip()
    # remove tudo que não é dígito (se quiser manter só números)
    s_digits = re.sub(r"\D", "", s)
    if s_digits == "":
        return s  # fallback
    # remove zeros à esquerda: "0089" -> "89"
    return s_digits.lstrip("0") or "0"

def make_key(grupo: str, cota: str) -> str:
    return f"{_norm_num_str(grupo)}::{_norm_num_str(cota)}"

@dataclass
class SheetIndex:
    header: List[str]
    col_by_name: Dict[str, int]
    row_by_key: Dict[str, int]
    values: List[List[str]]  # matriz completa (inclui header)

def build_index(values: List[List[str]]) -> SheetIndex:
    if not values:
        raise ValueError("Planilha vazia (sem linhas).")

    header = [(h or "").strip() for h in values[0]]
    col_by_name = {name: idx for idx, name in enumerate(header)}

    if COL_GRUPO not in col_by_name or COL_COTA not in col_by_name:
        raise ValueError(f"Header precisa conter colunas '{COL_GRUPO}' e '{COL_COTA}'.")

    g_col = col_by_name[COL_GRUPO]
    c_col = col_by_name[COL_COTA]

    row_by_key: Dict[str, int] = {}
    for r in range(1, len(values)):
        row = values[r] if r < len(values) else []
        grupo = (row[g_col] if g_col < len(row) else "") or ""
        cota = (row[c_col] if c_col < len(row) else "") or ""
        grupo = str(grupo).strip()
        cota = str(cota).strip()
        if not grupo or not cota:
            continue
        row_by_key[make_key(grupo, cota)] = r

    return SheetIndex(header=header, col_by_name=col_by_name, row_by_key=row_by_key, values=values)

def col_to_a1(col_index_0: int) -> str:
    # 0->A, 25->Z, 26->AA...
    n = col_index_0 + 1
    s = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        s = chr(65 + rem) + s
    return s
