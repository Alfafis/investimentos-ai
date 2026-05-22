---
title: Metodologias de Leitura de Mercado
area: ia-financeira
---

# Metodologias de Leitura de Mercado

Referência das metodologias analíticas usadas pelos agentes. Organizado por tipo de análise e por vertical onde se aplica.

---

## 1. Análise Fundamentalista (Bolsa / FIIs)

### Base conceitual
Premissa: o preço de mercado diverge do valor intrínseco no curto prazo, mas converge no longo. O analista estima o valor real e age quando o desconto é suficiente.

### Escola Graham (Value Investing clássico)
- **Margem de segurança:** comprar apenas quando preço < valor intrínseco com desconto de 30–50%
- **P/L < 15** e **P/VP < 1,5** como filtros de entrada
- **Current ratio > 2** e dívida/patrimônio < 1 como filtros de solidez
- Ignora crescimento; foca em ativos tangíveis e poder de lucro atual

### Escola Damodaran (Valuation moderno)
- **DCF (Discounted Cash Flow):** desconta fluxos de caixa livres futuros a WACC
  - Inputs: receita projetada, margem EBITDA, CapEx, WACC, g (crescimento na perpetuidade)
  - Sensível a WACC e g — sempre rodar análise de sensibilidade
- **EV/EBITDA:** compara valor da firma vs geração de caixa operacional; < 8x costuma ser barato em mercados emergentes
- **P/L (Price-to-Earnings):** simples, mas distorcido por não-recorrentes; usar P/L normalizado
- **ROE (Return on Equity):** mede eficiência do capital próprio; excelente > 15% de forma sustentada
- **ROIC vs WACC:** empresa destrói valor quando ROIC < WACC, mesmo crescendo

### Escola Buffett / Munger (Qualidade + Moat)
- **Vantagem competitiva durável (moat):** marca, switching cost, efeito de rede, custo baixo, ativo escasso
- **Free cash flow yield:** FCF / Market Cap > 5% é referência de valor
- **Crescimento de receita consistente** por 5–10 anos como filtro qualitativo
- **Management quality:** histórico de alocação de capital, insider ownership, recompras vs diluição

### FIIs — métricas específicas
- **P/VP (Preço / Valor Patrimonial):** < 1 = desconto sobre NAV; > 1 = prêmio
- **Dividend Yield:** dividendo anual / preço de mercado; comparar com Selic + spread de risco
- **Vacância:** física (área vaga) vs financeira (receita não recebida); < 5% é excelente em logística
- **Inadimplência:** % de locatários em atraso; alto em períodos de estresse econômico
- **Cap Rate implícito:** NOI anual / valor de mercado do FII; deve superar Selic para compensar risco

---

## 2. Análise Técnica (Bolsa / Cripto / Câmbio)

### Premissa
Toda informação relevante está refletida no preço. Padrões históricos de preço e volume se repetem porque derivam de comportamento humano (medo e ganância).

### Estrutura de mercado
- **Tendência:** sequência de topos e fundos ascendentes (alta) ou descendentes (baixa)
- **Suporte:** nível onde compradores historicamente superam vendedores (demanda)
- **Resistência:** nível onde vendedores historicamente superam compradores (oferta)
- **Rompimento (breakout):** preço fecha além de suporte/resistência com volume acima da média

### Candlestick patterns (reversão)
| Padrão | Sinal | Contexto necessário |
|---|---|---|
| Martelo / Hanging Man | Reversão | Após tendência definida |
| Engolfo de alta / baixa | Reversão forte | Volume confirmando |
| Doji | Indecisão | Após movimento extenso |
| Estrela da manhã / noite | Reversão de 3 candles | Após tendência clara |
| Pin bar | Rejeição de nível | Em suporte/resistência relevante |

### Indicadores de tendência
- **EMA 9/21:** cruzamento sinaliza mudança de tendência de curto prazo
- **EMA 200:** separador de regime; acima = bull market, abaixo = bear market
- **MACD (12, 26, 9):** momentum; sinal de compra quando linha MACD cruza acima do sinal
- **ADX:** força da tendência; > 25 = tendência forte; < 20 = mercado lateral

