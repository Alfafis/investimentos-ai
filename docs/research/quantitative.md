---
title: Metodologias de IA e Quantitativas para Mercado Financeiro
area: ia-financeira
fontes: out.pdf, 694-artigo.pdf, admin-CoVaR.pdf, ElisangelaLopesDeFaria.pdf
---

# Metodologias de IA e Quantitativas para Mercado Financeiro

Métodos extraídos de pesquisas acadêmicas aplicadas ao mercado financeiro brasileiro e internacional. Complementa `metodologias.md` (análise clássica) com técnicas de machine learning, redes neurais e medidas de risco quantitativas.

---

## 1. Teorias de Eficiência de Mercado

Base teórica que todo modelo preditivo precisa considerar antes de implementar.

### Teoria de Dow (1890–1902)
- Premissa: preços tendem a agir em concerto; tendências se repetem
- Três movimentos de preço:
  - **Tendência primária** (mercado Touro/Urso) — dura meses a anos
  - **Reação secundária** — correções da tendência primária
  - **Flutuações diárias** — ruído de curto prazo, baixo valor preditivo
- As médias refletem toda informação conhecida pelo mercado

### Teoria do Passeio Aleatório — Fama (1965)
- Mudanças de preço sucessivas são **independentes** (sem memória)
- O passado não pode ser usado para prever o futuro de forma significativa
- Contraposição direta à Análise Técnica

### Hipótese de Eficiência dos Mercados — HEM, Fama (1970)
Preço atual reflete **integralmente** toda informação disponível. Três formas:

| Forma | O que os preços incorporam |
|---|---|
| Fraca | Histórico de preços e volume |
| Semiforte | Toda informação pública disponível (balanços, notícias) |
| Forte | Toda informação, inclusive privilegiada (insider) |

**Implicação prática:** Se o mercado for eficiente na forma forte, nenhuma análise gera alpha consistente. Na prática, há evidências de que o mercado é semi-forte com desfasagens — janela de oportunidade para estratégias quantitativas.

---

## 2. Medidas de Risco Quantitativas

### VaR — Value at Risk

**Definição:** Perda máxima esperada de um portfólio em um período T com nível de confiança (1 − α).

```
VaR_α(X) = −inf{x | F(x) > α}
```

Onde α é o nível de confiança (tipicamente 1%, 5% ou 10%) e F(x) = Pr(X ≤ x).

**Interpretação:** VaR de 5% = "há 5% de probabilidade de perda exceder esse valor em um dia."

**Limitações:**
- Medida individual — não captura dependências entre ativos
- Não conta spillover effects (contágio entre ativos)
- Pressupõe distribuição normal; mercados têm caudas pesadas (leptocúrtica)

**Variações:**
- **CVaR (Conditional VaR):** média das perdas além do VaR — mais robusto para caudas
- **CAViaR (Conditional Autoregressive VaR):** modela VaR como série temporal

---

### CoVaR — Conditional Value at Risk Sistêmico

**Fonte:** Adrian & Brunnermeier (2011). Método para medir risco sistêmico e efeito contágio.

**Definição:** VaR do ativo j condicionado a um evento C(Xᵢ) no ativo i:

```
Pr[Xʲ ≤ CoVaR^(j|C(Xᵢ))_q | C(Xᵢ)] = q
```

**ΔCoVaR — Contribuição Marginal ao Risco Sistêmico:**
```
ΔCoVaR^(j|i) = CoVaR^(j|Xᵢ=VaR_q(i)) − CoVaR^(j|Xᵢ=mediana)
```

Mede o quanto o risco de j aumenta quando i está em distress, em relação ao cenário normal (mediana).

**Estimação por Regressão Quantílica (Koenker & Bassett, 1978):**
- Mais robusto que MQO frente a outliers
- Não exige distribuição normal dos resíduos
- Fornece estimativas em qualquer quantil (não só na média)

**Três usos do CoVaR:**

| Métrica | O que mede |
|---|---|
| CoVaR | Risco do sistema dado distress no ativo i |
| ΔCoVaR | Contribuição marginal do ativo i ao risco sistêmico |
| Matriz de Contágio | Inter-relações de spillover entre todos os ativos (K×K) |

