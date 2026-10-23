param([Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference = 'Stop'
$report = @{state='FAILED';events=@();scope='UnrealEditor-Cmd.exe Application Error events only'}
try {
    $events = @(Get-WinEvent -FilterHashtable @{LogName='Application';Id=1000;StartTime=(Get-Date).AddHours(-2)} -ErrorAction SilentlyContinue)
    foreach ($event in $events) {
        [xml]$xml = $event.ToXml()
        $fields = @{}
        foreach ($entry in $xml.Event.EventData.Data) { $fields[[string]$entry.Name]=[string]$entry.'#text' }
        if ($fields['AppName'] -ne 'UnrealEditor-Cmd.exe') { continue }
        $item = @{timeUtc=$event.TimeCreated.ToUniversalTime().ToString('o')}
        foreach ($name in @('AppName','AppVersion','ModuleName','ModuleVersion','ExceptionCode','FaultingOffset','ModulePath')) { $item[$name]=$fields[$name] }
        $report.events += $item
        if ($report.events.Count -ge 10) { break }
    }
    $report.state='COLLECTED_EDITOR_CRASH_MODULES_ONLY'
} catch { $report.error=$_.Exception.Message }
$parent = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Path $parent -Force | Out-Null
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
$report | ConvertTo-Json -Depth 8 | Write-Output
# Read-only diagnostic failure must not mask the existing native test result.
exit 0
