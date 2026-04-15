from playwright.async_api import Page


class RodobensLoginPage:
    def __init__(self, page: Page, url_login: str):
        self.page = page
        self.url_login = url_login

        self.user_input = "#edtUsuario"
        self.password_input = "#edtSenha"
        self.submit_button = "#btnLogin"

    async def goto(self):
        await self.page.goto(self.url_login)

    async def fill_credentials(self, user: str, password: str):
        await self.page.wait_for_selector(self.user_input, state="visible")
        await self.page.fill(self.user_input, user)
        await self.page.fill(self.password_input, password)

    async def submit(self):
        await self.page.wait_for_selector(self.submit_button, state="attached")
        await self.page.evaluate("""
            () => {
                const btn = document.querySelector('#btnLogin');
                if (btn) btn.disabled = false;
            }
        """)
        await self.page.click(self.submit_button)

    async def login(self, user: str, password: str):
        await self.goto()
        await self.fill_credentials(user, password)
        await self.submit()