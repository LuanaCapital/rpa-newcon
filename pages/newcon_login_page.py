from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

class NewconLoginPage:
    def __init__(self, page: Page):
        self.page = page

        self.login_input = "#edtUsuario"
        self.password_input = "#edtSenha"
        self.submit_button = "#btnLogin"

        # Algo que indica que o login deu certo (ajuste se necessário)
        self.after_login_selector = "#ctl00_img_Atendimento"

    async def login(self, login: str, password: str):
        # 1) garantir que a tela de login carregou
        await self.page.wait_for_selector(self.login_input, state="visible", timeout=15000)
        await self.page.wait_for_selector(self.password_input, state="visible", timeout=15000)

        # 2) preencher do jeito mais “humano” (dispara eventos)
        await self.page.click(self.login_input)
        await self.page.fill(self.login_input, "")
        await self.page.type(self.login_input, login, delay=30)

        await self.page.click(self.password_input)
        await self.page.fill(self.password_input, "")
        await self.page.type(self.password_input, password, delay=30)

        # (opcional) tirar foco pra disparar onblur/onchange se tiver
        await self.page.keyboard.press("Tab")

        # 3) clicar Login e esperar por “pós-login”
        # ASP.NET às vezes navega, às vezes só faz postback e atualiza a mesma página.
        # Então fazemos: click + esperar por seletor que só existe após login.
        await self.page.click(self.submit_button)

        # Não use networkidle aqui (pode travar por requests longos)
        try:
            await self.page.wait_for_selector(self.after_login_selector, state="visible", timeout=20000)
        except PlaywrightTimeoutError:
            # Se não apareceu, vamos checar se ainda está no login (provável falha)
            still_login = await self.page.locator(self.login_input).count() > 0
            if still_login:
                raise RuntimeError("Falha ao logar no NewCon (permaneceu na tela de login).")
            raise
