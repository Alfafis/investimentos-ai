param(
    [string]$Watchlist = "PETR4,VALE3,ITUB4,BBAS3,WEGE3,ABEV3,RENT3,SUZB3,GGBR4,CMIG4",
    [float]$Cash = 5000.0
)

# Force UTF-8 so claude's output is captured correctly on Windows
[Console]::InputEncoding  = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding           = [System.Text.Encoding]::UTF8

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$Now       = Get-Date
$SessionId = $Now.ToString("yyyy-MM-dd-HH") + "h"

$LogDir = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$LogFile = Join-Path $LogDir "agent_$SessionId.log"

# UTF-8 without BOM writer — Add-Content in PS 5.1 adds BOM on first write
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
function Write-Log([string]$Line) {
    [System.IO.File]::AppendAllText($LogFile, "$Line`n", $utf8NoBom)
}

$PlaybookPath = Join-Path $ProjectRoot "docs\playbooks\investing.md"
$SystemPrompt = Get-Content $PlaybookPath -Raw -Encoding UTF8

$UserPrompt = @"
Sessao: $SessionId
Data/hora: $($Now.ToString("yyyy-MM-dd HH:mm")) BRT
Watchlist: $Watchlist
Caixa disponivel: R$ $Cash

Execute o pipeline completo do playbook de investimentos:

1. get_macro_context — verificar se mercado esta aberto e contexto macro atual
2. get_decision_log (last_n=3) — ler ultimas decisoes para contexto e aprendizado
3. get_paper_portfolio — verificar posicoes abertas em papel
4. get_trade_outcomes (since_date=2026-05-26) — P&L acumulado do experimento

Se mercado aberto:
5. run_investing_decision (watchlist=$Watchlist, posicoes do portfolio atual, cash=$Cash)
6. Para cada recomendacao de venda: save_paper_trade (action=sell, com preco atual e razao)
7. Para cada recomendacao de compra aprovada pelos criterios do playbook: save_paper_trade (action=buy)
8. save_decision (session_id='$SessionId') com JSON contendo: macro, portfolio_state, scores, sell_signals, buy_recommendations, reasoning, alertas

Se mercado fechado:
5. score_tickers para a watchlist (preparacao para proxima abertura)
6. save_decision com analise pre-mercado

Criterios do playbook sao lei. Justifique cada decisao de forma auditavel.

ULTIMO PASSO (obrigatorio): Use a ferramenta Write para gerar o relatorio da sessao:
- Arquivo: logs/investing-$SessionId.md
- NAO sobrescreva — o SessionId no nome garante unicidade
- Conteudo em markdown:

# Pipeline Diario de Investimentos — $SessionId

## Contexto Macro
[modo do mercado, Ibovespa, USD/BRL, modo conservador?]

## Equity Snapshot
[cash_brl | invested_brl | unrealized_pnl_brl | total_equity_brl | return_pct]

## Portfolio — Posicoes Abertas
[ticker | qty | preco medio | preco atual | P&L% | distancia do stop]

## Scoring da Watchlist
[ticker | score | RSI | MACD | EMA200 | sinal]

## Acoes Tomadas
### Vendas: [ticker | razao | preco | P&L]
### Compras: [ticker | qty | preco | razao]

## Reasoning e Alertas
[decisoes principais e riscos identificados]

---
_Sessao: $SessionId | Gerado: [timestamp completo]_
"@

Write-Log "[$SessionId] Iniciando sessao do agente"

try {
    claude -p $UserPrompt --system-prompt $SystemPrompt --max-turns 30 --dangerously-skip-permissions 2>&1 | ForEach-Object {
        $line = "$_"
        [System.IO.File]::AppendAllText($LogFile, "$line`n", $utf8NoBom)
        Write-Host $line
    }
    Write-Log "[$SessionId] Sessao concluida com sucesso"
} catch {
    Write-Log "[$SessionId] ERRO: $_"
}

Write-Host "Log: $LogFile"
