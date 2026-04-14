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
        self.lbl_errmsg = "#ctl00_Conteudo_lblErrMsg"

        self.lbl_nome_completo = "#ctl00_Conteudo_lblCD_Cota"
        self.lbl_data_adesao = "#ctl00_Conteudo_lblDT_Adesao"
        self.lbl_data_alocacao = "#ctl00_Conteudo_lblDT_Alocacao"
        self.lbl_contrato = "#ctl00_Conteudo_lblID_Documento"
        self.lbl_quantidade_parcelas = "#ctl00_Conteudo_lblNO_Parcela"
        self.lbl_data_vencimento = "#ctl00_Conteudo_lblDT_Vencimento"

    async def ir_para_tela_grupo_cota(self):
        await self.page.click(self.btn_atendimento)
        await self.page.wait_for_selector(self.input_grupo)

    async def buscar_consorciado(self, grupo: str, cota: str):
        await self.ir_para_tela_grupo_cota()

        await self.page.fill(self.input_grupo, grupo)
        await self.page.fill(self.input_cota, cota)
        await self.page.click(self.btn_localizar)

        await self.page.wait_for_load_state("networkidle")
        await self.page.wait_for_timeout(1500)

        if await self.page.locator(self.lbl_errmsg).count() > 0:
            msg = (await self.page.locator(self.lbl_errmsg).inner_text()).strip().lower()
            if msg and "inválido" in msg:
                raise ConsorciadoInvalidoError(msg)

    async def extrair_dados_cadastrais(self) -> dict:
        texto_cota = (await self.page.locator(self.lbl_nome_completo).inner_text()).strip()

        partes = texto_cota.split()

        nome_completo = " ".join(partes[2:]) if len(partes) > 2 else texto_cota

        return {
            "nome_completo": nome_completo,
            "data_adesao": (await self.page.locator(self.lbl_data_adesao).inner_text()).strip(),
            "data_alocacao": (await self.page.locator(self.lbl_data_alocacao).inner_text()).strip(),
            "contrato": (await self.page.locator(self.lbl_contrato).inner_text()).strip(),
            "quantidade_parcelas": (await self.page.locator(self.lbl_quantidade_parcelas).inner_text()).strip(),
            "data_vencimento": (await self.page.locator(self.lbl_data_vencimento).inner_text()).strip(),
        }