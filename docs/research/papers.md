# Resumos Completos — 4 PDFs Acadêmicos

Conteúdo integral dos quatro artigos/teses lidos, incluindo introdução, revisão de literatura, metodologia, dados, resultados, conclusões e referências-chave.

---

## PDF 1 — Análise do Mercado Financeiro com Self-Organizing Maps

**Título:** Análise do Mercado Financeiro baseada em Análise Técnica com Self-Organizing Maps  
**Subtítulo:** SOM: Uma abordagem para análise do mercado financeiro — os sinais de crise  
**Autora:** Gisele Cristina Panosso  
**Instituição:** Instituto Superior de Estatística e Gestão de Informação, Universidade Nova de Lisboa  
**Tipo:** Dissertação de Mestrado em Estatística e Gestão de Informação (Business Intelligence)  
**Orientador:** Prof. Fernando Bação | Coorientador: Prof. Nuno Cavalheiro Marques  
**Índice utilizado:** Dow Jones Industrial Average (DJI), 2001–2011

---

### 1.1 Introdução

O mercado de ações representa alternativa de alto risco/retorno. As principais abordagens são **Análise Técnica** (histórico de preços, tendências) e **Análise Fundamental** (balanços, setores, gestão). A pesquisa emprega indicadores da Análise Técnica combinados com Mapas Auto-Organizáveis (SOM) para segmentação e identificação de padrões nos movimentos de preços.

**Objetivos:**
- Experimentar combinação de indicadores técnicos com SOM para identificar padrões
- Determinar quais variáveis melhor descrevem movimentos de preços e sinalizam crises
- Identificar intervalos ótimos (curto/médio/longo prazo) para cada variável
- Eliminar variáveis com alta correlação
- Validar os resultados simulando investimentos

**Relevância:** Identificar indicadores que sinalizem estabilidade ou crise financeira pode evitar grandes perdas e construir ferramentas de apoio à decisão.

---

### 1.2 Revisão da Literatura

#### Teorias Econômicas

**Teoria de Dow (Charles Henry Dow, 1889–1902)**
- Publicada por Hamilton em "The Stock Market Barometer"
- As médias refletem toda informação financeira relevante
- Três movimentos: **tendência primária** (mercado Touro/Urso, < 1 ano a vários anos), **reação secundária** (correção), **flutuações diárias** (baixo poder preditivo)
- Análise Técnica foca no preço; Análise Fundamental foca em resultados financeiros corporativos

**Teoria dos Passeios Aleatórios (Fama, 1965)**
- Mudanças sucessivas de preço são independentes (série sem memória)
- Passado não prevê futuro de forma significativa

**Hipótese de Eficiência dos Mercados — HEM (Fama, 1970)**
- Preço atual reflete integralmente toda informação disponível
- Três formas: **fraca** (incorpora histórico de preços), **semiforte** (incorpora toda informação pública), **forte** (incorpora até informações privilegiadas)
- Basu (1977): comportamento de preços não é completamente descrito pela HEM; há defasagens no ajuste
- Crítica: mercados instáveis acompanham instabilidade das informações

