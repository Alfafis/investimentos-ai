---
title: Frameworks Recomendados
area: ia-financeira
---

# Frameworks Recomendados

---

## Comparativo

| Framework | Modelo de execução | Tipo de orquestração | Complexidade | Melhor para |
|---|---|---|---|---|
| **CrewAI** | Multi-agente hierárquico | Manager → Workers | Baixa–Média | MVPs, equipes de agentes com papéis fixos |
| **LangGraph** | Grafo de estados (stateful) | Nós + Arestas + Ciclos | Média–Alta | Workflows complexos, loops de feedback, controle fino |
| **AutoGen** | Conversacional multi-agente | Peer-to-peer / GroupChat | Média | Agentes que negociam entre si, código que executa |
| **Semantic Kernel** | Plugins + Planner | Hierárquico + Plugin-based | Média | Integração com ecossistema Microsoft (Azure, .NET) |

---

## Análise por Framework

### CrewAI

**Pontos fortes:**
- Abstração simples: define `Agent`, `Task`, `Crew` — curva de aprendizado baixa
- Suporte nativo a processos hierárquicos (Manager delega para Workers)
- Integração com LangChain tools e RAG

**Pontos fracos:**
- Pouco controle sobre fluxo de execução (difícil implementar loops condicionais complexos)
- Estado entre execuções precisa ser gerenciado externalmente
- Sem suporte nativo a grafos de estado

**Adequado para este projeto:** MVP da Fase 1 — um swarm por vertical com papel bem definido.

---

### LangGraph

**Pontos fortes:**
- Orquestração baseada em grafos dirigidos — controle total sobre o fluxo
- Estado persistente nativo entre nós (ideal para workflows de multi-step)
- Suporte a ciclos: agente pode revisar e iterar antes de finalizar
- Human-in-the-loop nativo — permite pausar e aguardar aprovação humana
- Compatível com LangChain e LCEL

**Pontos fracos:**
- Mais verboso para definir — curva de aprendizado maior que CrewAI
- Requer planejamento cuidadoso do grafo antes de implementar

**Adequado para este projeto:** Cenário B (Gestão de Risco Macro) — workflow de rebalanceamento é naturalmente um grafo com condicionais, loops e checkpoints.

---

### AutoGen

**Pontos fortes:**
- Agentes conversam entre si naturalmente (GroupChat)
- Suporte nativo a execução de código Python em sandbox
- Boa para agentes que precisam "negociar" uma resposta final

**Pontos fracos:**
- Conversas longas podem derivar (drift) sem guardrails explícitos
- Custo de tokens alto em GroupChats grandes
- Controle de fluxo menos determinístico que LangGraph

**Adequado para este projeto:** Agente de Síntese no Cenário A — quando Fundamentalista, Técnico e Sentimento precisam "debater" e chegar a consenso.

---

### Semantic Kernel

**Pontos fortes:**
- Integração nativa com Azure OpenAI, Microsoft Graph
- Sistema de plugins modular e reutilizável
- Bom suporte a .NET — relevante se o stack for C#/Azure

**Pontos fracos:**
- Ecossistema mais fechado (forte acoplamento com stack Microsoft)
- Comunidade menor que LangGraph/CrewAI em Python
- Planner pode ser menos previsível em cenários complexos

**Adequado para este projeto:** Não recomendado como framework principal — relevante apenas se houver integração com sistemas Microsoft existentes.

---

## Recomendação para Este Projeto

### Arquitetura híbrida: LangGraph + CrewAI

```
┌────────────────────────────────────────┐
│  ORQUESTRADOR MACRO                    │
│  LangGraph                             │
│  (grafo de estados, workflow Cenário B)│
└──────────────┬─────────────────────────┘
               │
    ┌──────────┼──────────┬──────────┐
    │          │          │          │
┌───▼──┐ ┌────▼─┐ ┌──────▼┐ ┌──────▼┐
│BOLSA │ │CRIPTO│ │IMÓVEL │ │CÂMBIO │
│CrewAI│ │CrewAI│ │CrewAI │ │CrewAI │
│Swarm │ │Swarm │ │ Swarm │ │ Swarm │
└──────┘ └──────┘ └───────┘ └───────┘
```

| Camada | Framework | Justificativa |
|---|---|---|
| Orquestrador Macro | **LangGraph** | Workflow de risco/rebalanceamento é um grafo com condicionais e loops |
| Swarms por vertical | **CrewAI** | Papéis fixos, hierarquia clara Manager→Worker, setup rápido |
| Agente de Síntese (debate) | **AutoGen GroupChat** (opcional) | Se consenso entre agentes for necessário no Cenário A |

### Modelo de LLM recomendado

| Uso | Modelo | Justificativa |
|---|---|---|
| Análise profunda (fundamentals, tese) | `claude-opus-4-7` | Raciocínio longo, menos alucinações em dados financeiros |
| Classificação, routing, síntese rápida | `claude-sonnet-4-6` | Custo-benefício para tasks de média complexidade |
| Sentiment scoring, extração simples | `claude-haiku-4-5` | Alta velocidade, baixo custo, tarefas mecânicas |

---

## Stack Completo Recomendado

```
Linguagem:        Python 3.12+
Orquestração:     LangGraph (macro) + CrewAI (swarms)
LLM:              Claude API (Anthropic) — Opus/Sonnet/Haiku por camada
RAG:              LangChain + pgvector (Supabase)
Embedding:        text-embedding-3-small (OpenAI) ou bge-m3 (local)
Observabilidade:  LangSmith (tracing) + Ragas (eval)
Dados:            TimescaleDB + PostgreSQL + Redis
Deploy:           Railway / Fly.io (MVP) → AWS ECS (produção)
```