### Indicadores de momentum / sobrecompra-sobrevenda
- **RSI (14):** < 30 sobrevendido, > 70 sobrecomprado; divergências são mais confiáveis que cruzamentos de zona
- **Estocástico (14,3,3):** similar ao RSI; útil em mercados laterais
- **CCI:** identifica reversões em extremos estatísticos (+100 / -100)

### Indicadores de volatilidade
- **Bandas de Bollinger (20, 2σ):** squeeze (bandas comprimidas) precede expansão de volatilidade; toque na banda superior/inferior não é sinal sozinho
- **ATR (Average True Range):** mede volatilidade absoluta; usado para dimensionar stop-loss

### Volume
- **OBV (On-Balance Volume):** confirma tendência; divergência OBV ↓ + preço ↑ = distribuição oculta
- **VWAP:** preço médio ponderado por volume no dia; institucional compra abaixo do VWAP

### Análise estrutural avançada
- **Ondas de Elliott:** mercados se movem em 5 ondas impulsivas + 3 corretivas; wave 3 é sempre a mais longa e forte
- **Fibonacci:** retracements 38,2% / 50% / 61,8% como zonas de suporte em correções; extensões 127,2% / 161,8% como alvos
- **Wyckoff:** fases de acumulação (spring / test) e distribuição (UTAD / LPSY) identificam onde o "dinheiro inteligente" opera

---

## 3. Análise On-Chain (Cripto)

### Premissa
Blockchain é um livro-razão público. Diferente de ações, é possível observar diretamente o comportamento de holders, fluxos entre carteiras e saúde da rede.

### Métricas de ciclo de mercado
- **MVRV Ratio (Market Value / Realized Value)**
  - > 3,5: mercado historicamente sobrecomprado (top de ciclo)
  - < 1: mercado abaixo do custo médio dos holders (bottom de ciclo)
  - 1–3,5: zona intermediária

- **SOPR (Spent Output Profit Ratio)**
  - > 1: holders estão realizando lucro em média
  - < 1: holders realizando prejuízo (capitulação)
  - Resetar para 1 em bull market = suporte; resistência em 1 em bear market

- **NVT Ratio (Network Value / Transactions)**
  - Alto NVT: preço alto em relação ao uso da rede (sobrecomprado)
  - Baixo NVT: rede bem utilizada vs preço (subavaliado)

### Comportamento de holders
- **LTH vs STH Supply:** Long Term Holders (>155 dias) acumulando = bullish; distribuindo = top de ciclo
- **HODL Waves:** % do supply por tempo de última movimentação; quanto mais vermelho (recente) = mais especulação
- **Realized Cap:** soma do valor de cada coin no preço da última transação; crescimento sustentado = entrada real de capital

### Métricas de mineração (Bitcoin)
- **Hash Rate:** poder computacional da rede; alta = mineradores confiantes; queda abrupta = capitulação de mineradores
- **Dificuldade de mineração:** ajuste automático a cada 2016 blocos; tendência crescente = rede saudável
- **Miner Reserve:** estoque em carteiras de mineradores; vendas massivas = pressão de baixa

### Fluxos de exchange
- **Exchange Inflow:** coins entrando em exchanges = intenção de venda (bearish no curto prazo)
- **Exchange Outflow:** coins saindo de exchanges = acumulação em cold wallets (bullish)
- **Exchange Reserve:** estoque total nas exchanges; redução sustentada = supply squeeze

---

## 4. Análise Macro (Transversal)

### Ciclo econômico e alocação de ativos
| Fase | Características | Ativos favorecidos |
|---|---|---|
| Expansão | PIB ↑, desemprego ↓, crédito ↑ | Ações cíclicas, imóveis, commodities |
| Pico | Inflação alta, juros subindo | Commodities, caixa, proteção |
| Contração | PIB ↓, lucros caindo, crédito restrito | Renda fixa, defesivos, ouro |
| Recovery | Juros caindo, liquidez retornando | Ações de crescimento, cripto, imóveis |

