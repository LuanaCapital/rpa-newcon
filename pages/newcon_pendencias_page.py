from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from playwright.async_api import Page


def _parse_br_date(s: str) -> date | None:
    s = (s or "").strip()
    if not s:
        return None
    try:
        return datetime.strptime(s, "%d/%m/%Y").date()
    except Exception:
        return None


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
    except Exception:
        return Decimal("0")


class NewconPendenciasPage:
    def __init__(self, page: Page, tipo_login: str = "canopus"):
        self.page = page
        self.tipo_login = tipo_login

        self.titulo = "#ctl00_Conteudo_Label5"
        self.grid = "#ctl00_Conteudo_grdBoleto_Avulso"
        self.rows = f"{self.grid} tbody tr"

        self.chk_outras_cotas = "#ctl00_Conteudo_chkUnificarParcelas"
        self.btn_localizar_pendencias = "#ctl00_Conteudo_btnLocalizar"

    async def esperar_carregar(self):
        await self.page.wait_for_load_state("domcontentloaded")
        await self.page.wait_for_selector(self.titulo, state="visible", timeout=30000)
        await self.page.wait_for_selector(self.grid, state="visible", timeout=30000)

    async def listar_outras_cotas_e_atualizar(self):
        await self.esperar_carregar()

        chk_handle = None
        try:
            chk_handle = await self.page.wait_for_selector(self.chk_outras_cotas, timeout=800)
        except Exception:
            chk_handle = None

        if chk_handle:
            try:
                chk = self.page.locator(self.chk_outras_cotas)
                if await chk.count() > 0 and await chk.is_enabled():
                    if not await chk.is_checked():
                        await chk.click(force=True)
                        try:
                            await self.page.wait_for_load_state("networkidle", timeout=8000)
                        except Exception:
                            await self.page.wait_for_load_state("domcontentloaded")
            except Exception:
                pass

        btn = self.page.locator(self.btn_localizar_pendencias)
        await btn.wait_for(state="visible", timeout=10000)
        await btn.click(force=True)

        try:
            await self.page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            await self.page.wait_for_load_state("domcontentloaded")

        await self.page.wait_for_selector(self.grid, state="visible", timeout=30000)

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

    async def resultado_por_cota_todas(self, *, cutoff_date: date | None = None) -> dict:
        linhas = await self.ler_linhas()

        por_cota = {}
        for l in linhas:
            por_cota.setdefault(l.cota, []).append(l)

        saida = []
        for cota, itens in por_cota.items():
            abertas = []
            for x in itens:
                if "RECBTO. PARCELA" not in (x.historico or "").upper():
                    continue
                if x.vl_devido <= 0:
                    continue

                if cutoff_date is not None:
                    dv = _parse_br_date(x.vencimento)
                    if dv is None:
                        continue
                    if dv > cutoff_date:
                        continue

                abertas.append(x)

            if not abertas:
                saida.append({
                    "cota": cota,
                    "em_aberto": False,
                    "vencimento": "",
                    "valor": "",
                })
            else:
                for a in abertas:
                    saida.append({
                        "cota": cota,
                        "em_aberto": True,
                        "vencimento": a.vencimento,
                        "valor": str(a.vl_devido),
                    })

        return {"cotas": saida}