# batch_runner.py
import os
from datetime import date

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

async def processar_cliente(
    newcon_page: Page,
    grupo: str,
    cota: str,
    csv_path: str,
) -> None:
    """
    Processa 1 cliente e salva resultado no CSV (append).
    """
    grupo6, cota4 = _zfill(grupo, cota)

    atendimento = NewconAtendimentoPage(newcon_page)
    menu = NewconMenuPage(newcon_page)
    pendencias = NewconPendenciasPage(newcon_page)

    try:
        # Volta/entra na tela de Grupo e Cota e localiza consorciado
        await atendimento.buscar_consorciado(grupo6, cota4)

        # Abre a opção "Emissão de Cobrança"
        await menu.abrir_emissao_cobranca()

        # Lista outras cotas e atualiza pendências
        await pendencias.listar_outras_cotas_e_atualizar()

        # Extrai resultado no formato solicitado
        resultado = await pendencias.resultado_por_cota_todas()

        cotas_do_cliente = newcon_result_to_cota_status(grupo=int(grupo6), resultado_por_cota=resultado)
        print(cotas_do_cliente)

        # 3) manda pro Sheets
        result = sync_payments_to_sheet(
            spreadsheet_id=os.getenv("SHEET_ID"),
            sheet_name=os.getenv("SHEET_NAME"),
            read_range_a1=os.getenv("READ_RANGE"),
            run_date=date.today(),
            results=cotas_do_cliente,
            token_path=os.getenv("TOKEN_PATH", "../token.json"),
        )
        print(result["updated"])
        print("SYNC RESULT:", result)
        print("UPDATED:", result.get("updated"))
        print("UPDATES:", result.get("updates"))

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

        # se por algum motivo não veio nada, grava ao menos uma linha
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
        # Se falhar, grava erro e segue o lote
        append_rows(csv_path, [{
            "grupo_base": grupo6,
            "cota_base": cota4,
            "em_aberto": "",
            "cota_pendencia": "",
            "vencimento": "",
            "valor": "",
            "erro": str(e),
        }])
