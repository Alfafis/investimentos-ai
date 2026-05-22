---
title: Arquitetura de Skills
area: ia-financeira
---

# Arquitetura de Skills (Habilidades Técnicas)

---

## Skills Gerais (Comuns a Todos os Agentes)

| Skill | Descrição | Input | Output |
|---|---|---|---|
| `news_sentiment_analysis` | NLP sobre feeds de notícias; retorna score de sentimento por ativo | ticker + janela de tempo | score [-1, 1] + headlines relevantes |
| `portfolio_tracker` | Consolida posições, P&L e exposição por vertical | lista de ativos + preços | resumo de carteira + alertas |
| `risk_calculator` | Calcula VaR, drawdown máximo e Sharpe Ratio | série histórica de retornos | métricas de risco quantitativas |
| `alert_dispatcher` | Envia alertas via webhook (Telegram, Slack, email) | evento + severidade + mensagem | notificação disparada |
| `rag_retriever` | Consulta vector DB com contexto relevante para enriquecer respostas | query + namespace do agente | chunks + score de relevância |
| `web_scraper` | Extrai dados de portais públicos (InfoMoney, Valor, CVM) | URL + seletor CSS/XPath | texto estruturado |
| `report_generator` | Gera relatório de análise em Markdown ou PDF | dados estruturados + template | documento formatado |
| `macro_context_loader` | Carrega contexto macro atual: Selic, IPCA, PIB, câmbio, S&P | — | snapshot macroeconômico |

---

## Skills Específicas por Vertical

### Bolsa de Valores

| Skill | Descrição |
|---|---|
| `parse_quarterly_earnings` | Extrai e estrutura dados de balanços trimestrais (CVM/SEC) — receita, lucro, dívida, EBITDA |
| `dcf_valuation` | Modelo de valuation por fluxo de caixa descontado (DCF) com inputs configuráveis de WACC e crescimento |
| `technical_pattern_detector` | Detecta padrões gráficos (cabeça-ombro, IFR sobrevendido, cruzamento de médias) via séries OHLCV |
| `insider_trade_monitor` | Monitora formulários de transações de insiders na CVM e SEC Form 4 |
| `peer_comparison` | Compara múltiplos de um ativo contra peers do mesmo setor (P/L, EV/EBITDA, ROE) |

### Criptomoedas

| Skill | Descrição |
|---|---|
| `onchain_metrics_fetcher` | Busca métricas on-chain via Glassnode API: MVRV, SOPR, NVT, LTH Supply |
| `whale_wallet_tracker` | Monitora wallets de grandes holders via Etherscan/BSCScan e detecta movimentações relevantes |
| `exchange_flow_analyzer` | Analisa fluxo líquido de entrada/saída de exchanges centralizadas (sinal de pressão de venda/compra) |
| `defi_yield_scanner` | Varre protocolos DeFi para APY, TVL e risco de smart contract via DeFiLlama API |
| `fear_greed_index_reader` | Lê e interpreta índice Fear & Greed do CoinMarketCap + LunarCrush Social Score |

### Mercado Imobiliário

| Skill | Descrição |
|---|---|
| `cap_rate_calculator` | Calcula Cap Rate (NOI / Valor do Imóvel) e compara com custo de oportunidade (Selic) |
| `fii_report_parser` | Extrai dados de relatórios gerenciais mensais de FIIs (vacância, inadimplência, DY, P/VP) |
| `real_estate_cma` | Análise comparativa de mercado (CMA): preço/m² por região via FIPE ZAP / OLX / QuintoAndar API |
| `incc_igpm_adjuster` | Ajusta projeções de fluxo de caixa imobiliário pelos índices INCC e IGPM |
| `credit_conditions_monitor` | Monitora condições de crédito habitacional: LTV, spread bancário, volume de FGTS liberado |

### Câmbio de Moedas

| Skill | Descrição |
|---|---|
| `order_book_reader` | Lê profundidade de mercado (bid/ask stacks) em corretoras e na B3 câmbio futuro |
| `carry_trade_calculator` | Calcula diferencial de juros entre pares e estima custo/benefício de carry trade |
| `cot_report_parser` | Extrai e interpreta posicionamento de participantes do COT Report (CFTC) para pares com USD |
| `fx_correlation_matrix` | Calcula matriz de correlação entre pares de moedas e ativos de risco (S&P, ouro, DXY) |
| `central_bank_calendar` | Monitora calendário de reuniões de BCs (BCB, Fed, ECB, BoJ) e analisa comunicados (forward guidance) |