**Stress Test com CoVaR:**
- Simular distress no Ibovespa → medir spillover sobre ações individuais
- Resultado pesquisa BR: distress no **Dow Jones** tem maior spillover sobre o Ibovespa (ΔCoVaR = −2,14) do que distress no Ibovespa sobre o Dow Jones (−1,27) — assimetria esperada de mercado emergente: absorve mais choque externo do que exporta
- Identificação setorial: papéis que mais "contaminam" vs. mais "contaminados"

**Aplicação nos agentes:**
- Agente de Risco usa ΔCoVaR para identificar posições que mais amplificam risco sistêmico da carteira
- Stress test do workflow B reproduz esse método: simular colapso em um ativo e medir propagação

---

## 3. Índice de Hurst — Memória de Longo Prazo

**Origem:** Harold Edwin Hurst (1951) — hidrólogo que estudou séries do rio Nilo.

**Estatística R/S (Rescaled Range) — estimação por regressão OLS:**

O método correto não usa uma única janela — calcula R/S para múltiplos tamanhos de janela n e estima H como o coeficiente angular da regressão:

```
Para cada janela n ∈ {n₁, n₂, ..., nₖ}:
  R(n) = max(cumulativo) − min(cumulativo) da série
  S(n) = desvio padrão da série na janela
  calcule R(n)/S(n)

H = slope de OLS: log(R/S) ~ β₀ + H × log(n)
```

Onde R é o range dos desvios cumulativos e S é o desvio padrão, ambos calculados sobre cada janela de tamanho n.

**Interpretação:**

| Valor de H | Interpretação |
|---|---|
| H = 0.5 | Série aleatória (passeio aleatório puro) |
| H > 0.5 | Série persistente — tendências se sustentam (memória de longo prazo) |
| H < 0.5 | Série anti-persistente — reversão à média dominante |

**Aplicação prática:**
- H próximo de 1 em certas janelas de preço → tendência forte; indicadores de seguimento de tendência funcionam melhor
- H próximo de 0.5 → mercado aleatório; indicadores de reversão à média funcionam melhor
- Pesquisa (Panosso, SOM): Índice de Hurst foi a variável mais discriminante para identificar períodos de crise vs. estabilidade no Dow Jones

**Como calcular no sistema (método DFA — Detrended Fluctuation Analysis):**

Alternativa ao R/S clássico; mais robusta para séries não-estacionárias. Calcula H como slope da variância de incrementos em múltiplas escalas:

```python
def hurst_exponent(series, max_lag=20):
    lags = range(2, max_lag)
    # desvio padrão dos incrementos em escala lag
    tau = [np.std(np.subtract(series[lag:], series[:-lag])) for lag in lags]
    poly = np.polyfit(np.log(lags), np.log(tau), 1)
    return poly[0]  # H = slope da regressão log-log
```

> **Nota:** este código usa variância de incrementos (DFA), não R/S clássico. Os dois métodos estimam H, mas podem divergir em séries curtas. Use DFA para séries com tendências; R/S para séries estacionárias.

---

## 4. Self-Organizing Maps (SOM) para Segmentação de Mercado

**Referência:** Kohonen (1982). Aplicação financeira: Panosso (dissertação, Universidade Nova de Lisboa).

**O que é:** Rede neural não supervisionada que reduz dados multidimensionais para um mapa 2D preservando topologia. Ativos similares são mapeados para neurônios próximos.

**Arquitetura:**
- Camada de entrada: vetor de indicadores técnicos (sem camadas ocultas)
- Camada de saída: grade 2D de neurônios (tamanho definido pelo usuário)
- **BMU (Best Matching Unit):** neurônio mais próximo ao vetor de entrada (distância Euclidiana)

**Algoritmo de treino:**
1. Inicializar pesos aleatoriamente
2. Para cada amostra: encontrar BMU
3. Atualizar BMU e vizinhos: `w(t+1) = w(t) + η(t) × h(t) × (x − w(t))`
   - η(t) = taxa de aprendizado decrescente
   - h(t) = função de vizinhança (Gaussiana ou chapéu mexicano)
4. Reduzir raio de vizinhança e η ao longo do treinamento

