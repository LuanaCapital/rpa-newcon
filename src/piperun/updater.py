from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional

from src.domain.types import RPACotaStatus
from src.piperun.client import PipeRunClient
from utils.betterstack_logger import get_logger

RETENTION_PIPELINE_ID = int(os.getenv("PIPERUN_RETENTION_PIPELINE_ID", "97775"))
RETENTION_STAGE_ID = int(os.getenv("PIPERUN_RETENTION_STAGE_ID", "625639"))

logger = get_logger(__name__)

@dataclass
class DealUpdateResult:
    deal_id: int
    grupo: str
    cota: str
    payload: Dict[str, Any]
    reason: str
    response: Dict[str, Any]


def _norm_num_str(v: object) -> str:
    s = "" if v is None else str(v).strip()
    digits = "".join(ch for ch in s if ch.isdigit())
    if not digits:
        return s
    return digits.lstrip("0") or "0"


def _find_status_for_cota(
    results: List[RPACotaStatus],
    *,
    grupo: object,
    cota: object,
) -> Optional[RPACotaStatus]:
    grupo_key = _norm_num_str(grupo)
    cota_key = _norm_num_str(cota)

    for item in results:
        if _norm_num_str(item.grupo) == grupo_key and _norm_num_str(item.cota) == cota_key:
            return item
    return None


def _build_won_payload(*, run_date: date) -> Dict[str, Any]:
    return {
        "status": 1,
        "closed_at": run_date.strftime("%Y-%m-%d"),
    }


def sync_payment_to_piperun(
    *,
    grupo: object,
    cota: object,
    run_date: date,
    results: List[RPACotaStatus],
    token: Optional[str] = None,
    base_url: Optional[str] = None,
    pipeline_id: int = RETENTION_PIPELINE_ID,
    stage_id: int = RETENTION_STAGE_ID,
) -> Dict[str, Any]:

    status_cota = _find_status_for_cota(results, grupo=grupo, cota=cota)

    if status_cota is None:
        logger.warning(
            "Cota base não encontrada no resultado do RPA",
            extra={
                "grupo": str(grupo),
                "cota": str(cota),
                "pipeline_id": pipeline_id,
                "stage_id": stage_id,
            },
        )
        return {
            "updated": False,
            "reason": "Cota base não encontrada no resultado do RPA.",
            "deal_id": None,
            "pipeline_id": pipeline_id,
            "stage_id": stage_id,
        }

    if not status_cota.pago_confirmado:
        logger.info(
            "Cota não está paga na Newcon; sync com PipeRun não será executado",
            extra={
                "grupo": str(grupo),
                "cota": str(cota),
                "boletos_em_aberto": status_cota.boletos_em_aberto,
                "pipeline_id": pipeline_id,
                "stage_id": stage_id,
            },
        )
        return {
            "updated": False,
            "reason": "Cota não está paga na Newcon — não será enviada ao PipeRun.",
            "deal_id": None,
            "boletos_em_aberto": status_cota.boletos_em_aberto,
            "pipeline_id": pipeline_id,
            "stage_id": stage_id,
        }

    try:
        client = PipeRunClient(token=token, base_url=base_url)

        deal = client.find_open_retention_deal(
            grupo=grupo,
            cota=cota,
            pipeline_id=pipeline_id,
            stage_id=stage_id,
        )

        if deal is None:
            logger.warning(
                "Nenhuma oportunidade encontrada no PipeRun para a cota",
                extra={
                    "grupo": str(grupo),
                    "cota": str(cota),
                    "pipeline_id": pipeline_id,
                    "stage_id": stage_id,
                },
            )
            return {
                "updated": False,
                "reason": "Nenhuma oportunidade encontrada no PipeRun para essa cota.",
                "deal_id": None,
                "pipeline_id": pipeline_id,
                "stage_id": stage_id,
            }

        deal_id = int(deal["id"])

        payload = _build_won_payload(run_date=run_date)
        response = client.update_deal(deal_id=deal_id, payload=payload)

        logger.info(
            "Oportunidade marcada como ganha no PipeRun",
            extra={
                "deal_id": deal_id,
                "grupo": str(grupo),
                "cota": str(cota),
                "deal_title": deal.get("title"),
                "payload": payload,
                "pipeline_id": pipeline_id,
                "stage_id": stage_id,
            },
        )

        return {
            "updated": True,
            "deal_id": deal_id,
            "grupo": str(grupo),
            "cota": str(cota),
            "payload": payload,
            "reason": "Oportunidade marcada como ganha no PipeRun.",
            "response": response,
            "pipeline_id": pipeline_id,
            "stage_id": stage_id,
            "deal_title": deal.get("title"),
        }

    except Exception:
        logger.exception(
            "Erro ao sincronizar pagamento com PipeRun",
            extra={
                "grupo": str(grupo),
                "cota": str(cota),
                "pipeline_id": pipeline_id,
                "stage_id": stage_id,
            },
        )
        raise
