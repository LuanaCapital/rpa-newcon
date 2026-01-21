# pages/newcon_pendencias_page.py

from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from playwright.async_api import Page

@dataclass
class PendenciaLinha:
    cota: str
    pcl: str
    historico: str
    vencimento: str
    vl_devido: Decimal

def _brl_to_decimal(text: str) -> Decimal:
    t = (text or "").strip()
    if not t:
        return Decimal("0")
    t = t.replace(".", "").replace(",", ".")
    try:
        return Decimal(t)
    except:
        return Decimal("0")

class NewconPendenciasPage:
    def __init__(self, page: Page):
        self.page = page

        # Tela Pendências
        self.titulo = "#ctl00_Conteudo_Label5"
        self.grid = "#ctl00_Conteudo_grdBoleto_Avulso"
        self.rows = f"{self.grid} tbody tr"

        # Listar outras cotas
        self.chk_outras_cotas = "#ctl00_Conteudo_chkUnificarParcelas"

        # Botão "Localizar pendências"
        self.btn_localizar_pendencias = "#ctl00_Conteudo_btnLocalizar"

    async def esperar_carregar(self):
        await self.page.wait_for_selector(self.titulo, state="visible")
        await self.page.wait_for_selector(self.grid, state="visible")

    async def listar_outras_cotas_e_atualizar(self):
        """
        Tenta marcar 'Listar parcelas de outras cotas' se o checkbox existir e estiver habilitado.
        Se não existir, segue normalmente.
        Evita erro de "Element is not attached to the DOM" usando waits curtos e locators "fresh".
        """
        await self.esperar_carregar()

        # 1) tenta detectar o checkbox com timeout curto (se não existir, OK)
        chk_handle = None
        try:
            chk_handle = await self.page.wait_for_selector(self.chk_outras_cotas, timeout=800)
        except Exception:
            chk_handle = None

        # 2) se existir, tenta marcar (sem scroll obrigatório)
        if chk_handle:
            try:
                chk = self.page.locator(self.chk_outras_cotas)

                # revalida estado no momento do clique
                if await chk.count() > 0 and await chk.is_enabled():
                    if not await chk.is_checked():
                        await chk.click(force=True)
                        # o checkbox dispara postback
                        try:
                            await self.page.wait_for_load_state("networkidle", timeout=8000)
                        except Exception:
                            await self.page.wait_for_load_state("domcontentloaded")
            except Exception:
                # não trava o lote se falhar marcar
                pass

        # 3) Sempre clicar em "Localizar pendências"
        btn = self.page.locator(self.btn_localizar_pendencias)
        await btn.click()

        try:
            await self.page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            await self.page.wait_for_load_state("domcontentloaded")

        await self.page.wait_for_selector(self.grid, state="visible")

    async def ler_linhas(self) -> list[PendenciaLinha]:
        await self.esperar_carregar()

        trs = await self.page.locator(self.rows).all()
        linhas: list[PendenciaLinha] = []

        for tr in trs:
            tds = tr.locator("td")
            count = await tds.count()
            if count < 10:
                continue

            cota = (await tds.nth(1).inner_text()).strip()
            pcl = (await tds.nth(2).inner_text()).strip()
            historico = (await tds.nth(3).inner_text()).strip()
            vencimento = (await tds.nth(4).inner_text()).strip()

            # Coluna "Vl. devido" é a 9ª (índice 8)
            vl_devido = _brl_to_decimal(await tds.nth(8).inner_text())

            linhas.append(
                PendenciaLinha(
                    cota=cota,
                    pcl=pcl,
                    historico=historico,
                    vencimento=vencimento,
                    vl_devido=vl_devido,
                )
            )

        return linhas

    async def resultado_por_cota_todas(self) -> dict:
        """
        Lê o grid e retorna resultado por cota (inclui cotas sem pendência em aberto).
        Saída:
        {
          "cotas": [
            {"cota": "...", "em_aberto": bool, "vencimento": "...", "valor": "..."},
            ...
          ]
        }
        """
        linhas = await self.ler_linhas()

        # agrupa por cota (a coluna já vem tipo 006650/2278-00)
        por_cota = {}
        for l in linhas:
            por_cota.setdefault(l.cota, []).append(l)

        saida = []
        for cota, itens in por_cota.items():
            # pendências em aberto = RECBTO. PARCELA com vl_devido > 0
            abertas = [
                x for x in itens
                if "RECBTO. PARCELA" in x.historico.upper() and x.vl_devido > 0
            ]

            if not abertas:
                # cota sem pendência em aberto → ainda entra no CSV
                saida.append({
                    "cota": cota,
                    "em_aberto": False,
                    "vencimento": "",
                    "valor": "",
                })
            else:
                # uma linha por pendência em aberto daquela cota
                for a in abertas:
                    saida.append({
                        "cota": cota,
                        "em_aberto": True,
                        "vencimento": a.vencimento,
                        "valor": str(a.vl_devido),
                    })

        return {"cotas": saida}