**Visualização com U-Matrix:**
- UMAT (Unified Distance Matrix): distância média entre neurônio e seus vizinhos
- Regiões claras no UMAT = clusters distintos
- Regiões escuras = fronteiras entre clusters

**Resultados da pesquisa (Dow Jones 2001–2011):**
- SOM com indicadores técnicos + Índice de Hurst identificou corretamente períodos de alta, baixa e crise
- Volume médio foi o indicador mais significativo para distinguir reversões de tendência
- Estratégia baseada em clusters SOM superou buy-and-hold nos períodos testados

**Uso no sistema:**
- Pré-processar série OHLCV + indicadores técnicos calculados
- Treinar SOM offline (semanal/mensal)
- Classificar período atual no mapa → determinar regime (alta/baixa/lateral/crise)
- Alimentar Agente Síntese com o regime identificado como contexto

---

## 5. Redes Neurais Profundas para Previsão de Mercado

### MLP — Multilayer Perceptron

**Treinamento por Backpropagation (Rumelhart et al., 1986):**

**Forward pass:**
```
z^(l)_j = Σᵢ w^(l)_ji × y^(l-1)_i + b_j      (soma ponderada + bias)
y^(l)_j = f(z_j)                                 (função de ativação)
```

**Função de erro:**
```
E = (1/N) × Σ (1/2) × Σ_j e²_j
```
onde e_j = d_j − o_j (erro no neurônio j de saída)

**Backward pass (regra delta generalizada):**
```
Δw_ji(n+1) = w_ji(n) + α × Δw_ji(n−1) + η(n) × δ_j × y_i(n)
```

**Funções de ativação:**

| Função | Fórmula | Uso |
|---|---|---|
| Sigmoide | f(z) = 1/(1 + e⁻ᶻ) | Saída binária |
| Tanh | f(z) = tanh(z) | Camadas internas (legado) |
| ReLU | f(z) = max(0, z) | Camadas profundas (padrão atual) |

**ReLU é preferida:** converge 6× mais rápido que tanh (Krizhevsky et al., 2012); menos suscetível ao problema do gradiente evanescente.

---

### CNN — Convolutional Neural Network para Texto Financeiro

**Referência:** Faria (tese COPPE/UFRJ, 2018). Ibovespa + notícias financeiras em PT-BR.

**Arquitetura CNN para NLP:**
1. **Embedding layer:** converte palavras em vetores densos (via Word2Vec)
2. **Camadas convolucionais:** aplicam filtros sobre janelas de palavras
   - Filtro k×d onde k = tamanho da janela (2, 3, 4 palavras) e d = dimensão do embedding
   - Captura padrões locais (bigramas, trigramas financeiros)
3. **Max pooling:** seleciona a feature mais relevante por filtro (invariância à posição)
4. **Dropout:** desativa neurônios aleatoriamente durante treino (previne overfitting)
5. **Camada totalmente conectada:** combina features extraídas

**Dropout:**
- Taxa p (tipicamente 0.3–0.5) → neurônio desativado com probabilidade p
- Durante inferência: multiplica pesos por (1−p)
- Equivale a ensemble de sub-redes

---

### ELM — Extreme Learning Machine

**Característica principal:** pesos da camada oculta são inicializados **aleatoriamente** e **não são atualizados**. Apenas os pesos de saída são treinados (via pseudo-inversa).

**Treinamento:**
```
H × β = T
β = H⁺ × T   (onde H⁺ é a pseudo-inversa de Moore-Penrose)
```

Onde H é a matriz de saída da camada oculta, β são os pesos de saída, T são os alvos.

**Vantagens sobre backpropagation:**
- Treinamento em milissegundos (uma única passagem)
- Sem hiperparâmetros de taxa de aprendizado
- Sem convergência local

**Desvantagem:** requer mais neurônios que MLP para mesma capacidade.

**Uso no modelo híbrido (I-CNNELM):**
- CNN extrai representações de features de notícias (mapa de características)
- ELM recebe as features da CNN e classifica (sobe/desce/neutro)
- Resultado: acurácia de 60.2% no Ibovespa — superior ao buy-and-hold

---

## 6. Processamento de Linguagem Natural (NLP) para Sentimento Financeiro

### Word2Vec — Representação Distribuída de Palavras

