param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$root='D:\ANOMALIA\unreal'
$project=Join-Path $root 'AnomaliaPrimeval.uproject'
if(!(Test-Path -LiteralPath $project)){throw 'Actual project unavailable'}
$canonical=(Get-FileHash -LiteralPath $project -Algorithm SHA256).Hash
function ProjectRefs([string]$text) {
    @([regex]::Matches($text,'(?i)([A-Z]:[^"\r\n]*?\.uproject)') | ForEach-Object {
        $path=$_.Groups[1].Value.Trim()
        $exists=Test-Path -LiteralPath $path -PathType Leaf
        [ordered]@{path=$path;exists=$exists;projectDescriptorMatchesActual=($exists -and ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -eq $canonical))}
    })
}
$worker=Join-Path $OutputDirectory 'resolve-one-shortcut.ps1'
@'
param([string]$Shortcut,[string]$Output)
$ErrorActionPreference='Stop'
$shell=New-Object -ComObject WScript.Shell
$link=$shell.CreateShortcut($Shortcut)
$projects=@([regex]::Matches([string]$link.Arguments,'(?i)([A-Z]:[^"\r\n]*?\.uproject)') | ForEach-Object {$_.Groups[1].Value})
$launchers=@([regex]::Matches([string]$link.Arguments,'(?i)([A-Z]:[^"\r\n]*?\.(?:ps1|cmd|bat|vbs))') | ForEach-Object {$_.Groups[1].Value})
[ordered]@{TargetPath=[string]$link.TargetPath;ProjectPaths=$projects;LauncherPaths=$launchers} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $Output -Encoding utf8
'@ | Set-Content -LiteralPath $worker -Encoding utf8
$shortcutCount=0
$progress=@()
function WriteProgress {
    [ordered]@{state='IDENTITY_CHECK_PROGRESS_NOT_RUNTIME_ACCEPTED';shortcutsSeen=$shortcutCount;events=$progress} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'identity-progress.json') -Encoding utf8
}
WriteProgress
$shortcuts=@()
$folders=@([Environment]::GetFolderPath('Desktop'),[Environment]::GetFolderPath('CommonDesktopDirectory')) | Select-Object -Unique
foreach($folder in $folders){
    if(!(Test-Path -LiteralPath $folder)){continue}
    foreach($file in (Get-ChildItem -LiteralPath $folder -File | Where-Object {$_.Name -match '(?i)anomalia|prigimalia'} | Sort-Object LastWriteTimeUtc -Descending)){
        if($shortcutCount -ge 24){break}
        $shortcutCount++
        $progress+=@([ordered]@{file=$file.FullName;state='READING_TARGET'})
        WriteProgress
        $row=[ordered]@{name=$file.Name;path=$file.FullName;type=$file.Extension;targetExists=$null;projects=@();nestedLaunchers=@();gameContentVersionVerified=$false}
        $text='';$target=$file.FullName
        if($file.Extension -eq '.lnk'){
            $workerOut=Join-Path $OutputDirectory ('shortcut-'+$shortcutCount+'.json')
            $child=Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',('"'+$worker+'"'),'-Shortcut',('"'+$file.FullName+'"'),'-Output',('"'+$workerOut+'"')) -PassThru -WindowStyle Hidden
            if(!$child.WaitForExit(12000)){
                $child.Kill()
                $row.shortcutReadTimedOut=$true;$shortcuts+=@($row);continue
            }
            if($child.ExitCode -ne 0 -or !(Test-Path -LiteralPath $workerOut)){
                $row.shortcutReadFailed=$true;$shortcuts+=@($row);continue
            }
            $link=Get-Content -LiteralPath $workerOut -Raw | ConvertFrom-Json
            $target=[string]$link.TargetPath
            $row.target=$target;$row.targetExists=Test-Path -LiteralPath $target
            $text=(@($link.ProjectPaths)+@($link.LauncherPaths)) -join [Environment]::NewLine
        }
        if(Test-Path -LiteralPath $target -PathType Leaf){
            $targetItem=Get-Item -LiteralPath $target
            if($targetItem.Attributes -band [IO.FileAttributes]::Offline){
                $row.cloudOnlyTargetNotHydrated=$true;$shortcuts+=@($row);continue
            }
        }
        $row.projects=@(ProjectRefs $text)
        if((Test-Path -LiteralPath $target -PathType Leaf) -and ([IO.Path]::GetExtension($target) -in @('.ps1','.cmd','.bat','.vbs'))){
            $item=Get-Item -LiteralPath $target
            if($item.Length -lt 2MB){
                $content=Get-Content -LiteralPath $target -Raw
                $row.projects+=@(ProjectRefs $content)
                $row.launcherSHA256=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
            }
        }
        # Inspect explicitly referenced launcher files; never execute them or expose full command lines.
        foreach($match in [regex]::Matches($text,'(?i)([A-Z]:[^"\r\n]*?\.(?:ps1|cmd|bat|vbs))')){
            $nested=$match.Groups[1].Value
            if((Test-Path -LiteralPath $nested -PathType Leaf) -and (Get-Item -LiteralPath $nested).Length -lt 2MB){
                $content=Get-Content -LiteralPath $nested -Raw
                $row.nestedLaunchers+=@([ordered]@{path=$nested;sha256=(Get-FileHash -LiteralPath $nested -Algorithm SHA256).Hash;projects=@(ProjectRefs $content)})
            }
        }
        if((Test-Path -LiteralPath $target -PathType Leaf) -and [IO.Path]::GetExtension($target) -eq '.exe'){
            $item=Get-Item -LiteralPath $target
            $binaryHash=$null
            if($item.Length -le 32MB -and !($item.Attributes -band [IO.FileAttributes]::Offline)){$binaryHash=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash}
            $row.executable=[ordered]@{path=$target;product=$item.VersionInfo.ProductName;version=$item.VersionInfo.FileVersion;sha256=$binaryHash;bytes=$item.Length;electronResourcesPresent=(Test-Path -LiteralPath (Join-Path $item.DirectoryName 'resources/app.asar'))}
        }
        $shortcuts+=@($row)
        $progress+=@([ordered]@{file=$file.FullName;state='TARGET_RECORDED'})
        WriteProgress
    }
}
$processes=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -match '^(UnrealEditor(?:-Cmd)?|AnomaliaPrimeval(?:-Win64-Development)?|AnomaliaZPrigimalia(?:-Win64-Development)?)\.exe$'} | ForEach-Object {
    [ordered]@{name=$_.Name;pid=$_.ProcessId;executablePath=$_.ExecutablePath;projects=@(ProjectRefs ([string]$_.CommandLine))}
})
$movies=@()
$movieRoot=Join-Path $root 'Content/Movies'
if(Test-Path -LiteralPath $movieRoot){
    $movies=@(Get-ChildItem -LiteralPath $movieRoot -File -Recurse | Where-Object {$_.Extension -in @('.mp4','.webm','.mov','.wmv','.bk2')} | Select-Object -First 100 | ForEach-Object {[ordered]@{path=$_.FullName;bytes=$_.Length;lastWriteUtc=$_.LastWriteTimeUtc;playbackVerified=$false}})
}
$startupMovies=@()
$startupMaps=@()
foreach($name in @('DefaultEngine.ini','DefaultGame.ini')){
    $path=Join-Path $root ('Config/'+$name)
    if(Test-Path -LiteralPath $path){
        $startupMovies+=@(Get-Content -LiteralPath $path | Where-Object {$_ -match '^\s*[+]?StartupMovies\s*='})
        $startupMaps+=@(Get-Content -LiteralPath $path | Where-Object {$_ -match '^\s*(GameDefaultMap|EditorStartupMap|GlobalDefaultGameMode)\s*='})
    }
}
$source=Join-Path $root 'Source/AnomaliaPrimeval'
$menus=@()
if(Test-Path -LiteralPath $source){
    foreach($file in (Get-ChildItem -LiteralPath $source -Filter '*SessionWidget.cpp' -File)){
        $text=Get-Content -LiteralPath $file.FullName -Raw
        $menus+=@([ordered]@{path=$file.FullName;sha256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash;startupIntroExplicitlyDisabled=($text -match 'bStartupIntro\s*=\s*false');usesMediaPlayer=($text -match 'MediaPlayer|MoviePlayer');widgetPlaybackTested=$false})
    }
}
$report=[ordered]@{state='INSTALLED_GAME_IDENTITY_AND_INTRO_CONFIGURATION_INSPECTED_NOT_RUNTIME_ACCEPTED';actualProject=$project;projectDescriptorSHA256=$canonical;shortcuts=$shortcuts;runningProcesses=$processes;startupMaps=$startupMaps;startupMovies=$startupMovies;movieFiles=$movies;menuSources=$menus;menuButtonsTested=$false;introPlaybackTested=$false;packagedGameMatchesCurrentAssetsVerified=$false;filesChanged=0;CFreeBytes=(Get-PSDrive C).Free;DFreeBytes=(Get-PSDrive D).Free}
$report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'installed-game-menu-intro.json') -Encoding utf8
Write-Output ('IDENTITY_CHECK_SHORTCUTS='+$shortcuts.Count+' MOVIES='+$movies.Count+' NO_GAMEPLAY_ACCEPTANCE=true')
