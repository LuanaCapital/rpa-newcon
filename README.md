# RPA NewCon - Documentação do Projeto

## 📋 Visão Geral

**RPA NewCon** é um sistema de automação robótica de processos (RPA) desenvolvido em Python que integra plataformas de gestão de consórcios (NewCon) com um CRM (PipeRun). O sistema automatiza a busca e atualização de informações sobre pendências de cotas em consórcios, sincronizando os dados com oportunidades no PipeRun.

### Objetivo Principal
Automatizar o processo de consulta de pendências de cotas para consórcios através da navegação no sistema NewCon e sincronizar os resultados com o CRM PipeRun, gerando relatórios em CSV.

---

## 🏗️ Arquitetura do Projeto

```
rpa-newcon/
├── main.py                          # API FastAPI (endpoints)
├── rpa.py                           # Fluxos principais de automação
├── batch_runner.py                  # Processamento em lote de clientes
├── csv_writer.py                    # Utilitários para escrita de CSV
├── mappers.py                       # Mapeamento de dados
├── playwright_stealth.py            # Stealth mode para navegador
├── requirements.txt                 # Dependências do projeto
├── Dockerfile                       # Configuração Docker
│
├── pages/                           # Page Objects para automação
│   ├── auth_flow.py                # Fluxo de autenticação
│   ├── login.py                    # Login no Parceiros
│   ├── newcon_login_page.py        # Login no NewCon
│   ├── newcon_atendimento_page.py  # Busca de consórcios
│   ├── newcon_menu_page.py         # Navegação do menu NewCon
│   ├── newcon_pendencias_page.py   # Consulta de pendências
│   ├── parceiros_home_page.py      # Home do Parceiros
│   ├── rodobens_login_page.py      # Login Rodobens
│   └── session_guard.py            # Verificação de sessão
│
├── src/                            # Código-fonte estruturado
│   ├── domain/
│   │   └── types.py               # Tipos de dados (RPACotaStatus)
│   ├── piperun/
│   │   ├── client.py              # Cliente API PipeRun
│   │   └── updater.py             # Atualização de oportunidades
│   └── sheets/                    # Integração Google Sheets
│
├── utils/                          # Utilitários
│   ├── betterstack_logger.py      # Logger centralizado
│   ├── bigquery_helper.py         # Integração BigQuery
│   ├── report_helper.py           # Geração de relatórios
│   └── human_delay.py             # Delays humanos para bot-detection
│
└── relatorios/                    # Saída de relatórios CSV
```

---

## 🔧 Tecnologias Utilizadas

| Tecnologia | Versão | Propósito |
|------------|--------|----------|
| **Python** | 3.11+ | Linguagem principal |
| **FastAPI** | 0.124.0 | Framework web/API REST |
| **Playwright** | 1.56.0 | Automação de navegador |
| **Pydantic** | 2.12.5 | Validação de dados |
| **Requests** | 2.32.5 | Cliente HTTP |
| **Google APIs** | 2.18.7 | Integração Google Sheets/BigQuery |
| **python-dotenv** | 1.2.1 | Variáveis de ambiente |
| **Uvicorn** | 0.38.0 | Servidor ASGI |
| **logTail** | 1.0.1 | Logging remoto |

---

## 🚀 Como Usar

### 1. Instalação

#### Localmente
```bash
# Clonar repositório
git clone <repository-url>
cd rpa-newcon

# Criar ambiente virtual
python -m venv venv
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Instalar Playwright
playwright install --with-deps
```

#### Com Docker
```bash
docker build -t rpa-newcon .
docker run -e PYTHONPATH=/app rpa-newcon
```

### 2. Configurar Variáveis de Ambiente

Criar arquivo `.env` na raiz do projeto:

```env
# Autenticação Parceiros/NewCon
LOGIN=seu_login
PASSWORD=sua_senha
URL_LOGIN=https://url-do-login.com

# Autenticação Rodobens (alternativa)
RODOBENS_USUARIO=usuario_rodobens
RODOBENS_SENHA=senha_rodobens
RODOBENS_URL=https://url-rodobens.com

# PipeRun API
PIPERUN_TOKEN=seu_token_piperun
PIPERUN_BASE_URL=https://api-piperun-url.com

# Google APIs
GOOGLE_CREDENTIALS_JSON=caminho/para/credentials.json

# Logging
BETTERSTACK_SOURCE_TOKEN=seu_token_betterstack
```

