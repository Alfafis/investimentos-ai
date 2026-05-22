# investimento-ai

Sistema de IA multi-agente especializado em análise de investimentos, cobrindo 4 verticais de mercado: Bolsa de Valores, Criptomoedas, Mercado Imobiliário e Câmbio.

## Estado do projeto

**Fase atual: Arquitetura e design.** Os arquivos `.md` da raiz definem toda a especificação; não há código implementado ainda. O próximo passo é escolher stack e iniciar implementação.

## Arquivos do projeto

### `agents.md`
Define os 13 agentes especializados organizados por vertical:

| Vertical | Agentes |
|---|---|
| Bolsa de Valores | Analista Fundamentalista, Analista Técnico, Rastreador de Smart Money, Agente de Sentimento e Notícias |
| Criptomoedas | Rastreador de Baleias, Analista On-Chain, Agente DeFi & Yield, Agente de Sentimento Cripto |
| Mercado Imobiliário | Analista de FIIs, Analista de Imóveis Físicos, Agente de Tendências Imobiliárias |
| Câmbio de Moedas | Analista Macro de Câmbio, Agente de Fluxo de Ordens, Agente de Carry Trade |

Cada agente tem `Objetivo` (o que faz) e `Backstory` (especialidade e fontes de dados que usa).

### `skills.md`
Define as 28 skills técnicas que os agentes usam como ferramentas:

**Skills gerais** (comuns a todos os agentes):
- `news_sentiment_analysis` — NLP sobre feeds de notícias; score [-1, 1] por ativo
- `portfolio_tracker` — consolida posições, P&L e exposição por vertical
- `risk_calculator` — VaR, drawdown máximo, Sharpe Ratio
- `alert_dispatcher` — notificações via Telegram, Slack, email (webhook)
- `rag_retriever` — consulta vector DB por namespace de agente
- `web_scraper` — extrai dados de portais públicos (InfoMoney, Valor, CVM)
- `report_generator` — gera relatórios em Markdown ou PDF
- `macro_context_loader` — snapshot Selic, IPCA, PIB, câmbio, S&P

**Skills específicas por vertical** (5 por vertical):
- Bolsa: `parse_quarterly_earnings`, `dcf_valuation`, `technical_pattern_detector`, `insider_trade_monitor`, `peer_comparison`
- Cripto: `onchain_metrics_fetcher`, `whale_wallet_tracker`, `exchange_flow_analyzer`, `defi_yield_scanner`, `fear_greed_index_reader`
- Imóvel: `cap_rate_calculator`, `fii_report_parser`, `real_estate_cma`, `incc_igpm_adjuster`, `credit_conditions_monitor`
- Câmbio: `order_book_reader`, `carry_trade_calculator`, `cot_report_parser`, `fx_correlation_matrix`, `central_bank_calendar`

### `metodologias.md`
Referência das metodologias analíticas clássicas usadas pelos agentes, organizadas por tipo:
- **Análise Fundamentalista** — escolas Graham, Damodaran e Buffett; métricas de FII (P/VP, DY, Cap Rate)
- **Análise Técnica** — estrutura de mercado, candlestick patterns, indicadores de tendência/momentum/volume, Elliott/Fibonacci/Wyckoff
- **Análise On-Chain** — MVRV, SOPR, NVT, LTH vs STH, fluxos de exchange
- **Análise Macro** — ciclo econômico, política monetária, inflação, risco-país
- **Análise de Sentimento** — VIX, Fear & Greed, posicionamento, narrativas cripto
- **Smart Money / Fluxo Institucional** — 13F, COT Report, order flow, dark pools
- **Análise Imobiliária** — Cap Rate, DCF, CMA, macro imobiliário
- **Carry Trade** — mecânica, diferencial de juros, risco de unwind

Inclui tabela de referência cruzada entre metodologias e agentes.

### `metodologias-ia.md`
Métodos quantitativos e de IA extraídos de pesquisas acadêmicas (4 papers). Focado em implementação com fórmulas e código:
- **Teorias de Eficiência** — Teoria de Dow, Passeio Aleatório (Fama 1965), HEM (Fama 1970)
- **Medidas de Risco** — VaR com fórmula, CoVaR/ΔCoVaR (Adrian & Brunnermeier 2011), regressão quantílica, matriz de contágio, stress test
- **Índice de Hurst** — estatística R/S, interpretação (H>0.5 = série persistente), código Python
- **SOM (Self-Organizing Maps)** — algoritmo Kohonen, BMU, U-Matrix, segmentação de regime de mercado
- **Redes Neurais** — MLP/backpropagation com equações completas, CNN para NLP, ELM (Extreme Learning Machine)
- **NLP Financeiro** — Word2Vec skip-gram, negative sampling, PMI para bigramas, pipeline PT-BR
- **Perfil do Investidor** — classificação conservador/moderado/agressivo, vieses cognitivos, Alfa de Cronbach
- **Estratégia de Negociação com ML** — modelo híbrido CNN+ELM, 60.2% acurácia no Ibovespa, minicontrato WIN

