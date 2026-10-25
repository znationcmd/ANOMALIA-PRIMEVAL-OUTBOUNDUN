param([Parameter(Mandatory=$true)][string]$ValidationDir)
$ErrorActionPreference='Stop'
$report=@{state='FAILED';commit=$env:GITHUB_SHA;gameUpdated=$false;productionMapModified=$false;gameplayApproved=$false}
try {
    $proof=Get-Content (Join-Path $ValidationDir 'process-report.json') -Raw | ConvertFrom-Json
    if ($proof.state -ne 'REAL_MODELS_NATIVE_IMPORTED_GPU_CAPTURED_NOT_GAMEPLAY_APPROVED' -or $proof.sourceCommit -ne $env:GITHUB_SHA) { throw 'Fresh native import and actual GPU captures are required.' }
    $base=Join-Path $env:LOCALAPPDATA 'CMD/ANOMALIA-UE5'
    $owner=Get-Content (Join-Path $base 'owner.json') -Raw | ConvertFrom-Json
    $active=Get-Content (Join-Path $base 'active.json') -Raw | ConvertFrom-Json
    if ($owner.product -ne 'ANOMALIA-UE5-EDITOR-v1') { throw 'Owned Editor installation not found.' }
    $target=[IO.Path]::GetFullPath((Split-Path -Parent $active.project))
    $versions=[IO.Path]::GetFullPath((Join-Path $base 'versions')).TrimEnd('\')+'\'
    if (-not $target.StartsWith($versions,[StringComparison]::OrdinalIgnoreCase)) { throw 'Unexpected installed project root.' }
    $source=Join-Path $env:GITHUB_WORKSPACE 'unreal'
    $relativeFiles=@()
    $contentRelative='Content/Anomalia/InteractiveRealismReview_v1'
    $sourceContent=Join-Path $source $contentRelative
    foreach ($file in Get-ChildItem -LiteralPath $sourceContent -File -Recurse) {
        if ($file.Extension -notin @('.uasset','.uexp','.ubulk','.uptnl')) { throw 'Unexpected imported asset extension.' }
        $relativeFiles += $file.FullName.Substring($source.Length).TrimStart('\','/')
    }
    $relativeFiles += 'Content/Maps/ANOMALIA_InteractiveRealismReview_v1.umap'
    if ($relativeFiles.Count -lt 4) { throw 'Real model content is missing.' }
    # Preflight every destination before any copy. Preserve all differing artist files.
    foreach ($relative in $relativeFiles) {
        $from=Join-Path $source $relative;$to=Join-Path $target $relative
        if (-not (Test-Path -LiteralPath $from -PathType Leaf)) { throw "Missing source: $relative" }
        if ((Test-Path -LiteralPath $to) -and (Get-FileHash $to).Hash -ne (Get-FileHash $from).Hash) { throw "Existing edited asset preserved: $relative" }
    }
    $copied=0
    foreach ($relative in $relativeFiles) {
        $from=Join-Path $source $relative;$to=Join-Path $target $relative
        if (-not (Test-Path -LiteralPath $to)) {
            New-Item -ItemType Directory -Path (Split-Path -Parent $to) -Force | Out-Null
            Copy-Item -LiteralPath $from -Destination $to
            $copied++
        }
        if ((Get-FileHash $to).Hash -ne (Get-FileHash $from).Hash) { throw 'Installed review asset hash mismatch.' }
    }
    $credits=Join-Path $source 'SourceAssets/InteractiveRealismPrepared_v1/CREDITS.md'
    $noticeDir=Join-Path $target 'Content/Anomalia/InteractiveRealismReview_v1'
    $notice=Join-Path $noticeDir 'CREDITS.md'
    if ((Test-Path $notice) -and (Get-FileHash $notice).Hash -ne (Get-FileHash $credits).Hash) { throw 'Existing edited credits preserved.' }
    if (-not (Test-Path $notice)) { Copy-Item $credits $notice }
    $env:ANOMALIA_REVIEW_INSTALL_PROBE=Join-Path $ValidationDir 'installed-review-probe.json'
    $editor=Join-Path $env:UE_ROOT 'Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
    $script=Join-Path $env:GITHUB_WORKSPACE 'unreal/Scripts/probe_interactive_review_install.py'
    $log=Join-Path $ValidationDir 'installed-review-probe.log'
    & $editor $active.project "-ExecutePythonScript=$script" -NullRHI -unattended -nopause -nosound "-abslog=$log"
    if ($LASTEXITCODE -ne 0) { throw 'Installed review reopen failed.' }
    $opened=Get-Content $env:ANOMALIA_REVIEW_INSTALL_PROBE -Raw | ConvertFrom-Json
    if ($opened.state -ne 'INSTALLED_REAL_MODEL_REVIEW_REOPENED' -or @($opened.models).Count -ne 3 -or $opened.sourceCommit -ne $env:GITHUB_SHA) { throw 'Installed models not verified.' }
    $shell=New-Object -ComObject WScript.Shell
    $link=Join-Path ([Environment]::GetFolderPath('Desktop')) 'ANOMALIA - Modeles 3D reels.lnk'
    $arguments='"'+$active.project+'" /Game/Maps/ANOMALIA_InteractiveRealismReview_v1 -d3d11 -sm5'
    if (Test-Path $link) {
        if ($shell.CreateShortcut($link).Arguments -ne $arguments) { throw 'Existing unrelated shortcut preserved.' }
    } else {
        $shortcut=$shell.CreateShortcut($link)
        $shortcut.TargetPath=Join-Path $env:UE_ROOT 'Engine/Binaries/Win64/UnrealEditor.exe'
        $shortcut.Arguments=$arguments;$shortcut.WorkingDirectory=$target
        $shortcut.Description='ANOMALIA - vrais modeles 3D, apercu technique; interactions en preparation'
        $shortcut.Save()
    }
    $report.state='REAL_MODEL_REVIEW_INSTALLED_AND_REOPENED'
    $report.copiedFiles=$copied;$report.verifiedFiles=$relativeFiles.Count;$report.shortcut=$link
    $report.activeEditorCommit=$active.commit;$report.mapPackage=$opened.mapPackage
} catch { $report.error=$_.Exception.Message }
$report | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $ValidationDir 'installed-review-report.json') -Encoding UTF8
$report | ConvertTo-Json -Depth 8 | Write-Host
if ($report.state -ne 'REAL_MODEL_REVIEW_INSTALLED_AND_REOPENED') { exit 1 }
