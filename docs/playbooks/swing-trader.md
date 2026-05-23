# Playbook — Agente Swing Trader (B3)

Estratégia baseada em análise técnica com horizonte de **2–5 pregões**.  
Infra: dados com ~15min delay (yfinance + Brapi), verificação em 3 checkpoints diários.  
Day trade e scalping são inviáveis com essa infra — não tente.

---

## Restrições de infra — leia antes de qualquer regra

| Recurso | Disponível | Impacto |
|---------|-----------|---------|
| Dados OHLCV diários | ✅ yfinance | Base para todos os indicadores |
| Cotação atual | ✅ Brapi (~15min delay) | Preço de entrada/saída aproximado |
| Dados intraday (tick) | ❌ | VWAP, order flow, scalping inviáveis |
| Book de ofertas | ❌ | Sem análise de fluxo L2 |
| Execução automática | ❌ | Paper trade — decisões registradas, sem ordem real |

---

## 1. Universo e Watchlist

Watchlist fixa (18 tickers — validados no Brapi):
```
VALE3, ITUB4, PETR4, B3SA3, SBSP3, ABEV3, WEGE3, BBAS3, PRIO3, EMBJ3,
EQTL3, RENT3, VIVT3, SUZB3, CMIG4, RDOR3, BBDC4, GGBR4
```

Critérios de inclusão: peso Ibovespa, liquidez, setor distinto, dados disponíveis no Brapi.

---

## 2. Setups Válidos

Apenas setups identificáveis com dados diários OHLCV. Três setups permitidos:

### Setup A — Reversão de Sobrevenda
**Quando usar:** ativo caiu em excesso, mostra sinais de esgotamento.

Condições obrigatórias (todas):
- RSI(14) < 32
- Preço > EMA200 (tendência de longo prazo intacta)
- MACD histograma virando positivo (mínimo menos negativo que o candle anterior)
- Candle de reversão no fechamento: pin bar, engolfo de alta ou doji com sombra inferior

### Setup B — Pullback em Tendência
**Quando usar:** ativo em tendência de alta, corrige para suporte sem quebrar a tese.

Condições obrigatórias (todas):
- EMA9 > EMA21 > EMA50 > EMA200 (alinhamento de tendência)
- Preço recua e toca a faixa EMA21 ± 1%
- RSI entre 38 e 55 no momento do toque (não sobrecomprado, não destruído)
- Volume da correção abaixo da média de 20 dias (correção saudável)

### Setup C — Rompimento de Resistência
**Quando usar:** ativo acumula e rompe nível técnico relevante.

Condições obrigatórias (todas):
- Fechamento diário acima de resistência testada ≥ 2 vezes
- RSI entre 48 e 65 (momentum sem sobrecompra)
- Volume do rompimento ≥ 120% da média de 20 dias
- Preço > EMA50 (força de médio prazo confirmada)

---

## 3. Vetos — Nunca Operar

**Vetos hard (automáticos, sem exceção):**
- Preço < EMA200 → proibido comprar
- RSI > 68 no momento da entrada → aguardar correção
- Circuit breaker do dia ativo (ver seção 6)
- Caixa < R$ 500 (reserva mínima 10%) → proibido abrir nova posição

**Vetos soft (documentar, aguardar confirmação):**
- MACD histograma negativo sem sinal de virada → setup A inválido, revisar amanhã
- Volume de rompimento < 120% da média → setup C inválido, aguardar confirmação
- Notícia negativa relevante no sentiment → reduzir size ou aguardar

---

## 4. Gestão de Risco — Parâmetros Fixos

```
Capital do experimento : R$ 5.000,00
Reserva mínima (10%)  : R$ 500,00  — nunca usar
Capital operável      : R$ 4.500,00

Risco por operação    : 1% do capital = R$ 50,00
Stop-loss             : 6% abaixo do preço de entrada
Position size         : R$ 50 ÷ 6% = R$ 833 → cap em R$ 500 (10% do capital)

Máx. posições abertas : 3 simultâneas (= R$ 1.500 investido, 70% em caixa)
```

**Fórmula de position sizing:**
```
Quantidade = min(R$ 500, R$ 50 / distância_stop_percentual) / preço_entrada
```

Exemplo: PETR4 a R$ 44,00, stop em R$ 41,36 (−6%):
- R$ 50 ÷ 6% = R$ 833 → cap em R$ 500
- Quantidade = R$ 500 ÷ R$ 44,00 ≈ 11 ações

---

## 5. Entradas e Saídas

### Entrada
- Preço de referência: cotação Brapi no checkpoint (aceitar até 1% de slippage)
- Registrar no `save_paper_trade`: action=buy, preço, quantity, reason com setup e condições
- Registrar stop e alvo no `save_decision` do mesmo checkpoint

### Saídas — em ordem de prioridade

