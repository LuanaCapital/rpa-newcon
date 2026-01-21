from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional

from googleapiclient.discovery import Resource

from src.domain.types import RPACotaStatus
from src.sheets.client import get_sheets_service
from src.sheets.indexer import build_index, make_key, col_to_a1
from src.sheets.schema import month_header, format_br, yesterday


@dataclass
class UpdatePlan:
    range_a1: str
    row_index: int      # 0-based
    col_index: int      # 0-based
    value: str
    reason: str


def _is_empty_cell(v: Optional[str]) -> bool:
    if v is None:
        return True
    s = str(v).strip()
    return s == "" or s.lower() == "nan"


def _get_sheet_id(service: Resource, spreadsheet_id: str, sheet_name: str) -> int:
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for sh in meta.get("sheets", []):
        props = sh.get("properties", {})
        if props.get("title") == sheet_name:
            return int(props["sheetId"])
    raise ValueError(f"Aba '{sheet_name}' não encontrada no spreadsheet.")


def _apply_green_background(
    service: Resource,
    spreadsheet_id: str,
    sheet_id: int,
    updates: List[UpdatePlan],
    *,
    green_rgb: Dict[str, float] | None = None,
) -> None:
    # Verde padrão (suave)
    if green_rgb is None:
        green_rgb = {"red": 0.22,
        "green": 0.55,
        "blue": 0.24,}

    requests: List[Dict[str, Any]] = []
    for u in updates:
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": u.row_index,
                    "endRowIndex": u.row_index + 1,
                    "startColumnIndex": u.col_index,
                    "endColumnIndex": u.col_index + 1,
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {
                            "red": float(green_rgb["red"]),
                            "green": float(green_rgb["green"]),
                            "blue": float(green_rgb["blue"]),
                        }
                    }
                },
                "fields": "userEnteredFormat.backgroundColor",
            }
        })

    if not requests:
        return

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requests},
    ).execute()


def sync_payments_to_sheet(
    *,
    spreadsheet_id: str,
    sheet_name: str,       # nome da aba (ex: "pag2")
    read_range_a1: str,    # ex: "pag2!A1:ZZ"
    run_date: date,        # data da execução (ex: date.today())
    results: List[RPACotaStatus],
    token_path: str = "./token.json",
    paint_green: bool = True,
) -> Dict[str, Any]:
    """
    Atualiza a coluna do mês correspondente à run_date (ex: "Janeiro - 2026")
    preenchendo com a data do pagamento (se vier) ou com ontem (run_date - 1),
    e opcionalmente pinta a célula de verde.

    Regras:
    - Só atualiza se item.pago_confirmado == True
    - Só escreve se a célula estiver vazia
    - Não sobrescreve valores existentes (inclusive textos como "1 PARC")
    - Ignora cotas que não existirem na planilha (Grupo+Cota)
    """

    service = get_sheets_service(token_path)
    sheets = service.spreadsheets()

    # 1) Ler valores
    resp = sheets.values().get(
        spreadsheetId=spreadsheet_id,
        range=read_range_a1
    ).execute()

    raw_values = resp.get("values", [])
    # Mantém matriz irregular, mas normaliza células para string
    values: List[List[str]] = [[str(c) for c in row] for row in raw_values]

    idx = build_index(values)

    # 2) Coluna do mês alvo
    month_col_name = month_header(run_date)  # "Janeiro - 2026"
    if month_col_name not in idx.col_by_name:
        raise ValueError(f"Coluna do mês não encontrada: '{month_col_name}'.")

    month_col = idx.col_by_name[month_col_name]

    # 3) Montar plano de updates
    updates: List[UpdatePlan] = []

    for item in results:
        if not item.pago_confirmado:
            continue

        key = make_key(str(item.grupo), str(item.cota))
        row_index = idx.row_by_key.get(key)
        if row_index is None:
            continue  # cota não existe na planilha

        row = idx.values[row_index] if row_index < len(idx.values) else []
        current = row[month_col] if month_col < len(row) else ""
        if not _is_empty_cell(current):
            continue  # não sobrescreve

        value_to_write = (item.data_pagamento or "").strip()
        if not value_to_write:
            value_to_write = format_br(yesterday(run_date))

        col_a1 = col_to_a1(month_col)
        row_a1 = row_index + 1  # A1 é 1-based
        cell_range = f"{sheet_name}!{col_a1}{row_a1}"

        updates.append(UpdatePlan(
            range_a1=cell_range,
            row_index=row_index,
            col_index=month_col,
            value=value_to_write,
            reason=f"Pago confirmado; célula vazia em '{month_col_name}'"
        ))

    # 4) Escrever valores em lote
    if not updates:
        return {"updated": 0, "updates": []}

    body = {
        "valueInputOption": "USER_ENTERED",
        "data": [{"range": u.range_a1, "values": [[u.value]]} for u in updates]
    }

    sheets.values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body
    ).execute()

    # 5) Pintar fundo verde (opcional)
    if paint_green:
        sheet_id = _get_sheet_id(service, spreadsheet_id, sheet_name)
        _apply_green_background(service, spreadsheet_id, sheet_id, updates)

    return {
        "updated": len(updates),
        "updates": [u.__dict__ for u in updates]
    }