**Análise Técnica — conceitos relevantes**
- **Preço + Volume:** a combinação revela informação sobre a força dos movimentos (Blume, Easley & O'Hara, 1994)
- **Médias Móveis:** média de 52 semanas rastreia nível médio; quando preço rompe média por baixo = sinal de alta; por cima = sinal de venda
- **Índice de Hurst:** memória de longo prazo em séries temporais (ver seção 1.4)

#### Self-Organizing Maps (SOM)

Proposto por Kohonen (1982). Rede neural não supervisionada com duas camadas (entrada + saída bidimensional). Utiliza aprendizagem competitiva: cada vetor de entrada ativa um neurônio vencedor (Best Matching Unit — BMU) e seus vizinhos têm seus pesos ajustados.

**Propriedades:**
- Reduz dados multidimensionais para mapas 2D preservando topologia
- Semelhantes no espaço de entrada → unidades próximas no mapa
- Sem camada oculta; número de neurônios na saída definido pelo usuário
- Ferramenta: GeoSOM Suite (segmentação visual)

**Trabalhos relacionados identificados:**
- Vários aplicam SOM a dados de séries financeiras, análise de crédito e segmentação de risco

---

### 1.3 Metodologia

**Classificação:** Pesquisa quantitativa, exploratória/descritiva  
**Fonte de dados:** Yahoo Finance — cotações diárias do Dow Jones Industrial Average  
**Períodos analisados:** 2001–2011 (completo) e subperíodo 2002–2007 (pré-crise)

**Variáveis calculadas (Tabela 3.1):**

| Variável | Descrição |
|---|---|
| Var. Preço | Variação percentual do preço de fechamento |
| SMA_x | Simple Moving Average — períodos curto/médio/longo |
| EMA_x | Exponential Moving Average |
| RSI_x | Relative Strength Index |
| Volume | Volume negociado diário |
| MACD | Moving Average Convergence Divergence |
| Bollinger Bands | Canais de volatilidade |
| Hurst | Índice de Hurst (médio e longo prazo) |
| ATR | Average True Range |
| OBV | On-Balance Volume |

**Redução de Variáveis:**
- Cálculo do Índice de Hurst para cada variável para identificar presença de memória
- Análise de correlação (árvore de clusters) para eliminar redundâncias
- Resultado: subconjunto de variáveis mais expressivas selecionado

**Tamanho do Mapa:**
- Fórmula: `N_neurônios = 5 × √(n_amostras)`
- Testados vários tamanhos; escolha baseada em gráfico Erros × Número de neurônios (elbow method)

**Topologia:** hexagonal (permite vizinhança mais natural que retangular)

**Normalização:** variáveis normalizadas para evitar dominância de escala

**Análise de Subconjuntos:** dois subperíodos — 2001–2011 (inclui crise 2008) e 2002–2007 (bull market)

**Ferramenta:** GeoSOM Suite (segmentação visual com U-Matrix e Component Planes)

---

### 1.4 Índice de Hurst — Metodologia de Cálculo (Apêndice)

**Harold Edwin Hurst (1951):** hidrólogo inglês, estudou cheias do rio Nilo. Desenvolveu estatística "Rescaled Range" (R/S).  
**Mandelbrot & Wallis (1969):** classificaram R/S como robusta para testar memória em séries não-cíclicas.  
**Mandelbrot (1971):** confirmou presença de memória em ativos financeiros.

**Algoritmo R/S:**

Para uma série `X_t` de comprimento `n`:
1. Calcular média: `m = (1/n) Σ X_t`
2. Série centrada: `Y_t = X_t − m`
3. Série acumulada: `Z_t = Σ(i=1..t) Y_i`
4. Range: `R(n) = max(Z_t) − min(Z_t)`
5. Desvio padrão: `S(n) = std(X_t)`
6. Estatística R/S: `(R/S)(n) = R(n)/S(n)`
7. Regredir `log(R/S)` em `log(n)` → inclinação = **H (expoente de Hurst)**

**Interpretação:**
- `H > 0.5`: série persistente (tendências se mantêm — memória positiva)
- `H = 0.5`: passeio aleatório puro (Brownian motion)
- `H < 0.5`: série antipersistente (reversão à média frequente)

**Implementação:** Package Oracle SQL utilizado para cálculo das variáveis

---

### 1.5 Resultados e Discussão

**Redução de Variáveis (Índice de Hurst Médio e Longo Prazo):**
- Análise por árvore de clusters revelou grupos de variáveis altamente correlacionadas
- Variáveis de longo prazo apresentaram maior índice de Hurst (maior persistência)
- Resultado: conjunto reduzido selecionado para o SOM

**Tamanho Ótimo do Mapa:**
- Período 2001–2011: elbow em ~X neurônios
- Período 2002–2007: elbow em ~Y neurônios (mapa menor; período mais homogêneo)

**Resultados SOM — Período 2001–2011:**
- **U-Matrix + Hits:** identifica clusters de comportamento de preços
- **Matriz de Labels (Var. Preço):** regiões "verdes" (alta) e "vermelhas" (baixa) claramente segregadas
- **Component Planes:** mapas por variável revelam quais indicadores discriminam melhor os estados do mercado
- Hurst Médio Prazo: período 2001–2011 mostra memória persistente em vários intervalos
- **Análise de Clusters — Vales:** identificação de fundos de mercado; momentos oportunos de compra
- **Análise de Clusters — Topos:** identificação de máximos; momentos oportunos de venda

**Resultados SOM — Período 2002–2007 (Pré-Crise):**
- Mapa mais homogêneo (bull market estável)
- **Volume Médio:** distinção clara entre tendências de baixa, alta e inversão de movimento
- Segmentação identifica regiões de estabilidade e regiões de transição de tendência

**Validação dos Resultados (Tabela 4.1 — Estratégias de Investimento):**
- Simulação de compra/venda baseada nos clusters do SOM
- Evolução do capital líquido no fechamento mensal mostrou resultado positivo
- A metodologia SOM conseguiu identificar momentos de entrada/saída superiores ao buy-and-hold

---

### 1.6 Conclusões

- SOM com indicadores da Análise Técnica é capaz de segmentar comportamentos do mercado e identificar momentos de estabilidade e crise
- O Índice de Hurst é útil para selecionar as variáveis mais persistentes (memoráveis)
- O subperíodo pré-crise (2002–2007) é mais facilmente segmentável; o período completo (2001–2011) captura eventos extremos como a crise de 2008
- Volume é um dos indicadores mais discriminantes para tendências de alta, baixa e inversão
- Limitações: análise retroativa; resultados futuros não garantidos; dados apenas do DJI

---

## PDF 2 — O Perfil do Investidor Individual no Mercado Financeiro

**Título:** O perfil do investidor individual no mercado financeiro  
**DOI:** 10.31994/rvs.v11i2.694  
**Autores:** Raiane Thainá Paiva, Helder Antônio da Silva, Júlio Cesar Mendes de Souza, Nicássia Feliciana Novôa, Cláudia Maria Miranda de Araújo Pereira  
**Instituição:** Instituto Federal de Educação, Ciência e Tecnologia do Sudeste de Minas Gerais — Campus Barbacena  
**Publicação:** Revista de Informação Contábil (v. 11, n. 2, 2020)

---

### 2.1 Introdução

O brasileiro contemporâneo tem dificuldade de poupar e quando poupa opta pela caderneta de poupança por desconhecer alternativas. Pesquisa SPC/CNDL (2017): 58% dos entrevistados não sabem quais investimentos têm melhores taxas de retorno (66% entre mulheres).

**Objetivo:** Analisar o perfil do investidor individual no mercado financeiro brasileiro.

**Objetivos específicos:**
- a) Levantar tipos de investimentos disponíveis para pessoa física
- b) Caracterizar perfis de investidores (conservador/moderado/arrojado)
- c) Apresentar possíveis riscos nos investimentos

---

### 2.2 Revisão de Literatura

#### Perfil do Investidor

Três categorias básicas:

| Perfil | Características |
|---|---|
| **Conservador** | Baixo risco, menor retorno, maior segurança, pouco conhecimento sobre investimentos |
| **Moderado** | Aceita diversificar, algum risco aceitável para ganhos maiores no longo prazo |
| **Arrojado** | Alto risco, busca retorno máximo, grande conhecimento ou assessoramento especializado |

**API (Análise do Perfil do Investidor):** instrumento obrigatório por código ANBIMA. Avalia grau de conhecimento do investidor. Crítica: linguagem formal dificulta entendimento; quem não responde não pode fazer aplicações.

#### Análise de Riscos

**Cinco tipos de risco (Oliveira & Pacheco, 2006):**

