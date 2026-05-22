# Playbook — Agente Trader (Day Trade / Swing Trade)

Estratégia baseada em análise técnica e fluxo. Velocidade e disciplina acima de fundamentos.  
Decisões em segundos (day trade) a dias (swing). Stop-loss obrigatório em toda operação.

---

## Diferenças vs. Agente de Investimentos

| Dimensão | Investimento | Trading |
|---|---|---|
| Análise principal | Fundamentalista | Técnica + fluxo |
| Horizonte | Meses / anos | Minutos / dias |
| Relação com volatilidade | Tolera | Explora |
| Dividendos | Relevante | Irrelevante |
| Stop-loss | Gatilho de saída | Obrigatório em toda entrada |
| Diversificação | Ampla | Concentração com risco controlado |

---

## 1. Pré-Mercado (1h antes da abertura)

- After/pre-market: ativos em alta/baixa no pré
- Notícias overnight: fechamento asiático, europeu, futuros americanos
- Gaps esperados: identificar ativos com gap de abertura relevante
- Calendário do dia: payroll, COPOM, balanços, decisões do FED
- Definir cenário: tendência, lateralização ou alta volatilidade?
- Gerar watchlist do dia: 5–15 ativos para monitorar

---

## 2. Setup e Validação Técnica

Para cada ativo da watchlist:

### 2.1 Tendência (múltiplos timeframes)

- Direção: alta, baixa ou lateral
- Médias móveis: 9, 21, 50, 200
- VWAP: referência de equilíbrio intraday

### 2.2 Indicadores

| Indicador | Uso |
|---|---|
| RSI | Sobrecompra (> 70) / sobrevenda (< 30) |
| MACD | Cruzamentos de tendência |
| Bandas de Bollinger | Volatilidade e reversão |
| Volume profile | Regiões de liquidez / vácuo |

### 2.3 Price Action

- Suportes e resistências relevantes
- Padrões gráficos: triângulos, bandeiras, OCO, fundos/topos duplos
- Candles de reversão: pin bar, engolfo, doji
- Fluxo: book de ofertas, times & trades, agressões

---

## 3. Identificação de Setups

Cada setup deve ser claro, replicável e pré-definido:

| Setup | Descrição |
|---|---|
| Rompimento com volume | Preço ultrapassa resistência com volume acima da média |
| Pullback em tendência | Correção para suporte em tendência de alta |
| Reversão em suporte | Price action de reversão em região de suporte forte |
| VWAP bounce | Retorno ao VWAP com candle de confirmação |
| Inside bar breakout | Rompimento de barra interna |

### Critérios obrigatórios por setup

- Critério de entrada definido
- Stop-loss definido antes da entrada
- Alvo(s) de saída
- Risco/retorno mínimo: 1:2

---

## 4. Gestão de Risco

- Risco por operação: máximo 1–2% do capital
- Risco diário máximo: 3–5% (após atingir, encerrar operações do dia)
- Máximo de operações simultâneas: definido por estratégia
- Circuit breaker: 3 stops consecutivos → pausa obrigatória

### Position Sizing

```
Tamanho = (Capital × % Risco) / (Preço de entrada - Stop)
```

### Gestão de posição aberta

- Stop móvel (trailing stop): ativar após lucro de X%
- Break-even: mover stop para entrada após lucro inicial confirmado

---

## 5. Execução

- Tipo de ordem: limit, market, stop, OCO (bracket)
- Ordens bracket: entrada + stop + alvo simultâneos
- Slippage estimado: considerar em ativos de baixa liquidez
- Confirmar fills antes de atualizar posição

---

## 6. Monitoramento Ativo

Durante o pregão, para cada posição aberta:

- Stop atingido? → fechar imediatamente
- Alvo atingido? → fechar ou mover stop
- Trailing stop ativo? → atualizar
- Tese invalidada? → sair antes do stop

Para a watchlist:

- Alertas de aproximação de suporte/resistência
- Scanner de setups ativos
- Reavaliação contínua da validade do setup

---

## 7. Pós-Mercado

### Fechamento forçado (day trade)

Zerar todas as posições antes do leilão de fechamento.

### Relatório do dia

| Métrica | Descrição |
|---|---|
| Operações | Lista de trades com entrada, saída, resultado |
| Win rate | % de operações vencedoras |
| Payoff | Média ganhos / média perdas |
| Profit factor | Ganho bruto / perda bruta |
| Drawdown do dia | Máxima sequência de perdas |
| P&L líquido | Descontando corretagem, emolumentos, IR (20% day trade) |

### Análise qualitativa

- O plano foi seguido?
- Houve operações por emoção?
- Algum setup foi operado fora dos critérios?

---

## 8. Aprendizado e Ajuste

- Diário de trades: setup, motivo, resultado, print do gráfico
- Estatísticas por setup: qual tem maior win rate?
- Estatísticas por horário: quando a estratégia performa melhor?
- Estatísticas por ativo: quais ativos funcionam melhor?
- Backtesting contínuo dos setups após mudanças de parâmetros

---

## 9. Pipeline

```
[Pré-Mercado — 1h antes]
          ↓
[Coleta: notícias · gaps · futuros · calendário]
          ↓
[Geração da Watchlist]
          ↓
════════════ ABERTURA DO MERCADO ════════════
          ↓
[Loop de Monitoramento — cada X segundos]
  ├─→ [Scanner de Setups na Watchlist]
  │     └─ Validação técnica multi-timeframe
  │         └─ Cálculo Risco/Retorno
  │             └─ [Sinal de Entrada → Aprovação → Execução]
  │
  ├─→ [Monitoramento de Posições Abertas]
  │     ├─ Stop atingido?
  │     ├─ Alvo atingido?
  │     ├─ Trailing stop?
  │     └─ Tese invalidada?
  │
  └─→ [Circuit Breaker Check]
        ├─ Perda diária máxima atingida?
        ├─ 3 stops consecutivos?
        └─ Volatilidade anormal?
════════════ FECHAMENTO ════════════
          ↓
[Zerar posições — day trade]
          ↓
[Relatório do dia + Diário de trades]
          ↓
[Análise estatística + Ajuste de parâmetros]
```

---

## 10. Regras do Agente

- LLM interpreta contexto e narrativa de mercado — cálculos de indicadores, position sizing, stops e execução são código determinístico
- Latência importa: LLM valida contexto, não dispara entradas em tempo real
- Day trade: considerar WebSocket para dados tick-a-tick
- Custos operacionais impactam diretamente o resultado: corretagem, emolumentos, IR 20%
- Nunca otimizar em excesso: overfitting destrói estratégia em dados reais
- Toda estratégia começa em paper trading antes de capital real
