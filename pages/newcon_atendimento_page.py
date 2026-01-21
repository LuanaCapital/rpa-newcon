from playwright.async_api import Page

class ConsorciadoInvalidoError(Exception):
    pass


class NewconAtendimentoPage:
    def __init__(self, page: Page):
        self.page = page
        self.btn_atendimento = "#ctl00_img_Atendimento"

        self.input_grupo = "#ctl00_Conteudo_edtGrupo"
        self.input_cota = "#ctl00_Conteudo_edtCota"
        self.btn_localizar = "#ctl00_Conteudo_btnLocalizar"

        self.titulo_identificacao = "#ctl00_Conteudo_Label7"

        # ✅ mensagem que você mostrou no início
        self.lbl_errmsg = "#ctl00_Conteudo_lblErrMsg"

    async def ir_para_tela_grupo_cota(self):
        await self.page.click(self.btn_atendimento)
        await self.page.wait_for_selector(self.titulo_identificacao, state="visible")

    async def informar_grupo_cota(self, grupo: str, cota: str):
        await self.page.fill(self.input_grupo, str(grupo))
        await self.page.fill(self.input_cota, str(cota))

    async def _raise_if_consorciado_invalido(self, timeout: int = 500):
        """
        Checa rápido (sem travar) se apareceu 'Consorciado inválido.' após localizar.
        """
        try:
            el = await self.page.wait_for_selector(self.lbl_errmsg, state="visible", timeout=timeout)
            txt = (await el.inner_text() or "").strip().lower()
            if "consorciado inválido" in txt or "consorciado invalido" in txt:
                raise ConsorciadoInvalidoError("Consorciado inválido.")
        except Exception as e:
            # se for a nossa exceção, propaga
            if isinstance(e, ConsorciadoInvalidoError):
                raise
            # senão, significa que não apareceu mensagem (timeout) -> ok
            return

    async def localizar(self):
        await self.page.click(self.btn_localizar)

        # networkidle às vezes demora demais em app legado (postback / polling).
        # então: espera "domcontentloaded" e checa mensagem já.
        try:
            await self.page.wait_for_load_state("networkidle", timeout=6000)
        except Exception:
            await self.page.wait_for_load_state("domcontentloaded")

        # ✅ se for inválido, aborta aqui
        await self._raise_if_consorciado_invalido(timeout=800)

    async def buscar_consorciado(self, grupo: str, cota: str):
        await self.ir_para_tela_grupo_cota()
        await self.informar_grupo_cota(grupo, cota)
        await self.localizar()