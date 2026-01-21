from __future__ import annotations
from datetime import date, timedelta, datetime
from typing import Iterable

COL_GRUPO = "Grupo"
COL_COTA = "Cota"

_MONTHS_PT = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

def month_header(d: date) -> str:
    return f"{_MONTHS_PT[d.month - 1]} - {d.year}"

def format_br(d: date) -> str:
    return d.strftime("%d/%m/%Y")

def yesterday(ref: date | datetime | None = None) -> date:
    """
    Retorna o último dia útil anterior (considera apenas fim de semana).
    - Sáb/Dom -> volta até sexta
    - Segunda -> volta até sexta
    - Ter..Sex -> volta 1 dia
    """
    if ref is None:
        ref_date = datetime.now().date()
    elif isinstance(ref, datetime):
        ref_date = ref.date()
    else:
        ref_date = ref

    d = ref_date - timedelta(days=1)
    while d.weekday() >= 5:  # 5=sábado, 6=domingo
        d -= timedelta(days=1)
    return d