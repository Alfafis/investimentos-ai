param(
    [string]$Watchlist = "PETR4,VALE3,ITUB4,BBAS3,WEGE3,ABEV3,RENT3,SUZB3,GGBR4,CMIG4",
    [float]$Cash = 5000.0
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$Now = Get-Date
$SessionId = $Now.ToString("yyyy-MM-dd-HH") + "h"

$LogDir = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$LogFile = Join-Path $LogDir "agent_$SessionId.log"

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
4. get_trade_outcomes (since_date=data de inicio do experimento) — P&L acumulado

Se mercado aberto:
5. run_investing_decision (watchlist=$Watchlist, posicoes do portfolio atual, cash=$Cash)
6. Para cada recomendacao de venda: save_paper_trade (action=sell, com preco atual e razao)
7. Para cada recomendacao de compra aprovada pelos criterios do playbook: save_paper_trade (action=buy)
8. save_decision (session_id='$SessionId') com JSON contendo: macro, portfolio_state, scores, sell_signals, buy_recommendations, reasoning, alertas

Se mercado fechado:
5. score_tickers para a watchlist (preparacao para proxima abertura)
6. save_decision com analise pre-mercado

Criterios do playbook sao lei. Justifique cada decisao de forma auditavel.
"@

"[$SessionId] Iniciando sessao do agente" | Add-Content $LogFile -Encoding UTF8

try {
    $result = claude -p $UserPrompt --system-prompt $SystemPrompt --max-turns 30 --dangerously-skip-permissions 2>&1
    $result | Add-Content $LogFile -Encoding UTF8
    "[$SessionId] Sessao concluida com sucesso" | Add-Content $LogFile -Encoding UTF8
} catch {
    "[$SessionId] ERRO: $_" | Add-Content $LogFile -Encoding UTF8
}

Write-Host "Log: $LogFile"