### Política monetária
- **Taxa Selic:** benchmark de risco no Brasil; Selic alta eleva custo de capital → pressiona valuation de ações e FIIs; Selic baixa favorece ativos de risco
- **Juros reais:** Selic – IPCA esperado; positivo alto = renda fixa atraente vs ações; negativo = fuga para ativos reais
- **Curva de juros:** inversão (curto > longo) antecede recessão em 12–18 meses historicamente
- **Forward guidance:** comunicados do Copom e Fed sinalizam trajetória; mercado precifica antes do evento

### Inflação
- **IPCA:** índice oficial BR; acima da meta (3%) pressiona Copom a subir juros
- **IGPM:** usado em contratos imobiliários e de energia; mais volátil que IPCA
- **CPI (EUA):** impacta Fed → impacta dólar → impacta câmbio BR e risco-país
- **Núcleo de inflação:** exclui voláteis (energia, alimentos); melhor indicador de tendência

### Câmbio e risco-país
- **CDS (Credit Default Swap) Brasil:** prêmio de risco soberano; alta = fuga de capital estrangeiro
- **Risco-país (EMBI+):** spread em bps acima do Treasury americano; > 300 bps = alto risco
- **Balança comercial:** superávit sustentado apoia o real; déficit em conta corrente exige financiamento externo
- **DXY (Dollar Index):** fortalecimento do dólar pressiona moedas emergentes e commodities

---

## 5. Análise de Sentimento (Transversal)

### Indicadores de medo e ganância
- **VIX (CBOE Volatility Index):** < 15 = complacência; 20–30 = estresse; > 30 = pânico (oportunidade contrária)
- **Fear & Greed Index (Cripto):** 0–25 = medo extremo; 75–100 = ganância extrema; extremos = sinais contrários
- **Put/Call Ratio:** > 1 = mais puts = pessimismo excessivo; < 0,7 = otimismo excessivo

### Posicionamento de mercado
- **AAII Sentiment Survey:** pesquisa semanal com investidores individuais; > 50% bearish historicamente precede alta
- **Short Interest:** % do float em posições vendidas; > 20% = alvo de short squeeze
- **Insider buying/selling:** compras de insiders = sinal de confiança; vendas massivas = distribuição

### Análise de narrativas (Cripto / Redes Sociais)
- **Google Trends:** pico de buscas por "Bitcoin" ou "como investir" frequentemente coincide com tops
- **Social Volume (LunarCrush):** volume de menções; explosão de menções em altcoins = distribuição iminente
- **Rotação de narrativas:** mercados cripto se movem por narrativas cíclicas (Layer 1 → DeFi → NFT → AI tokens → RWA); identificar o estágio da narrativa determina o momento de entrada/saída

---

## 6. Smart Money e Fluxo Institucional

### Rastreamento de grandes players
- **Formulários 13F (SEC):** fundos com > US$100M devem declarar posições trimestralmente; atraso de 45 dias
- **COT Report (CFTC):** posicionamento de Commercials, Non-Commercials e Non-Reportables em futuros; Non-Commercials (fundos) em posição extrema = sinal contrário
- **Custódia B3:** relatório semanal de fluxo de capital estrangeiro em ações e renda fixa; saída sistemática = pressão cambial

### Order flow (Câmbio / Futuros)
- **Order book depth:** desequilíbrio grande em bids/asks indica pressão direcional iminente
- **Large trades (iceberg orders):** ordens fracionadas executadas em sequência = institucional acumulando sem mover preço
- **Delta de volume:** volume em agressores compradores vs vendedores por candle; delta positivo crescente = acumulação

### Dark pools e mercado OTC
- **Dark pool prints:** negociações fora de bolsa; volume expressivo em dark pool antes de movimento = insider/institucional
- **Block trades:** negociações de grandes lotes; direção revela confiança do institucional

---

## 7. Análise Imobiliária

### Rentabilidade de imóvel físico
- **Cap Rate (Capitalization Rate):** NOI anual / valor do imóvel; > Selic + 2–3% justifica o risco de iliquidez
- **DCF imobiliário:** projeta aluguéis + valorização + custos ao longo de 10 anos; desconta a taxa mínima de atratividade (TMA)
- **Gross Rent Multiplier (GRM):** preço / aluguel anual; GRM 12–15 é razoável no BR; acima de 20 é caro