**Referência:** Mikolov et al. (2013).

**Dois modelos:**
- **CBOW:** prevê palavra central dado contexto
- **Skip-gram:** prevê contexto dado palavra central ← mais eficaz para vocabulário financeiro

**Skip-gram com Negative Sampling:**

Objetivo: maximizar probabilidade de contexto real e minimizar para palavras negativas (amostradas aleatoriamente):
```
L = log σ(v'_wo · v_wi) + Σₖ Eₗ[log σ(−v'_wₗ · v_wi)]
```

**Softmax Hierárquico:** alternativa ao negative sampling; usa árvore binária de Huffman para reduzir custo de O(V) para O(log V).

**Pipeline para notícias financeiras em PT-BR:**
1. **Tokenização:** separar palavras, remover stopwords (de, e, o, a...)
2. **Detecção de n-gramas:** identificar frases compostas via métricas de associação estatística
   - **Bigrama PMI:**
     ```
     PMI(w1, w2) = log[P(w1,w2) / (P(w1) × P(w2))]
     ```
   - **Trigrama PMI:**
     ```
     PMI(w1, w2, w3) = log[P(w1,w2,w3) / (P(w1) × P(w2) × P(w3))]
     ```
   - **7 métricas testadas por Faria (2018):** Mi, Mi-like, PMI, PMI², PMI³, DICE, DICE2
   - **Melhor resultado:** **trigramas com Mi-like** (janela ω=100) — superou bigramas e as demais métricas para corpus financeiro PT-BR
3. **Treino Word2Vec:** janela de contexto 5, dimensão 100–300
4. **Sentence Embedding:** média dos vetores de palavras da notícia
5. **TF-IDF como feature complementar:** pondera relevância de termos por documento

**Exemplo de trigramas financeiros detectados:**
- "taxa_selic_meta", "ibovespa_fechou_alta", "banco_central_brasil", "petrobras_resultado_trimestral"

**Resultado (Faria, 2018):**
- Modelo treinado em notícias do InfoMoney + outros portais BR (2012–2013)
- 60.2% de acurácia na previsão diária da direção do Ibovespa
- Estratégia de negociação com minicontrato WIN superou buy-and-hold

---

## 7. Perfil do Investidor e Finanças Comportamentais

**Referência:** Paiva et al. (2020) — "O perfil do investidor individual no mercado financeiro"

### Classificação de Perfil por Suitability

| Perfil | Característica | Alocação típica |
|---|---|---|
| Conservador | Preservação de capital; baixa tolerância a risco | Renda fixa > 80% |
| Moderado | Equilíbrio retorno/risco; aceita oscilação moderada | Mix 50/50 |
| Agressivo (Arrojado) | Maximização de retorno; alta tolerância a risco | Renda variável > 70% |

**Resultado do estudo (60 investidores BR):** maioria conservador — busca preservação com menor rentabilidade e maior segurança.

### Erros Cognitivos (Finanças Comportamentais)
Influenciam decisões mesmo em investidores experientes:

| Viés | Descrição | Impacto |
|---|---|---|
| Excesso de confiança | Superestima o próprio conhecimento | Opera em excesso, ignora stop-loss |
| Aversão à perda | Perda dói 2× mais que ganho equivalente (Kahneman-Tversky) | Carrega posições perdedoras, realiza ganhos cedo |
| Ancoragem | Ancora em preço de compra como referência | Não realiza perda mesmo com fundamento mudado |
| Efeito manada | Segue o comportamento da maioria | Compra no topo de narrativas |
| Disponibilidade | Superpondera eventos recentes | Após crash, subestima probabilidade de alta |

### Métricas para Classificação Automatizada do Perfil
Para implementar suitability no sistema:
- **Alfa de Cronbach:** consistência interna do questionário de perfil (> 0.7 = confiável)
- **Análise Discriminante Multivariada:** classifica investidores em grupos com base em variáveis (prazo, tolerância a perda, experiência, renda)
- Minimizar variância intra-grupo e maximizar inter-grupo

---

## 8. Estratégia de Negociação com ML

### Estrutura geral (Faria, 2018)

