# playwright_stealth.py
"""
Módulo para contornar detecção de automação Playwright.
Implementa técnicas de stealth mode e mascaramento de propriedades do navegador.
"""

from typing import Optional
from playwright.async_api import BrowserContext, Page


async def apply_stealth_mode(page: Page) -> None:
    """
    Aplica técnicas de stealth para contornar detecção de automação.
    Remove propriedades que indicam automação e mascara o navegador.
    """

    # Injetar JavaScript para mascarar propriedades de automação
    await page.add_init_script("""
    // Remover propriedades que indicam automação
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
    });
    
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5],
    });
    
    Object.defineProperty(navigator, 'languages', {
        get: () => ['pt-BR', 'pt', 'en-US', 'en'],
    });
    
    // Chrome headless signal
    window.chrome = {
        runtime: {}
    };
    
    // Mascarar o User-Agent
    Object.defineProperty(navigator, 'userAgent', {
        get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    });
    
    Object.defineProperty(navigator, 'platform', {
        get: () => 'Win32',
    });
    
    // Remover sinais de headless
    Object.defineProperty(window, 'outerHeight', {
        writable: true,
        value: 1080,
    });
    
    Object.defineProperty(window, 'outerWidth', {
        writable: true,
        value: 1920,
    });
    
    // Mascarar devicePixelRatio
    Object.defineProperty(window, 'devicePixelRatio', {
        writable: true,
        value: 1,
    });
    
    // Remover sinais de automation via chrome
    const originalQuery = window.matchMedia;
    window.matchMedia = function(query) {
        if (query === '(prefers-color-scheme: dark)') {
            return {
                matches: false,
                media: query,
                onchange: null,
                addListener: () => {},
                removeListener: () => {},
                addEventListener: () => {},
                removeEventListener: () => {},
                dispatchEvent: () => true,
            };
        }
        return originalQuery(query);
    };
    
    // Mascarar permissões
    const originalQuery2 = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery2(parameters)
    );
    """)


async def setup_context_with_stealth(browser_context: BrowserContext) -> None:
    """
    Configura um contexto do navegador com headers e propriedades de stealth.
    """

    # Headers customizados para simular navegador real
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Cache-Control': 'max-age=0',
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
    }

    # Adicionando headers extras para parecer mais natural
    await browser_context.set_extra_http_headers(headers)


async def apply_stealth_to_page(page: Page) -> None:
    """
    Aplica todas as técnicas de stealth a uma página específica.
    Deve ser chamado logo após criar uma nova page.
    """
    await apply_stealth_mode(page)


async def create_stealth_page(browser_context: BrowserContext) -> Page:
    """
    Cria uma nova página com configurações de stealth já aplicadas.

    Args:
        browser_context: O contexto do navegador

    Returns:
        Uma página configurada com stealth mode
    """
    page = await browser_context.new_page()
    await apply_stealth_to_page(page)
    return page

