---
title: Fluxos de Trabalho e Orquestração
area: ia-financeira
---

# Fluxos de Trabalho e Orquestração

---

## Cenário A — Identificação de Oportunidade (Geração de Alpha)

> Trigger: usuário faz query de análise OU sistema detecta sinal em monitoramento contínuo.

```
┌─────────────────────────────────────────────────────────────────┐
│  TRIGGER: "Analise PETR4" / Sinal automático de RSI < 30       │
└────────────────────────┬────────────────────────────────────────┘
                         │
              ┌──────────▼──────────┐
              │  ROUTER / PLANNER   │
              │  Identifica vertical│
              │  Delega ao swarm    │
              └──────────┬──────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
┌────────▼──────┐ ┌──────▼──────┐ ┌─────▼───────┐
│  Fundamenta-  │ │  Técnico    │ │  Sentimento  │
│  lista        │ │             │ │  & Notícias  │
│               │ │             │ │              │
│ parse_qtrly   │ │ tech_patt   │ │ news_senti   │
│ dcf_valuation │ │ _detector   │ │ _analysis    │
│ peer_compare  │ │             │ │ rag_retriever│
└───────┬───────┘ └──────┬──────┘ └──────┬───────┘
        │                │               │
        └────────────────▼───────────────┘
                         │
              ┌──────────▼──────────┐
              │   AGENTE SÍNTESE    │
              │                     │
              │  Consolida sinais:  │
              │  - Fundamentals OK? │
              │  - Técnico: entrada?│
              │  - Sentimento: +/-? │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  GERADOR DE TESE    │
              │                     │
              │  Output estruturado:│
              │  - Recomendação     │
              │  - Preço-alvo       │
              │  - Stop-loss        │
              │  - Prazo e risco    │
              │  - Fontes citadas   │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  alert_dispatcher   │
              │  report_generator   │
              └─────────────────────┘
```

### Passo a Passo

1. **Trigger** — query do usuário ou sinal de monitoramento (preço, indicador, evento)
2. **Router** — classifica vertical e intencão (análise completa / sinal pontual / comparação)
3. **Swarm paralelo** — Fundamentalista + Técnico + Sentimento executam em paralelo
4. **RAG enrichment** — cada agente consulta vector DB do seu namespace antes de responder
5. **Síntese** — agente consolidador pondera os 3 sinais (peso configurável por perfil de risco)
6. **Tese de investimento** — output estruturado com recomendação, preço-alvo e stop
7. **Dispatch** — entrega via relatório, alerta ou interface

---

## Cenário B — Gestão de Risco Macro e Rebalanceamento

> Trigger: evento macro relevante (mudança de Selic, CPI acima do esperado, crise cambial) OU revisão periódica de carteira (semanal/mensal).

```
┌─────────────────────────────────────────────────────────────────┐
│  TRIGGER: Evento macro / Revisão periódica de carteira          │
└────────────────────────┬────────────────────────────────────────┘
                         │
              ┌──────────▼──────────┐
              │  ORQUESTRADOR MACRO │
              │                     │
              │  1. Carrega snapshot │
              │     de carteira      │
              │  2. Aciona todos os  │
              │     swarms           │
              └──────────┬──────────┘
                         │
     ┌──────────┬─────────┴──────────┬──────────┐
     │          │                    │          │
┌────▼───┐ ┌───▼────┐ ┌────────┐ ┌──▼─────┐
│ BOLSA  │ │ CRIPTO │ │ IMÓVEL │ │ CÂMBIO │
│ Swarm  │ │ Swarm  │ │ Swarm  │ │ Swarm  │
│        │ │        │ │        │ │        │
│ Reavalia│ │Reavalia│ │Reavalia│ │Reavalia│
│ posições│ │posições│ │posições│ │exposição│
└────┬───┘ └───┬────┘ └───┬────┘ └───┬────┘
     │         │          │          │
     └─────────┴──────────┴──────────┘
                         │
              ┌──────────▼──────────┐
              │  AGENTE DE RISCO    │
              │                     │
              │  - VaR consolidado  │
              │  - Correlações cross│
              │    -vertical        │
              │  - Concentração por │
              │    ativo/setor      │
              │  - Stress test      │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  AGENTE DE          │
              │  REBALANCEAMENTO    │
              │                     │
              │  Compara:           │
              │  - Alocação atual   │
              │  - Alocação alvo    │
              │                     │
              │  Gera:              │
              │  - Lista de ordens  │
              │  - Prioridade       │
              │  - Impacto fiscal   │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  OUTPUT             │
              │  - Relatório macro  │
              │  - Ordens sugeridas │
              │  - Alertas de risco │
              └─────────────────────┘
```

### Passo a Passo

1. **Trigger** — evento externo (webhook de notícia classificada como "alto impacto") ou cron job
2. **Orquestrador** — carrega estado atual da carteira e aciona os 4 swarms em paralelo
3. **Reavaliação por vertical** — cada swarm reavalia suas posições no novo contexto macro
4. **Agente de Risco** — consolida exposições cross-vertical, calcula VaR, detecta concentração
5. **Stress test** — simula cenários adversos (ex: alta de 200bps na Selic, BTC -50%, USD/BRL +10%)
6. **Rebalanceamento** — calcula delta entre alocação atual e alvo; gera lista de ordens priorizadas
7. **Impacto fiscal** — avalia ganho de capital realizado, prazo de custódia e isenções (ações < R$20k)
8. **Output** — relatório executivo + ordens sugeridas + alertas críticos disparados