| Tipo | Definição |
|---|---|
| Operacional | Falhas em sistemas, equipamentos ou humanas |
| Legal | Contratos mal formulados, descumprimento de legislação |
| Liquidez | Dificuldade de comprar/vender ativo por baixo volume de negócios |
| Crédito | Títulos não honrados na data de vencimento |
| Mercado | Incerteza nos preços por oscilações de juros, câmbio, ações |

#### Tipos de Investimentos

**Renda Fixa:**
- **Caderneta de Poupança:** criada por D. Pedro II (Decreto 2.723/1861). Nova Poupança (Lei 12.703/2012): quando SELIC ≤ 8,5% → rende 70% da SELIC + TR; quando > 8,5% → TR + 0,5% ao mês. 65% dos brasileiros que poupam escolhem poupança (CNDL/SPC)
- **CDB (Certificado de Depósito Bancário):** renda fixa, IR regressivo: 22,5% (≤180 dias) → 15% (>720 dias)
- **RDB (Recibo de Depósito Bancário):** prazo mínimo 30 dias (taxa mercado) ou 120 dias (TR/TBF)
- **LC (Letra de Câmbio):** emitida por instituições financeiras; IR igual ao CDB
- **LCI (Letra de Crédito Imobiliário):** isenta IR para PF; garantia FGC até R$250k por CPF por instituição
- **LCA (Letra de Crédito do Agronegócio):** isenta IR para PF; FGC R$250k; investimento mínimo R$5.000; lastreada em CDI, IPCA ou IGPM
- **Tesouro Direto:** criado 2002 (Tesouro Nacional + BM&F Bovespa); IR regressivo + IOF nos primeiros 30 dias; títulos públicos = baixo risco

**Taxa CDI (Tabela Cetip 2013–2019):**

| Ano | Acumulado |
|---|---|
| 2013 | 8,06% |
| 2014 | 10,81% |
| 2015 | 13,24% |
| 2016 | 14,00% |
| 2017 | 9,93% |
| 2018 | 6,42% |
| 2019 (jan-nov) | 5,10% aprox. |

**Renda Variável:**
- **Ações:** menor fração do capital social de SA; captação de recursos
- **Fundos de Ações:** diversificação; gestão profissional sem necessidade de conhecimento aprofundado do investidor
- **Fundos Multimercado e Cambiais:** exposição a múltiplos fatores de risco

---

### 2.3 Metodologia

**Tipo:** Pesquisa quantitativa, qualitativa e descritiva com levantamento bibliográfico  
**Instrumento:** Questionário de 14 questões via SurveyMonkey  
**Amostra:** 60 entrevistados — investidores brasileiros (com e sem vínculo a instituições financeiras)  
**Tamanho mínimo calculado (GPower):** 46 entrevistados (poder do teste 95,35%)

**Variáveis do Questionário:**
- Dados sociodemográficos: idade, estado civil, profissão, renda média
- Atitude financeira: estilo de vida, controle do dinheiro
- Comportamento financeiro: percentual investido, tipos de investimento
- Educação financeira: conhecimento sobre investimentos, experiência em finanças
- Perfil de risco: perdas passadas, objetivo do investimento, tolerância a risco

**Análise de Confiabilidade — Alfa de Cronbach:**
- Desenvolvido por Lee J. Cronbach (1951)
- Mede consistência interna de um questionário
- Resultado obtido: **α = 0,665** (13 itens padronizados) → consistência **Substancial** (tabela: 0,61–0,80)
- Software: SPSS 24

**Análise Multivariada — Fatores Discriminantes:**
- Objetivo: classificar objetos em grupos homogêneos
- Lambda de Wilks funções 1 e 2: **0,582** (aceitável — quanto mais próximo de zero, maior poder discriminante)
- Escala Likert utilizada para capturar atitudes e motivações

---

### 2.4 Resultados e Discussão

**Matriz de Estruturas — Funções Discriminantes:**

| Variável | Função 1 | Função 2 |
|---|---|---|
| Conhecimento sobre Investimento | **0,649*** | 0,166 |
| Estilo de Vida | **0,560*** | 0,305 |
| Controle do Dinheiro | **0,560*** | 0,145 |
| Profissão | **-0,429*** | 0,090 |
| Renda Média | **0,311*** | 0,300 |
| Percentual Investido | **0,284*** | -0,119 |
| Estado Civil | **0,200*** | 0,007 |
| Idade | **0,156*** | 0,116 |
| Experiência em Finanças | 0,145 | **0,619*** |
| Tipos de Investimento | -0,270 | **0,534*** |
| Perdas Passadas | 0,135 | **0,487*** |

*(\*) Maior correlação absoluta entre variável e função discriminante*

**Interpretação:**
- **Investidores via Bancos (Função 1):** influenciados por Conhecimento, Estilo de Vida e Controle do Dinheiro
- **Investidores via Corretores (Função 2):** influenciados por Experiência prévia, Tipos de Investimentos oferecidos e Perdas passadas

**Perfil Demográfico:**
- Faixa etária predominante: 21–30 anos (jovens mais dispostos a risco, porém com baixo capital)
- Estado civil: solteiros mais propensos a investir (menores gastos individuais, maior ousadia)
- Profissão: dispersa — sem padrão específico
- Renda mensal: R$1.001 a R$5.000 (maioria)

**Comportamento e Atitude Financeira:**
- Percentual investido: ~10% da renda
- Investimento preferido: **poupança** via agências bancárias
- Finalidade: reserva para segurança futura
- Baixa tolerância a perdas; baixo conhecimento de mercado
- Permanecem em "zona de conforto" mesmo sem perdas passadas significativas

**Resultado Final — Perfil do Investidor (Gráfico 1):**

| Perfil | Percentual |
|---|---|
| **Conservador** | **63%** |
| Moderado | 20% |
| Agressivo/Arrojado | 17% |

---

### 2.5 Conclusões

