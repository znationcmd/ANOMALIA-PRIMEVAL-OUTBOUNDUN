param([Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference='Stop'
$report=@{state='READ_ONLY_INSTALLATION_DIAGNOSTIC';sourceCommit=$env:GITHUB_SHA;installations=@();shortcuts=@();running=@()}
foreach($entry in @(@('CMD/ANOMALIA-Windows','ANOMALIA-WINDOWS-TEST-v1'),@('CMD/ANOMALIA-UE5','ANOMALIA-UE5-EDITOR-v1'))) {
    $root=Join-Path $env:LOCALAPPDATA $entry[0]
    $row=@{product=$entry[1];exists=(Test-Path -LiteralPath $root);ownerVerified=$false}
    try {
        if($row.exists) {
            $owner=Get-Content -LiteralPath (Join-Path $root 'owner.json') -Raw | ConvertFrom-Json
            $row.ownerVerified=($owner.product -eq $entry[1])
            if($row.ownerVerified) {
                $row.root=$root
                if(Test-Path -LiteralPath (Join-Path $root 'active.json')) {
                    $active=Get-Content -LiteralPath (Join-Path $root 'active.json') -Raw | ConvertFrom-Json
                    $row.active=$active
                    foreach($field in @('executable','project')) {
                        $path=[string]$active.$field
                        if($path -and (Test-Path -LiteralPath $path)) {
                            $file=Get-Item -LiteralPath $path
                            $row[$field+'Metadata']=@{exists=$true;bytes=$file.Length;modifiedUtc=$file.LastWriteTimeUtc.ToString('o');sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash}
                        }
                    }
                }
            }
        }
    } catch {$row.error=$_.Exception.Message}
    $report.installations+=,$row
}
$shell=New-Object -ComObject WScript.Shell
foreach($folder in @([Environment]::GetFolderPath('Desktop'),[Environment]::GetFolderPath('StartMenu'))) {
    if(-not (Test-Path -LiteralPath $folder)) {continue}
    foreach($file in Get-ChildItem -LiteralPath $folder -Filter '*ANOMALIA*.lnk' -File -Recurse -ErrorAction SilentlyContinue) {
        $link=$shell.CreateShortcut($file.FullName)
        $report.shortcuts+=@{name=$file.Name;path=$file.FullName;target=$link.TargetPath;arguments=$link.Arguments;workingDirectory=$link.WorkingDirectory}
    }
}
foreach($name in @('AnomaliaZPrigimalia','AnomaliaZPrigimalia-Win64-Shipping','AnomaliaZPrigimalia-Win64-Development','UnrealEditor')) {
    foreach($process in Get-Process -Name $name -ErrorAction SilentlyContinue) {
        try {$report.running+=@{name=$process.ProcessName;id=$process.Id;executable=$process.Path;windowTitle=$process.MainWindowTitle}} catch {}
    }
}
New-Item -ItemType Directory -Path (Split-Path -Parent $OutputPath) -Force | Out-Null
$report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
$report | ConvertTo-Json -Depth 12 | Write-Host
