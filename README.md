# Investimentos AI

Sistema de análise de investimentos para a Bolsa B3, composto por uma REST API, um servidor MCP com 23 ferramentas para Claude, e infraestrutura de experimento com agente autônomo.

## Arquitetura

```
investimentos-ai/
├── app/
│   ├── config.py               # Settings via pydantic-settings
│   ├── models.py               # Pydantic models
│   ├── main.py                 # FastAPI app + CORS
│   ├── quotes/
│   │   └── client.py           # yfinance client — Redis cache → in-memory fallback
│   ├── simulation/
│   │   ├── strategies.py       # 4 estratégias (RSI, EMA, Combined, Dividend Value)
│   │   └── engine.py           # Backtesting engine
│   ├── skills/
│   │   ├── shared/             # macro, risk, portfolio, sentiment, scorer, sell_evaluator
│   │   └── stocks/             # technical, fundamental
│   ├── agent/
│   │   └── investing_pipeline.py  # Orquestrador do playbook (usado pelo MCP)
│   ├── experiment/
│   │   └── store.py            # SQLite — decisions + paper trades
│   └── routers/
│       ├── quotes.py           # GET /quotes
│       ├── simulation.py       # POST /simulation
│       └── analysis.py         # GET /analysis/* (macro, risk, technical, fundamental…)
├── mcp_server/
│   └── server.py               # 23 MCP tools para Claude
├── agent/
│   ├── run_rotina.ps1              # Runner principal — carrega rotina + playbook → claude -p
│   ├── setup_scheduler.ps1         # Registra 6 tasks no Windows Task Scheduler (rodar 1x como Admin)
│   ├── rotina-00-radar.md          # 08h — scan de notícias overnight
│   ├── rotina-01-investing-abertura.md  # 10h — scoring + compras/vendas
│   ├── rotina-02-investing-fechamento.md # 17h — stops/takes + P&L + prep amanhã
│   ├── rotina-03-trader-pre.md     # 09h — análise overnight + setups
│   ├── rotina-04-trader-mid.md     # 13h — monitoramento mid-session
│   ├── rotina-05-trader-fechamento.md   # 17h30 — zerar posições + relatório
│   ├── claude_desktop_scheduled.md # Referência das rotinas (Claude Desktop alternativo)
│   └── run_experiment.ps1          # Runner legado (sessão única manual)
├── docs/
│   ├── playbooks/              # investing.md, swing-trader.md, day-trader.md — fonte de verdade do agente
│   ├── spec/                   # agents.md, skills.md, workflows.md, infrastructure.md
│   ├── architecture/           # frameworks.md, training.md
│   └── research/               # methodologies.md, quantitative.md, papers.md
├── Dockerfile
├── docker-compose.yml          # api + mcp + redis
└── .env.example
```

**Separação de responsabilidades:**
- **API + MCP** = dados, persistência, execução de skills determinísticas
- **Claude (agente)** = raciocínio, regras, métricas, decisões — via MCP tools

---

## Setup

### 1. Variáveis de ambiente

```bash
cp .env.example .env
```

```env
APP_PORT=8000
CACHE_TTL_SECONDS=60
REDIS_URL=redis://redis:6379/0
BRAPI_API_KEY=          # obter em brapi.dev — necessário para cotações em tempo real
```

### 2. Docker (recomendado)

```bash
docker compose up --build
```

| Serviço | URL |
|---------|-----|
| REST API + Swagger | `http://localhost:8000/docs` |
| MCP HTTP server | `http://localhost:8001` |
| Redis | `localhost:6379` |

### 3. Local (sem Docker)

```bash
pip install -r requirements.txt

# REST API
uvicorn app.main:app --reload --port 8000

# MCP server (stdio — Claude Desktop)
python -m mcp_server.server

# MCP server (HTTP)
python -m mcp_server.server --transport streamable-http --port 8001
```

---

## REST API

### Cotações

```
GET /quotes?tickers=PETR4,VALE3,ITUB4
GET /quotes?tickers=PETR4&sort=change_percent:desc
GET /quotes/{ticker}
```

### Simulação

```
POST /simulation
GET  /simulation/strategies
```

### Análise

