from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Union

NumStr = Union[int, str]

@dataclass(frozen=True)
class RPACotaStatus:
    grupo: NumStr
    cota: NumStr
    pago_confirmado: bool
    data_pagamento: Optional[str] = None
    boletos_em_aberto: int = 0