- Investidor individual brasileiro típico: 21–30 anos, solteiro, renda R$1.001–5.000, aplica 10% na poupança, **perfil conservador (63%)**
- Baixo conhecimento financeiro limita acesso a melhores rentabilidades
- Rambo (2014): investidor brasileiro ignora princípios financeiros, considera poupança segura sem saber que é o investimento de menor retorno real
- Costa et al. (2018): necessidade urgente de educação financeira
- Lopes, Daleaste e Bianchet (2018): consulta a bancos/corretoras certificados pela ANBIMA como caminho para melhores decisões

---

## PDF 3 — Medidas de Risco e Matriz de Contágio

**Título:** Medidas de Risco e Matriz de Contágio  
**Autores:** Antonio Clécio Fontelles Thomaz de Almeida, Bruno Ferreira Frascaroli, Dimas Menezes Cunha  
**Publicação:** Revista Brasileira de Finanças (Online), Rio de Janeiro, Vol. 10, No. 4, December 2012, pp. 549–584  
**Contexto:** Artigo de pesquisa empírica aplicado ao mercado de capitais brasileiro

---

### 3.1 Introdução

Motivado pelas crises financeiras globais (em especial a crise americana de 2007–2009), o artigo propõe aplicar a metodologia **CoVaR** de Adrian & Brunnermeier (2011) para construir uma **Matriz de Contágio** entre ativos do mercado brasileiro.

Diferencial em relação a trabalhos anteriores:
- Uso de **regressão quantílica** (ao invés de modelos paramétricos)
- Estimação de efeitos assimétricos (perdas extremas ≠ ganhos extremos)
- Construção de matriz K×K de contágios entre papéis
- Aplicação ao contexto doméstico (IBOV) e internacional (DJIA)

---

### 3.2 Revisão da Literatura

#### Value at Risk (VaR)

Medida de risco individual mais comum. Definição formal:

```
VaR_α(X) = −inf{x | F_X(x) > α}
```

Onde `α` é o nível de confiança (ex: 5%) e `F_X` é a função de distribuição acumulada do retorno X.

**Limitações do VaR:**
- Mede apenas risco individual; não captura interdependências sistêmicas
- Assume simetria de efeitos positivos e negativos (modelo Markowitz 1952)
- Sensível a outliers nos modelos paramétricos

#### CoVaR (Adrian & Brunnermeier, 2011)

**CoVaR** = Value at Risk condicional de um ativo/sistema dado que outro ativo está em distress.

```
Definição: CoVaR_{i|j}^α = VaR_α(X_i | X_j = VaR_α(X_j))
```

**ΔCoVaR** = contribuição marginal ao risco sistêmico:

```
ΔCoVaR_{i|j}^α = CoVaR_{i|j}^α − CoVaR_{i|j=0}^{50%}
```

**Vantagem sobre VaR:** identifica papéis que **geram** risco sistêmico (não apenas os mais arriscados individualmente).

#### Regressão Quantílica (Koenker & Bassett, 1978)

Estima quantis condicionais da distribuição, minimizando:

```
min_β Σ ρ_τ(y_i − x_i'β)
```

onde `ρ_τ(u) = u(τ − I(u<0))` é a função de perda assimétrica ("check function").

**Vantagens:**
- Robusta a outliers
- Não assume normalidade
- Estima efeitos assimétricos (perdas extremas diferentes de ganhos)
- Mais informativa que regressão OLS em situações de distress

#### Auto-regulação e Basileia III

Regulação "auto-regulação" (Basileia III, 2010): IF's escolhem mecanismos adequados para cada situação mantendo-se dentro dos limites regulatórios. CoVaR como suporte quantitativo à regulação.

---

### 3.3 Dados e Metodologia

**Amostra:** 16 ativos de maior liquidez do Ibovespa (2006–2011):

| Papel | Empresa |
|---|---|
| PETR4 | Petrobras PN |
| PETR3 | Petrobras ON |
| VALE5 | Vale PNA |
| VALE3 | Vale ON |
| AMBV4 | Ambev PN |
| BBAS3 | Banco do Brasil ON |
| BBDC4 | Bradesco PN |
| CMIG4 | Cemig PN |
| CSNA3 | CSN ON |
| GGBR4 | Gerdau PN |
| ITSA4 | Itaúsa PN |
| ITUB4 | Itaú Unibanco PN |
| USIM5 | Usiminas PNA |
| PCAR4 | Pão de Açúcar PN |
| GOAU4 | Gerdau Met PN |
| LAME4 | Lojas Americanas PN |

**Índices:** IBOV (Ibovespa) e DJIA (Dow Jones Industrial Average)

**Variável:** retornos logarítmicos diários `r_t = ln(P_t/P_{t-1})`

**Quantil estimado:** τ = 5% (perdas extremas)

**Modelos estimados via regressão quantílica:**
1. `VaR_{5%}(papel_i)` — risco individual
2. `CoVaR_{5%}(IBOV | papel_i)` — risco sistêmico (impacto no índice)
3. `ΔCoVaR_{5%}(IBOV | papel_i)` — contribuição marginal
4. Matriz K×K: `CoVaR_{5%}(papel_j | papel_i)` para todos i,j

**Equação do modelo CoVaR:**

```
R_j = α_j + β_j·R_i + ε_j     (estimada no quantil 5%)
CoVaR_{j|i} = α̂_j + β̂_j·VaR_{5%}(R_i)
ΔCoVaR_{j|i} = β̂_j·(VaR_{5%}(R_i) − VaR_{50%}(R_i))
```

---

### 3.4 Resultados

#### Risco Individual (VaR 5%)

| Papel | VaR (5%) |
|---|---|
| USIM5 | -4,948% |
| LAME4 | -4,702% |
| BBAS3 | -4,445% |
| GGBR4 | -4,436% |
| CMIG4 | -4,305% |
| CSNA3 | -4,263% |
| GOAU4 | -4,183% |
| PETR3 | -4,139% |
| PETR4 | -3,961% |
| VALE5 | -3,922% |
| VALE3 | -3,824% |
| ITUB4 | -3,767% |
| ITSA4 | -3,697% |
| PCAR4 | -3,702% |
| BBDC4 | -3,742% |
| AMBV4 | -3,246% |