```
Notícias do dia D → Extração de Features (Word2Vec + CNN) 
→ Classificação ELM (sobe/desce) 
→ Regra de negociação para dia D+1:
   - Classificação "sobe" → comprar minicontrato WIN na abertura
   - Classificação "desce" → vender (short) minicontrato WIN na abertura
   - Manter posição até fechamento (day trade)
```

**Minicontrato do Ibovespa (WIN):**
- 1 ponto = R$0,20
- Menor barreira de entrada que contrato cheio (WDO)
- Vencimento a cada 2 meses (código: WINM, WINQ, WINV, WINZ)

### Métricas de avaliação do modelo preditivo

| Métrica | Fórmula | Uso |
|---|---|---|
| Acurácia | (VP + VN) / Total | Avaliação geral |
| Precisão | VP / (VP + FP) | Qualidade dos positivos classificados |
| Recall | VP / (VP + FN) | Cobertura dos positivos reais |
| F1-Score | 2 × (P × R) / (P + R) | Balanço precisão/recall |

**Matriz de Confusão (binária: sobe/desce):**
```
           Previsto: Sobe   Previsto: Desce
Real: Sobe    VP (acerto)     FN (erro)
Real: Desce   FP (erro)       VN (acerto)
```

**Benchmark obrigatório:** comparar sempre com estratégia buy-and-hold e com modelo random (50% de acurácia esperada para binário balanceado).

**Resultados da pesquisa (Faria, 2018 — 32 pregões, minicontrato WIN):**

| Configuração ótima | Valor |
|---|---|
| Métrica n-grama | Mi-like, trigramas, ω=100 |
| Dimensão Word2Vec (d) | 300 |
| Filtros CNN | 96 filtros de tamanho 3 |
| Neurônios ELM | 67 |
| Acurácia | 60,22% |
| Resultado financeiro I-CNNELM | +1.645 pontos = **R$329** |
| Resultado buy-and-hold | +150 pontos = **R$30** |

> Benchmark concreto: qualquer implementação deve superar R$30 em 32 pregões e 50% de acurácia para ser considerada não-trivial.

---

## 9. Pipeline de Dados para Implementação

### Séries temporais financeiras (dados numéricos)

```
Fonte (B3/CVM/Yahoo Finance)
  → OHLCV diário (Open, High, Low, Close, Volume)
  → Calcular indicadores técnicos: RSI, MACD, EMA, Bollinger, OBV
  → Calcular Índice de Hurst (janelas 20, 50, 200 dias)
  → Normalizar (Z-score ou Min-Max por janela deslizante)
  → Input para SOM (segmentação de regime) ou MLP/CNN
```

### Dados textuais (notícias e sentimento)

```
Fonte (InfoMoney, Valor, Reuters BR)
  → Coleta via RSS/scraping
  → Pré-processamento: tokenização, remoção stopwords, stemming
  → Detecção de bigramas/trigramas via PMI
  → Embedding via Word2Vec (pré-treinado em corpus financeiro PT)
  → Sentence embedding (média dos vetores)
  → Classificação CNN+ELM → score sentimento [-1, 1]
```

### Integração no sistema multi-agente

| Dado | Agente consumidor | Skill |
|---|---|---|
| Regime SOM (cluster) | Agente Síntese | `rag_retriever` + contexto de regime |
| Score sentimento | Agente de Sentimento e Notícias | `news_sentiment_analysis` |
| VaR / ΔCoVaR | Agente de Risco | `risk_calculator` |
| Hurst > 0.5 | Analista Técnico | `technical_pattern_detector` |
| Perfil do investidor | Router | Ajuste de pesos na síntese |

---

## Referências dos PDFs

| Documento | Autores | Contribuição |
|---|---|---|
| `out.pdf` | Gisele Cristina Panosso (Universidade Nova de Lisboa) | SOM + AT + Índice de Hurst |
| `694-artigo.pdf` | Paiva et al. (IF Sudeste MG) | Perfil do investidor + análise discriminante |
| `admin-CoVaR.pdf` | Almeida, Frascaroli, Cunha (UFPB) | VaR, CoVaR, matriz de contágio |
| `ElisangelaLopesDeFaria.pdf` | Elisangela Lopes de Faria (COPPE/UFRJ) | CNN + ELM + Word2Vec para Ibovespa |