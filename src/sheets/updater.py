from __future__ import annotations

import re
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


def _norm_grupo(v: object) -> str:
    """
    ✅ Importante: NÃO zfill no grupo, porque no Sheets o grupo está como "6600".
    """
    return str(v).strip()

def _norm_num_str(v: object) -> str:
    s = str(v).strip()
    s_digits = re.sub(r"\D", "", s)
    if s_digits == "":
        return s
    return s_digits.lstrip("0") or "0"


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
    if green_rgb is None:
        green_rgb = {"red": 0.22, "green": 0.55, "blue": 0.24}

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
    sheet_name: str,
    read_range_a1: str,
    run_date: date,
    results: List[RPACotaStatus],
    token_path: str = "./token.json",
    paint_green: bool = True,
) -> Dict[str, Any]:
    service = get_sheets_service(token_path)
    sheets = service.spreadsheets()

    resp = sheets.values().get(
        spreadsheetId=spreadsheet_id,
        range=read_range_a1
    ).execute()

    raw_values = resp.get("values", [])
    values: List[List[str]] = [[str(c) for c in row] for row in raw_values]

    idx = build_index(values)

    month_col_name = month_header(run_date)
    if month_col_name not in idx.col_by_name:
        raise ValueError(f"Coluna do mês não encontrada: '{month_col_name}'.")

    month_col = idx.col_by_name[month_col_name]

    updates: List[UpdatePlan] = []

    for item in results:
        if not item.pago_confirmado:
            continue

        # ✅ chave agora bate com o Sheets: grupo "6600" e cota "0742"
        grupo_key = _norm_num_str(item.grupo)
        cota_key = _norm_num_str(item.cota)

        key = make_key(grupo_key, cota_key)
        row_index = idx.row_by_key.get(key)
        if row_index is None:
            continue

        row = idx.values[row_index] if row_index < len(idx.values) else []
        current = row[month_col] if month_col < len(row) else ""
        if not _is_empty_cell(current):
            continue

        value_to_write = (item.data_pagamento or "").strip()
        if not value_to_write:
            value_to_write = format_br(yesterday(run_date))

        col_a1 = col_to_a1(month_col)
        row_a1 = row_index + 1
        cell_range = f"{sheet_name}!{col_a1}{row_a1}"

        updates.append(UpdatePlan(
            range_a1=cell_range,
            row_index=row_index,
            col_index=month_col,
            value=value_to_write,
            reason=f"Pago confirmado; célula vazia em '{month_col_name}'"
        ))

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

    if paint_green:
        sheet_id = _get_sheet_id(service, spreadsheet_id, sheet_name)
        _apply_green_background(service, spreadsheet_id, sheet_id, updates)

    return {
        "updated": len(updates),
        "updates": [u.__dict__ for u in updates]
    }