#### Risco Sistêmico (ΔCoVaR 5% em relação ao IBOV)

| Papel | β (theta) | ΔCoVaR (5%) |
|---|---|---|
| **PETR4** | **0,955** | **-3,369** |
| PETR3 | 0,939 | -3,313 |
| USIM5 | 0,957 | -3,378 |
| CMIG4 | 0,890 | -3,140 |
| BBDC4 | 0,816 | -2,880 |
| CSNA3 | 0,784 | -2,767 |
| VALE5 | 0,779 | -2,749 |
| BBAS3 | 0,712 | -2,512 |
| VALE3 | 0,680 | -2,400 |
| LAME4 | 0,607 | -2,141 |
| GGBR4 (ref. IBOV) | 0,765 | -2,701 |
| PCAR4 | 0,517 | -1,824 |
| AMBV4 | 0,514 | -1,814 |

**Resultado-chave:** PETR4 tem VaR individual moderado (-3,961%) mas **maior ΔCoVaR** (-3,369) → maior contribuição marginal ao risco do IBOV. VaR individual não identifica isso.

#### Risco Sistêmico vs. Individual

- ΔCoVaR fornece **ranking distinto** do VaR individual
- Demonstra que o papel de maior VaR (USIM5, -4,948%) não é necessariamente o maior contribuidor sistêmico
- Mostra que regressores quantílicos são mais robustos por não assumir simetria

#### Matriz de Contágio K×K

Estrutura: elemento (i,j) = ΔCoVaR estimado para papel_j dado distress em papel_i

**Total de contágio (coluna — ato de contaminar):**

| Papel | Total (coluna) |
|---|---|
| **PETR4** | **-31,07** |
| USIM5 | -28,41 |
| ITSA4 | -27,25 |
| ... | ... |
| LAME4 | -17,75 |
| PCAR4 | -20,35 |
| AMBV4 | -20,52 |

**Total de ser contaminado (linha):**

| Papel | Total (linha) |
|---|---|
| **USIM5** | **-32,80** |
| PETR4 | -31,41 |
| PETR3 | -30,77 |
| ... | ... |
| AMBV4 | -18,46 |
| PCAR4 | -20,51 |
| LAME4 | -23,87 |

**Insight:** O papel que mais contamina (PETR4) não é necessariamente o mais contaminado (USIM5). Diferente de modelos baseados em matriz de variância-covariância de Markowitz (1952).

#### Efeito Contágio IBOV ↔ DJIA (Tabela 6)

| Índices | IBOV | DJIA |
|---|---|---|
| IBOV | – | -2,14 |
| DJIA | -1,27 | – |

**Interpretação:** distress no DJIA afeta IBOV mais intensamente (-2,14) que o inverso (-1,27). Confirma transmissão de risco do mercado americano para o brasileiro.

#### Stress Test: Impacto do IBOV sobre Papéis (Tabela A.2)

Os maiores impactos do DJIA sobre papéis domésticos via stress test:

| Papel | ΔCoVaR (via DJIA) |
|---|---|
| CSNA3 | -2,02 |
| GGBR4 | -2,03 |
| PETR4 | -1,91 |
| BBDC4 | -1,85 |
| USIM5 | -2,28 |

---

### 3.5 Conclusões

- O desenvolvimento do sistema financeiro exige regulação avançada para acompanhar inovações (Basileia III)
- CoVaR é metodologia robusta para mensurar risco sistêmico e identificar papéis que mais afetam o sistema
- **Principal achado:** PETR4 lidera o ato de contaminar; USIM5 é o mais contaminado no efeito acumulado
- ΔCoVaR fornece ranking distinto do VaR individual — papéis mais arriscados individualmente não são necessariamente os maiores geradores de risco sistêmico
- Efeito contágio DJIA → IBOV é significativo e maior que IBOV → DJIA
- Questões para trabalhos futuros: por que contribuição marginal do IBOV supera a do DJIA sobre papéis domésticos?

---

## PDF 4 — Previsão do Ibovespa via CNN + ELM + Word2Vec

**Título:** (Tese de Doutorado — título não explicitado na capa extraída, mas identificado pelo conteúdo)  
**Autora:** Elisangela Lopes de Faria  
**Instituição:** Universidade Federal do Rio de Janeiro (inferido do conteúdo)  
**Tipo:** Tese de Doutorado  
**Modelo proposto:** I-CNNELM — CNN + OS-ELM + Word2Vec Skip-gram  
**Objetivo:** Previsão diária da tendência do Ibovespa usando classificação de notícias financeiras

---

### 4.1 Introdução

Previsão do mercado financeiro é tarefa difícil por dados ruidosos, não estruturados e com alto grau de incerteza. Esta tese propõe ferramenta automática de classificação de notícias financeiras combinando:
- **CNN (Convolutional Neural Network)** — extração de características de textos
- **ELM (Extreme Learning Machine)** — classificador rápido e preciso
- **Word2Vec Skip-gram** — representação distribuída de palavras em português

**Diferencial em relação à literatura:**
- Único trabalho focado no mercado **brasileiro** (Ibovespa) com dados em **português**
- Combina CNN + ELM (híbrido) — outros trabalhos usam CNN ou ELM separados
- ELM (OS-ELM) elimina iterações do backpropagation → muito mais rápido

**Resultado anterior da autora (mestrado, FARIA 2012):** previsão do Ibovespa usando redes MLP e RBF, confirmando que 2 classes (positiva/negativa) superam 3 classes.

---

### 4.2 Revisão de Literatura — Redes Neurais Artificiais

#### MLP (Multi-Layer Perceptron) e Backpropagation

Redes feedforward com camadas: entrada → ocultas → saída. Treinamento via **backpropagation** (Rumelhart, Hinton & Williams, 1986).

