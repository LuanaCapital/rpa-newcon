# Guia de Setup e Desenvolvimento - RPA NewCon

## 🚀 Setup Inicial

### Pré-requisitos
- Python 3.11 ou superior
- Git
- pip ou conda
- (Opcional) Docker

### Passo 1: Clonar o Repositório

```bash
git clone <repository-url>
cd rpa-newcon
```

### Passo 2: Criar Ambiente Virtual

```bash
# Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Passo 3: Instalar Dependências

```bash
# Instalar packages Python
pip install -r requirements.txt

# Instalar Playwright browsers
playwright install --with-deps

# Para Chromium apenas (mais leve)
playwright install chromium --with-deps
```

### Passo 4: Configurar Variáveis de Ambiente

Criar arquivo `.env` na raiz:

```env
# ===== AUTENTICAÇÃO PARCEIROS/NEWCON =====
LOGIN=seu_usuario_parceiros
PASSWORD=sua_senha_parceiros
URL_LOGIN=https://login.parceiros.com.br/login

# ===== AUTENTICAÇÃO RODOBENS (opcional) =====
RODOBENS_USUARIO=seu_usuario_rodobens
RODOBENS_SENHA=sua_senha_rodobens
RODOBENS_URL=https://newcon.rodobens.com.br

# ===== PIPERUN API =====
PIPERUN_TOKEN=seu_token_piperun_aqui
PIPERUN_BASE_URL=https://api-piperun-url/v1

# ===== GOOGLE APIs (opcional) =====
GOOGLE_CREDENTIALS_JSON=/caminho/para/credentials.json
# OU
GOOGLE_CREDENTIALS_JSON='{"type": "service_account", ...}'

# ===== BETTERSTACK LOGGING (opcional) =====
BETTERSTACK_SOURCE_TOKEN=seu_token_betterstack

# ===== VARIÁVEIS OPCIONAIS =====
DEBUG=false
LOG_LEVEL=INFO
```

### Passo 5: Validar Instalação

```bash
# Testar importações
python -c "import fastapi; print('FastAPI OK')"
python -c "from playwright.async_api import async_playwright; print('Playwright OK')"

# Rodar testes básicos
pytest tests/ -v  # Se houver testes
```

---

## 🏃 Executando a Aplicação

### Desenvolvimento

```bash
# Modo watch (auto-reload)
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Acesse documentação: http://localhost:8000/docs
```

### Produção

```bash
# Modo production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1

# Com Gunicorn (opcional)
gunicorn -w 1 -k uvicorn.workers.UvicornWorker main:app
```

### Com Docker

```bash
# Build
docker build -t rpa-newcon:latest .

# Run
docker run \
  -e LOGIN=seu_login \
  -e PASSWORD=sua_senha \
  -e URL_LOGIN=https://... \
  -e PIPERUN_TOKEN=seu_token \
  -e PIPERUN_BASE_URL=https://... \
  -p 8000:8000 \
  rpa-newcon:latest

# Com arquivo .env
docker run --env-file .env -p 8000:8000 rpa-newcon:latest
```

---

## 🧪 Testando Endpoints

### Via cURL

#### 1. Login Único NewCon
```bash
curl -X POST "http://localhost:8000/login-newcon" \
  -H "Content-Type: application/json" \
  -d '{
    "grupo": "001234",
    "cota": "0001"
  }' | json_pp
```

#### 2. Processar Lote NewCon
```bash
curl -X POST "http://localhost:8000/newcon/lote" \
  -H "Content-Type: application/json" \
  -d '{
    "execution_id": "batch_001",
    "analysis_month": 4,
    "analysis_year": 2026,
    "clientes": [
      {"grupo": "001234", "cota": "0001"},
      {"grupo": "001235", "cota": "0002"}
    ]
  }' | json_pp
```

#### 3. Processar Lote Rodobens
```bash
curl -X POST "http://localhost:8000/rodobens/lote/rodobens" \
  -H "Content-Type: application/json" \
  -d '{
    "execution_id": "batch_rodobens_001",
    "analysis_month": 4,
    "analysis_year": 2026,
    "clientes": [
      {"grupo": "001234", "cota": "0001"}
    ]
  }' | json_pp
```

### Via Swagger UI

1. Abra: `http://localhost:8000/docs`
2. Expanda o endpoint
3. Clique em "Try it out"
4. Preencha os valores
5. Clique em "Execute"

### Via Insomnia/Postman

1. Import: `http://localhost:8000/openapi.json`
2. Crie requisição
3. Configure headers e body
4. Execute

---

## 🔨 Desenvolvimento

### Estrutura de Projeto

```
rpa-newcon/
├── main.py                 # API endpoints
├── rpa.py                  # Orquestração RPA
├── batch_runner.py         # Processamento batch
├── pages/                  # Page Objects
│   ├── auth_flow.py
│   ├── login.py
│   ├── newcon_*.py
│   └── ...
├── src/
│   ├── domain/
│   ├── piperun/            # Integração PipeRun
│   └── sheets/             # Google Sheets
├── utils/                  # Utilitários
├── relatorios/             # Output CSVs
├── tests/                  # (Criar conforme necessário)
└── .env                    # Variáveis locais
```

### Adicionando Novo Endpoint

1. **Criar função assíncrona em rpa.py**:
```python
async def nova_funcao(param1: str, param2: int):
    # Implementar lógica
    return {"resultado": "ok"}
```

2. **Adicionar endpoint em main.py**:
```python
@app.post("/novo-endpoint")
async def novo_endpoint(param1: str, param2: int):
    try:
        return await nova_funcao(param1, param2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

3. **Testar via Swagger**: `http://localhost:8000/docs`

### Criando Page Object

