# Investimentos AI

Python server for B3 stock market data, investment simulation, and MCP integration with Claude.

## Architecture

```
investimentos-ai/
├── app/
│   ├── config.py               # Settings via pydantic-settings
│   ├── models.py               # Pydantic models (Quote, Trade, SimulationResult…)
│   ├── main.py                 # FastAPI app + CORS
│   ├── quotes/
│   │   └── client.py           # yfinance client — Redis cache → in-memory fallback
│   ├── simulation/
│   │   ├── strategies.py       # Buy/sell criteria (4 strategies)
│   │   └── engine.py           # Backtesting engine via yfinance
│   └── routers/
│       ├── quotes.py           # GET /quotes
│       └── simulation.py       # POST /simulation
├── mcp_server/
│   └── server.py               # FastMCP server — 4 tools for Claude
├── Dockerfile
├── docker-compose.yml          # api + mcp + redis
└── .env.example
```

## Setup

### 1. Environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
APP_PORT=8000
CACHE_TTL_SECONDS=60
REDIS_URL=redis://redis:6379/0
```

### 2. Docker (recommended)

```bash
docker compose up --build
```

Services:
| Service | URL |
|---------|-----|
| REST API + Swagger | `http://localhost:8000/docs` |
| MCP HTTP server | `http://localhost:8001` |
| Redis | `localhost:6379` |

### 3. Local (without Docker)

```bash
pip install -r requirements.txt

# REST API
uvicorn app.main:app --reload --port 8000

# MCP server (stdio — for Claude Desktop)
python -m mcp_server.server

# MCP server (HTTP — for network use)
python -m mcp_server.server --transport streamable-http --port 8001
```

## REST API

### Quotes

```
GET /quotes?tickers=PETR4,VALE3,ITUB4
GET /quotes?tickers=PETR4&sort=change_percent:desc
GET /quotes/{ticker}
```

Sort options: `value:asc`, `value:desc`, `change_percent:asc`, `change_percent:desc`, `volume:asc`, `volume:desc`

**Response:**

```json
{
  "cached": false,
  "response_time_ms": 120,
  "results": [
    {
      "ticker": "B3:PETR4",
      "symbol": "PETR4",
      "name": "Petrobrás",
      "currency": "BRL",
      "quote": {
        "value": 45.47,
        "change_value": 0.47,
        "change_percent": 1.04,
        "market_cap": 618988000000,
        "updated_at": "2026-05-15T17:07:45-03:00"
      },
      "dividends": {
        "yield_12m_percent": 8.3,
        "yield_12m_cash": 3.77
      }
    }
  ]
}
```

### Simulation

```
POST /simulation
GET  /simulation/strategies
```

**Request body:**

```json
{
  "ticker": "PETR4",
  "start_date": "2023-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 10000.0,
  "strategy": "combined",
  "stop_loss_pct": 0.08,
  "take_profit_pct": 0.20
}
```

**Response:**

```json
{
  "ticker": "PETR4",
  "strategy": "combined",
  "period_start": "2023-01-02",
  "period_end": "2024-12-30",
  "initial_capital": 10000.0,
  "final_capital": 13450.22,
  "total_return_percent": 34.5,
  "max_drawdown_percent": 11.2,
  "total_trades": 8,
  "winning_trades": 5,
  "losing_trades": 2,
  "win_rate_percent": 71.4,
  "trades": [...],
  "final_portfolio": [...]
}
```

## Strategies

| Name | Buy Criterion | Sell Criterion |
|------|--------------|----------------|
| `rsi` | RSI < 30 | RSI > 70 |
| `ema_crossover` | EMA9 crosses above EMA21 | EMA9 crosses below EMA21 |
| `combined` ⭐ | RSI < 35 AND price above EMA200 | RSI > 65 |
| `dividend_value` | 5-day drop > 5% AND RSI < 40 | RSI > 60 |

Universal exits applied to all strategies:
- **Stop-loss:** -8% from entry (configurable)
- **Take-profit:** +20% from entry (configurable)

**Recommended:** `combined` — uses EMA200 as trend filter to avoid buying in downtrends.

## MCP Tools (Claude integration)

### Claude Desktop (stdio)

Add to your `claude_desktop_config.json`:

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

See `claude_desktop_config.example.json` for reference.

### Available tools

| Tool | Description |
|------|-------------|
| `get_stock_quotes` | B3 prices via Yahoo Finance (~15min delay) |
| `simulate_investment` | Backtest a strategy on historical data |
| `screen_stocks` | Filter buy candidates by dividend yield and daily drop |
| `list_strategies` | List strategies with buy/sell criteria |

### Example prompts

```
Busca cotações de PETR4, VALE3 e ITUB4
```
```
Simula investimento de R$10.000 em VALE3 de 2022 até 2024 com estratégia combined
```
```
Faz um screening das ações [PETR4, VALE3, BBDC4, ITUB4, WEGE3] com dividend yield acima de 5%
```

## Data Sources

| Data | Source | Use |
|------|--------|-----|
| Quotes (~15min delay) | Yahoo Finance via `yfinance` | Prices, dividend yield, market cap |
| Historical OHLCV | Yahoo Finance via `yfinance` | Backtesting and indicator calculation |

> **Note:** For production backtesting, replace `yfinance` with B3 Market Data or Economatica — Yahoo Finance data for B3 tickers can have gaps and delays.

## Caching

- **Primary:** Redis with configurable TTL (`CACHE_TTL_SECONDS`, default 60s)
- **Fallback:** In-memory dict if Redis is unavailable

## Next Steps

- [ ] FIIs support (same B3 source, different tickers)
- [ ] Crypto vertical (CoinGecko API)
- [ ] FX vertical (BCB API — `api.bcb.gov.br`)
- [ ] Fundamental analysis (CVM data, pgvector RAG)
- [ ] CrewAI swarms per vertical (Fundamentalista, Técnico, Sentimento)
- [ ] LangGraph orchestrator for macro risk / portfolio rebalancing
- [ ] Portfolio persistence (PostgreSQL)
