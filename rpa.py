import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright

from batch_runner import processar_cliente
from pages.auth_flow import autenticar_e_abrir_newcon
from pages.login import LoginPage
from pages.newcon_atendimento_page import NewconAtendimentoPage
from pages.newcon_menu_page import NewconMenuPage
from pages.newcon_pendencias_page import NewconPendenciasPage
from pages.parceiros_home_page import ParceirosHomePage
from pages.newcon_login_page import NewconLoginPage
from pages.session_guard import is_session_blocked

load_dotenv()

LOGIN = os.getenv("LOGIN")
PASSWORD = os.getenv("PASSWORD")
URL_LOGIN_PARCEIROS = os.getenv("URL_LOGIN")

if not LOGIN or not PASSWORD or not URL_LOGIN_PARCEIROS:
    raise RuntimeError("LOGIN, PASSWORD ou URL_LOGIN não estão definidos no .env")


async def run_fluxo_newcon(grupo: str, cota: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        parceiros_login = LoginPage(page, URL_LOGIN_PARCEIROS)
        await parceiros_login.login(LOGIN, PASSWORD)

        parceiros_home = ParceirosHomePage(page)
        newcon_page = await parceiros_home.abrir_newcon()

        newcon_login = NewconLoginPage(newcon_page)
        await newcon_login.login(LOGIN, PASSWORD)

        atendimento = NewconAtendimentoPage(newcon_page)
        await atendimento.buscar_consorciado(grupo=grupo, cota=cota)

        menu = NewconMenuPage(newcon_page)
        await menu.abrir_emissao_cobranca()

        pendencias_page = NewconPendenciasPage(newcon_page)
        await pendencias_page.listar_outras_cotas_e_atualizar()

        resultado = await pendencias_page.resultado_em_aberto_por_cota()
        await browser.close()

        return {
            "status": "ok",
            "grupo": grupo,
            "cota_base": cota,
            "resultado": resultado,
            "url": newcon_page.url,
        }


async def run_lote(
    clientes: list[dict],
    *,
    analysis_month: int,
    analysis_year: int,
) -> dict:
    resultados = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        context = await browser.new_context()
        newcon_page = await autenticar_e_abrir_newcon(context)

        os.makedirs("relatorios", exist_ok=True)
        csv_path = os.path.join("relatorios", "resultado_lote.csv")
        final_csv_path = os.path.join("relatorios", "relatorio_final.csv")

        for item in clientes:
            grupo = item["grupo"]
            cota = item["cota"]

            if await is_session_blocked(newcon_page):
                await context.close()
                context = await browser.new_context()
                newcon_page = await autenticar_e_abrir_newcon(context)

            resultado = await processar_cliente(
                newcon_page,
                grupo,
                cota,
                csv_path=csv_path,
                final_csv_path=final_csv_path,
                analysis_month=analysis_month,
                analysis_year=analysis_year,
            )
            resultados.append(resultado)

        await context.close()
        await browser.close()

        if resultados:
            print(f"CSV atualizado em: {final_csv_path}")
        else:
            print("Nenhum resultado para salvar no CSV")

    return {
        "ok": True,
        "resultados": resultados,
    }