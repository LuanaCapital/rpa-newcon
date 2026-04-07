from __future__ import annotations

import asyncio
import calendar
import traceback
from datetime import date
from typing import Any

from dotenv import load_dotenv
from playwright.async_api import Page

from mappers import newcon_result_to_cota_status
from pages.newcon_atendimento_page import NewconAtendimentoPage
from pages.newcon_menu_page import NewconMenuPage
from pages.newcon_pendencias_page import NewconPendenciasPage
from csv_writer import append_rows
from src.piperun.updater import sync_payment_to_piperun
from utils.betterstack_logger import get_logger

load_dotenv()

logger = get_logger(__name__)

def _zfill(grupo: str, cota: str) -> tuple[str, str]:
    return str(grupo).zfill(6), str(cota).zfill(4)


def _cutoff_last_day(month: int, year: int) -> date:
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, last_day)


def _run_date_for_sheet(today: date, month: int, year: int) -> date:
    day = min(today.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


async def processar_cliente(
    newcon_page: Page,
    grupo: str,
    cota: str,
    csv_path: str,
    *,
    analysis_month: int,
    analysis_year: int,
) -> dict[str, Any]:
    grupo6, cota4 = _zfill(grupo, cota)

    atendimento = NewconAtendimentoPage(newcon_page)
    menu = NewconMenuPage(newcon_page)
    pendencias = NewconPendenciasPage(newcon_page)

    try:
        await atendimento.buscar_consorciado(grupo6, cota4)
        await menu.abrir_emissao_cobranca()
        await pendencias.listar_outras_cotas_e_atualizar()

        today = date.today()
        cutoff = _cutoff_last_day(analysis_month, analysis_year)
        run_date = _run_date_for_sheet(today, analysis_month, analysis_year)

        resultado = await pendencias.resultado_por_cota_todas(cutoff_date=cutoff)

        cotas_do_cliente = newcon_result_to_cota_status(
            grupo=int(grupo6),
            resultado_por_cota=resultado,
        )

        logger.info(
            "Resultado da Newcon obtido",
            extra={
                "event": "newcon_resultado_obtido",
                "grupo": grupo6,
                "cota": cota4,
                "qtd_cotas_resultado": len(resultado.get("cotas", [])),
                "qtd_cotas_status": len(cotas_do_cliente),
            },
        )

        logger.info(
            "Iniciando sync com PipeRun",
            extra={
                "event": "piperun_sync_start",
                "grupo": grupo6,
                "cota": cota4,
                "run_date": run_date.isoformat(),
            },
        )

        piperun_result = await asyncio.to_thread(
            sync_payment_to_piperun,
            grupo=grupo6,
            cota=cota4,
            run_date=run_date,
            results=cotas_do_cliente,
        )

        logger.info(
            "Sync com PipeRun concluído",
            extra={
                "event": "piperun_sync_done",
                "grupo": grupo6,
                "cota": cota4,
                "deal_id": piperun_result.get("deal_id") if piperun_result else None,
                "updated": piperun_result.get("updated") if piperun_result else None,
                "reason": piperun_result.get("reason") if piperun_result else None,
            },
        )

        rows = []
        for item in resultado.get("cotas", []):
            rows.append({
                "grupo_base": grupo6,
                "cota_base": cota4,
                "em_aberto": item.get("em_aberto", ""),
                "cota_pendencia": item.get("cota", ""),
                "vencimento": item.get("vencimento", ""),
                "valor": item.get("valor", ""),
                "deal_id": piperun_result.get("deal_id") or "",
                "piperun_result": str(piperun_result) if piperun_result else "",
                "erro": "",
            })

        if not rows:
            logger.warning(
                "Sem linhas no grid de pendências",
                extra={
                    "event": "newcon_sem_linhas_grid",
                    "grupo": grupo6,
                    "cota": cota4,
                },
            )
            rows.append({
                "grupo_base": grupo6,
                "cota_base": cota4,
                "em_aberto": "",
                "cota_pendencia": "",
                "vencimento": "",
                "valor": "",
                "deal_id": piperun_result.get("deal_id") or "",
                "piperun_result": str(piperun_result) if piperun_result else "",
                "erro": "Sem linhas no grid",
            })

        append_rows(csv_path, rows)

        logger.info(
            "Processamento do cliente concluído com sucesso",
            extra={
                "event": "processar_cliente_success",
                "grupo": grupo6,
                "cota": cota4,
                "deal_id": piperun_result.get("deal_id") if piperun_result else None,
            },
        )

        cotas = resultado.get("cotas", [])

        tem_em_aberto = False

        for item in cotas:
            em_aberto = item.get("em_aberto")

            if isinstance(em_aberto, str):
                em_aberto = em_aberto.strip().lower() == "true"

            if em_aberto:
                tem_em_aberto = True
                break

        pago = "Não" if tem_em_aberto else "Sim"

        return {
            "grupo": grupo6,
            "cota": cota4,
            "resultado": resultado,
            "piperun_result": piperun_result,
            "erro": None,
            "pago": pago,
        }

    except Exception:
        logger.exception(
            "Erro ao processar cliente",
            extra={
                "event": "processar_cliente_error",
                "grupo": grupo6,
                "cota": cota4,
                "analysis_month": analysis_month,
                "analysis_year": analysis_year,
                "csv_path": csv_path,
            },
        )

        erro_detalhado = traceback.format_exc()

        append_rows(csv_path, [{
            "grupo_base": grupo6,
            "cota_base": cota4,
            "em_aberto": "",
            "cota_pendencia": "",
            "vencimento": "",
            "valor": "",
            "deal_id": "",
            "piperun_result": "",
            "erro": erro_detalhado,
        }])

        return {
            "grupo": grupo6,
            "cota": cota4,
            "resultado": None,
            "piperun_result": None,
            "erro": erro_detalhado,
            "pago": ""
        }