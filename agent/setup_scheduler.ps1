# Registra as 6 rotinas do Investimentos AI no Windows Task Scheduler
# Rodar uma vez como Administrador: .\agent\setup_scheduler.ps1

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$RunnerPath  = Join-Path $ProjectRoot "agent\run_rotina.ps1"

# Rotinas: nome da task, parametro -Rotina, horario (HH:mm), dias da semana
$Rotinas = @(
    @{ Task = "InvestimentosAI-Radar";             Rotina = "00-radar";              Hora = "08:00" }
    @{ Task = "InvestimentosAI-TraderPre";          Rotina = "03-trader-pre";         Hora = "09:00" }
    @{ Task = "InvestimentosAI-InvestingAbertura";  Rotina = "01-investing-abertura"; Hora = "10:00" }
    @{ Task = "InvestimentosAI-TraderMid";          Rotina = "04-trader-mid";         Hora = "13:00" }
    @{ Task = "InvestimentosAI-InvestingFechamento";Rotina = "02-investing-fechamento";Hora = "17:00" }
    @{ Task = "InvestimentosAI-TraderFechamento";   Rotina = "05-trader-fechamento";  Hora = "17:30" }
)

$Weekdays = "Monday","Tuesday","Wednesday","Thursday","Friday"

$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit ([TimeSpan]::FromMinutes(45)) `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable

$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

foreach ($r in $Rotinas) {
    if (Get-ScheduledTask -TaskName $r.Task -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $r.Task -Confirm:$false
    }

    $Action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NonInteractive -ExecutionPolicy Bypass -File `"$RunnerPath`" -Rotina `"$($r.Rotina)`"" `
        -WorkingDirectory $ProjectRoot

    $Trigger = New-ScheduledTaskTrigger `
        -Weekly `
        -DaysOfWeek $Weekdays `
        -At $r.Hora

    Register-ScheduledTask `
        -TaskName  $r.Task `
        -Action    $Action `
        -Trigger   $Trigger `
        -Settings  $Settings `
        -Principal $Principal `
        -Description "Investimentos AI -- rotina $($r.Rotina) -- seg-sex $($r.Hora) BRT" | Out-Null

    Write-Host "  [OK] $($r.Task) -- $($r.Hora) seg-sex"
}

Write-Host ""
Write-Host "6 tasks registradas. Horarios (BRT, seg-sex):"
Write-Host "  08:00  InvestimentosAI-Radar"
Write-Host "  09:00  InvestimentosAI-TraderPre"
Write-Host "  10:00  InvestimentosAI-InvestingAbertura"
Write-Host "  13:00  InvestimentosAI-TraderMid"
Write-Host "  17:00  InvestimentosAI-InvestingFechamento"
Write-Host "  17:30  InvestimentosAI-TraderFechamento"
Write-Host ""
Write-Host "Runner: $RunnerPath"
Write-Host ""
Write-Host "Comandos uteis:"
Write-Host "  Listar:      Get-ScheduledTask -TaskName 'InvestimentosAI-*'"
Write-Host "  Rodar agora: Start-ScheduledTask -TaskName 'InvestimentosAI-Radar'"
Write-Host "  Pausar:      Get-ScheduledTask -TaskName 'InvestimentosAI-*' | Disable-ScheduledTask"
Write-Host "  Remover:     Get-ScheduledTask -TaskName 'InvestimentosAI-*' | Unregister-ScheduledTask -Confirm:`$false"
