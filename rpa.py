import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright

from batch_runner import processar_cliente, logger
from pages.auth_flow import autenticar_e_abrir_newcon, autenticar_rodobens_e_abrir_newcon
from pages.login import LoginPage
from pages.newcon_atendimento_page import NewconAtendimentoPage
from pages.newcon_menu_page import NewconMenuPage
from pages.newcon_pendencias_page import NewconPendenciasPage
from pages.parceiros_home_page import ParceirosHomePage
from pages.newcon_login_page import NewconLoginPage
from pages.session_guard import is_session_blocked
from playwright_stealth import apply_stealth_to_page, setup_context_with_stealth
from utils.report_helper import salvar_resultado_csv

load_dotenv()

LOGIN = os.getenv("LOGIN")
PASSWORD = os.getenv("PASSWORD")
URL_LOGIN_PARCEIROS = os.getenv("URL_LOGIN")

if not LOGIN or not PASSWORD or not URL_LOGIN_PARCEIROS:
    raise RuntimeError("LOGIN, PASSWORD ou URL_LOGIN não estão definidos no .env")


async def run_fluxo_newcon(
    grupo: str,
    cota: str,
    tipo_login: str = "canopus",
):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()

        await setup_context_with_stealth(context)

        if tipo_login == "canopus":
            newcon_page = await autenticar_e_abrir_newcon(context)
        elif tipo_login == "rodobens":
            newcon_page = await autenticar_rodobens_e_abrir_newcon(context)
        else:
            raise ValueError(f"tipo_login inválido: {tipo_login}")

        atendimento = NewconAtendimentoPage(newcon_page)
        await atendimento.buscar_consorciado(grupo=grupo, cota=cota)

        menu = NewconMenuPage(newcon_page)
        await menu.abrir_emissao_cobranca()

        pendencias_page = NewconPendenciasPage(newcon_page, tipo_login=tipo_login)
        await pendencias_page.listar_outras_cotas_e_atualizar()

        resultado = await pendencias_page.resultado_em_aberto_por_cota()
        url_final = newcon_page.url

        await context.close()
        await browser.close()

        return {
            "status": "ok",
            "grupo": grupo,
            "cota_base": cota,
            "resultado": resultado,
            "url": url_final,
            "tipo_login": tipo_login,
        }


async def run_lote(
    clientes: list[dict],
    *,
    analysis_month: int,
    analysis_year: int,
    execution_id: str,
    tipo_login: str = "canopus",
) -> dict:
    resultados = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        context = await browser.new_context()

        await setup_context_with_stealth(context)

        if tipo_login == "canopus":
            newcon_page = await autenticar_e_abrir_newcon(context)
        elif tipo_login == "rodobens":
            newcon_page = await autenticar_rodobens_e_abrir_newcon(context)
        else:
            raise ValueError(f"tipo_login inválido: {tipo_login}")

        os.makedirs("relatorios", exist_ok=True)
        data_str = f"{analysis_year}-{analysis_month:02d}"

        csv_path = os.path.join("relatorios", f"resultado_lote_{data_str}.csv")
        final_csv_path = os.path.join("relatorios", f"relatorio_final_{data_str}.csv")

        for item in clientes:
            grupo = item["grupo"]
            cota = item["cota"]

            logger.info(
                "Processando cliente",
                extra={
                    "execution_id": execution_id,
                    "grupo": grupo,
                    "cota": cota,
                    "analysis_month": analysis_month,
                    "analysis_year": analysis_year,
                    "tipo_login": tipo_login,
                },
            )

            if await is_session_blocked(newcon_page):
                await context.close()
                context = await browser.new_context()

                await setup_context_with_stealth(context)

                if tipo_login == "canopus":
                    newcon_page = await autenticar_e_abrir_newcon(context)
                elif tipo_login == "rodobens":
                    newcon_page = await autenticar_rodobens_e_abrir_newcon(context)
                else:
                    raise ValueError(f"tipo_login inválido: {tipo_login}")

            resultado = await processar_cliente(
                newcon_page,
                grupo,
                cota,
                csv_path=csv_path,
                final_csv_path=final_csv_path,
                analysis_month=analysis_month,
                analysis_year=analysis_year,
                tipo_login=tipo_login,
            )
            resultados.append(resultado)

            if resultado.get("erro"):
                logger.warning(
                    "Cliente com erro no processamento",
                    extra={
                        "execution_id": execution_id,
                        "grupo": grupo,
                        "cota": cota,
                        "erro": resultado.get("erro"),
                        "tipo_login": tipo_login,
                    },
                )

            try:
                salvar_resultado_csv(execution_id, resultado)
            except Exception as e:
                logger.error(
                    "Erro ao salvar relatório",
                    extra={
                        "execution_id": execution_id,
                        "grupo": grupo,
                        "cota": cota,
                        "error": str(e),
                        "tipo_login": tipo_login,
                    },
                )

        await context.close()
        await browser.close()

        if resultados:
            logger.info(
                "Processamento finalizado",
                extra={
                    "execution_id": execution_id,
                    "total_clientes": len(resultados),
                    "csv_path": final_csv_path,
                    "tipo_login": tipo_login,
                },
            )
        else:
            print("Nenhum resultado para salvar no CSV")

    return {
        "ok": True,
        "tipo_login": tipo_login,
        "resultados": resultados,
    }