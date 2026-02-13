# batch_runner.py
import os
from datetime import date
import calendar

from dotenv import load_dotenv
from playwright.async_api import Page

from mappers import newcon_result_to_cota_status
from pages.newcon_atendimento_page import NewconAtendimentoPage
from pages.newcon_menu_page import NewconMenuPage
from pages.newcon_pendencias_page import NewconPendenciasPage
from csv_writer import append_rows
from src.sheets.updater import sync_payments_to_sheet

load_dotenv()

def _zfill(grupo: str, cota: str) -> tuple[str, str]:
    return str(grupo).zfill(6), str(cota).zfill(4)

def _analysis_month_year(today: date) -> tuple[int, int]:
    m = os.getenv("ANALYSIS_MONTH", "").strip()
    y = os.getenv("ANALYSIS_YEAR", "").strip()

    month = int(m) if m else today.month
    year = int(y) if y else today.year
    return month, year

def _cutoff_last_day(month: int, year: int) -> date:
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, last_day)

def _run_date_for_sheet(today: date, month: int, year: int) -> date:
    # run_date precisa cair dentro do mês analisado pra bater com a coluna "Janeiro - 2026"
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
) -> None:
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

        # ✅ filtra pendências até o mês analisado
        resultado = await pendencias.resultado_por_cota_todas(cutoff_date=cutoff)

        cotas_do_cliente = newcon_result_to_cota_status(grupo=int(grupo6), resultado_por_cota=resultado)

        result = sync_payments_to_sheet(
            spreadsheet_id=os.getenv("SHEET_ID"),
            sheet_name=os.getenv("SHEET_NAME"),
            read_range_a1=os.getenv("READ_RANGE"),
            run_date=run_date,
            results=cotas_do_cliente,
            token_path=os.getenv("TOKEN_PATH", "../token.json"),
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
                "erro": "",
            })

        if not rows:
            rows.append({
                "grupo_base": grupo6,
                "cota_base": cota4,
                "em_aberto": "",
                "cota_pendencia": "",
                "vencimento": "",
                "valor": "",
                "erro": "Sem linhas no grid",
            })

        append_rows(csv_path, rows)

    except Exception as e:
        append_rows(csv_path, [{
            "grupo_base": grupo6,
            "cota_base": cota4,
            "em_aberto": "",
            "cota_pendencia": "",
            "vencimento": "",
            "valor": "",
            "erro": str(e),
        }])