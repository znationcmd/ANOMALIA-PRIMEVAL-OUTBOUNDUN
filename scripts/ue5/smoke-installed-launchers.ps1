param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
New-Item -ItemType Directory -Path $OutputDirectory -Force|Out-Null
$shell=New-Object -ComObject WScript.Shell
$desktop=[Environment]::GetFolderPath('Desktop')
$public=[Environment]::GetFolderPath('CommonDesktopDirectory')
function Resolve-BrandShortcut([string]$folder,[string[]]$names) {
    foreach ($name in $names) {
        $candidate=Join-Path $folder $name
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    return Join-Path $folder $names[0]
}
$tests=@(
    @{name='Editor';shortcut=(Resolve-BrandShortcut $public @('ANOMALIA’Z PRIGIMALIA Editor.lnk','ANOMALIA Editor.lnk'));process='ANOMALIA Editor';timeout=20},
    @{name='Tools';shortcut=(Resolve-BrandShortcut $public @('ANOMALIA’Z PRIGIMALIA Tools.lnk','ANOMALIA Tools.lnk'));process='ANOMALIA Tools';timeout=45},
    @{name='Jouer';shortcut=(Resolve-BrandShortcut $desktop @('ANOMALIA’Z PRIGIMALIA - Jouer.lnk','ANOMALIA - Jouer.lnk'));process='AnomaliaPrimeval';timeout=180},
    @{name='UnrealEditor';shortcut=(Resolve-BrandShortcut $desktop @('ANOMALIA’Z PRIGIMALIA - Unreal.lnk','ANOMALIA - Unreal.lnk'));process='UnrealEditor';timeout=120}
)
$results=@()
foreach($test in $tests){
    if(!(Test-Path -LiteralPath $test.shortcut)){throw "Required shortcut missing: $($test.name)"}
    $before=@(Get-Process -Name $test.process -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Id)
    if($before.Count -gt 0){throw "Cannot safely test $($test.name): process already running."}
    $link=$shell.CreateShortcut($test.shortcut)
    if(!(Test-Path -LiteralPath $link.TargetPath)){throw "Launcher target missing: $($test.name)"}
    $target=Get-Item -LiteralPath $link.TargetPath
    if([string]::IsNullOrWhiteSpace([string]$link.Arguments)){
        $started=Start-Process -FilePath $link.TargetPath -WorkingDirectory $link.WorkingDirectory -PassThru
    }else{
        $started=Start-Process -FilePath $link.TargetPath -ArgumentList ([string]$link.Arguments) -WorkingDirectory $link.WorkingDirectory -PassThru
    }
    $deadline=(Get-Date).AddSeconds([int]$test.timeout);$new=@();$visible=$null
    while((Get-Date) -lt $deadline){
        Start-Sleep -Seconds 2
        $new=@(Get-Process -Name $test.process -ErrorAction SilentlyContinue|Where-Object{$_.Id -notin $before})
        $visible=@($new|Where-Object{$_.MainWindowHandle -ne 0}|Select-Object -First 1)
        if($visible.Count -gt 0){break}
        if($started.HasExited -and $new.Count -eq 0){break}
    }
    $windowTitle=''
    if($visible.Count -gt 0){$windowTitle=[string]$visible[0].MainWindowTitle}
    $result=@{name=$test.name;target=$link.TargetPath;fileVersion=$target.VersionInfo.FileVersion;processStarted=($new.Count -gt 0);windowVisible=($visible.Count -gt 0);windowTitle=$windowTitle;processCount=$new.Count}
    foreach($process in $new){try{$null=$process.CloseMainWindow()}catch{}}
    Start-Sleep -Seconds 2
    foreach($process in $new){try{$process.Refresh();if(!$process.HasExited){Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue}}catch{}}
    $result.processClosedByTest=$true
    $results+=,$result
    if(!$result.processStarted -or !$result.windowVisible){throw "Post-cleanup launcher did not show a window: $($test.name)"}
}
$report=@{state='POST_CLEANUP_LAUNCHERS_VISIBLE';machine=$env:COMPUTERNAME;results=$results;cDriveFreeBytes=[int64](Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'").FreeSpace;dDriveFreeBytes=[int64](Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='D:'").FreeSpace}
$report|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $OutputDirectory 'post-cleanup-smoke.json') -Encoding UTF8
$report|ConvertTo-Json -Depth 8|Write-Output