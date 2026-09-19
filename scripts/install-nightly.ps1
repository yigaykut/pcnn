<#
.SYNOPSIS
  Register the nightly PCNN consolidation as a Windows scheduled task.

.DESCRIPTION
  The nightly run costs nothing: merging near-duplicates, reinforcing edges,
  re-auditing and re-rendering are all plain Python. Sessions report what they
  learned in their own closing message, so there is normally nothing left for a
  model to work out. Pass -Distill to also pay a model to read the days no
  session reported on.

  A cloud-scheduled agent cannot do this job: the networks, the transcripts and
  the rendered HTML all live on this machine.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\install-nightly.ps1
  powershell -ExecutionPolicy Bypass -File scripts\install-nightly.ps1 -At 02:00
  powershell -ExecutionPolicy Bypass -File scripts\install-nightly.ps1 -Uninstall
#>
[CmdletBinding()]
param(
    [string]$At = "23:30",
    [string]$TaskName = "PCNN nightly consolidation",
    [switch]$Distill,
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

if ($Uninstall) {
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Removed scheduled task '$TaskName'."
    } else {
        Write-Host "No scheduled task named '$TaskName'."
    }
    return
}

$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) { throw "python was not found on PATH." }

$script = Join-Path $root "scripts\nightly.py"
if (-not (Test-Path $script)) { throw "Missing $script" }

$argList = @("`"$script`"")
if ($Distill) { $argList += "--distill" }

$action  = New-ScheduledTaskAction -Execute $python -Argument ($argList -join " ") -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Daily -At $At
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopIfGoingOnBatteries `
    -AllowStartIfOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 2)

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Settings $settings -Description "Merge, reweight, audit and re-render every PCNN network." | Out-Null

Write-Host "Registered '$TaskName' - runs daily at $At."
Write-Host "  command: $python $($argList -join ' ')"
Write-Host "  log:     $root\scripts\nightly.log"
Write-Host "Run it now with: Start-ScheduledTask -TaskName '$TaskName'"
