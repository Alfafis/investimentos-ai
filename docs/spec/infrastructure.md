---
title: Infraestrutura de Dados e Integrações
area: ia-financeira
---

# Infraestrutura de Dados e Integrações

---

## Bolsa de Valores

### APIs e Fontes

| Fonte | Tipo | Dados | Acesso |
|---|---|---|---|
| **CVM (dados.cvm.gov.br)** | REST/FTP | Balanços, DRE, formulários de referência | Gratuito |
| **B3 Market Data** | WebSocket / REST | Cotações OHLCV, book de ofertas, índices | Pago (B3) |
| **Economatica** | REST | Séries históricas, fundamentos, pares | Pago |
| **StatusInvest API** | REST (scraping) | Indicadores fundamentalistas (P/L, DY, ROE) | Gratuito |
| **Alpha Vantage** | REST | OHLCV internacional, earnings calendar | Freemium |
| **SEC EDGAR (EUA)** | REST | 10-K, 10-Q, Form 4 (insider) | Gratuito |
| **InfoMoney / Valor RSS** | RSS + scraping | Notícias por ticker | Gratuito |

### Bancos de Dados

| Componente | Tecnologia | Uso |
|---|---|---|
| Séries temporais de preços | TimescaleDB ou InfluxDB | OHLCV histórico e realtime |
| Documentos de fundamentals | PostgreSQL + pgvector | RAG sobre balanços e relatórios |
| Cache de cotações | Redis | Preços realtime com TTL curto |

---

## Criptomoedas

### APIs e Fontes

| Fonte | Tipo | Dados | Acesso |
|---|---|---|---|
| **Glassnode** | REST | Métricas on-chain (MVRV, SOPR, NVT, LTH) | Pago |
| **Nansen** | REST | Labeling de wallets, smart money flows | Pago |
| **Etherscan / BSCScan** | REST | Transações on-chain, saldo de wallets | Freemium |
| **CoinGecko API** | REST | Preços, market cap, volume, dominância | Freemium |
| **CoinMarketCap** | REST | Fear & Greed Index, trending | Freemium |
| **DeFiLlama** | REST | TVL por protocolo, APY, chain breakdown | Gratuito |
| **LunarCrush** | REST | Social score, sentimento cripto | Freemium |
| **Binance / Bybit WS** | WebSocket | Order book realtime, trades | Gratuito |

### Bancos de Dados

| Componente | Tecnologia | Uso |
|---|---|---|
| Métricas on-chain históricas | TimescaleDB | Séries temporais de MVRV, SOPR etc |
| Embeddings de narrativas cripto | pgvector | RAG sobre análises e relatórios |
| Alertas de whale wallets | PostgreSQL | Rastreamento de endereços monitorados |

---

## Mercado Imobiliário

### APIs e Fontes

| Fonte | Tipo | Dados | Acesso |
|---|---|---|---|
| **FundsExplorer / StatusInvest** | Scraping | Dados de FIIs: DY, P/VP, vacância | Gratuito |
| **CVM (FIIs)** | REST/FTP | Relatórios gerenciais mensais, informe mensal | Gratuito |
| **FIPE ZAP API** | REST | Preço/m² por cidade, bairro e tipologia | Pago |
| **OLX / QuintoAndar** | Scraping | Preços de mercado em tempo real | Gratuito (scraping) |
| **BCB (crédito imobiliário)** | REST | Volume de crédito habitacional, LTV, spreads | Gratuito |
| **CBIC** | Scraping/PDF | INCC mensal e acumulado | Gratuito |
| **IBGE** | REST | IPCA, IGPM, dados demográficos por região | Gratuito |

### Bancos de Dados

| Componente | Tecnologia | Uso |
|---|---|---|
| Série histórica de preços/m² | PostgreSQL | Análise de tendência por região |
| Relatórios gerenciais de FIIs | pgvector | RAG sobre relatórios mensais |
| Índices de inflação | Redis / PostgreSQL | Ajuste de projeções em tempo real |

---

## Câmbio de Moedas

### APIs e Fontes

| Fonte | Tipo | Dados | Acesso |
|---|---|---|---|
| **BCB (api.bcb.gov.br)** | REST | Selic, PTax, boletim Focus, notas de reunião | Gratuito |
| **B3 Câmbio Futuro** | WebSocket | DOL futuro, order book de câmbio | Pago (B3) |
| **CFTC COT Report** | FTP/CSV | Posicionamento de participantes em pares com USD | Gratuito |
| **Alpha Vantage FX** | REST | OHLCV de pares de moedas (Forex) | Freemium |
| **OANDA API** | REST/WebSocket | Cotações realtime, book de ordens | Freemium |
| **FMI / BIS** | REST/Download | Dados macroeconômicos globais, balanço de pagamentos | Gratuito |
| **Investing.com** | Scraping | Calendário econômico global | Gratuito |

### Bancos de Dados

| Componente | Tecnologia | Uso |
|---|---|---|
| Série histórica de pares FX | TimescaleDB | Backtesting e análise técnica |
| Comunicados de BCs | pgvector | RAG sobre forward guidance e atas |
| Posicionamento COT histórico | PostgreSQL | Análise de extremos de posicionamento |

---

## Infraestrutura Compartilhada

### Pipeline de Ingestão (RAG)

```
Fonte bruta
    → Extração (scraper / API)
    → Limpeza e normalização
    → Chunking (400–600 tokens, overlap 50–80)
    → Embedding (text-embedding-3-small ou bge-m3)
    → Upsert no Vector DB (namespace por vertical/agente)
    → Indexação de metadados (fonte, data, vertical, autor)
```

### Stack de Infraestrutura

| Componente | Tecnologia recomendada | Alternativa |
|---|---|---|
| Vector DB | Supabase pgvector | Pinecone, Weaviate |
| Relacional | PostgreSQL (Supabase) | PlanetScale, Neon |
| Séries temporais | TimescaleDB | InfluxDB, QuestDB |
| Cache | Redis (Upstash) | Valkey |
| Message broker | Redis Streams | RabbitMQ, Kafka |
| Observabilidade | LangSmith | Langfuse, Arize |
| Eval RAG | Ragas | TruLens |
| Deploy de agentes | Railway / Fly.io | AWS ECS, GCP Cloud Run |