**Forward pass:**
```
z_l = W_l · a_{l-1} + b_l
a_l = f(z_l)
```

**Backward pass (gradiente descendente):**
```
δ_L = ∇_a C ⊙ f'(z_L)             (camada de saída)
δ_l = (W_{l+1}^T · δ_{l+1}) ⊙ f'(z_l)   (camadas ocultas)
∂C/∂W_l = δ_l · a_{l-1}^T
∂C/∂b_l = δ_l
```

**Funções de ativação:**
```
Sigmoide:  σ(x) = 1/(1 + e^{-x})
Tanh:      tanh(x) = (e^x − e^{-x})/(e^x + e^{-x})
ReLU:      f(x) = max(0, x)   ← melhor para DLNN (Glorot et al., 2011)
```

**Hiperparâmetros:** taxa de aprendizado, momentum, número de camadas/neurônios, épocas.

#### CNN (Convolutional Neural Network)

**Três características distintivas:**
1. **Conexões esparsas:** kernel menor que a entrada → cada neurônio de saída afetado por região local
2. **Campos receptivos locais:** filtro de h×k aplicado em janela deslizante sobre a entrada
3. **Compartilhamento de parâmetros:** mesmo filtro aplicado em diferentes posições → aprende padrões independente da posição

**Camadas de uma CNN:**
- **Convolucional:** aplica filtros F ∈ ℝ^{h×k}; `y_i = f(F · x_{i:i+h−1} + b)`; wide vs. narrow convolution; stride
- **Pooling:** redução dimensional — max pooling seleciona valor máximo da região; fornece saída de tamanho fixo (crucial para textos de tamanho variável)
- **Dropout (Hinton et al., 2012):** zera saídas aleatoriamente com p=0,5; previne overfitting; eficiente computacionalmente
- **Fully Connected:** camadas densas para classificação final
- **Softmax:** `softmax(y_i) = e^{y_i} / Σ_j e^{y_j}` — vetor de probabilidades na saída

#### ELM (Extreme Learning Machine)

Rede feedforward com camada oculta única. Pesos entre entrada e oculta são **aleatórios e fixos**. Apenas pesos de saída são calculados analiticamente pela pseudoinversa de Moore-Penrose.

**Formulação:**

Para N padrões, p entradas, q neurônios ocultos, C saídas:

```
h(k) = [f(W_1^T·a(k)+b_1), ..., f(W_q^T·a(k)+b_q)]^T
o_i(k) = β_i^T · h(k)
```

Relação matricial: `T = β^T · H`

**Cálculo da pseudoinversa:**
```
β = (H·H^T)^{-1} · H · T^T
```

Com regularização (N < q):
```
β = (I/C + H·H^T)^{-1} · H · T^T
```

Com regularização (N > q, caso geral):
```
β = (I/C + H^T·H)^{-1} · H^T · T^T
```

**Vantagens:**
- Velocidade: centenas de vezes mais rápida que backpropagation e SVR
- Boa generalização: similar ao SVR na maioria das bases UCI
- Simplicidade: único parâmetro a ajustar = número de neurônios ocultos

**Variações:**
- **OS-ELM** (Liang et al., 2006): versão online sequencial — aprende dados novos sem retreinar do zero
- **E-ELM** (Zhu et al., 2005): usa algoritmo Evolucionário Diferencial para selecionar neurônios relevantes
- **I-ELM** (Huang et al., 2006): versão incremental — adiciona neurônios até atingir erro alvo
- **ELM regularizada** com lasso, ridge, elastic net (Martínez-Martínez et al., 2011)

---

### 4.3 Revisão de Literatura — PLN e Representação de Palavras

#### Vector Space Model (VSM)

Documentos representados como vetores em espaço t-dimensional (Salton et al., 1975). Métricas de similaridade:

```
Similaridade cosseno: sim(d_j, d_q) = (Σ w_ij·w_iq) / (√Σw²_ij · √Σw²_iq)
TF-IDF:  tfidf_ij = tf_ij · log(N/df_i)
```

**Bag-of-Words (BOW):** representa documento como saco de palavras; ignora ordem; alta dimensionalidade ("maldição da dimensionalidade").

#### Hipótese Distribucional

"Você conhece uma palavra pela companhia que ela mantém" (Rupert, 1961). Palavras com vizinhos similares têm significados similares.

**Categorias:**
1. **Métodos baseados em contagem:** matriz de co-ocorrência + SVD (LSA — Deerwester et al., 1990) + PMI
2. **Métodos preditivos:** Word2Vec (Mikolov et al., 2013), GloVe (Pennington et al., 2014), NNLM (Bengio et al., 2003)

#### Word2Vec Skip-gram

Prevê contexto dado a palavra atual. Objetivo: maximizar log-probabilidade média:

```
(1/T) · Σ_{t=1}^T Σ_{-C≤j≤C, j≠0} log p(w_{t+j} | w_t)
```

**Probabilidade softmax:**
```
p(w_i | w_j) = exp(u_w^T · v_w) / Σ_{l=1}^V exp(u_l^T · v_w)
                    i    j                              wj
```

**Otimizações para reduzir custo O(V):**

*Softmax Hierárquico* — árvore binária; avalia log₂(V) nós em vez de V:
```
p(w=w_O) = Π_{j=1}^{L(w)−1} σ([[n(w,j+1)=ch(n(w,j))]] · v'_{n(w,j)}^T · h)
```

*Amostragem Negativa* — treina para discriminar palavra correta de N palavras ruidosas:
```
log σ(v'_w^T · v_w) + Σ_{i=1}^N E_{w_i~P_n(w)} log σ(−v'_w^T · v_w)
              O    I                                            i    I
```

Distribuição de ruído: `P(w_i) = f(w_i)^{3/4} / Σ_j f(w_j)^{3/4}`

**PMI (Pointwise Mutual Information)** para detecção de n-gramas:
```
PMI_bigrama  = log(O_11 / e_11)
PMI_trigrama = log(O_111 / e_111)
```

