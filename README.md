# Investimentos AI

Sistema de análise de investimentos para a Bolsa B3, composto por uma REST API, um servidor MCP com 21 ferramentas para Claude, e infraestrutura de experimento com agente autônomo.

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
│   └── server.py               # 21 MCP tools para Claude
├── agent/
│   ├── run_experiment.ps1      # Runner do agente autônomo (Claude Code CLI)
│   └── setup_scheduler.ps1     # Registra task horária no Windows Task Scheduler
├── docs/
│   ├── playbooks/              # investing.md, trader.md — fonte de verdade do agente
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

## MCP Tools (21 ferramentas para Claude)

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
| 1 | `get_stock_quotes` | Cotações B3 via Yahoo Finance (~15min delay) |
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
| 17 | `save_decision` | Persiste contexto completo de decisão (SQLite) |
| 18 | `get_decision_log` | Lê histórico de decisões por data ou últimas N |
| 19 | `save_paper_trade` | Registra compra/venda virtual (paper trading) |
| 20 | `get_paper_portfolio` | Posições abertas em papel com custo médio |
| 21 | `get_trade_outcomes` | P&L realizado de operações fechadas + posições abertas |

---

## Agente Autônomo (Experimento)

Runner que executa o playbook de investimentos de hora em hora via Claude Code CLI.

### Rodar manualmente

```powershell
.\agent\run_experiment.ps1
.\agent\run_experiment.ps1 -Watchlist "PETR4,VALE3,ITUB4" -Cash 10000
```

### Ativar agendamento (Admin)

```powershell
.\agent\setup_scheduler.ps1
```

Executa seg–sex, 10h–18h, a cada 1 hora. Logs em `logs/agent_YYYY-MM-DD-HHh.log`.

### Controle da task

```powershell
Start-ScheduledTask  -TaskName "InvestimentosAI-Agente"   # forçar agora
Disable-ScheduledTask -TaskName "InvestimentosAI-Agente"  # pausar
Unregister-ScheduledTask -TaskName "InvestimentosAI-Agente" -Confirm:$false  # remover
```

### Fluxo do agente por ciclo

```
get_macro_context → get_decision_log (últimas 3) → get_paper_portfolio
    → run_investing_decision → save_paper_trade (sells + buys)
    → save_decision (contexto completo)
```

---

## Fontes de Dados

| Dado | Fonte | Uso |
|------|--------|-----|
| Cotações (~15min delay) | Yahoo Finance via `yfinance` | Preços, dividend yield, market cap |
| Histórico OHLCV | Yahoo Finance via `yfinance` | Backtesting e indicadores |
| Macro BR | BCB API (gratuita, sem key) | Selic, IPCA, PTax |
| Notícias | InfoMoney RSS, Investing.com BR RSS | Sentimento PT-BR |

> **Nota:** Para backtesting em produção, substituir `yfinance` por B3 Market Data ou Economatica.

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
