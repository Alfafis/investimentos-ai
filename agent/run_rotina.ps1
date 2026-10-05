param(
    [Parameter(Mandatory)][string]$Rotina  # ex: "00-radar", "01-investing-abertura"
)

# Force UTF-8 so claude output is captured correctly on Windows
[Console]::InputEncoding  = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding           = [System.Text.Encoding]::UTF8

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$Now       = Get-Date
$DateStr   = $Now.ToString("yyyy-MM-dd")
$TimeStr   = $Now.ToString("HH:mm")
$SessionId = "$DateStr-$Rotina"

# Log dir
$LogDir = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$LogFile = Join-Path $LogDir "agent-$Rotina-$DateStr.log"

$utf8NoBom = New-Object System.Text.UTF8Encoding $false
function Write-Log([string]$Line) {
    [System.IO.File]::AppendAllText($LogFile, "$Line`n", $utf8NoBom)
}

# Read rotina file and extract instructions block (first ``` ... ``` section)
$RotinaFile = Join-Path $ProjectRoot "agent\rotina-$Rotina.md"
if (-not (Test-Path $RotinaFile)) {
    Write-Log "[$SessionId] ERRO: rotina nao encontrada: $RotinaFile"
    Write-Error "Arquivo nao encontrado: $RotinaFile"
    exit 1
}

$RotinaContent = Get-Content $RotinaFile -Raw -Encoding UTF8
$InstructionsMatch = [regex]::Match($RotinaContent, '(?s)```\r?\n(.+?)\r?\n```')
if (-not $InstructionsMatch.Success) {
    Write-Log "[$SessionId] ERRO: bloco de instrucoes nao encontrado em $RotinaFile"
    Write-Error "Bloco de instrucoes nao encontrado em $RotinaFile"
    exit 1
}
$Instructions = $InstructionsMatch.Groups[1].Value

# Playbook por prefixo de rotina
$RotinaNum = $Rotina.Substring(0, 2)
$PlaybookFile = switch ($RotinaNum) {
    { $_ -in "00","01","02" } { Join-Path $ProjectRoot "docs\playbooks\investing.md" }
    { $_ -in "03","04","05" } { Join-Path $ProjectRoot "docs\playbooks\swing-trader.md" }
    default                   { Join-Path $ProjectRoot "docs\playbooks\investing.md" }
}

if (-not (Test-Path $PlaybookFile)) {
    Write-Log "[$SessionId] ERRO: playbook nao encontrado: $PlaybookFile"
    Write-Error "Playbook nao encontrado: $PlaybookFile"
    exit 1
}
$SystemPrompt = Get-Content $PlaybookFile -Raw -Encoding UTF8

# Injeta contexto de sessao no topo das instrucoes
$UserPrompt = @"
Sessao: $SessionId
Data/hora: $DateStr $TimeStr BRT

$Instructions
"@

# SEGURANCA: o agente roda sem ninguem olhando e le texto externo (RSS via
# scan_market_news / get_sentiment). Uma manchete com prompt injection nao pode
# virar comando na maquina, entao NAO usar --dangerously-skip-permissions:
#   --permission-mode dontAsk  tool fora da allowlist e negada na hora, sem travar em prompt
#   --allowedTools             so as tools MCP que as rotinas usam
#   --disallowedTools          tira Bash/Write/Edit/Read/Web* do contexto, mesmo que o
#                              settings.json da maquina as libere (deny vence allow)
#   --strict-mcp-config        so o servidor de agent/mcp-config.json (nome fixo -> prefixo fixo)
# Sem Write, o relatorio .md e gravado por este script a partir da resposta final.
$McpConfig = Join-Path $PSScriptRoot "mcp-config.json"
$AllowedTools = @(
    "get_macro_context", "get_decision_log", "get_paper_portfolio", "get_trade_outcomes",
    "run_investing_decision", "score_tickers", "technical_analysis", "get_stock_quotes",
    "get_sentiment", "check_stock_circuit_breaker", "scan_market_news",
    "save_decision", "save_paper_trade"
) | ForEach-Object { "mcp__investimentos-ai__$_" }
$AllowedTools = $AllowedTools -join ","
$DeniedTools  = "Bash,PowerShell,Write,Edit,NotebookEdit,WebFetch,WebSearch,Read,Glob,Grep"

$ReportFile = Join-Path $LogDir ("$Rotina-$DateStr-" + $Now.ToString("HH") + "h" + $Now.ToString("mm") + ".md")
$n = 2
while (Test-Path $ReportFile) {
    $ReportFile = Join-Path $LogDir ("$Rotina-$DateStr-" + $Now.ToString("HH") + "h" + $Now.ToString("mm") + "-$n.md")
    $n++
}

Write-Log "[$SessionId] Iniciando rotina $Rotina"
Write-Host "[$SessionId] Rotina: $Rotina | Playbook: $(Split-Path $PlaybookFile -Leaf)"

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
        Write-Error "[$SessionId] ERRO: claude saiu com codigo $ClaudeExit"
        exit 1
    }
    Write-Log "[$SessionId] Rotina $Rotina concluida com sucesso"
    Write-Host "[$SessionId] Concluida. Log: $LogFile"
} catch {
    Write-Log "[$SessionId] ERRO: $_"
    Write-Error "[$SessionId] ERRO: $_"
    exit 1
}