### 3. Executar a API

```bash
# Desenvolvimento
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Produção
uvicorn main:app --host 0.0.0.0 --port 8000
```

Acesse a documentação interativa em: `http://localhost:8000/docs`

---

## 📡 Endpoints da API

### 1. Login Único NewCon
```http
POST /login-newcon
Content-Type: application/json

{
  "cota": "0001",
  "grupo": "001234"
}
```

**Resposta (200)**
```json
{
  "status": "ok",
  "grupo": "001234",
  "cota_base": "0001",
  "resultado": {
    "cotas": [
      {
        "cota": "0001",
        "em_aberto": true,
        "vencimento": "2026-04-15",
        "valor": "1500.00"
      }
    ]
  },
  "url": "https://...",
  "tipo_login": "canopus"
}
```

### 2. Processar Lote NewCon
```http
POST /newcon/lote
Content-Type: application/json

{
  "execution_id": "batch_001",
  "analysis_month": 4,
  "analysis_year": 2026,
  "clientes": [
    {
      "grupo": "001234",
      "cota": "0001"
    },
    {
      "grupo": "001235",
      "cota": "0002"
    }
  ]
}
```

**Resposta (200)**
```json
{
  "ok": true,
  "tipo_login": "canopus",
  "resultados": [
    {
      "grupo": "001234",
      "cota": "0001",
      "resultado": {...},
      "piperun_result": {...},
      "erro": null,
      "pago": "Sim"
    }
  ]
}
```

### 3. Processar Lote Rodobens
```http
POST /rodobens/lote/rodobens
Content-Type: application/json

{
  "execution_id": "batch_rodobens_001",
  "analysis_month": 4,
  "analysis_year": 2026,
  "clientes": [
    {
      "grupo": "001234",
      "cota": "0001"
    }
  ]
}
```

---

## 🔄 Fluxo de Processamento

### Fluxo Principal (run_fluxo_newcon)
```
1. Inicializar Playwright
2. Criar contexto com Stealth Mode
3. Autenticar no Parceiros (LoginPage)
4. Abrir NewCon (ParceirosHomePage)
5. Autenticar no NewCon (NewconLoginPage)
6. Buscar consórcios (NewconAtendimentoPage)
7. Abrir emissão de cobrança (NewconMenuPage)
8. Listar pendências e atualizar (NewconPendenciasPage)
9. Retornar resultado e fechar navegador
```

### Fluxo em Lote (run_lote)
```
1. Para cada cliente na lista:
   a. Verificar se sessão está bloqueada
   b. Se bloqueada: criar nova sessão e re-autenticar
   c. Buscar consórcios
   d. Abrir emissão de cobrança
   e. Listar pendências
   f. Mapear resultado para RPACotaStatus
   g. Sincronizar com PipeRun (atualizar deal)
   h. Salvar resultado em CSV
   i. Tratar erros e logar
2. Gerar relatório final
3. Fechar navegador
```

---

## 📊 Estrutura de Dados

### RPACotaStatus
```python
@dataclass(frozen=True)
class RPACotaStatus:
    grupo: NumStr              # Número do grupo/consorte
    cota: NumStr               # Número da cota
    pago_confirmado: bool      # Se o pagamento foi confirmado
    data_pagamento: Optional[str]  # Data do pagamento
    boletos_em_aberto: int     # Quantidade de boletos em aberto
```

### Resultado de Pendências
```python
{
    "cotas": [
        {
            "cota": "0001",
            "em_aberto": bool,      # True se há boletos pendentes
            "vencimento": "YYYY-MM-DD",
            "valor": "1500.00"
        }
    ]
}
```

### Resposta PipeRun
```python
{
    "deal_id": 12345,
    "updated": bool,           # Se a oportunidade foi atualizada
    "reason": "string"         # Motivo da atualização/recusa
}
```

---

## 📄 Relatórios Gerados

### 1. Relatório de Resultado Lote
**Arquivo**: `relatorios/resultado_lote_YYYY-MM.csv`

