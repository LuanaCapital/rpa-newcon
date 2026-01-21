# pages/login_page.py

from playwright.async_api import Page

class LoginPage:
    def __init__(self, page: Page, url_login: str):
        self.page = page
        self.url_login = url_login

        # Seletores
        self.user_input = 'input[formcontrolname="Usuario"]'
        self.password_input = 'input[formcontrolname="Senha"]'
        self.submit_button = 'button.submit-button'

    async def goto(self):
        """Abre a página de login."""
        await self.page.goto(self.url_login)

    async def fill_credentials(self, user: str, password: str):
        """Preenche usuário e senha no formulário."""
        await self.page.fill(self.user_input, user)
        await self.page.fill(self.password_input, password)

    async def submit(self):
        """Clica no botão de login."""
        await self.page.click(self.submit_button)

    async def login(self, user: str, password: str):
        """Fluxo completo: entrar na página, preencher e logar."""
        await self.goto()
        await self.fill_credentials(user, password)
        await self.submit()

        # Opcional: aguardar algo que indique que o login funcionou
        # Exemplo genérico (ajuste depois):
        # await self.page.wait_for_url("**/dashboard")
