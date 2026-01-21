from src.domain.types import RPACotaStatus

def _extrair_numero_cota(cota_str: str) -> int:
    # "006650/1736-00" -> 1736
    s = (cota_str or "").strip()
    if "/" in s:
        s = s.split("/", 1)[1]
    if "-" in s:
        s = s.split("-", 1)[0]
    return int(s)

def newcon_result_to_cota_status(grupo: int, resultado_por_cota: dict) -> list[RPACotaStatus]:
    """
    Espera algo no formato:
    {"cotas": [{"cota": "...", "em_aberto": bool, ...}, ...]}
    """
    saida: list[RPACotaStatus] = []
    for item in resultado_por_cota.get("cotas", []):
        cota_num = _extrair_numero_cota(item.get("cota", ""))
        em_aberto = bool(item.get("em_aberto", False))

        saida.append(
            RPACotaStatus(
                grupo=int(grupo),
                cota=int(cota_num),
                pago_confirmado=not em_aberto,
                data_pagamento=None,
            )
        )
    return saida