| Coluna | Descrição |
|--------|-----------|
| `grupo_base` | Grupo/consorte (6 dígitos) |
| `cota_base` | Cota base (4 dígitos) |
| `em_aberto` | True/False se há pendência |
| `cota_pendencia` | Número da cota com pendência |
| `vencimento` | Data de vencimento |
| `valor` | Valor da pendência |
| `deal_id` | ID da oportunidade no PipeRun |
| `piperun_result` | Resultado da sincronização |
| `erro` | Mensagem de erro (se houver) |
| `pago` | "Sim"/"Não" |

### 2. Relatório Final
**Arquivo**: `relatorios/relatorio_final_YYYY-MM.csv`

| Coluna | Descrição |
|--------|-----------|
| `grupo` | Grupo (6 dígitos) |
| `cota` | Cota (4 dígitos) |
| `resultado` | JSON com resultado completo |
| `piperun_result` | JSON com resposta PipeRun |
| `pago` | Status de pagamento |
| `erro` | Mensagem de erro (se houver) |

### 3. Relatório de Execução
**Arquivo**: `{execution_id}.csv` (salvo via report_helper.py)

Contém informações detalhadas de cada cota processada.

---

## 🛡️ Segurança e Anti-Detecção

### Stealth Mode
O projeto utiliza técnicas de stealth para evitar detecção por bot:

- **Aplicação de stealth via script**: Injeta JavaScript para disfarçar Playwright
- **Contexto com stealth**: Headers customizados e behavior humano
- **Delays humanos**: Pausas aleatórias entre ações (veja `utils/human_delay.py`)
- **Session Guard**: Verifica se a sessão foi bloqueada entre requisições

### Arquivo: playwright_stealth.py
```python
async def setup_context_with_stealth(context):
    # Adiciona headers humanos
    # Configura viewport humano
    # Injeta scripts anti-detecção

async def apply_stealth_to_page(page):
    # Injeta JavaScript para disfarçar Playwright
```

---

## 📝 Estrutura de Páginas (Page Objects)

### NewconAtendimentoPage
Responsável por buscar consórcios no sistema NewCon.
```python
await atendimento.buscar_consorciado(grupo="001234", cota="0001")
```

### NewconMenuPage
Navega pelos menus do NewCon.
```python
await menu.abrir_emissao_cobranca()
```

### NewconPendenciasPage
Lista pendências e extrai informações de cotas.
```python
resultado = await pendencias.resultado_por_cota_todas(cutoff_date=date(2026, 4, 30))
```

### ParceirosHomePage
Abre a página NewCon a partir do Parceiros.
```python
newcon_page = await parceiros_home.abrir_newcon()
```

---

## 🔐 Integração PipeRun

### Cliente PipeRun (src/piperun/client.py)

#### Buscar Deal Aberto
```python
client = PipeRunClient(token="...", base_url="...")
deal = client.find_open_retention_deal(
    grupo="001234",
    cota="0001",
    pipeline_id=123,
    stage_id=456
)
```

#### Atualizar Deal
```python
result = client.update_deal(
    deal_id=12345,
    payload={
        "custom_field_1": "value",
        "status": "won"
    }
)
```

### Updater (src/piperun/updater.py)
Sincroniza resultados de cotas com oportunidades no PipeRun.

---

## 📊 Logging e Monitoramento

### Betterstack Logger
Centraliza logs remotos via BetterStack.

```python
from utils.betterstack_logger import get_logger

logger = get_logger(__name__)
logger.info("Mensagem", extra={"event": "event_name", "grupo": "001234"})
logger.warning("Aviso", extra={...})
logger.exception("Erro", extra={...})
```

### Eventos Importantes
- `newcon_resultado_obtido` - Resultado da NewCon extraído
- `piperun_sync_start` - Sincronização com PipeRun iniciada
- `piperun_sync_done` - Sincronização com PipeRun concluída
- `processar_cliente_success` - Cliente processado com sucesso
- `processar_cliente_error` - Erro ao processar cliente
- `piperun_open_retention_deal_found` - Deal aberto encontrado
- `piperun_open_retention_deal_not_found` - Deal não encontrado

---

## 🔄 Mappers e Transformação de Dados

### newcon_result_to_cota_status
Transforma resultado do NewCon em objetos RPACotaStatus.