---

### 4.4 Trabalhos Correlatos

| Trabalho | Dados | Modelo | Mercado | Acurácia |
|---|---|---|---|---|
| Ding et al. (2015) | Reuters + Bloomberg (2006–2013) | DLNN + word2vec | S&P500 | 55,21% |
| Peng et al. (2015) | Reuters + Bloomberg (2006–2013) | MLP 4 camadas + BoK + word2vec | S&P500 | 56,87% |
| Huynh et al. (2017) | Reuters + Bloomberg (2006–2013) | BGRU + word embeddings | S&P500 | 59,98% |
| Yoshihara et al. (2017) | Jornais Nikkei (1999–2008) | RBM + DBN + RNN | Nikkei (10 ações) | < SVM |
| Dos Santos et al. (2017) | Reuters + Bloomberg | RNN + LSTM char-level | S&P500 | 64,74% (interday) |

**Gap identificado:** poucos trabalhos com mercados emergentes e dados em português.

---

### 4.5 Modelo Proposto — I-CNNELM

**Pipeline completo:**

```
[Notícias Web] → [Coleta Python] → [Pré-processamento] 
→ [Word2Vec Skip-gram] → [Sentence Embeddings] 
→ [CNN (conv + pooling)] → [OS-ELM] → [Previsão: Alta/Baixa]
```

#### Dados

**Base nw2v (treinamento word2vec):**
- 380.592 títulos de notícias financeiras (Infomoney, Exame, Estadão, G1)
- Período: jan/2012 a dez/2016
- ~4.823.507 tokens após pré-processamento

**Base nprev (previsão do Ibovespa):**
- 162.001 títulos agrupados por data (jan/2012 a mai/2013)
- 337 documentos (dias de negociação)
- Mínimo diário: 269 títulos; Média: 479; Máximo: 915

**Série temporal Ibovespa:**
- Cotações diárias de fechamento (jan/2012 – mai/2013)
- 337 dias de negociação

**Tendência diária:**
```
tendencia(t) = (fechamento(t) − fechamento(t−1)) / fechamento(t−1) × 100
```

**Classificação:**
- Positiva: tendência(t) ≥ 0 → 156 documentos (46,29%)
- Negativa: tendência(t) < 0 → 181 documentos (53,70%)
- Previsão um dia à frente: notícias do dia t preveem tendência do dia t+1

#### Pré-processamento

**3 etapas:**

1. **Tokenização:** quebra texto em tokens; delimitadores: espaços, pontuação
2. **Limpeza + remoção de stopwords:** remove números, pontuação, espaços extras; converte para minúsculas; stoplist NLTK português
3. **N-grama (trigramas):** detecta expressões financeiras frequentes via PMI e outras 6 métricas

**7 métricas de associação testadas:** PMI, T-Student, Chi-quadrada, Razão de Verossimilhança, Mi-like, Poisson-Stirling, Jaccard

**Limiares de filtragem:** ω = 50 e ω = 100 ocorrências mínimas

**Exemplos de trigramas (PMI, ω=100):**

| Trigrama |
|---|
| ('dólar', 'fecha', 'alta') |
| ('bovespa', 'opera', 'queda') |
| ('bolsas', 'europa', 'caem') |
| ('ibovespa', 'opera', 'alta') |
| ('pib', 'eua', 'cresce') |
| ('desemprego', 'eua', 'sobem') |

#### Geração do Word2Vec

Ferramenta: Gensim (Radim, 2010) — biblioteca Python

**Parâmetros finais:**
- `size` = 100 ou 300 (dimensão do vetor)
- `window` = 5 (contexto)
- `min_count` = 50
- `workers` = 32
- `sg` = 1 (Skip-gram)

28 vocabulários gerados (7 métricas × 2 limiares × 2 dimensões)

**Validação dos vetores — similaridade cosseno para "bovespa":**

| Palavra similar | Score |
|---|---|
| ibovespa | 0,847 |
| dólar | 0,649 |
| ouro | 0,645 |
| bovespa_opera_alta | 0,639 |
| pregões | 0,619 |
| Ibovespa_fecha_alta | 0,618 |

#### Vetores Sentença (Sentence Embeddings)

```
sentence_embedding = (1/N) · Σ_{t=1}^N word_embedding(token_t)
```

Matriz de entrada CNN: 450 × k (450 notícias/dia × k dimensões do embedding).

#### Arquitetura CNN

- 1 camada convolucional com múltiplos filtros (32–160)
- Tamanho dos filtros: 3×k, 5×k ou 7×k
- Stride = 1; narrow convolution (sem padding)
- Camada max-pooling (1 valor por filtro)
- Concatenação → vetor unidimensional → entrada para ELM

```
y_i = f(F · x_{i:i+h−1} + b)     (mapa de características)
```

#### OS-ELM (classificador final)

Versão online do ELM; aprende sequencialmente. Quantidade de neurônios ocultos L = K × N (K ∈ {0,2; 0,4; 0,6} → L ∈ {67, 135, 200}). Função de ativação: sigmoide.

#### Validação

**K-Fold Cross Validation** (k=10): 10 execuções, cada uma usa um fold diferente para teste; 10% do treino reservado para validação durante treinamento. Resultado final = média das 10 acurácias.

---

### 4.6 Resultados

#### Tabela 7.2 — Acurácia por Configuração (melhores resultados)

| Métrica | ω=50, d=100 | ω=50, d=300 | ω=100, d=100 | ω=100, d=300 |
|---|---|---|---|---|
| PMI | 54,90 | 57,86 | 58,14 | 58,51 |
| T-Student | 54,95 | 56,08 | 56,09 | 54,29 |
| Chi-quadrada | 57,29 | 56,35 | 59,05 | 56,45 |
| Razão Verossimilhança | 57,93 | 56,38 | 56,39 | 57,26 |
| **Mi-like** | 54,05 | 56,98 | 56,61 | **60,22** |
| Poisson-Stirling | 54,64 | 55,17 | 58,16 | 57,61 |
| Jaccard | 55,81 | 54,96 | 57,27 | 56,39 |

