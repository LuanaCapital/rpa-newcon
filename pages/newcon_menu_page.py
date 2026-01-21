# pages/newcon_menu_page.py

from playwright.async_api import Page

class NewconMenuPage:
    def __init__(self, page: Page):
        self.page = page

        # Link "Emissão de Cobrança"
        self.link_emissao_cobranca = 'a#ctl00_Conteudo_Menu_CONAT_grdMenu_CONAT_ctl05_hlkFormulario'

    async def abrir_emissao_cobranca(self):
        """Clica no link Emissão de Cobrança e espera navegar."""
        await self.page.click(self.link_emissao_cobranca)
        await self.page.wait_for_load_state("networkidle")