```python
cotas = newcon_result_to_cota_status(
    grupo=1234,
    resultado_por_cota={
        "cotas": [
            {
                "cota": "0001",
                "em_aberto": True,
                "vencimento": "2026-04-15"
            }
        ]
    }
)
# Retorna: [RPACotaStatus(grupo=1234, cota=1, pago_confirmado=False, boletos_em_aberto=1)]
```

---

## 🚨 Tratamento de Erros

### Fluxo de Erro
1. **Erro na busca de consórcios**: Capturado em batch_runner.py
2. **Sessão bloqueada**: Detectada por session_guard.py, nova autenticação realizada
3. **Erro PipeRun**: Capturado e logado, continua processamento
4. **Erro CSV**: Logado e continua processar

### Recuperação
- Erros são detalhados em traceback completo nos CSVs
- Sessões bloqueadas são automaticamente reabertas
- Cada cliente é processado independentemente (um erro não bloqueia outros)

---

## 📦 Estrutura de Requisições/Respostas

### ClienteItem (Pydantic)
```python
class ClienteItem(BaseModel):
    grupo: str      # Ex: "001234"
    cota: str       # Ex: "0001"
```

### NewconLoteRequest (Pydantic)
```python
class NewconLoteRequest(BaseModel):
    execution_id: str           # ID único de execução
    analysis_month: int         # 1-12
    analysis_year: int          # Ex: 2026
    clientes: List[ClienteItem] # Lista de clientes
```

---

## 🐳 Docker

### Build
```bash
docker build -t rpa-newcon:latest .
```

### Run
```bash
docker run \
  -e LOGIN=seu_login \
  -e PASSWORD=sua_senha \
  -e URL_LOGIN=https://... \
  -e PIPERUN_TOKEN=... \
  -e PIPERUN_BASE_URL=... \
  -p 8000:8000 \
  rpa-newcon:latest
```

### Arquivo Dockerfile
- Base: Python 3.11-slim
- Instala dependências de sistema para Playwright
- Instala Playwright com dependências
- Configura PYTHONPATH=/app
- Expõe porta 8000
- Executa uvicorn

---

## 🔍 Troubleshooting

### Sessão Bloqueada
**Sintoma**: Mensagem "Sessão bloqueada" após alguns clientes
**Solução**: O sistema detecta e cria nova sessão automaticamente

### Timeout Playwright
**Sintoma**: Erro `TimeoutError` em buscar_consorciado
**Solução**: Aumentar timeout em playwright.py ou verificar se site está disponível

### Erro PipeRun 401
**Sintoma**: `PipeRunAPIError: HTTP 401`
**Solução**: Verificar PIPERUN_TOKEN no .env

### Variáveis de Ambiente Não Encontradas
**Sintoma**: `RuntimeError: LOGIN, PASSWORD ou URL_LOGIN não estão definidos`
**Solução**: Criar arquivo .env com variáveis necessárias

---

## 📈 Escalabilidade

### Processamento em Lote
O sistema pode processar múltiplos clientes em sequência:
- Reutiliza navegador entre clientes (performance)
- Detecta bloqueio de sessão e reabre automaticamente
- Logs centralizados para monitoramento

### Limites Recomendados
- **Por batch**: 100-500 clientes (depende de timeouts)
- **Frequência**: 1x por dia (recomendado)
- **Paralelismo**: Não suportado (um cliente por vez)

---

## 🎯 Próximos Passos e Melhorias

### Potenciais Melhorias
1. Suporte a paralelismo (múltiplos navegadores simultaneamente)
2. Cache de sessões autenticadas
3. Retry automático com backoff exponencial
4. Integração com message queues (RabbitMQ/Kafka)
5. Métricas Prometheus
6. Dashboard de monitoramento em tempo real

---

## 📞 Suporte e Contato

Para dúvidas ou problemas:
1. Verificar logs em BetterStack
2. Consultar relatórios CSV gerados em `relatorios/`
3. Verificar variáveis de ambiente (.env)
4. Contatar time de desenvolvimento

---

## 📜 Licença

[Adicionar informação de licença conforme necessário]

---

**Última atualização**: 2026-04-16  
**Versão da Documentação**: 1.0