**Melhor configuração:** Mi-like + ω=100 + d=300 + 96 filtros (tamanho 3) + 67 neurônios ELM → **60,22% de acurácia**

#### Matriz Confusão — Melhor Modelo (60,22%)

|  | Prevista Positiva | Prevista Negativa | Total Real |
|---|---|---|---|
| **Real Positiva** | TP = 93 | FN = 63 | 156 |
| **Real Negativa** | FP = 71 | TN = 110 | 181 |
| **Total Previsto** | 164 | 173 | **337** |

| Métrica | Valor |
|---|---|
| Acurácia | 60,2% |
| Recall (sensitividade) | 59,6% |
| Precisão (positivo) | 56,7% |
| F-Measure (positivo) | 58% |
| Especificidade | 60,8% |
| Negative Pred. Value | 63,6% |
| F-Measure (negativo) | 62% |

**Insight:** modelo ligeiramente mais eficiente na classe negativa (F=62% vs 58%) — deve-se ao desbalanceamento (181 negativos vs 156 positivos).

#### Comparação entre Modelos (Tabela 7.5)

| Modelo | 5 Maiores Acurácias (%) |
|---|---|
| **I-CNNELM** | **60,2 / 59,0 / 58,5 / 58,1 / 57,9** |
| I-CNN | 57,0 / 57,0 / 56,0 / 56,0 / 55,0 |
| I-ELM | 55,0 / 51,0 / 49,0 / 47,0 / 47,0 |
| I-BoK (MLP 4×1024) | 56,0 / 55,0 / 54,0 / 53,0 / 53,0 |

**420 modelos I-CNN + 84 modelos I-ELM + 28 modelos I-BoK** testados para comparação justa.

#### Tempo de Treinamento (Tabela 7.6)

| Modelo | Acurácia | Tempo Médio |
|---|---|---|
| **I-CNNELM** | 60,2% | **1h 41min 20s** |
| I-CNN | 57,0% | 27h 45min 26s |
| I-ELM | 55,0% | 1min 30s |
| I-BoK | 56,0% | 34min 55s |

**I-CNNELM tem melhor custo-benefício:** melhor acurácia com tempo razoável (17× mais rápido que I-CNN).

Hardware: Python 3.5, PC 3.4 GHz, 32 cores, 256 GB RAM.

#### Estratégia de Negociação (Minicontratos WIN)

**Período:** 04/abr/2013 a 20/mai/2013 (32 dias úteis)  
**Contrato:** WINM13 (minicontrato Ibovespa, vencimento junho 2013)  
**Valor por ponto:** R$0,20  
**Regras:**
- Previsão positiva → compra na abertura
- Previsão negativa → vende na abertura; recompra no fechamento se confirmar queda

**Resultado:**
- Lucro bruto: **1.645 pontos**
- Lucro líquido: **R$329,00**
- Buy-and-hold no mesmo período: apenas 150 pontos (R$30,00)

→ **I-CNNELM superou buy-and-hold em ~11×**

---

### 4.7 Conclusões

**Achados principais:**
- I-CNNELM (60,22%) supera todos os modelos comparados (I-CNN, I-ELM, I-BoK)
- Mi-like foi a melhor métrica de associação para trigramas
- ω=100 (frequência mínima) melhora qualidade dos trigramas
- d=300 foi a melhor dimensão para os word embeddings
- Mais filtros convolucionais → melhor acurácia; tamanho de filtro depende da tarefa
- A combinação CNN+ELM supera CNN ou ELM isolados
- OS-ELM é 17× mais rápido que CNN puro com melhor acurácia
- Estratégia de negociação com minicontratos validou lucratividade do modelo

**Limitações:**
- Período de negociação limitado (dados de 2013 apenas)
- Corpus em português com quantidade limitada de tokens
- Sem uso de GPU (limitação de hardware)
- Sem custos de transação e IR na simulação de negociação

**Trabalhos futuros:**
- Testar com período 2015–2017 (período político conturbado)
- Explorar janelas de previsão intraday
- Incorporar indicadores macroeconômicos como variáveis adicionais
- Estudar abordagem Big Data e arquiteturas com GPU
- Aplicar metodologia a diagnósticos médicos em português

---

## Síntese Cruzada — Conexões entre os 4 PDFs

| Tema | PDF 1 (SOM) | PDF 2 (Perfil) | PDF 3 (CoVaR) | PDF 4 (CNN+ELM) |
|---|---|---|---|---|
| **Mercado brasileiro** | DJI como proxy | Investidores BR | IBOV + B3 | Ibovespa (previsão) |
| **Análise técnica** | Central (indicadores) | Referenciada | Não usa | Referenciada (MACD) |
| **Risco** | Hurst (memória) | Perfis (conservador/arrojado) | VaR / CoVaR / ΔCoVaR | Não central |
| **Machine Learning** | SOM (não supervisionado) | Análise discriminante | Regressão quantílica | CNN + ELM + Word2Vec |
| **Dados textuais** | Não usa | Não usa | Não usa | Central (380K notícias) |
| **Validação** | Simulação de investimentos | Alfa de Cronbach | Stress test IBOV/DJIA | K-Fold + estratégia WIN |
| **Python/ferramentas** | Oracle SQL | SPSS 24 | R (regressão quantílica) | Python (NLTK, Gensim, Keras, TF) |

**Implicações para o projeto investimento-ai:**

1. **SOM + indicadores técnicos** → regime detection automático (agente Bolsa: identificar bull/bear/crise)
2. **Perfil de investidor** → personalização do sistema (onboarding: conservador/moderado/arrojado)
3. **CoVaR / ΔCoVaR** → monitoramento de risco sistêmico (agente de risco: alertas de contágio)
4. **CNN + ELM + Word2Vec** → classificação de notícias financeiras em português (skill de sentimento em português)