| Tipo | Regra | Ação |
|------|-------|------|
| Stop hard | Preço ≤ entrada × 0,94 (−6%) | Vender imediatamente, sem exceção |
| Take-profit | Preço ≥ entrada × 1,12 (+12%) | Realizar posição completa |
| Trailing stop | Lucro ≥ +6% → mover stop para break-even (+0%) | Documentar novo stop na decisão |
| EMA cross | Fechamento abaixo da EMA21 com posição lucrativa | Sair — tendência enfraqueceu |
| Time stop | 5 pregões sem atingir +5% | Sair — capital preso sem tese |
| Tese quebrada | Fundamento do setup invalidado (gap negativo, notícia relevante) | Sair antes do stop |

### Risco/Retorno mínimo
- R/R ≥ 1:2 obrigatório: se alvo é +12%, stop deve ser ≤ −6% ✓
- Não operar setup com R/R < 1:2

---

## 6. Circuit Breaker

Verificar em **todo checkpoint** (09h, 13h, 17h30):

| Condição | Ação |
|----------|------|
| 3 stops consecutivos (acumulado na semana) | Não abrir novas posições até segunda-feira |
| Perda do dia ≥ 3% do patrimônio total | Encerrar todas as posições abertas, encerrar operações do dia |
| Perda acumulada da semana ≥ 8% do capital | Encerrar experimento trader, só monitorar |

Circuit breaker **não é opcional** — registrar no `save_decision` quando ativado.

---

## 7. Gestão de Posições Abertas

### No checkpoint de 13h
Para cada posição aberta:
1. Verificar preço atual (get_stock_quotes) vs. stop e alvo definidos na entrada
2. Stop atingido? → vender (save_paper_trade action=sell, reason="stop-loss atingido")
3. Alvo atingido? → vender (reason="take-profit atingido")
4. Lucro ≥ +6%? → mover stop para break-even (documentar na decisão)
5. Tese ainda válida? → manter com stop documentado

### No checkpoint de 17h30
1. Verificar stops e takes (igual ao 13h)
2. Avaliar overnight: manter ou zerar?
   - **Manter:** setup ainda válido + stop claro + sem evento macro amanhã + não é sexta
   - **Zerar:** tese enfraquecida, evento de risco overnight, ou sexta-feira (preferir não carregar fim de semana)
3. Registrar decisão de overnight no save_decision com justificativa

### Sexta-feira — regra de fim de semana
Padrão: **zerar todas as posições no fechamento**.  
Exceção permitida: posição com lucro ≥ +8% + stop em break-even + sem risco macro no fim de semana → pode manter, com justificativa explícita.

---

## 8. Checkpoints Diários

### 09h — Pré-Mercado
1. Macro: Ibovespa futuro, USD/BRL, modo de mercado
2. Equity snapshot: caixa, patrimônio, circuit breaker status
3. Sentimento: notícias overnight nos 3 tickers mais movimentados
4. Análise técnica da watchlist: identificar setups válidos
5. Para cada setup: calcular entrada, stop, alvo, position size, R/R
6. Registrar plano do dia no save_decision

### 13h — Meio-Sessão
1. Gestão das posições abertas (stops, takes, trailing)
2. Atualizar equity snapshot
3. Novos setups emergentes: avaliar entradas se circuit breaker inativo
4. Registrar ações tomadas

### 17h30 — Fechamento
1. Gestão final das posições (stops, takes)
2. Decisão de overnight para cada posição
3. Equity snapshot final do dia
4. Score da watchlist: quais têm setup para amanhã
5. Relatório do dia: win rate, payoff, P&L
6. Análise qualitativa: plano foi seguido? erros?
7. **Sexta:** relatório semanal completo (ver rotinas)

---

## 9. Métricas de Performance

Calcular e registrar no fechamento de cada dia:

| Métrica | Fórmula |
|---------|---------|
| Win rate | Trades vencedores ÷ total de trades fechados |
| Payoff | Média dos ganhos ÷ média das perdas |
| Profit factor | Soma dos ganhos ÷ soma das perdas |
| P&L líquido do dia | realized_pnl_brl do dia (sem IR — paper trade) |
| Drawdown máximo | Maior queda de patrimônio intraday estimada |
| Stops consecutivos | Contador para circuit breaker |

---

## 10. Diferenças vs. Agente de Investimentos

| Dimensão | Investimentos (LP) | Swing Trade |
|---|---|---|
| Horizonte | Meses / anos | 2–5 pregões |
| Análise principal | Fundamentalista | Técnica (OHLCV diário) |
| Stop-loss | -8% | -6% |
| Take-profit | +20% | +12% (ou EMA21 cross) |
| Max posição | 10% do capital | 10% do capital (cap igual) |
| Max simultâneas | Sem limite explícito | 3 posições |
| Dividendos | Relevante | Irrelevante |
| Trailing stop | Não | Ativa com lucro ≥ +6% |
| Time stop | Não | 5 pregões sem +5% → sair |
| Weekend | Carrega normalmente | Padrão: zerar na sexta |
