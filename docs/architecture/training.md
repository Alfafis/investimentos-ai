---
title: Proposta de Arquitetura de Treinamento — Agentes Financeiros
status: draft
area: ia-financeira
version: 2.0
---

# Arquitetura de Treinamento — Agentes Financeiros

> Não alimente a IA com vídeos ou livros inteiros sem critério.  
> Divida o conhecimento em camadas técnicas para os agentes.

---

## 0. Fine-Tuning vs RAG — Quando Usar Cada Um

| Técnica | Quando usar | Quando evitar |
|---|---|---|
| **RAG** | Conteúdo dinâmico, fontes atualizáveis, base grande | — |
| **Fine-Tuning** | Estilo de escrita fixo, tom consistente, persona | Conhecimento factual (congela na data do treino) |
| **System Prompt** | Personalidade, regras de comportamento, restrições | Base de conhecimento volumosa |

**Recomendação:** Use RAG para o conhecimento factual (teses, estratégias, dados). Use System Prompt para estilo e persona. Reserve Fine-Tuning apenas se RAG não capturar o tom adequado após testes.

---

## 1. Divisão por Especialidade

Distribua o conhecimento de cada fonte para o agente correto no fluxo:

| Agente | Fonte de Conhecimento | Domínio |
|---|---|---|
| Macro (Câmbio e Cenários) | BCB, FMI, relatórios Focus, InfoMoney | Câmbio, política fiscal, juros |
| Finanças Pessoais & Renda Fixa | Nathalia Arcuri — metodologia Me Poupe! | Orçamento, renda fixa, dívidas |
| Bolsa e Alocação | Primo Rico — regras de fundos e ações | Dividendos, alocação, FIIs |
| Imobiliário e Custo de Vida | Primo Pobre — visão realista de consumo | Imóveis, juros, financiamento |

> ⚠️ **Paulo Guedes removido como fonte macro.** Conteúdo datado (2019–2022) e politicamente carregado. Substituído por fontes institucionais neutras (BCB, FMI, Focus).

---

## 2. Pipeline de Ingestão de Dados

```
Fonte bruta → Extração → Chunking → Embedding → Vector DB → Agente
```

### 2.1 Fontes Legais (sem risco de copyright)

| Tipo | Fonte | Método de extração |
|---|---|---|
| Podcasts/vídeos públicos | YouTube (canais oficiais) | Whisper API — transcrição automática |
| Artigos públicos | InfoMoney, Valor Econômico | Scraping de HTML público |
| Relatórios oficiais | BCB, CVM, FMI | Download PDF direto |
| Newsletters públicas | Portais próprios dos criadores | RSS / scraping |

> ⚠️ **Scraping de livros publicados viola copyright.** Não use PDFs de *Me Poupe!*, *Do Mil ao Milhão* ou similares.

### 2.2 Estratégia de Chunking

- **Tamanho:** 400–600 tokens por chunk
- **Overlap:** 50–80 tokens entre chunks adjacentes
- **Metadados obrigatórios:** `fonte`, `autor`, `data`, `dominio`, `url`

### 2.3 Embedding e Vector DB

| Componente | Opção recomendada | Alternativa |
|---|---|---|
| Modelo de embedding | `text-embedding-3-small` (OpenAI) | `bge-m3` (local, multilíngue) |
| Vector DB | Supabase pgvector (já no stack) | Pinecone, Weaviate |
| Refresh | Semanal para artigos; mensal para podcasts | — |

---

## 3. Engenharia de Prompt (System Prompts)

Use transcrições textuais dos autores para extrair estilo. Defina no System Prompt de cada agente:

### Estilo Primo Pobre
- Linguagem simples, metáforas do dia a dia
- Foco em evitar taxas abusivas e juros de financiamento
- Tom: "cidadão comum tentando não se ferrar"

### Estilo Primo Rico
- Foco em consistência e aportes mensais
- Conceitos de *skin in the game*
- Ênfase em dividendos e longo prazo
- Tom: disciplina > oportunismo

### Estilo Macro/Institucional
- Neutro, baseado em dados
- Citar fontes (BCB, FMI, relatório Focus)
- Sem opinião política

---

## 4. Orquestração entre Agentes

Sem um **agente roteador**, o sistema não sabe qual especialista chamar. Arquitetura mínima:

```
Usuário → [Router Agent] → [Agente Especializado] → Resposta
                ↓
         Classifica intenção:
         - macro / câmbio
         - renda fixa / orçamento
         - bolsa / FII
         - imóvel / custo de vida
```

### Regras de conflito entre agentes

Primo Rico e Primo Pobre têm filosofias opostas em tópicos como financiamento imobiliário e perfil de consumo. Quando ativados para a mesma query:

1. Apresentar **ambas as perspectivas** explicitamente
2. Indicar qual se aplica ao perfil do usuário (agressivo vs conservador)
3. Nunca sintetizar em resposta única sem deixar claro a origem

---

## 5. Avaliação e Métricas

Sem eval, o sistema não melhora. Implemente antes de ir para produção:

### 5.1 Dataset de Avaliação
- Mínimo 50 pares pergunta/resposta esperada por domínio
- Cobrir: perguntas factuais, perguntas de estilo, casos de conflito entre agentes

### 5.2 Métricas RAG

| Métrica | O que mede | Ferramenta |
|---|---|---|
| **Faithfulness** | Resposta baseada no contexto recuperado? | Ragas |
| **Answer Relevance** | Resposta responde a pergunta? | Ragas |
| **Context Recall** | Chunks certos foram recuperados? | Ragas / LangSmith |
| **MRR** | Chunk mais relevante está no topo? | Manual / custom |

### 5.3 Ferramentas sugeridas
- [Ragas](https://docs.ragas.io) — eval de RAG pipelines
- [LangSmith](https://smith.langchain.com) — tracing e eval end-to-end
- Planilha manual para bootstrap inicial (barato, suficiente para v1)

---

## Roadmap Sugerido

```
Fase 1 — MVP
  ├── 1 agente (Renda Fixa / Primo Pobre)
  ├── Fonte: YouTube transcripts via Whisper
  ├── RAG com pgvector
  └── System Prompt com estilo definido

Fase 2 — Expansão
  ├── Adicionar agentes: Bolsa, Macro
  ├── Router básico (classificação por intenção)
  └── Eval com Ragas (50 queries)

Fase 3 — Produção
  ├── Pipeline de refresh automático
  ├── Tratamento de conflitos entre agentes
  └── Dashboard de métricas (LangSmith)
```
