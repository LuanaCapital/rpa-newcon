# pages/parceiros_home_page.py

from playwright.async_api import Page

class ParceirosHomePage:
    def __init__(self, page: Page):
        self.page = page
        # Botão "NewCon" dentro do <a ... target="_blank">
        self.newcon_button = 'button[title="NewCon"]'

    async def abrir_newcon(self) -> Page:
        """
        Clica no botão NewCon, que abre uma nova aba (_blank),
        e retorna a página (Page) do NewCon.
        """
        # Espera o popup (nova aba)
        async with self.page.expect_popup() as popup_info:
            await self.page.click(self.newcon_button)

        newcon_page = await popup_info.value

        # Garante que a nova página carregou
        await newcon_page.wait_for_load_state("networkidle")

        return newcon_page