### Comparação de mercado (CMA)
- **Preço por m²:** comparar com imóveis similares (padrão, localização, idade) em raio de 500m–2km
- **Ajustes:** m² de área privativa vs total, vaga coberta, andar, reformas, estado de conservação
- **Absorção:** tempo médio de venda/locação na região indica liquidez do mercado

### Macro imobiliário
- **Selic e crédito habitacional:** Selic alta encarece financiamento; parcela/renda > 30% estrangula demanda
- **INCC (Índice Nacional de Custo de Construção):** corrige contratos de imóveis na planta; alta = projetos encarecem
- **Lançamentos vs estoques:** excesso de lançamentos + estoques crescentes = desequilíbrio de oferta → pressão de queda nos preços
- **Déficit habitacional:** demanda estrutural que sustenta o mercado mesmo em ciclos negativos

---

## 8. Análise de Carry Trade (Câmbio)

### Mecânica
Tomar emprestado em moeda de baixo juro (JPY, CHF) e investir em moeda de alto juro (BRL, TRY). O lucro é o diferencial de juros menos o risco de variação cambial.

### Métricas-chave
- **Diferencial de juros:** Selic – Fed Funds (ou outra taxa benchmark); > 5 p.p. = carry atrativo
- **Volatilidade implícita (vol do par):** alta vol come o carry; posição só faz sentido quando vol implícita < carry anualizado
- **VIX como proxy de risco:** VIX > 25 = ambiente hostil para carry trades; reversões abruptas são comuns em crises

### Risco de reversão (Unwind)
- Carry trades são "pegar moedas na frente de um rolo-compressor"
- Em momentos de aversão ao risco global (Lehman, COVID), todos desfazem carry simultaneamente
- Resultado: moedas de alto juro colapsam rápido e profundamente; stop-loss é obrigatório

---

## Referência cruzada com agentes

| Metodologia | Agentes que aplicam |
|---|---|
| Fundamentalista (Graham/Damodaran) | Analista Fundamentalista, Analista de FIIs |
| Análise técnica | Analista Técnico, Rastreador de Baleias (confirmação) |
| On-chain | Analista On-Chain, Rastreador de Baleias, Agente DeFi & Yield |
| Macro | Analista Macro de Câmbio, Agente de Tendências Imobiliárias, Agente de Carry Trade |
| Sentimento | Agente de Sentimento e Notícias, Agente de Sentimento Cripto |
| Smart Money / Order Flow | Rastreador de Smart Money, Agente de Fluxo de Ordens |
| Imobiliária (Cap Rate / CMA) | Analista de Imóveis Físicos, Analista de FIIs |
| Carry Trade | Agente de Carry Trade, Analista Macro de Câmbio |

---

## Integração com métodos quantitativos (`metodologias-ia.md`)

Os métodos clássicos acima são complementados por técnicas de ML e métricas quantitativas. Pontos de integração:

| Sinal clássico | Método quantitativo que confirma ou contextualiza |
|---|---|
| Indicador de tendência (EMA, MACD) | **Índice de Hurst > 0,5** confirma que a série é persistente — aumenta peso dos sinais de seguimento de tendência |
| Indicador de reversão (RSI, Bollinger) | **Hurst < 0,5** confirma regime anti-persistente — reversão à média é mais provável |
| Identificação de regime de mercado | **SOM** segmenta o período atual em cluster (alta / baixa / lateral / crise) baseado em indicadores técnicos OHLCV |
| Análise de sentimento de notícias | **CNN + ELM + Word2Vec** (trigramas Mi-like) classifica direção diária a partir de corpus PT-BR; score alimenta `news_sentiment_analysis` |
| Gestão de risco de portfólio | **ΔCoVaR** identifica quais posições amplificam risco sistêmico — complementa VaR individual da skill `risk_calculator` |
| Stress test macro | **Matriz de contágio** (K×K) simula propagação de choque entre ativos; assimetria EUA→BR maior que BR→EUA por padrão |
| Suitability do usuário | **Análise discriminante + Alfa de Cronbach** classifica perfil conservador/moderado/agressivo; Router usa perfil para ponderar síntese |