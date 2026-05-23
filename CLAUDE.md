# investimento-ai

Sistema de IA multi-agente especializado em análise de investimentos — foco atual: Bolsa de Valores (B3/Ibovespa).

## Estado do projeto

**Fase atual: Phase 1 em implementação.** Stack definida (FastAPI + yfinance + FastMCP). Skills compartilhadas e de análise de ações já implementadas. Próximo passo: agentes CrewAI e pipeline do Cenário A.

## Estrutura de /docs

```
docs/
├── playbooks/           # Como cada agente opera (acionável, fonte de verdade para implementação)
│   ├── investing.md     # Pipeline do agente de investimentos de longo prazo
│   └── trader.md        # Pipeline do agente day-trade/swing
├── spec/                # Contratos do sistema (o que será construído)
│   ├── agents.md        # 13 agentes especializados por vertical
│   ├── skills.md        # 28 skills técnicas com contratos input/output
│   ├── workflows.md     # Cenário A (Alpha) e Cenário B (Risco/Rebalanceamento)
│   └── infrastructure.md # Fontes de dados, bancos, APIs por vertical
├── architecture/        # Decisões técnicas
│   ├── frameworks.md    # Comparativo CrewAI vs LangGraph vs AutoGen
│   └── training.md      # Estratégia de treinamento e RAG por agente
└── research/            # Referência acadêmica (background, não operacional)
    ├── methodologies.md # Graham, Damodaran, Análise Técnica, On-Chain, Carry Trade
    ├── quantitative.md  # VaR/CoVaR, SOM, CNN+ELM, Word2Vec, Kelly, Hurst
    └── papers.md        # Resumos completos dos 4 papers acadêmicos
```

**Regra:** `playbooks/` e `spec/` guiam a implementação. `architecture/` registra decisões tomadas. `research/` é referência — não muda o código diretamente.

## Decisões tomadas

| Decisão | Escolha |
|---|---|
| Stack backend | Python — FastAPI + CrewAI + FastMCP |
| LLM | Claude (function calling nativo via MCP) |
| Dados históricos | yfinance (B3: sufixo `.SA`) |
| Dados real-time | PENDENTE |
| Macro gratuito | BCB API (Selic série 11, IPCA série 13522, PTax) |
| Cache | Redis + fallback in-memory |
| Deploy | Docker Compose (redis + api + mcp) |
| Foco Phase 1 | Bolsa de Valores / Ibovespa apenas |

## Arquitetura atual

```
app/
├── quotes/           # yfinance client (cotações ~15min delay)
├── simulation/       # Backtesting engine (RSI, EMA, Combined, Dividend Value)
├── skills/
│   ├── shared/       # macro, risk, portfolio, sentiment
│   └── stocks/       # technical, fundamental
├── routers/          # REST: quotes, simulation, analysis
└── models.py         # Todos os modelos Pydantic
mcp_server/
└── server.py         # 14 tools MCP expostos para Claude
```

## Skills implementadas (Phase 1)

| Skill | Arquivo | Status |
|---|---|---|
| `macro_context_loader` | `skills/shared/macro.py` | ✅ |
| `risk_calculator` | `skills/shared/risk.py` | ✅ |
| `portfolio_tracker` | `skills/shared/portfolio.py` | ✅ |
| `news_sentiment_analysis` | `skills/shared/sentiment.py` | ✅ |
| `technical_pattern_detector` | `skills/stocks/technical.py` | ✅ |
| `fundamental_analyzer` | `skills/stocks/fundamental.py` | ✅ |

## Próximos passos

1. **Phase 2** — Agentes CrewAI: Analista Fundamentalista, Analista Técnico, Agente de Sentimento
2. **Phase 3** — Pipeline Cenário A (`docs/spec/workflows.md`): Router → swarm paralelo → síntese → tese
3. **Phase 4** — Exposição completa via MCP + REST

## Integrações externas

| Área | Fontes |
|---|---|
| Bolsa BR (cotações ~15min) | yfinance (`.SA` suffix) |
| Bolsa BR (histórico) | yfinance (`.SA` suffix) |
| Macro BR | BCB API (gratuita, sem key) |
| Notícias | InfoMoney RSS, Investing.com BR RSS |
| Bolsa US | SEC (Form 4, 13F) — Phase 3+ |
| Cripto | Glassnode, CryptoQuant — Phase 3+ |
| Imóvel | FIPE ZAP, CBIC — Phase 3+ |
| Câmbio | B3 futuro, COT Report — Phase 3+ |
