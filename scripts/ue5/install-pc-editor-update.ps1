param(
    [string]$SourceRoot = $env:GITHUB_WORKSPACE,
    [string]$EngineRoot = $env:UE_ROOT,
    [string]$Commit = $env:GITHUB_SHA,
    [Parameter(Mandatory=$true)][string]$ValidationDir,
    [string]$BuildValidationDir,
    [ValidateSet('/Game/Maps/ANOMALIA_Archipelago_v2','/Game/Maps/ANOMALIA_Inhabited_v2')][string]$MapPackage='/Game/Maps/ANOMALIA_Archipelago_v2'
)
$ErrorActionPreference = 'Stop'
$report = @{state='FAILED';commit=$Commit;packagedGame=$false;editorLaunchTested=$false;startupAfterRebootTested=$false}
try {
    if ($Commit -notmatch '^[0-9a-f]{40}$') { throw 'A full source commit is required.' }
    $SourceRoot = [IO.Path]::GetFullPath($SourceRoot)
    $proofFile = Join-Path $ValidationDir 'real-graphics/capture-process-report.json'
    $proof = Get-Content -LiteralPath $proofFile -Raw | ConvertFrom-Json
    if ($proof.state -ne 'REOPENED_GPU_CAPTURES_AWAITING_REVIEW' -or $proof.sourceCommit -ne $Commit) { throw 'A fresh successful GPU reopen proof is required.' }
    if (-not $BuildValidationDir) { $BuildValidationDir=$ValidationDir }
    if ($MapPackage -eq '/Game/Maps/ANOMALIA_Inhabited_v2' -and $proof.mapPackage -ne $MapPackage) { throw 'GPU proof does not cover the populated world.' }
    $native = Get-Content -LiteralPath (Join-Path $BuildValidationDir 'report.json') -Raw | ConvertFrom-Json
    if ($native.compilation -ne 'passed') { throw 'Native compilation is not validated.' }
    $verify = @($proof.phases | Where-Object { $_.phase -eq 'verify' })
    if ($verify.Count -ne 1 -or $verify[0].exitCode -ne 0 -or $verify[0].nativeReport.renderResourceRefresh.landscapesLayerMergeRequested -ne 0) { throw 'Independent reopen is not validated.' }
    $source = Join-Path $SourceRoot 'unreal'
    $editor = Join-Path $EngineRoot 'Engine/Binaries/Win64/UnrealEditor.exe'
    if (-not (Test-Path -LiteralPath $editor)) { throw 'Installed Unreal Editor is required for this development preview.' }
    $base = Join-Path $env:LOCALAPPDATA 'CMD/ANOMALIA-UE5'
    $owner = Join-Path $base 'owner.json'
    if (Test-Path -LiteralPath $base) {
        if (-not (Test-Path -LiteralPath $owner)) { throw 'Existing unowned install directory preserved.' }
        $identity = Get-Content -LiteralPath $owner -Raw | ConvertFrom-Json
        if ($identity.product -ne 'ANOMALIA-UE5-EDITOR-v1') { throw 'Unrecognized install preserved.' }
    } else {
        New-Item -ItemType Directory -Path $base | Out-Null
        @{product='ANOMALIA-UE5-EDITOR-v1'} | ConvertTo-Json | Set-Content -LiteralPath $owner -Encoding UTF8
    }
    $existingProfiles=@{}
    $profileRoot=Join-Path $base 'userdata/Saved/Servers'
    if (Test-Path -LiteralPath $profileRoot) {
        foreach ($file in Get-ChildItem -LiteralPath $profileRoot -File -Recurse) { $existingProfiles[$file.FullName]=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash }
    }
    $versions = Join-Path $base 'versions';New-Item -ItemType Directory -Path $versions -Force | Out-Null
    $target = Join-Path $versions $Commit
    $baseVersion=$null
    $installedActivePath=Join-Path $base 'active.json'
    if(Test-Path -LiteralPath $installedActivePath){
        $installedActive=Get-Content -LiteralPath $installedActivePath -Raw|ConvertFrom-Json
        if($installedActive.project){
            $candidateBase=[IO.Path]::GetFullPath((Split-Path ([string]$installedActive.project) -Parent))
            $versionsFull=[IO.Path]::GetFullPath($versions)
            if($candidateBase.StartsWith($versionsFull+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -and (Test-Path -LiteralPath $candidateBase -PathType Container)){$baseVersion=$candidateBase}
        }
    }
    $critical = @('AnomaliaPrimeval.uproject','Binaries/Win64/UnrealEditor-AnomaliaPrimeval.dll',('Content/'+$MapPackage.Substring(6)+'.umap'),'Config/DefaultEngine.ini')
    if (-not (Test-Path -LiteralPath $target)) {
        $stage = Join-Path $versions ('.staging-' + [Guid]::NewGuid().ToString('N'))
        . (Join-Path $SourceRoot 'scripts/ue5/differential-version-store.ps1')
        $diff=Invoke-AnomaliaDifferentialVersionStage -SourceRoot $source -StagePath $stage -BaseVersionRoot $baseVersion -ExcludePaths @('Saved','Intermediate','DerivedDataCache','.vs')
        $report.differentialInstall=$diff
        foreach ($relative in $critical) {
            $from=Join-Path $source $relative;$to=Join-Path $stage $relative
            if (-not (Test-Path -LiteralPath $from) -or -not (Test-Path -LiteralPath $to)) { throw "Missing required project file: $relative" }
            if ((Get-FileHash -LiteralPath $from -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $to -Algorithm SHA256).Hash) { throw "Copied file mismatch: $relative" }
        }
        # Saved/Servers remains shared across versions. Import missing files only.
        $saved = Join-Path $base 'userdata/Saved';New-Item -ItemType Directory -Path $saved -Force | Out-Null
        foreach ($group in @('Servers','Config','SaveGames','Profiles','Worlds','Maps')) {
        $sourceServers=Join-Path $source ('Saved/'+$group)
        if (Test-Path -LiteralPath $sourceServers) {
            foreach ($file in Get-ChildItem -LiteralPath $sourceServers -File -Recurse) {
                $relative=$file.FullName.Substring($sourceServers.Length).TrimStart('\','/')
                $dest=Join-Path (Join-Path $saved $group) $relative
                if (-not (Test-Path -LiteralPath $dest)) {
                    New-Item -ItemType Directory -Path (Split-Path -Parent $dest) -Force | Out-Null
                    Copy-Item -LiteralPath $file.FullName -Destination $dest
                }
            }
        }
        }
        New-Item -ItemType Junction -Path (Join-Path $stage 'Saved') -Target $saved | Out-Null
        Move-Item -LiteralPath $stage -Destination $target
    }
    foreach ($relative in $critical) { if (-not (Test-Path -LiteralPath (Join-Path $target $relative))) { throw 'Existing version is incomplete; preserved without activation.' } }
    $bootstrap = Join-Path $base 'bootstrap';New-Item -ItemType Directory -Path $bootstrap -Force | Out-Null
    $ownerState=Get-Content -LiteralPath $owner -Raw | ConvertFrom-Json
    $newHashes=@{}
    foreach ($name in @('Launch-AnomaliaUE5.ps1','Launch-AnomaliaUE5.vbs')) {
        $from=Join-Path $SourceRoot "distribution/windows-editor/$name";$to=Join-Path $bootstrap $name
        $newHash=(Get-FileHash -LiteralPath $from -Algorithm SHA256).Hash
        if (Test-Path -LiteralPath $to) {
            $currentHash=(Get-FileHash -LiteralPath $to -Algorithm SHA256).Hash
            $registered=$null
            if ($null -ne $ownerState.bootstrapSHA) { $registered=$ownerState.bootstrapSHA.$name }
            # Accept only registered bytes or this exact first shipped launcher.
            $firstShipped=if ($name -eq 'Launch-AnomaliaUE5.ps1') { @('4F47639732D67BFEF9FAEADF612523F257631816E5FC6DAC63C17DF66533E7CE','479DF1FA241DED7B2AEB352736322C41DFDF26D5F20685ADEF892E611B223105') } else { @($newHash) }
            if ($currentHash -ne $newHash -and $currentHash -ne $registered -and $firstShipped -notcontains $currentHash) { throw 'Modified launcher preserved; inspect before updating it.' }
            if ($currentHash -ne $newHash) {
                $historyDir=Join-Path $base ('bootstrap-history/'+[Guid]::NewGuid().ToString('N'));New-Item -ItemType Directory -Path $historyDir -Force | Out-Null
                Copy-Item -LiteralPath $to -Destination (Join-Path $historyDir $name)
                $newFile=Join-Path $bootstrap ([Guid]::NewGuid().ToString('N')+'.tmp')
                Copy-Item -LiteralPath $from -Destination $newFile
                [IO.File]::Replace($newFile,$to,(Join-Path $historyDir ($name+'.replaced')))
            }
        } else { Copy-Item -LiteralPath $from -Destination $to }
        $newHashes[$name]=$newHash
    }
    $ownerState | Add-Member -MemberType NoteProperty -Name bootstrapSHA -Value $newHashes -Force
    $ownerTemp=Join-Path $base ([Guid]::NewGuid().ToString('N')+'.owner.json')
    $ownerState | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ownerTemp -Encoding UTF8
    $ownerHistory=Join-Path $base 'owner-history';New-Item -ItemType Directory -Path $ownerHistory -Force | Out-Null
    [IO.File]::Replace($ownerTemp,$owner,(Join-Path $ownerHistory ([Guid]::NewGuid().ToString('N')+'.json')))
    $env:ANOMALIA_EXPECTED_SAVED=Join-Path $base 'userdata/Saved'
    $env:ANOMALIA_PC_UPDATE_REPORT=Join-Path $ValidationDir 'pc-editor-open-probe.json'
    $enginePython=Join-Path $EngineRoot 'Engine/Binaries/ThirdParty/Python3/Win64/python.exe'
    $copiedProject=Join-Path $target 'AnomaliaPrimeval.uproject'
    & $enginePython (Join-Path $SourceRoot 'scripts/ue5/verify-installed-project.py') --engine-root $EngineRoot --project $copiedProject --saved $env:ANOMALIA_EXPECTED_SAVED --output $ValidationDir --map $MapPackage
    if ($LASTEXITCODE -ne 0) { throw 'Copied project native process verification failed; inspect pc-editor-open-process.json.' }
    $opened=Get-Content -LiteralPath $env:ANOMALIA_PC_UPDATE_REPORT -Raw | ConvertFrom-Json
    if ($opened.state -ne 'COPIED_EDITOR_PROJECT_OPENED_HEADLESS') { throw 'Copied project or shared saves failed validation.' }
    $report.installedProjectHeadlessOpenTested=$true
    $report.editorLaunchTested=$true
    $report.installedProjectDX11SM5Tested=$true
    $active=@{state='VALIDATED_EDITOR_PROJECT_INSTALLED';commit=$Commit;project=(Join-Path $target 'AnomaliaPrimeval.uproject');engineRoot=$EngineRoot;mapPackage=$MapPackage;userData=(Join-Path $base 'userdata');validation=$proofFile}
    $temp=Join-Path $base ('active-'+[Guid]::NewGuid().ToString('N')+'.json')
    $active | ConvertTo-Json | Set-Content -LiteralPath $temp -Encoding UTF8
    $current=Join-Path $base 'active.json'
    if (Test-Path -LiteralPath $current) {
        $history=Join-Path $base 'history';New-Item -ItemType Directory -Path $history -Force | Out-Null
        [IO.File]::Replace($temp,$current,(Join-Path $history ([Guid]::NewGuid().ToString('N')+'.json')))
    } else { Move-Item -LiteralPath $temp -Destination $current }
    $shell = New-Object -ComObject WScript.Shell
    $desktop = [Environment]::GetFolderPath('Desktop')
    $link=Join-Path $desktop 'ANOMALIA - Unreal.lnk'
    $wscript=Join-Path $env:WINDIR 'System32/wscript.exe'
    $launcher=Join-Path $bootstrap 'Launch-AnomaliaUE5.vbs'
    if (Test-Path -LiteralPath $link) {
        $existing=$shell.CreateShortcut($link)
        if ($existing.Arguments -ne ('"'+$launcher+'"')) { throw 'Existing unrelated desktop shortcut preserved.' }
    } else {
        $shortcut=$shell.CreateShortcut($link);$shortcut.TargetPath=$wscript;$shortcut.Arguments='"'+$launcher+'"';$shortcut.WorkingDirectory=$base;$shortcut.Description='ANOMALIA — projet Unreal mis à jour après validation';$shortcut.IconLocation=$editor+',0';$shortcut.Save()
    }
    # Restart the existing trusted repository runner at Windows sign-in; stop none.
    $runnerRoot=([IO.Path]::GetFullPath((Join-Path $env:RUNNER_WORKSPACE '../..'))).TrimEnd([IO.Path]::DirectorySeparatorChar)
    if (-not (Test-Path -LiteralPath (Join-Path $runnerRoot 'run.cmd'))) { throw 'Existing runner root not found.' }
    $runnerScript=Join-Path $bootstrap 'Start-AnomaliaRunner.vbs'
    $vbRoot=$runnerRoot.Replace('"','""')
    $vb=@"
Option Explicit
Dim shell, service, processes, proc, runnerRoot
runnerRoot = "$vbRoot"
Set service = GetObject("winmgmts:\\.\root\cimv2")
Set processes = service.ExecQuery("SELECT ExecutablePath FROM Win32_Process WHERE Name='Runner.Listener.exe'")
For Each proc In processes
    If Not IsNull(proc.ExecutablePath) Then
        If LCase(proc.ExecutablePath) = LCase(runnerRoot & "\bin\Runner.Listener.exe") Then WScript.Quit 0
    Else
        WScript.Quit 0
    End If
Next
Set shell = CreateObject("WScript.Shell")
shell.CurrentDirectory = runnerRoot
shell.Run Chr(34) & runnerRoot & "\run.cmd" & Chr(34), 0, False
"@
    if (Test-Path -LiteralPath $runnerScript) {
        if ((Get-Content -LiteralPath $runnerScript -Raw).Trim() -ne $vb.Trim()) { throw 'Modified runner bootstrap preserved.' }
    } else { Set-Content -LiteralPath $runnerScript -Value $vb -Encoding ASCII }
    $startupLink=Join-Path ([Environment]::GetFolderPath('Startup')) 'ANOMALIA - mises a jour.lnk'
    if (Test-Path -LiteralPath $startupLink) {
        if ($shell.CreateShortcut($startupLink).Arguments -ne ('"'+$runnerScript+'"')) { throw 'Unrelated startup shortcut preserved.' }
    } else {
        $start=$shell.CreateShortcut($startupLink);$start.TargetPath=$wscript;$start.Arguments='"'+$runnerScript+'"';$start.WorkingDirectory=$runnerRoot;$start.Save()
    }
    $readback=Get-Content -LiteralPath $current -Raw | ConvertFrom-Json
    if ($readback.commit -ne $Commit -or $shell.CreateShortcut($link).Arguments -ne ('"'+$launcher+'"')) { throw 'Installation readback failed.' }
    # Execute bootstrap while the runner is already present: must exit without duplicate.
    $listenersBefore=@(Get-Process -Name Runner.Listener -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id | Sort-Object)
    if ($listenersBefore.Count -eq 0) { throw 'No existing runner listener observed; bootstrap probe refused.' }
    & $enginePython -c 'import subprocess,sys; sys.exit(subprocess.run([sys.argv[1],sys.argv[2]],timeout=20).returncode)' $wscript $runnerScript
    if ($LASTEXITCODE -ne 0) { throw 'Runner bootstrap probe failed.' }
    $listenersAfter=@(Get-Process -Name Runner.Listener -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id | Sort-Object)
    if (Compare-Object -ReferenceObject $listenersBefore -DifferenceObject $listenersAfter) { throw 'Runner listener set changed during bootstrap probe.' }
    $report.runnerListenerIdsUnchanged=$true
    foreach ($path in $existingProfiles.Keys) {
        if (-not (Test-Path -LiteralPath $path) -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $existingProfiles[$path]) { throw 'Existing server profile changed during update.' }
    }
    $report.existingServerFilesPreserved=$existingProfiles.Count
    $report.state='EDITOR_PROJECT_UPDATE_INSTALLED';$report.installRoot=$base;$report.project=$readback.project;$report.shortcut=$link;$report.startupShortcut=$startupLink;$report.runnerBootstrapExistingSessionTested=$true
} catch { $report.error=$_.Exception.Message }
New-Item -ItemType Directory -Path $ValidationDir -Force | Out-Null
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $ValidationDir 'pc-editor-update.json') -Encoding UTF8
$report | ConvertTo-Json -Depth 8 | Write-Host
if ($report.state -ne 'EDITOR_PROJECT_UPDATE_INSTALLED') { exit 1 }

exit 0
