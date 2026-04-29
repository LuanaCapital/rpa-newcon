# auth_flow.py

import os
from playwright.async_api import BrowserContext, Page

from pages.newcon_login_page import NewconLoginPage
from pages.rodobens_login_page import RodobensLoginPage
from playwright_stealth import apply_stealth_to_page

LOGIN = os.getenv("LOGIN")
PASSWORD = os.getenv("PASSWORD")
URL_LOGIN_NEWCON = os.getenv("URL_LOGIN")

RODOBENS_USUARIO = os.getenv("RODOBENS_USUARIO")
RODOBENS_SENHA = os.getenv("RODOBENS_SENHA")
RODOBENS_URL = os.getenv("RODOBENS_URL")


async def autenticar_e_abrir_newcon(context: BrowserContext) -> Page:
    """
    Fluxo Canopus direto:
    login -> clicar em Atendimento (ctl00$img_Atendimento)
    """
    page = await context.new_page()

    # Stealth
    await apply_stealth_to_page(page)

    # Acessa direto a URL do NewCon
    await page.goto(URL_LOGIN_NEWCON, wait_until="domcontentloaded")

    # Login
    newcon_login = NewconLoginPage(page)
    await newcon_login.login(LOGIN, PASSWORD)

    # Clicar no Atendimento
    atendimento_button = page.locator('#ctl00_img_Atendimento, [name="ctl00$img_Atendimento"]')
    await atendimento_button.wait_for(state="visible", timeout=20000)
    await atendimento_button.click()

    return page


async def autenticar_rodobens_e_abrir_newcon(context: BrowserContext) -> Page:
    page = await context.new_page()
    await apply_stealth_to_page(page)

    rodobens_login = RodobensLoginPage(page, RODOBENS_URL)
    await rodobens_login.login(RODOBENS_USUARIO, RODOBENS_SENHA)

    await page.wait_for_selector("#ctl00_img_Atendimento", state="visible")

    return page