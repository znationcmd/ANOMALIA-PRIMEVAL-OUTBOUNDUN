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
    $target=Join-Path $versions ($Commit+'-'+[Guid]::NewGuid().ToString('N').Substring(0,8))
    $testSaved=Join-Path $base ('validation/'+[Guid]::NewGuid().ToString('N')+'/Saved')
    New-Item -ItemType Directory -Path $testSaved -Force | Out-Null
    if (-not (Test-Path -LiteralPath $target)) {
        $stage=Join-Path $versions ('.stage-'+[Guid]::NewGuid().ToString('N'));New-Item -ItemType Directory -Path $stage | Out-Null
        & robocopy.exe $proof.archive $stage /E /COPY:DAT /DCOPY:DAT /XJ /XD Saved /R:1 /W:1 /NFL /NDL /NJH /NJS | Out-Null
        if ($LASTEXITCODE -gt 7) { throw 'Packaged version copy failed.' }
        New-Item -ItemType Junction -Path (Join-Path $stage 'AnomaliaPrimeval/Saved') -Target $testSaved | Out-Null
        Move-Item -LiteralPath $stage -Destination $target
    }
    $exe=Join-Path $target 'AnomaliaPrimeval.exe'
    if (-not (Test-Path -LiteralPath $exe)) { throw 'Installed packaged executable missing.' }
    if ((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $proof.executable -Algorithm SHA256).Hash) { throw 'Installed executable hash mismatch.' }
    $probe=Join-Path $ValidationDir ('installed-smoke-'+[Guid]::NewGuid().ToString('N')+'.json')
    $scope='playable-smoke-'+[Guid]::NewGuid().ToString('N')
    $enginePython=Join-Path $env:UE_ROOT 'Engine/Binaries/ThirdParty/Python3/Win64/python.exe'
    & $enginePython -c 'import subprocess,sys; sys.exit(subprocess.run(sys.argv[1:],timeout=180).returncode)' $exe "/Game/Maps/ANOMALIA_Playable_v1?AnomaliaServerId=$scope" -windowed -ResX=1280 -ResY=720 -d3d11 -sm5 -unattended -nosound "-AnomaliaPlayableProbe=$probe"
    if ($LASTEXITCODE -ne 0) { throw 'Installed game process failed.' }
    $native=Get-Content -LiteralPath $probe -Raw | ConvertFrom-Json
    if ($native.state -ne 'PACKAGED_GAME_SMOKE_PASSED') { throw "Installed gameplay smoke failed: $($native.error)" }
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
    if (Test-Path -LiteralPath $active) {
        $history=Join-Path $base 'history';New-Item -ItemType Directory -Path $history -Force | Out-Null
        [IO.File]::Replace($temp,$active,(Join-Path $history ([Guid]::NewGuid().ToString('N')+'.json')))
    } else { Move-Item -LiteralPath $temp -Destination $active }
    $shell=New-Object -ComObject WScript.Shell
    $link=Join-Path ([Environment]::GetFolderPath('Desktop')) 'ANOMALIA - Jouer.lnk'
    if (Test-Path -LiteralPath $link) {
        $old=$shell.CreateShortcut($link)
        if (-not $old.TargetPath.StartsWith($versions+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Unrelated desktop shortcut preserved.' }
    }
    $shortcut=$shell.CreateShortcut($link);$shortcut.TargetPath=$exe;$shortcut.Arguments='-d3d11 -sm5';$shortcut.WorkingDirectory=$target;$shortcut.Description='ANOMALIA — version de test Windows autonome';$shortcut.Save()
    $report.state='PACKAGED_WINDOWS_INSTALLED_AND_SMOKE_TESTED';$report.executable=$exe;$report.shortcut=$link;$report.userData=$saved;$report.existingUserFilesPreserved=$hashes.Count;$report.installedProbe=$native
} catch { $report.error=$_.Exception.Message }
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $ValidationDir 'installed-package-report.json') -Encoding UTF8
$report | ConvertTo-Json -Depth 8 | Write-Host
if ($report.state -ne 'PACKAGED_WINDOWS_INSTALLED_AND_SMOKE_TESTED') { exit 1 }
exit 0
