# auth_flow.py

import os
from playwright.async_api import BrowserContext, Page

from pages.login import LoginPage
from pages.parceiros_home_page import ParceirosHomePage
from pages.newcon_login_page import NewconLoginPage

LOGIN = os.getenv("LOGIN")
PASSWORD = os.getenv("PASSWORD")
URL_LOGIN_PARCEIROS = os.getenv("URL_LOGIN")

async def autenticar_e_abrir_newcon(context: BrowserContext) -> Page:
    """
    Faz login no Parceiros e abre o NewCon (nova aba) + loga no NewCon.
    Retorna a Page do NewCon pronta.
    """
    page = await context.new_page()

    # Parceiros login
    parceiros_login = LoginPage(page, URL_LOGIN_PARCEIROS)
    await parceiros_login.login(LOGIN, PASSWORD)

    # Abrir NewCon
    parceiros_home = ParceirosHomePage(page)
    newcon_page = await parceiros_home.abrir_newcon()

    # Login NewCon
    newcon_login = NewconLoginPage(newcon_page)
    await newcon_login.login(LOGIN, PASSWORD)

    return newcon_page
