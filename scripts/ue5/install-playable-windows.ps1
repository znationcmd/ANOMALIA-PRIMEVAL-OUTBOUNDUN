param([Parameter(Mandatory=$true)][string]$ValidationDir,[string]$Commit=$env:GITHUB_SHA)
$ErrorActionPreference='Stop'
$report=@{state='FAILED';commit=$Commit;packagedGame=$true}
try {
    # Unreal resolves relative output paths from its executable, not the shell workspace.
    $ValidationDir=(Resolve-Path -LiteralPath $ValidationDir).ProviderPath
    $proof=Get-Content -LiteralPath (Join-Path $ValidationDir 'package-report.json') -Raw | ConvertFrom-Json
    if ($proof.state -ne 'PACKAGED_WINDOWS_SMOKE_PASSED' -or $proof.sourceCommit -ne $Commit) { throw 'Fresh packaged executable smoke proof required.' }
    $base=Join-Path $env:LOCALAPPDATA 'CMD/ANOMALIA-Windows'
    $owner=Join-Path $base 'owner.json'
    if (Test-Path -LiteralPath $base) {
        if (-not (Test-Path -LiteralPath $owner)) { throw 'Existing unowned install preserved.' }
        if ((Get-Content -LiteralPath $owner -Raw | ConvertFrom-Json).product -ne 'ANOMALIA-WINDOWS-TEST-v1') { throw 'Unrecognized existing install preserved.' }
    } else {
        New-Item -ItemType Directory -Path $base | Out-Null
        @{product='ANOMALIA-WINDOWS-TEST-v1'} | ConvertTo-Json | Set-Content -LiteralPath $owner -Encoding UTF8
    }
    $saved=Join-Path $base 'userdata/Saved';New-Item -ItemType Directory -Path $saved -Force | Out-Null
    $hashes=@{};foreach($f in Get-ChildItem -LiteralPath $saved -Recurse -File) { $hashes[$f.FullName]=(Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash }
    $versions=Join-Path $base 'versions';New-Item -ItemType Directory -Path $versions -Force | Out-Null
    $baseVersion=$null
    $installedActivePath=Join-Path $base 'active.json'
    if(Test-Path -LiteralPath $installedActivePath){
        $installedActive=Get-Content -LiteralPath $installedActivePath -Raw|ConvertFrom-Json
        if($installedActive.executable){
            $candidateBase=[IO.Path]::GetFullPath((Split-Path ([string]$installedActive.executable) -Parent))
            $versionsFull=[IO.Path]::GetFullPath($versions)
            if($candidateBase.StartsWith($versionsFull+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -and (Test-Path -LiteralPath $candidateBase -PathType Container)){$baseVersion=$candidateBase}
        }
    }
    # The full commit remains in active.json. A shorter unique folder leaves
    # room for native server/map/profile names and atomic-save GUID suffixes.
    $target=Join-Path $versions ($Commit.Substring(0,12)+'-'+[Guid]::NewGuid().ToString('N').Substring(0,8))
    $testSaved=Join-Path $base ('validation/'+[Guid]::NewGuid().ToString('N')+'/Saved')
    New-Item -ItemType Directory -Path $testSaved -Force | Out-Null
    if (-not (Test-Path -LiteralPath $target)) {
        $stage=Join-Path $versions ('.stage-'+[Guid]::NewGuid().ToString('N'))
        . (Join-Path $PSScriptRoot 'differential-version-store.ps1')
        $diff=Invoke-AnomaliaDifferentialVersionStage -SourceRoot $proof.archive -StagePath $stage -BaseVersionRoot $baseVersion -ExcludePaths @('Saved','Saved-validation','Intermediate','DerivedDataCache')
        $report.differentialInstall=$diff
        New-Item -ItemType Junction -Path (Join-Path $stage 'AnomaliaPrimeval/Saved') -Target $testSaved | Out-Null
        Move-Item -LiteralPath $stage -Destination $target
    }
    $exe=Join-Path $target 'AnomaliaPrimeval.exe'
    if (-not (Test-Path -LiteralPath $exe)) { throw 'Installed packaged executable missing.' }
    if ((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $proof.executable -Algorithm SHA256).Hash) { throw 'Installed executable hash mismatch.' }
    $probe=Join-Path $ValidationDir ('installed-smoke-'+[Guid]::NewGuid().ToString('N')+'.json')
    $scope='playable-smoke-'+[Guid]::NewGuid().ToString('N')
    $enginePython=Join-Path $env:UE_ROOT 'Engine/Binaries/ThirdParty/Python3/Win64/python.exe'
    $progressArguments=@()
    if ($proof.progressArt) { $progressArguments=@('-AnomaliaProgressArt') }
    & $enginePython -c 'import subprocess,sys; sys.exit(subprocess.run(sys.argv[1:],timeout=180).returncode)' $exe "/Game/Maps/ANOMALIA_Playable_v1?AnomaliaServerId=$scope" -windowed -ResX=1280 -ResY=720 -d3d11 -sm5 -unattended -nosound "-AnomaliaPlayableProbe=$probe" @progressArguments
    if ($LASTEXITCODE -ne 0) { throw 'Installed game process failed.' }
    $native=Get-Content -LiteralPath $probe -Raw | ConvertFrom-Json
    if ($native.state -ne 'PACKAGED_GAME_SMOKE_PASSED') { throw "Installed gameplay smoke failed: $($native.error)" }
    if ($native.buildCommit -ne $Commit -or $native.checks -notcontains 'visible_executable_build_identity') { throw 'Installed executable build identity mismatch.' }
    if ($native.checks -notcontains 'user_branding_intro_animates_and_reveals_main_menu') { throw 'Installed intro and menu artwork did not pass.' }
    if ($proof.progressArt -and ($native.checks -notcontains 'validated_progress_houses_and_twenty_real_trees' -or $native.checks -notcontains 'validated_progress_real_rocks_and_ground_foliage' -or $native.checks -notcontains 'validated_playable_pbr_landscape_and_forest')) { throw 'Installed progress art is missing.' }
    if ($proof.visualReview.state -ne 'PACKAGED_VISUAL_REVIEW_PASSED') { throw 'Imported-art package validation missing.' }
    $visualDir=Join-Path $ValidationDir 'installed-visual';New-Item -ItemType Directory -Path $visualDir -Force | Out-Null
    $visualProbe=Join-Path $visualDir 'review.json'
    $visualScope='visual-smoke-'+[Guid]::NewGuid().ToString('N')
    & $enginePython -c 'import subprocess,sys; sys.exit(subprocess.run(sys.argv[1:],timeout=300).returncode)' $exe "/Game/Maps/ANOMALIA_VisualValidation_v1?AnomaliaServerId=$visualScope" -windowed -ResX=1280 -ResY=720 -d3d11 -sm5 -unattended -nosound "-AnomaliaVisualReview=$visualProbe"
    if ($LASTEXITCODE -ne 0) { throw 'Installed imported-art process failed.' }
    $visualNative=Get-Content -LiteralPath $visualProbe -Raw | ConvertFrom-Json
    if ($visualNative.state -ne 'PACKAGED_VISUAL_REVIEW_PASSED' -or @($visualNative.screenshots).Count -ne 8 -or -not $visualNative.dayAndNightCaptured) { throw 'Installed imported-art validation failed.' }
    foreach($image in $visualNative.screenshots) { if (-not (Test-Path -LiteralPath $image) -or (Get-Item -LiteralPath $image).Length -lt 10000) { throw 'Installed imported-art screenshot missing.' } }
    $report.installedVisualReview=$visualNative
    $observed=([IO.Path]::GetFullPath($native.savedDir)).TrimEnd('\','/')
    $expected=([IO.Path]::GetFullPath((Join-Path $target 'AnomaliaPrimeval/Saved'))).TrimEnd('\','/')
    if ($observed -ne $expected -and $observed -ne ([IO.Path]::GetFullPath($saved)).TrimEnd('\','/')) { throw "Unexpected packaged save location: $observed" }
    foreach($f in $hashes.Keys) { if (-not (Test-Path -LiteralPath $f) -or (Get-FileHash -LiteralPath $f -Algorithm SHA256).Hash -ne $hashes[$f]) { throw ('Existing user data changed during installation: '+$f) } }
    # Keep smoke-test output separate from all real saves and settings. Preserve the test link too.
    $savedLink=Join-Path $target 'AnomaliaPrimeval/Saved'
    $testLink=Get-Item -LiteralPath $savedLink
    if ($testLink.LinkType -ne 'Junction' -or @($testLink.Target)[0] -ne $testSaved) { throw 'Unexpected validation save junction preserved.' }
    Rename-Item -LiteralPath $savedLink -NewName 'Saved-validation'
    New-Item -ItemType Junction -Path $savedLink -Target $saved | Out-Null
    if (@((Get-Item -LiteralPath $savedLink).Target)[0] -ne $saved) { throw 'Shared player save junction readback failed.' }
    $report.validationSaveIsolationVerified=$true
    $active=Join-Path $base 'active.json';$temp=Join-Path $base ([Guid]::NewGuid().ToString('N')+'.json')
    @{commit=$Commit;executable=$exe;userData=$saved} | ConvertTo-Json | Set-Content -LiteralPath $temp -Encoding UTF8
    $previous=$null
    if (Test-Path -LiteralPath $active) {
        $previous=Get-Content -LiteralPath $active -Raw | ConvertFrom-Json
        $report.previousCommit=$previous.commit
        $history=Join-Path $base 'history';New-Item -ItemType Directory -Path $history -Force | Out-Null
        [IO.File]::Replace($temp,$active,(Join-Path $history ([Guid]::NewGuid().ToString('N')+'.json')))
    } else { Move-Item -LiteralPath $temp -Destination $active }
    $shell=New-Object -ComObject WScript.Shell
    $link=Join-Path ([Environment]::GetFolderPath('Desktop')) 'ANOMALIA - Jouer.lnk'
    if (Test-Path -LiteralPath $link) {
        $old=$shell.CreateShortcut($link)
        if (-not $old.TargetPath.StartsWith($versions+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Unrelated desktop shortcut preserved.' }
    }
    $icon=Join-Path $target 'Anomalia.ico'
    if (-not (Test-Path -LiteralPath $icon)) { throw 'Installed ANOMALIA logo missing.' }
    $shortcut=$shell.CreateShortcut($link);$shortcut.TargetPath=$exe;$shortcut.Arguments='-d3d11 -sm5';$shortcut.WorkingDirectory=$target;$shortcut.IconLocation=$icon+',0';$shortcut.Description='ANOMALIA — version de test Windows autonome';$shortcut.Save()
    $readback=Get-Content -LiteralPath $active -Raw | ConvertFrom-Json
    $desktop=$shell.CreateShortcut($link)
    if ($readback.commit -ne $Commit -or $readback.executable -ne $exe -or $desktop.TargetPath -ne $exe -or $desktop.WorkingDirectory -ne $target -or $desktop.Arguments -ne '-d3d11 -sm5') { throw 'Active version or desktop shortcut readback failed.' }
    $report.activeVersionAndShortcutVerified=$true
    if ($shell.CreateShortcut($link).IconLocation -ne ($icon+',0')) { throw 'Windows logo shortcut readback failed.' }
    $report.userIconVerified=$true
    $visualLink=Join-Path ([Environment]::GetFolderPath('Desktop')) 'ANOMALIA - Validation visuelle.lnk'
    if (Test-Path -LiteralPath $visualLink) {
        if (-not $shell.CreateShortcut($visualLink).TargetPath.StartsWith($versions+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Unrelated visual shortcut preserved.' }
    }
    $visualShortcut=$shell.CreateShortcut($visualLink);$visualShortcut.TargetPath=$exe
    $visualShortcut.Arguments='/Game/Maps/ANOMALIA_VisualValidation_v1?AnomaliaServerId=visual-review-local -d3d11 -sm5'
    $visualShortcut.WorkingDirectory=$target;$visualShortcut.Description='ANOMALIA — zone de validation des nouvelles ressources 3D';$visualShortcut.Save()
    if ($shell.CreateShortcut($visualLink).TargetPath -ne $exe) { throw 'Visual shortcut readback failed.' }
    $report.visualShortcut=$visualLink
    $report.trigger=$env:GITHUB_EVENT_NAME
    $report.updatedExistingInstallation=($null -ne $previous -and $previous.commit -ne $Commit)
    $report.state='PACKAGED_WINDOWS_INSTALLED_AND_SMOKE_TESTED';$report.executable=$exe;$report.shortcut=$link;$report.userData=$saved;$report.existingUserFilesPreserved=$hashes.Count;$report.installedProbe=$native
} catch { $report.error=$_.Exception.Message }
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $ValidationDir 'installed-package-report.json') -Encoding UTF8
$report | ConvertTo-Json -Depth 8 | Write-Host
if ($report.state -ne 'PACKAGED_WINDOWS_INSTALLED_AND_SMOKE_TESTED') { exit 1 }
exit 0