```
GET /analysis/macro
GET /analysis/risk/{ticker}
GET /analysis/technical/{ticker}
GET /analysis/fundamental/{ticker}
GET /analysis/sentiment/{ticker}
GET /analysis/correlation?tickers=PETR4,VALE3
GET /analysis/dcf/{ticker}
GET /analysis/peers/{ticker}?peers=CSAN3,VBBR3
POST /analysis/portfolio
```

---

## Estratégias de Simulação

| Nome | Critério de Compra | Critério de Venda |
|------|-------------------|-------------------|
| `rsi` | RSI < 30 | RSI > 70 |
| `ema_crossover` | EMA9 cruza acima EMA21 | EMA9 cruza abaixo EMA21 |
| `combined` ⭐ | RSI < 35 E preço acima EMA200 | RSI > 65 |
| `dividend_value` | Queda 5d > 5% E RSI < 40 | RSI > 60 |

Saídas universais: stop-loss -8% e take-profit +20% (configuráveis).

---

## MCP Tools (23 ferramentas para Claude)

### Integração

```json
{
  "mcpServers": {
    "investimentos-ai": {
      "type": "http",
      "url": "http://127.0.0.1:8001/mcp"
    }
  }
}
```

### Ferramentas disponíveis

| # | Tool | Descrição |
|---|------|-----------|
| 1 | `get_stock_quotes` | Cotações B3 via Brapi (primário) ou yfinance fallback (~15min delay) |
| 2 | `simulate_investment` | Backtest de estratégia em dados históricos |
| 3 | `screen_stocks` | Filtro por dividend yield e queda diária |
| 4 | `list_strategies` | Lista estratégias com critérios de compra/venda |
| 5 | `get_macro_context` | Selic, IPCA, USD/BRL, Ibovespa, mercado aberto |
| 6 | `analyze_risk` | VaR, Sharpe, Sortino, beta, Kelly, max drawdown |
| 7 | `check_stock_circuit_breaker` | Verifica se ticker atingiu limite de perda |
| 8 | `get_correlation_matrix` | Correlação de Pearson entre ativos |
| 9 | `track_portfolio_positions` | P&L, exposição setorial, melhor/pior posição |
| 10 | `get_sentiment` | Sentimento de notícias PT-BR (InfoMoney, Investing.com) |
| 11 | `technical_analysis` | RSI, MACD, EMA, Bollinger, padrões de candle |
| 12 | `fundamental_analysis` | P/L, P/VP, ROE, EV/EBITDA, dividend yield, DCF |
| 13 | `run_dcf_valuation` | DCF configurável (WACC + growth rate) |
| 14 | `compare_peers` | Comparação de múltiplos com peers do setor |
| 15 | `run_investing_decision` | Pipeline completo do playbook de investimentos |
| 16 | `score_tickers` | Score combinado técnica 40% + fund. 40% + sent. 10% + macro 10% |
| 17 | `save_decision` | Persiste contexto completo de decisão no SQLite |
| 18 | `get_decision_log` | Lê histórico de decisões por data ou últimas N |
| 19 | `save_paper_trade` | Registra compra/venda virtual (paper trading) |
| 20 | `get_paper_portfolio` | Posições abertas com custo médio (FIFO) |
| 21 | `get_trade_outcomes` | Snapshot completo: caixa, P&L realizado/não realizado, patrimônio total, retorno % |
| 22 | `export_experiment_csv` | Exporta trades e decisões para CSV em `/data/` |
| 23 | `scan_market_news` | Varre RSS feeds e retorna B3 tickers rankeados por volume de notícias × sentimento |

---

## Agente Autônomo (Experimento 5 dias úteis)

Experimento de paper trading com agente autônomo rodando de seg–sex via **Windows Task Scheduler**.

### Mecanismo principal — Windows Task Scheduler

Registrar as 6 tasks (rodar uma vez como Administrador):

```powershell
.\agent\setup_scheduler.ps1
```

