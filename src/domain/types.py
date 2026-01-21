from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Union

NumStr = Union[int, str]

@dataclass(frozen=True)
class RPACotaStatus:
    grupo: NumStr
    cota: NumStr
    pago_confirmado: bool
    # opcional: se sua RPA conseguir a data real do pagamento no sistema:
    data_pagamento: Optional[str] = None  # "dd/mm/aaaa"
