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

### 4. Permissões do agente autônomo (allowlist)

O agente roda sem supervisão e lê texto externo (RSS via `scan_market_news` e `get_sentiment`).
Uma manchete com prompt injection não pode virar comando na máquina, por isso os runners
(`agent/run_rotina.ps1`, `agent/run_experiment.ps1`) **não** usam `--dangerously-skip-permissions`:

| Flag | Efeito |
|------|--------|
| `--mcp-config agent/mcp-config.json --strict-mcp-config` | Carrega só o servidor `investimentos-ai` (`http://127.0.0.1:8001/mcp`) do arquivo versionado; ignora MCPs globais da máquina |
| `--permission-mode dontAsk` | Tool fora da allowlist é negada na hora — não trava esperando prompt |
| `--allowedTools mcp__investimentos-ai__<tool>,...` | Só as tools MCP usadas pelas rotinas (lista explícita no runner) |
| `--disallowedTools Bash,PowerShell,Write,Edit,NotebookEdit,WebFetch,WebSearch,Read,Glob,Grep` | Remove essas tools do contexto, mesmo que o `settings.json` da máquina as libere |

Consequências:
- O agente não escreve arquivos. O relatório `.md` é a resposta final do `claude -p`, gravada pelo runner em `logs/`.
- O MCP server precisa estar rodando em `127.0.0.1:8001` antes das rotinas (`docker compose up -d`). Não é preciso `claude mcp add`.
- Para liberar uma tool MCP nova para o agente, adicione o nome em `$AllowedTools` no runner. Nunca libere Bash, Write, Edit, WebFetch nem WebSearch.
- Requer Claude Code com suporte a `--permission-mode dontAsk` e `--strict-mcp-config`. Em versão antiga o CLI recusa o flag e a rotina falha com erro no log, sem rodar sem proteção.

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
| 19 | `save_paper_trade` | Registra compra/venda virtual (paper trading). Idempotente: mesma `idempotency_key` (padrão `<session_id>:<action>:<TICKER>`) devolve o trade existente com `duplicate: true` |
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

Logs em `logs/agent-<rotina>-YYYY-MM-DD.log` e relatórios em `logs/<rotina>-YYYY-MM-DD-<HH>h<MM>.md` (ignorados pelo git). O relatório é gravado pelo runner a partir da resposta final do agente — o agente não tem Write.

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

## Resultados e aprendizados

Experimento de paper trading de 5 dias úteis (capital inicial de R$ 5.000), com seis rotinas agendadas rodando `claude -p`. A análise de 28 logs (6 agentes x 4 dias, de 2026-05-25 a 2026-05-28) levantou 9 falhas; o estado de cada uma está abaixo.

### O que funcionou

- **Vetos por fundamentos.** VALE3 foi vetada 3 vezes em 4 dias (P/L 25, ROE 6,84%, DCF -40%) mesmo com sinal técnico de compra com confiança 1,0.
- **Saída por tempo.** O time stop de ABEV3 foi executado sem desvio: 5 pregões, +1,77%.
- **Alerta de EMA200.** O risco de CMIG4 perder a EMA200 foi apontado 2 dias antes e escalado duas vezes no dia 28; o playbook protegeu sem intervenção.

### Resultado da carteira

Último registro nas notas (2026-05-28): R$ 5.008,86, +0,18%, 100% em caixa.

### As 9 falhas encontradas

| # | Falha | Tratamento |
|---|-------|-----------|
| 1 | `score_tickers` não aplicava o veto de preço abaixo da EMA200 (SUZB3 saiu "buy" a -14,9% da EMA200) | Corrigido: veto no scorer (`d276b80`) |
| 2 | Rotina das 09h ativava Setup B/C sem checar fundamentos (VALE3, 3 dias seguidos) | Em aberto: a rotina `agent/rotina-03-trader-pre.md` ainda não chama `fundamental_analysis` |
| 3 | Rotinas executadas duas vezes (radar, abertura, trader-pre) | Parcial: `save_decision` idempotente com `session_id` único (`d276b80`) e `save_paper_trade` idempotente por `idempotency_key` (`acd1393`). O lock de execução no scheduler continua em aberto |
| 4 | `run_investing_decision` voltou vazio sem erro | Parcial: corrigida a causa (caixa ignorado quando `positions=[]`, o que zerava o Kelly) em `d276b80`. Retorno de erro explícito continua em aberto |
| 5 | Stop de CMIG4 (R$ 15,06) acima da entrada (R$ 11,30) | Corrigido: `save_paper_trade` rejeita stop >= entrada em compra e stop <= entrada em venda (`d276b80`) |
| 6 | Stop de ABEV3 divergente entre rotinas por 2 sessões | Em aberto: `stop_price` e `target_price` agora são gravados em `paper_trades` (`d276b80`), mas `get_paper_portfolio` não os devolve e as rotinas ainda calculam o stop por conta própria |
| 7 | NLP com falso negativo em manchetes financeiras BR (SUZB3: `sentiment_score=-1.0`) | Parcial: termos como "autoriza", "joint venture" e "bilhões" adicionados ao léxico (`d276b80`). A regra de `review_manual` antes do veto continua em aberto |
| 8 | Volume não verificável (Setup C exige volume >= 120% da média de 20d) | Corrigido: `technical_analysis` devolve `volume_last`, `volume_avg_20d` e `volume_ratio_20d` (`d276b80`) |
| 9 | `ibovespa_change_pct = null` intermitente | Parcial: corrigido o `isinstance` incorreto em `macro.py` (`d276b80`). Cache do último valor do BCB com flag `stale_data` continua em aberto |

Fora da lista de 9, o commit `410f7ec` trocou `--dangerously-skip-permissions` por allowlist de tools MCP no agente (seção "Permissões do agente autônomo"), porque o agente lê texto externo (RSS) sem supervisão.

Bugs conhecidos que ainda não foram corrigidos estão registrados como `xfail` em `tests/` (venda sem posição aberta aceita, `PETR4` e `PETR4.SA` tratados como tickers diferentes, custo médio que ignora o consumo FIFO, Sortino sem retorno negativo devolvendo NaN).

## Testes

Os testes não usam rede: yfinance, Brapi, BCB e RSS são substituídos por mocks e sockets ficam bloqueados. O banco SQLite é temporário.

Requer Python 3.10 ou superior (o `mcp_server/server.py` exige). Use um venv:

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -q
```

`requirements-dev.txt` fixa `mcp<2`, porque `server.py` usa `mcp.server.fastmcp`, que o `mcp` 2.x renomeou. Os testes marcados `xfail(strict=True)` documentam bugs conhecidos: ao corrigir um deles, o teste passa a falhar como XPASS e o marcador deve ser removido.

---

## Próximos Passos

- [ ] Agentes CrewAI: Analista Fundamentalista, Analista Técnico, Agente de Sentimento
- [ ] Pipeline Cenário A (`docs/spec/workflows.md`): Router → swarm paralelo → síntese → tese
- [ ] FIIs (mesma fonte B3, tickers diferentes)
- [ ] Vertical cripto (CoinGecko API)
- [ ] Câmbio (B3 futuro, BCB PTax)
- [ ] Análise fundamentalista via dados CVM (pgvector RAG)
- [ ] Persistência de portfólio real (PostgreSQL)
