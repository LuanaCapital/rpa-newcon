from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional

from src.domain.types import RPACotaStatus
from src.piperun.client import PipeRunClient
from utils.betterstack_logger import get_logger
from utils.bigquery_helper import pode_atualizar_oportunidade

RETENTION_PIPELINE_ID = int(os.getenv("PIPERUN_RETENTION_PIPELINE_ID", "97775"))
RETENTION_STAGE_ID = int(os.getenv("PIPERUN_RETENTION_STAGE_ID", "625639"))

logger = get_logger(__name__)

PIPERUN_PAID_BY_FIELD_ID = int(os.getenv("PIPERUN_PAID_BY_FIELD_ID", "731079"))
PIPERUN_PAID_BY_DEFAULT = os.getenv("PIPERUN_PAID_BY_DEFAULT", "Cliente")


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


def _build_paid_by_payload(*, paid_by: str) -> Dict[str, Any]:
    return {
        "custom_fields": [
            {
                "id": PIPERUN_PAID_BY_FIELD_ID,
                "value": paid_by,
            }
        ]
    }


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
                "reason": "NÃO ENCONTRADO NO PIPERUN - Oportunidade não localizada após buscar 50 páginas.",
                "deal_id": None,
                "pipeline_id": pipeline_id,
                "stage_id": stage_id,
            }

        deal_id = int(deal["id"])

        mes_payload = run_date.month

        try:
            if not pode_atualizar_oportunidade(deal_id, mes_payload):
                logger.info(
                    "Pulando oportunidade (status ou mês inválido)",
                    extra={
                        "deal_id": deal_id,
                        "mes_payload": mes_payload,
                    },
                )
                return {
                    "updated": False,
                    "reason": "Pulado - status ou mês inválido",
                    "deal_id": deal_id,
                }

        except Exception as e:
            logger.error(
                "Erro ao validar oportunidade no BigQuery",
                extra={
                    "deal_id": deal_id,
                    "error": str(e),
                },
            )
            return {
                "updated": False,
                "reason": "Erro ao validar oportunidade no BigQuery",
                "deal_id": deal_id,
            }

        paid_by_payload = _build_paid_by_payload(
            paid_by=PIPERUN_PAID_BY_DEFAULT,
        )

        logger.info(
            "Atualizando campo 'Foi pago por quem?' no PipeRun",
            extra={
                "deal_id": deal_id,
                "grupo": str(grupo),
                "cota": str(cota),
                "payload": paid_by_payload,
            },
        )

        paid_by_response = client.update_deal(deal_id=deal_id, payload=paid_by_payload)

        # COMENTADO: Atualização da oportunidade para "ganha" foi comentada
        # won_payload = _build_won_payload(run_date=run_date)
        #
        # logger.info(
        #     "Marcando oportunidade como ganha no PipeRun",
        #     extra={
        #         "deal_id": deal_id,
        #         "grupo": str(grupo),
        #         "cota": str(cota),
        #         "payload": won_payload,
        #     },
        # )
        #
        # won_response = client.update_deal(deal_id=deal_id, payload=won_payload)
        won_payload = None
        won_response = None

        logger.info(
            "Tentativas de atualização enviadas ao PipeRun",
            extra={
                "deal_id": deal_id,
                "grupo": str(grupo),
                "cota": str(cota),
                "deal_title": deal.get("title"),
                "paid_by_payload": paid_by_payload,
                "paid_by_response": paid_by_response,
                "won_payload": won_payload,
                "won_response": won_response,
                "pipeline_id": pipeline_id,
                "stage_id": stage_id,
            },
        )

        return {
            "updated": True,
            "deal_id": deal_id,
            "grupo": str(grupo),
            "cota": str(cota),
            "payload": won_payload,
            "paid_by_payload": paid_by_payload,
            "paid_by_response": paid_by_response,
            "response": won_response,
            "reason": "Campo obrigatório atualizado e tentativa de marcar oportunidade como ganha enviada ao PipeRun.",
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