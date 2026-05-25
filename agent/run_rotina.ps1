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

Write-Log "[$SessionId] Iniciando rotina $Rotina"
Write-Host "[$SessionId] Rotina: $Rotina | Playbook: $(Split-Path $PlaybookFile -Leaf)"

try {
    claude -p $UserPrompt --system-prompt $SystemPrompt --max-turns 30 --dangerously-skip-permissions 2>&1 | ForEach-Object {
        $line = "$_"
        [System.IO.File]::AppendAllText($LogFile, "$line`n", $utf8NoBom)
        Write-Host $line
    }
    Write-Log "[$SessionId] Rotina $Rotina concluida com sucesso"
    Write-Host "[$SessionId] Concluida. Log: $LogFile"
} catch {
    Write-Log "[$SessionId] ERRO: $_"
    Write-Error "[$SessionId] ERRO: $_"
    exit 1
}