| # | Rotina | Horário | Função |
|---|--------|---------|--------|
| 0 | Radar de Mercado | seg–sex 08h | `scan_market_news` — detecta tickers em alta nas notícias |
| 1 | Investimentos — Abertura | seg–sex 10h | Macro + scoring + compras/vendas + decisão |
| 2 | Investimentos — Fechamento | seg–sex 17h | Stops/takes + P&L do dia + prep amanhã + relatório semanal (sex) |
| 3 | Trader — Pré-Mercado | seg–sex 09h | Análise overnight + setups do dia (swing trade) |
| 4 | Trader — Meio-Dia | seg–sex 13h | Gestão de posições abertas + novos setups |
| 5 | Trader — Fechamento | seg–sex 17h30 | Zerar posições + relatório + relatório semanal (sex) |

Cada task chama `run_rotina.ps1 -Rotina <id>`, que carrega o arquivo `agent/rotina-<id>.md` e o playbook correspondente como system prompt para `claude -p`.

### Fluxo de cada sessão

```
get_macro_context
  → get_decision_log (últimas 3)
  → get_paper_portfolio
  → get_trade_outcomes(since_date="2026-05-26", initial_capital=5000)
      # retorna: caixa, P&L realizado/não realizado, patrimônio total, retorno %
  → run_investing_decision (ou technical_analysis para trader)
  → save_paper_trade (sells + buys aprovados)
  → save_decision (equity_snapshot + reasoning auditável)
```

Sextas-feiras: relatório semanal completo com patrimônio final, win rate, aprendizados.

### Runner manual

```powershell
# Rodar rotina específica
.\agent\run_rotina.ps1 -Rotina "00-radar"
.\agent\run_rotina.ps1 -Rotina "01-investing-abertura"

# Comandos Task Scheduler
Get-ScheduledTask -TaskName "InvestimentosAI-*"             # listar
Start-ScheduledTask -TaskName "InvestimentosAI-Radar"       # disparar manualmente
Get-ScheduledTask -TaskName "InvestimentosAI-*" | Disable-ScheduledTask  # pausar tudo
```

Logs em `logs/agent-<rotina>-YYYY-MM-DD.log` e relatórios em `logs/<rotina>-YYYY-MM-DD-<hora>.md` (ignorados pelo git).

### Persistência (SQLite via Docker volume)

```bash
# Ver trades acumulados
docker exec investimentos-ai-mcp-1 sqlite3 /data/experiment.db \
  "SELECT action, ticker, price, quantity, reason FROM paper_trades ORDER BY timestamp"

# Exportar para CSV (via MCP tool export_experiment_csv)
docker cp investimentos-ai-mcp-1:/data/trades.csv ./trades.csv
docker cp investimentos-ai-mcp-1:/data/decisions.csv ./decisions.csv
```

---

## Fontes de Dados

| Dado | Fonte | Uso |
|------|--------|-----|
| Cotações B3 (primário) | [Brapi](https://brapi.dev) (`BRAPI_API_KEY`) | Preços em tempo real, dividend yield, market cap |
| Cotações B3 (fallback) | Yahoo Finance via `yfinance` | Quando Brapi não tem o ticker |
| Histórico OHLCV | Yahoo Finance via `yfinance` | Backtesting e indicadores técnicos (200+ dias) |
| Macro BR | BCB API (gratuita, sem key) | Selic, IPCA, PTax |
| Notícias (sentimento) | InfoMoney RSS, Investing.com BR RSS | Sentimento ticker-specific PT-BR |
| Notícias (radar) | MoneyTimes RSS, Suno RSS, InfoMoney RSS, Investing.com BR RSS | Detecção de tickers em alta |

> **Nota:** Day trade real exige dados tick-a-tick (latência < 1s). yfinance tem ~15min delay — adequado apenas para swing trade e análise fundamentalista.

## Cache

- **Primário:** Redis com TTL configurável (`CACHE_TTL_SECONDS`, padrão 60s)
- **Fallback:** dict in-memory se Redis indisponível

---

## Próximos Passos

- [ ] Agentes CrewAI: Analista Fundamentalista, Analista Técnico, Agente de Sentimento
- [ ] Pipeline Cenário A (`docs/spec/workflows.md`): Router → swarm paralelo → síntese → tese
- [ ] FIIs (mesma fonte B3, tickers diferentes)
- [ ] Vertical cripto (CoinGecko API)
- [ ] Câmbio (B3 futuro, BCB PTax)
- [ ] Análise fundamentalista via dados CVM (pgvector RAG)
- [ ] Persistência de portfólio real (PostgreSQL)
