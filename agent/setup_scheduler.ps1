# Registra o agente de investimentos no Windows Task Scheduler
# Executa de hora em hora das 10h as 18h, segunda a sexta
# Rodar uma vez como Administrador: .\agent\setup_scheduler.ps1

$TaskName = "InvestimentosAI-Agente"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ScriptPath = Join-Path $ProjectRoot "agent\run_experiment.ps1"

# Remove task existente se houver
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Task anterior removida."
}

$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NonInteractive -ExecutionPolicy Bypass -File `"$ScriptPath`"" `
    -WorkingDirectory $ProjectRoot

# Trigger: seg-sex, das 10h ate 18h, repetindo a cada 1 hora
$Trigger = New-ScheduledTaskTrigger -Weekly `
    -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday `
    -At "10:00"

$Trigger.RepetitionInterval = [TimeSpan]::FromHours(1)
$Trigger.RepetitionDuration = [TimeSpan]::FromHours(8)   # 10h -> 18h

$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit ([TimeSpan]::FromMinutes(20)) `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable

$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Agente de investimentos B3 — roda horario 10h-18h seg-sex" | Out-Null

Write-Host ""
Write-Host "Task registrada: '$TaskName'"
Write-Host "Script: $ScriptPath"
Write-Host "Horario: 10h-18h, seg-sex, a cada 1 hora"
Write-Host ""
Write-Host "Comandos uteis:"
Write-Host "  Ver task:     Get-ScheduledTask -TaskName '$TaskName'"
Write-Host "  Rodar agora:  Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "  Pausar:       Disable-ScheduledTask -TaskName '$TaskName'"
Write-Host "  Remover:      Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