1. **Criar novo arquivo em pages/**:
```python
from playwright.async_api import Page

class NovaPage:
    def __init__(self, page: Page):
        self.page = page
    
    async def acao_importante(self):
        # Implementar ação
        await self.page.fill("#id-campo", "valor")
        await self.page.click("#id-botao")
        await self.page.wait_for_selector(".resultado")
```

2. **Usar em batch_runner.py**:
```python
from pages.nova_page import NovaPage

nova = NovaPage(page)
resultado = await nova.acao_importante()
```

### Adicionando Mapper

1. **Criar função em mappers.py**:
```python
def novo_mapeamento(dados_brutos: dict) -> dict:
    """Transforma dados brutos em formato esperado"""
    return {
        "campo1": dados_brutos.get("field1"),
        "campo2": int(dados_brutos.get("field2", 0))
    }
```

2. **Usar em batch_runner.py**:
```python
from mappers import novo_mapeamento

resultado_mapeado = novo_mapeamento(resultado_bruto)
```

---

## 📝 Logging

### Estrutura de Logs

```python
from utils.betterstack_logger import get_logger

logger = get_logger(__name__)

# Info
logger.info("Evento iniciado", extra={
    "event": "evento_iniciado",
    "grupo": "001234",
    "cota": "0001"
})

# Warning
logger.warning("Aviso importante", extra={
    "event": "aviso",
    "grupo": "001234"
})

# Exception (com traceback)
try:
    # algum código
except Exception as e:
    logger.exception("Erro ao processar", extra={
        "event": "erro_processamento",
        "grupo": "001234"
    })
```

### Acesso aos Logs

**BetterStack Dashboard**:
- Acesse com token configurado em `.env`
- Monitore eventos em tempo real
- Configure alertas

**Arquivo de Log Local** (se configurado):
- Arquivo criado em `logs/` (criar conforme necessário)

---

## 🐛 Debugging

### Modo Debug no Playwright

```python
# Em rpa.py, durante desenvolvimento
browser = await p.chromium.launch(headless=False)  # Ver navegador
# headless=True para produção
```

### Pauses e Breakpoints

```python
# Pausar execução para inspecionar
await page.pause()  # Abre devtools do navegador

# Breakpoint Python
import pdb
pdb.set_trace()
```

### Logs Detalhados

```python
# Habilitar logs Playwright
import logging
logging.getLogger("playwright").setLevel(logging.DEBUG)
```

---

## 🔍 Troubleshooting Comum

### Erro: "Playwright não instalado"
```bash
playwright install --with-deps
```

### Erro: "Variáveis de ambiente não encontradas"
```bash
# Verificar .env
cat .env
# ou criar novo
cp .env.example .env
# Editar com suas credenciais
```

### Erro: "Timeout em buscar_consorciado"
```python
# Aumentar timeout em pages/newcon_atendimento_page.py
await self.page.wait_for_selector(selector, timeout=60000)  # 60 segundos
```

### Erro: "Sessão bloqueada"
- Sistema detecta e recria automaticamente
- Se persistir, aguardar alguns minutos
- Verificar se credenciais estão corretas

### Erro: "PipeRun 401 Unauthorized"
- Verificar PIPERUN_TOKEN em `.env`
- Verificar se token não expirou
- Contatar time PipeRun

---

## 📊 Monitorando Execução

### Verificar Logs de Execução

```bash
# Último lote processado
cat relatorios/relatorio_final_2026-04.csv

# Resultado detalhado
cat relatorios/resultado_lote_2026-04.csv

# Erro específico
grep "erro" relatorios/*.csv
```

### Métricas Importantes

**Arquivo**: `relatorios/relatorio_final_YYYY-MM.csv`

| Métrica | Descrição |
|---------|-----------|
| Total de linhas | Total de clientes processados |
| Linhas com erro | Falhas no processamento |
| "Pago"/"Não Pago" | Status de pagamento |

---

## 🚢 Deploy

### Deploy Local (Desenvolvimento)

```bash
# Terminal 1: Rodar API
uvicorn main:app --reload

# Terminal 2: Monitores logs
tail -f logs/app.log
```

### Deploy com Docker

```bash
# Build image
docker build -t rpa-newcon:v1.0 .

# Push para registry (opcional)
docker tag rpa-newcon:v1.0 seu-registry/rpa-newcon:v1.0
docker push seu-registry/rpa-newcon:v1.0

# Run container
docker run -d \
  --name rpa-newcon-prod \
  --env-file .env \
  -p 8000:8000 \
  rpa-newcon:v1.0
```

### Deploy em Servidor

```bash
# Clonar e setup
git clone repo
cd rpa-newcon
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install --with-deps

# Criar .env com credenciais
nano .env

# Usar systemd ou supervisor
# Exemplo com systemd: /etc/systemd/system/rpa-newcon.service
[Unit]
Description=RPA NewCon
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/app/rpa-newcon
Environment=PYTHONUNBUFFERED=1
ExecStart=/app/rpa-newcon/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

---

## 📚 Referências

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Playwright Python](https://playwright.dev/python/)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [Python asyncio](https://docs.python.org/3/library/asyncio.html)

---

## 🤝 Contribuindo

1. **Fork** o repositório
2. **Create** branch para feature: `git checkout -b feature/nova-feature`
3. **Commit** mudanças: `git commit -am 'Add nova feature'`
4. **Push** branch: `git push origin feature/nova-feature`
5. **Open** Pull Request

### Padrões de Código

- Usar type hints em todas as funções
- Docstrings em classes e funções públicas
- Format com Black (opcional): `black .`
- Lint com Pylint/Flake8 (opcional)

---

## 📞 Suporte

- **Issues**: Abrir issue no repositório
- **Logs**: Consultar BetterStack dashboard
- **Email**: [adicionar contato]

---

**Última atualização**: 2026-04-16

