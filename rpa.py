# rpa.py

import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright

from batch_runner import processar_cliente
from csv_writer import build_csv_path
from pages.auth_flow import autenticar_e_abrir_newcon
from pages.login import LoginPage
from pages.newcon_atendimento_page import NewconAtendimentoPage
from pages.newcon_menu_page import NewconMenuPage
from pages.newcon_pendencias_page import NewconPendenciasPage
from pages.parceiros_home_page import ParceirosHomePage
from pages.newcon_login_page import NewconLoginPage
from pages.session_guard import is_session_blocked

# Carrega variáveis de ambiente
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

        # 1) Login Parceiros
        parceiros_login = LoginPage(page, URL_LOGIN_PARCEIROS)
        await parceiros_login.login(LOGIN, PASSWORD)

        # 2) Abrir NewCon em nova aba
        parceiros_home = ParceirosHomePage(page)
        newcon_page = await parceiros_home.abrir_newcon()

        # 3) Login NewCon
        newcon_login = NewconLoginPage(newcon_page)
        await newcon_login.login(LOGIN, PASSWORD)

        # 4) Atendimento -> Identificação -> Localizar
        atendimento = NewconAtendimentoPage(newcon_page)
        await atendimento.buscar_consorciado(grupo=grupo, cota=cota)

        # Só para debug
        menu = NewconMenuPage(newcon_page)
        await menu.abrir_emissao_cobranca()

        pendencias_page = NewconPendenciasPage(newcon_page)

        # Para listar todas as cotas do mesmo cliente:
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

from utils.human_delay import human_delay

async def run_lote(
    clientes: list[dict],
    *,
    analysis_month: int,
    analysis_year: int,
) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        context = await browser.new_context()
        newcon_page = await autenticar_e_abrir_newcon(context)

        for item in clientes:
            grupo = item["grupo"]
            cota = item["cota"]

            if await is_session_blocked(newcon_page):
                await context.close()
                context = await browser.new_context()
                newcon_page = await autenticar_e_abrir_newcon(context)

            try:
                await processar_cliente(
                    newcon_page,
                    grupo,
                    cota,
                    csv_path="...",
                    analysis_month=analysis_month,
                    analysis_year=analysis_year,
                )

                if await is_session_blocked(newcon_page):
                    await context.close()
                    context = await browser.new_context()
                    newcon_page = await autenticar_e_abrir_newcon(context)

            except Exception:
                if await is_session_blocked(newcon_page):
                    await context.close()
                    context = await browser.new_context()
                    newcon_page = await autenticar_e_abrir_newcon(context)

                    await processar_cliente(
                        newcon_page,
                        grupo,
                        cota,
                        csv_path="...",
                        analysis_month=analysis_month,
                        analysis_year=analysis_year,
                    )
                else:
                    pass

        await context.close()
        await browser.close()

    return {"ok": True}

