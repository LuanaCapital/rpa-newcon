from playwright.async_api import Page

BLOCK_TEXT = "Página não acessível"
VIOLATION_TEXT = "Violation Category:"
APPFW_TEXT = "APPFW_SIGNATURE_MATCH"

async def is_session_blocked(page: Page) -> bool:
    """
    Detecta a tela de bloqueio/sessão inválida pelo texto.
    Não depende de layout específico.
    """
    content = (await page.content()).lower()
    return (
        "página não acessível" in content
        or "violation category" in content
        or "appfw_signature_match" in content
    )
