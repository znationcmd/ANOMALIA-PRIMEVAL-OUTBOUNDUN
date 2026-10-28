[CmdletBinding()]
param([switch]$Apply)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'

$restoreReportPath='C:\ANOMALIA-Validation\Reports\restore-verification-40774337425\restore-report.json'
$smokeReportPath='C:\ANOMALIA-Validation\Reports\installed-launcher-smoke-40778503900\launcher-smoke.json'
$backupRoot='D:\ANOMALIA-Backups\pre-differential-40767016246'
$backupManifestPath=Join-Path $backupRoot 'backup-manifest.json'
if(!(Test-Path -LiteralPath $restoreReportPath)){throw 'Verified restore report is missing; refusing cleanup.'}
if(!(Test-Path -LiteralPath $smokeReportPath)){throw 'Successful launcher smoke report is missing; refusing cleanup.'}
if(!(Test-Path -LiteralPath $backupManifestPath)){throw 'D: backup manifest is missing; refusing cleanup.'}
$restore=Get-Content -LiteralPath $restoreReportPath -Raw|ConvertFrom-Json
$smoke=Get-Content -LiteralPath $smokeReportPath -Raw|ConvertFrom-Json
$backup=Get-Content -LiteralPath $backupManifestPath -Raw|ConvertFrom-Json
if($restore.state -ne 'ACTIVE_VERSIONS_AND_USERDATA_SHA256_RESTORE_VERIFIED'){throw 'D: restore verification state is not successful.'}
if($smoke.state -ne 'INSTALLED_LAUNCHER_PROCESS_SMOKES_PASSED'){throw 'Launcher smoke state is not successful.'}
$requiredLaunchers=@('Editor','Tools','Jouer','UnrealEditor')
foreach($name in $requiredLaunchers){
    $result=@($smoke.results|Where-Object{$_.name -eq $name})
    if($result.Count -ne 1 -or !$result[0].processStarted -or !$result[0].windowVisible){throw "Launcher not visibly started: $name"}
}
if($backup.items.Count -lt 2){throw 'Expected active game/editor backups missing; refusing cleanup.'}
if(!(Test-Path -LiteralPath 'D:\')){throw 'D: is unavailable; refusing cleanup.'}

$profile=$env:USERPROFILE
$local=Join-Path $env:LOCALAPPDATA 'CMD'
$productDefs=@(
    @{name='ANOMALIA-UE5';activeField='project';pattern='^[0-9a-f]{40}$'},
    @{name='ANOMALIA-Windows';activeField='executable';pattern='^[0-9a-f]{12,40}-[0-9a-f]{8}$'}
)
$shell=New-Object -ComObject WScript.Shell
$shortcutRoots=@(
    [Environment]::GetFolderPath('Desktop'),
    [Environment]::GetFolderPath('CommonDesktopDirectory'),
    [Environment]::GetFolderPath('StartMenu'),
    (Join-Path $env:ProgramData 'Microsoft\Windows\Start Menu\Programs')
)
$shortcutTexts=@()
foreach($root in $shortcutRoots){
    if(Test-Path -LiteralPath $root){
        foreach($link in Get-ChildItem -LiteralPath $root -Filter '*.lnk' -Recurse -File -ErrorAction SilentlyContinue){
            $lnk=$shell.CreateShortcut($link.FullName)
            $shortcutTexts+=(([string]$lnk.TargetPath)+' '+[string]$lnk.Arguments+' '+[string]$lnk.WorkingDirectory)
        }
    }
}
$report=[ordered]@{
    state='FAILED'
    machine=$env:COMPUTERNAME
    restoreReport=$restoreReportPath
    launcherSmokeReport=$smokeReportPath
    backupRoot=$backupRoot
    cFreeBytesBefore=[int64](Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'").FreeSpace
    dFreeBytesBefore=[int64](Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='D:'").FreeSpace
    products=@()
    removed=@()
    planned=@()
    preserved=@()
    skipped=@()
}
$manifestHashes=@{}
$allRemovals=@()
foreach($def in $productDefs){
    $base=Join-Path $local $def.name
    $activePath=Join-Path $base 'active.json'
    $versions=Join-Path $base 'versions'
    if(!(Test-Path -LiteralPath $activePath) -or !(Test-Path -LiteralPath $versions)){throw "Active manifest/version root missing: $($def.name)"}
    $manifestHashes[$activePath]=(Get-FileHash -LiteralPath $activePath -Algorithm SHA256).Hash
    $active=Get-Content -LiteralPath $activePath -Raw|ConvertFrom-Json
    $activeValue=[string]$active.($def.activeField)
    if([string]::IsNullOrWhiteSpace($activeValue)){throw "Active field $($def.activeField) missing in $($def.name)"}
    $activeDir=[IO.Path]::GetFullPath((Split-Path $activeValue -Parent)).TrimEnd([char]92)
    $versionsFull=[IO.Path]::GetFullPath($versions).TrimEnd([char]92)
    if(!$activeDir.StartsWith($versionsFull+'\',[StringComparison]::OrdinalIgnoreCase)){throw "Active target escapes versions root: $($def.name)"}
    if(!(Test-Path -LiteralPath $activeDir -PathType Container)){throw "Active version folder missing: $activeDir"}
    $dirs=@(Get-ChildItem -LiteralPath $versions -Directory -Force)
    $inactive=@($dirs|Where-Object{[IO.Path]::GetFullPath($_.FullName).TrimEnd([char]92) -ine $activeDir -and $_.Name -match $def.pattern})
    $rollback=$null
    if($inactive.Count -gt 0){$rollback=$inactive|Sort-Object LastWriteTimeUtc -Descending|Select-Object -First 1}
    $productReport=[ordered]@{product=$def.name;activeFolder=(Split-Path $activeDir -Leaf);versionFoldersBefore=$dirs.Count;rollbackPreserved=if($rollback){$rollback.Name}else{$null};candidates=@()}
    foreach($candidate in $inactive){
        $path=[IO.Path]::GetFullPath($candidate.FullName).TrimEnd([char]92)
        if($rollback -and $candidate.FullName -ieq $rollback.FullName){
            $entry=@{folder=$candidate.Name;status='preserved-rollback';logicalBytes=0L}
            $report.preserved+=@{product=$def.name;folder=$candidate.Name;reason='latest inactive rollback'}
            $productReport.candidates+=,$entry
            continue
        }
        if($shortcutTexts -match [regex]::Escape($path)){
            $report.skipped+=@{product=$def.name;folder=$candidate.Name;reason='referenced by a Windows shortcut'}
            $productReport.candidates+=,@{folder=$candidate.Name;status='skipped-shortcut-reference'}
            continue
        }
        $tree=@(Get-ChildItem -LiteralPath $path -Recurse -Force -ErrorAction Stop)
        $reparse=@($tree|Where-Object{($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0})
        if(($candidate.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $reparse.Count -gt 0){
            $report.skipped+=@{product=$def.name;folder=$candidate.Name;reason='contains a reparse point'}
            $productReport.candidates+=,@{folder=$candidate.Name;status='skipped-reparse-point'}
            continue
        }
        $userdata=@($tree|Where-Object{$_.PSIsContainer -and $_.Name -in @('Saved','SaveGames','Saves','UserData','Profiles','PlayerData')})
        if($userdata.Count -gt 0){
            $report.skipped+=@{product=$def.name;folder=$candidate.Name;reason='contains user/save data';paths=@($userdata|ForEach-Object{$_.FullName})}
            $productReport.candidates+=,@{folder=$candidate.Name;status='skipped-user-data';preservedPaths=@($userdata|ForEach-Object{$_.FullName})}
            continue
        }
        $bytes=0L
        foreach($file in @($tree|Where-Object{-not $_.PSIsContainer})){ $bytes+=[int64]$file.Length }
        $entry=@{product=$def.name;folder=$candidate.Name;path=$path;logicalBytes=$bytes}
        $allRemovals+=,$entry
        $productReport.candidates+=,@{folder=$candidate.Name;status='eligible';logicalBytes=$bytes}
    }
    $productReport.versionFoldersAfterPlanned=$dirs.Count-@($productReport.candidates|Where-Object{$_.status -eq 'eligible'}).Count
    $report.products+=,$productReport
}
if($allRemovals.Count -eq 0){$report.state='NO_SAFE_OLD_VERSIONS_TO_REMOVE'}elseif(-not $Apply){$report.state='CLEANUP_PLAN_ONLY';$report.planned=$allRemovals}else{
    foreach($entry in $allRemovals){
        $p=[IO.Path]::GetFullPath($entry.path).TrimEnd([char]92)
        $root=[IO.Path]::GetFullPath((Join-Path (Join-Path $local $entry.product) 'versions')).TrimEnd([char]92)
        if(!$p.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)){throw "Deletion target outside managed versions root: $p"}
        if(!(Test-Path -LiteralPath $p -PathType Container)){throw "Deletion target disappeared: $p"}
        Remove-Item -LiteralPath $p -Recurse -Force
        if(Test-Path -LiteralPath $p){throw "Deletion did not complete: $p"}
        $report.removed+=@{product=$entry.product;folder=$entry.folder;logicalBytes=$entry.logicalBytes}
    }
    foreach($manifest in $manifestHashes.Keys){
        if((Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash -ne $manifestHashes[$manifest]){throw "Active pointer changed during cleanup: $manifest"}
    }
    $report.state='INACTIVE_VERSIONS_CLEANED'
}
$report.cFreeBytesAfter=[int64](Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'").FreeSpace
$report.dFreeBytesAfter=[int64](Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='D:'").FreeSpace
$report.cDriveRecoveredBytes=[int64]($report.cFreeBytesAfter-$report.cFreeBytesBefore)
$report.cDriveRecoveredGiB=[math]::Round($report.cDriveRecoveredBytes/1GB,3)
$output='C:\ANOMALIA-Validation\Reports\version-cleanup-'+$env:GITHUB_RUN_ID
New-Item -ItemType Directory -Path $output -Force|Out-Null
$report|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $output 'cleanup-report.json') -Encoding UTF8
$report|ConvertTo-Json -Depth 12|Write-Output
