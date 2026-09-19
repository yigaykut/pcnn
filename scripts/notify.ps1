<#
.SYNOPSIS
  Show one Windows toast for the nightly PCNN run.

.DESCRIPTION
  Uses the WinRT toast API directly so nothing has to be installed. The toast is
  fire-and-forget: it is handed to the shell and this script exits, so nothing
  stays resident. Clicking it opens the rendered network in the default browser.

  Notifications can be off, or Focus Assist can be on, or the API can be absent
  on a stripped-down Windows. None of that is worth failing a nightly run over,
  so every failure here is swallowed and reported on stdout only.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\notify.ps1 `
      -Line1 "39 facts, 21 days waiting" -Line2 "nothing needs attention" `
      -Link "C:\...\output\network.html"
#>
[CmdletBinding()]
param(
    [string]$Line1 = "",
    [string]$Line2 = "",
    [string]$Link = "",
    [string]$Title = "PCNN"
)

try {
    [void][Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]
    [void][Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom, ContentType = WindowsRuntime]
} catch {
    Write-Output "toast unavailable: $($_.Exception.Message)"
    exit 0
}

function Esc([string]$s) {
    if (-not $s) { return "" }
    $s.Replace("&", "&amp;").Replace("<", "&lt;").Replace(">", "&gt;").Replace('"', "&quot;")
}

# protocol activation opens the file with whatever handles it, normally the
# browser; a bare file path is not a valid launch target
$launch = ""
if ($Link) {
    $uri = ([uri]"file:///$($Link -replace '\\','/')").AbsoluteUri
    $launch = " activationType=`"protocol`" launch=`"$(Esc $uri)`""
}

$xml = @"
<toast$launch>
  <visual>
    <binding template="ToastGeneric">
      <text>$(Esc $Title)</text>
      <text>$(Esc $Line1)</text>
      <text>$(Esc $Line2)</text>
    </binding>
  </visual>
</toast>
"@

try {
    $doc = New-Object Windows.Data.Xml.Dom.XmlDocument
    $doc.LoadXml($xml)
    $toast = New-Object Windows.UI.Notifications.ToastNotification $doc
    # PowerShell's own registered AppID; using it avoids having to install a
    # shortcut just to own a notification
    $appId = "{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe"
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($appId).Show($toast)
    Write-Output "toast shown"
} catch {
    Write-Output "toast failed: $($_.Exception.Message)"
}
exit 0