### `resumos-pdfs.md`
Resumos completos (conteúdo integral, não apenas metodologia) dos 4 artigos/teses acadêmicos lidos:
- **PDF 1 — SOM + Análise Técnica** (Panosso, UNL): dissertação de mestrado aplicando Self-Organizing Maps a indicadores técnicos do DJI (2001–2011); inclui Teoria de Dow, HEM, algoritmo SOM, Índice de Hurst (R/S statistic), variáveis técnicas, resultados por período e validação com simulação de investimentos
- **PDF 2 — Perfil do Investidor** (Paiva et al., IF Sudeste MG): artigo empírico com 60 investidores brasileiros; todos os tipos de investimento (poupança, CDB, LCI, LCA, Tesouro Direto, ações, fundos), 5 tipos de risco, análise discriminante (Lambda Wilks=0,582), Alfa de Cronbach=0,665; resultado: 63% conservador, 20% moderado, 17% agressivo
- **PDF 3 — CoVaR e Matriz de Contágio** (Almeida et al., RBFIN 2012): artigo sobre risco sistêmico via regressão quantílica; VaR/CoVaR/ΔCoVaR para 16 ações do Ibovespa; PETR4 = maior gerador de contágio; USIM5 = mais contaminado; contágio DJIA→IBOV = -2,14
- **PDF 4 — CNN+ELM+Word2Vec para Ibovespa** (Faria, tese doutorado): arquitetura I-CNNELM completa; 380k notícias financeiras em PT; 60,22% acurácia; comparação I-CNN/I-ELM/I-BoK; estratégia de negociação com minicontrato WIN (lucro R$329 vs R$30 buy-and-hold); todas as fórmulas, hiperparâmetros e tabelas de resultados

### `workflows.md`
Define 2 fluxos de orquestração com diagramas ASCII:

**Cenário A — Geração de Alpha**
Trigger (query do usuário ou sinal automático) → Router identifica vertical → Swarm paralelo de 3 agentes (Fundamentalista + Técnico + Sentimento) cada um com RAG enrichment → Agente Síntese pondera sinais → Gerador de Tese (recomendação, preço-alvo, stop-loss) → Dispatch (alerta/relatório)

**Cenário B — Gestão de Risco e Rebalanceamento**
Trigger (evento macro ou cron job) → Orquestrador Macro carrega carteira → 4 swarms (um por vertical) em paralelo → Agente de Risco consolida VaR cross-vertical e faz stress test → Agente de Rebalanceamento calcula delta e impacto fiscal → Output com ordens sugeridas e alertas

## Arquitetura de referência

- **Orquestração multi-agente:** Router distribui para swarms verticais; agentes rodam em paralelo dentro do swarm
- **RAG:** Cada agente enriquece respostas consultando vector DB no seu próprio namespace
- **Skills como tools:** Cada skill é uma função/tool independente com contrato `input → output` definido em `skills.md`
- **Alertas multi-canal:** `alert_dispatcher` entrega via Telegram, Slack ou email dependendo de severidade

## Integrações externas previstas

| Área | Fontes |
|---|---|
| Bolsa BR | CVM, B3 (custódia, câmbio futuro), InfoMoney, Valor Econômico |
| Bolsa US | SEC (Form 4, 13F), Bloomberg |
| Cripto | Etherscan, BSCScan, Glassnode, Nansen, CryptoQuant, LunarCrush, DeFiLlama, CoinMarketCap |
| Imóvel | FIPE ZAP, OLX, QuintoAndar, CBIC (INCC), Banco Central (crédito imobiliário) |
| Câmbio | B3 futuro, COT Report (CFTC), BCB, FMI, BIS |
| Macro | Banco Central do Brasil (Selic, IPCA, PIB, câmbio) |
| Social | Twitter/X, Reddit (r/CryptoCurrency), Google Trends |

## Decisões de implementação pendentes

Antes de começar a codificar, definir:
1. **Stack backend:** Python (FastAPI + CrewAI/LangChain) ou Node.js/TypeScript
2. **LLM:** Claude (recomendado — function calling nativo) ou multi-provider
3. **Vector DB:** Supabase pgvector, Pinecone ou Weaviate
4. **Interface:** API REST pura ou dashboard web (Next.js)
5. **Execução de agentes:** serverless (Edge Functions) ou servidor dedicado