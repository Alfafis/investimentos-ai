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

ULTIMO PASSO (obrigatorio): sua resposta final deve ser exclusivamente o relatorio da sessao
em markdown, sem texto antes ou depois. NAO use a ferramenta Write (ela esta bloqueada) - este
runner grava a resposta final em logs/investing-$SessionId.md.
Conteudo:

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

# SEGURANCA: mesma politica de run_rotina.ps1 (ver comentario la). O agente le RSS
# externo; prompt injection nao pode virar comando na maquina. Nada de
# --dangerously-skip-permissions: so tools MCP da allowlist, resto negado sem prompt.
$McpConfig = Join-Path $PSScriptRoot "mcp-config.json"
$AllowedTools = @(
    "get_macro_context", "get_decision_log", "get_paper_portfolio", "get_trade_outcomes",
    "run_investing_decision", "score_tickers", "save_decision", "save_paper_trade"
) | ForEach-Object { "mcp__investimentos-ai__$_" }
$AllowedTools = $AllowedTools -join ","
$DeniedTools  = "Bash,PowerShell,Write,Edit,NotebookEdit,WebFetch,WebSearch,Read,Glob,Grep"

$ReportFile = Join-Path $LogDir "investing-$SessionId.md"
$n = 2
while (Test-Path $ReportFile) {
    $ReportFile = Join-Path $LogDir "investing-$SessionId-$n.md"
    $n++
}

Write-Log "[$SessionId] Iniciando sessao do agente"

try {
    $Report = New-Object System.Collections.Generic.List[string]
    claude -p $UserPrompt --system-prompt $SystemPrompt --max-turns 30 `
        --mcp-config $McpConfig --strict-mcp-config `
        --permission-mode dontAsk `
        --allowedTools $AllowedTools `
        --disallowedTools $DeniedTools 2>&1 | ForEach-Object {
        $line = "$_"
        [System.IO.File]::AppendAllText($LogFile, "$line`n", $utf8NoBom)
        Write-Host $line
        # stdout (sem stderr) do modo -p text = resposta final = relatorio
        if ($_ -isnot [System.Management.Automation.ErrorRecord]) { $Report.Add($line) }
    }
    $ClaudeExit = $LASTEXITCODE

    if ($Report.Count -gt 0) {
        [System.IO.File]::WriteAllText($ReportFile, (($Report -join "`n") + "`n"), $utf8NoBom)
        Write-Log "[$SessionId] Relatorio: $ReportFile"
    }
    if ($ClaudeExit -ne 0) {
        Write-Log "[$SessionId] ERRO: claude saiu com codigo $ClaudeExit"
    } else {
        Write-Log "[$SessionId] Sessao concluida com sucesso"
    }
} catch {
    Write-Log "[$SessionId] ERRO: $_"
}

Write-Host "Log: $LogFile"
