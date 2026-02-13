from src.domain.types import RPACotaStatus

def _extrair_numero_cota(cota_str: str) -> int:
    s = (cota_str or "").strip()
    if "/" in s:
        s = s.split("/", 1)[1]
    if "-" in s:
        s = s.split("-", 1)[0]
    return int(s)

def newcon_result_to_cota_status(grupo: int, resultado_por_cota: dict) -> list[RPACotaStatus]:
    """
    Agora agrega por cota e calcula quantos boletos estão em aberto (dentro do cutoff).
    """
    por_cota_count: dict[int, int] = {}

    # resultado_por_cota["cotas"] pode vir com várias linhas por cota (cada boleto em aberto)
    for item in resultado_por_cota.get("cotas", []):
        cota_num = _extrair_numero_cota(item.get("cota", ""))
        em_aberto = bool(item.get("em_aberto", False))
        if em_aberto:
            por_cota_count[cota_num] = por_cota_count.get(cota_num, 0) + 1
        else:
            por_cota_count.setdefault(cota_num, 0)

    saida: list[RPACotaStatus] = []
    for cota_num, open_count in por_cota_count.items():
        saida.append(
            RPACotaStatus(
                grupo=int(grupo),
                cota=int(cota_num),
                pago_confirmado=(open_count == 0),
                data_pagamento=None,
                boletos_em_aberto=open_count,
            )
        )
    return saida