# Playbook — Agente de Investimentos (Longo Prazo)

Estratégia baseada em fundamentos + técnica. Horizonte de semanas a meses.  
Operações sujeitas à aprovação humana antes da execução.

---

## 1. Pré-Análise

Verificações obrigatórias antes de qualquer processamento:

- Bolsa aberta? Verificar horário B3 (10h–17h55 BRT) e feriados
- Contexto macro: Selic, IPCA, USD/BRL, variação do Ibovespa no dia
- Notícias relevantes: sentiment analysis nos feeds (InfoMoney, Valor)
- Calendário econômico: divulgação de balanços, reunião COPOM, dados de inflação

Se mercado fechado → gerar análise para execução na próxima abertura.  
Se volatilidade anormal (Ibovespa > ±3%) → modo conservador, sem novas compras.

---

## 2. Avaliação da Carteira

### 2.1 Exposição

- % por ativo (limite: 10% por posição)
- % por setor (limite: 30% por setor)
- % em caixa (mínimo: 10% reserva)
- Correlação entre ativos: alertar se par com |corr| ≥ 0.7

### 2.2 Performance

- P&L realizado e não realizado por posição
- Comparação com benchmark: Ibovespa e CDI
- Métricas da carteira: Sharpe Ratio, Sortino, beta, drawdown máximo

### 2.3 Gatilhos de saída automática

- Stop-loss atingido (padrão: -8%)
- Take-profit atingido (padrão: +20%)
- Tempo máximo de holding ultrapassado

---

## 3. Critérios de Venda

| Gatilho | Ação |
|---|---|
| Stop-loss ≤ -8% | Venda imediata |
| Take-profit ≥ +20% | Venda parcial ou total |
| Mudança de fundamentos | Reavaliação + venda se tese quebrada |
| Concentração > 10% | Redução de posição |
| Sinais técnicos de reversão | RSI > 70 + MACD cruzamento bearish |
| Rebalanceamento necessário | Redução proporcional |

---

## 4. Critérios de Compra

### 4.1 Filtros de qualidade (obrigatórios)

- Liquidez mínima: volume médio diário > R$ 5M
- Market cap > R$ 500M
- Sem investigação CVM ativa

### 4.2 Análise técnica

- Tendência: preço acima da EMA200
- Momentum: RSI < 40 (zona de oportunidade)
- Confirmação: MACD histograma positivo ou cruzamento bullish

### 4.3 Análise fundamentalista

- P/L < 20 (ou abaixo da média do setor)
- ROE > 10%
- Dívida/EBITDA < 3x
- Dividend yield > 0 (para perfil renda)

### 4.4 Score combinado

| Critério | Peso |
|---|---|
| Técnica | 40% |
| Fundamentalista | 40% |
| Sentimento de notícias | 10% |
| Contexto macro | 10% |

Score mínimo para recomendação de compra: **0.6 / 1.0**

---

## 5. Gestão de Risco

- Position sizing via Kelly Criterion (cap: 10% do capital por operação)
- Risco máximo por operação: 2% do capital total
- Máximo de posições simultâneas: 10
- Circuit breaker: parar operações se perda diária ≥ 2% ou semanal ≥ 5%
- Reserva de caixa: mínimo 10% da carteira sempre

---

## 6. Relatório de Saída

Cada ciclo de análise gera um relatório com:

- Resumo macro (Selic, IPCA, USD/BRL, Ibovespa)
- Estado atual da carteira (P&L, exposição, métricas)
- Alertas ativos (stops próximos, concentração excessiva)
- Oportunidades identificadas (com score e justificativa)
- Recomendações: **vender X**, **comprar Y com tamanho Z**
- Cenários: otimista / realista / pessimista para cada recomendação
- Histórico de decisões anteriores e acertos (para auditoria)

---

## 7. Pipeline

```
[Trigger: agendado ou evento]
          ↓
[Pré-Análise]
  mercado aberto? · macro · notícias · calendário
          ↓
[Avaliação da Carteira]
  exposição · P&L · stops · correlação
          ↓
[Screening de Oportunidades]
  filtros de qualidade · técnica · fundamentalista · score
          ↓
[Gestão de Risco]
  position sizing · circuit breaker · limites
          ↓
[Decisão]
  o que vender · o que comprar · quanto
          ↓
[Aprovação Humana]
          ↓
[Execução / Relatório]
          ↓
[Logging + Backtesting Contínuo]
```

---

## 8. Regras do Agente

- LLM raciocina e interpreta contexto — cálculos críticos são código determinístico
- Toda decisão deve ter justificativa auditável registrada
- Backtesting valida a estratégia com dados históricos antes de cada ciclo real
- Paper trading precede operação com capital real em novas estratégias
