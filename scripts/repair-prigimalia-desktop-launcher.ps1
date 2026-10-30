<#
.SYNOPSIS
  Fix a broken Unreal Engine packaged game desktop launcher without moving the
  bootstrap exe away from its complete Windows packaged directory.

  Never deletes or overwrites desktop items, game files or user saves.
  Refuses incomplete packages and preserves all existing shortcuts.
#>
[CmdletBinding()]
param(
    [string]$RunId = 'manual'
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$gameName = 'AnomaliaZPrigimalia'
$projectHome = 'D:\ANOMALIAZ-PRIGIMALIA'
$packageRoot = Join-Path $projectHome 'PackagedWindows\NativeValidated\Windows'
$bootstrap = Join-Path $packageRoot ($gameName + '.exe')
$binaryRoot = Join-Path $packageRoot ($gameName + '\Binaries\Win64')
$pakRoot = Join-Path $packageRoot ($gameName + '\Content\Paks')
$logRoot = Join-Path $projectHome ('Saved\DesktopLauncherRepair\run-' + $RunId)
if (-not (Test-Path -LiteralPath $projectHome -PathType Container)) {
    throw 'Isolated D project missing; do not guess or modify source/desktop.'
}
if ((Get-Item -LiteralPath $projectHome).Attributes -band [IO.FileAttributes]::ReparsePoint) {
    throw 'Project root is linked; refuse unsafe path.'
}
if (Test-Path -LiteralPath $logRoot) {
    throw 'This repair run already exists; do not overwrite an audit.'
}
New-Item -ItemType Directory -Path $logRoot -Force | Out-Null

$report = [ordered]@{
    timestampUtc = (Get-Date).ToUniversalTime().ToString('o')
    runId = $RunId
    reportedFailure = 'CreateProcess() returned 2'
    reportedMissingBinary = 'C:\Users\utilisateur\Desktop\AnomaliaZPrigimalia\Binaries\Win64\AnomaliaZPrigimalia.exe'
    packageRoot = $packageRoot
    bootstrap = $bootstrap
    packageBootstrapExists = $false
    validPeHeader = $false
    packagedBinaryPaths = @()
    pakFiles = @()
    completePackage = $false
    desktopFolder = ''
    existingAnomaliaShortcuts = @()
    desktopStandaloneBootstraps = @()
    createdShortcut = ''
    result = 'not verified'
}

function Write-Audit {
    $dest = Join-Path $logRoot 'desktop-launcher-audit.json'
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $dest -Encoding UTF8
    Write-Host ('PRIGIMALIA_DESKTOP_LAUNCHER_AUDIT=' + $dest)
}
try {
    if ((Test-Path -LiteralPath $bootstrap -PathType Leaf) -and
        (Test-Path -LiteralPath $binaryRoot -PathType Container) -and
        (Test-Path -LiteralPath $pakRoot -PathType Container)) {
        $report.packageBootstrapExists = $true
        $bytes = [IO.File]::ReadAllBytes($bootstrap)
        $report.validPeHeader = ($bytes.Length -gt 1024 -and $bytes[0] -eq 77 -and $bytes[1] -eq 90)
        $executables = @(Get-ChildItem -LiteralPath $binaryRoot -File -Filter '*.exe' -ErrorAction Stop |
            Where-Object { $_.Name -like '*AnomaliaZPrigimalia*' -and $_.Length -gt 1024 })
        $packageFiles = @(Get-ChildItem -LiteralPath $pakRoot -File -ErrorAction Stop |
            Where-Object { $_.Extension -in '.pak', '.ucas', '.utoc' -and $_.Length -gt 0 })
        $report.packagedBinaryPaths = @($executables | ForEach-Object { $_.FullName })
        $report.pakFiles = @($packageFiles | ForEach-Object { $_.FullName })
        $report.completePackage = [bool]($report.validPeHeader -and $executables.Count -gt 0 -and $packageFiles.Count -gt 0)
    } elseif (Test-Path -LiteralPath $bootstrap -PathType Leaf) {
        $report.packageBootstrapExists = $true
    }

    # This is the actual desktop path advertised by the Windows error dialog.
    # Do not rely on the service runner's own profile/desktop.
    $desktopCandidates = @(
        'C:\Users\utilisateur\Desktop',
        'C:\Users\utilisateur\OneDrive\Desktop',
        'C:\Users\utilisateur\OneDrive\Bureau'
    )
    foreach ($candidate in $desktopCandidates) {
        if (Test-Path -LiteralPath $candidate -PathType Container) {
            if ((Get-Item -LiteralPath $candidate).Attributes -band [IO.FileAttributes]::ReparsePoint) { continue }
            $report.desktopFolder = $candidate
            break
        }
    }
    if (-not $report.desktopFolder) {
        $report.result = 'No verified interactive desktop folder. No changes performed.'
        Write-Host 'PRIGIMALIA_DESKTOP_LAUNCHER_NO_USER_DESKTOP=true'
        return
    }

    $shell = New-Object -ComObject WScript.Shell
    $links = @(Get-ChildItem -LiteralPath $report.desktopFolder -Filter '*.lnk' -File -ErrorAction Stop)
    foreach ($link in $links) {
        if ($link.Name -notmatch '(?i)Anomalia|Prigimalia') { continue }
        try {
            $shortcut = $shell.CreateShortcut($link.FullName)
            $target = [string]$shortcut.TargetPath
            $report.existingAnomaliaShortcuts += [pscustomobject]@{
                link = $link.FullName
                target = $target
                exists = (Test-Path -LiteralPath $target -PathType Leaf)
                workingDirectory = [string]$shortcut.WorkingDirectory
            }
        } catch {
            $report.existingAnomaliaShortcuts += [pscustomobject]@{
                link = $link.FullName
                error = $_.Exception.Message
            }
        }
    }
    $report.desktopStandaloneBootstraps = @(
        Get-ChildItem -LiteralPath $report.desktopFolder -Filter '*AnomaliaZPrigimalia*.exe' -File -ErrorAction SilentlyContinue |
        ForEach-Object { $_.FullName }
    )

    if (-not $report.completePackage) {
        $report.result = 'Packaged build on D is incomplete. Shortcut not created; an executable alone is not a full UE5 game.'
        Write-Host 'PRIGIMALIA_DESKTOP_LAUNCHER_BLOCKED_INCOMPLETE_PACKAGE=true'
        return
    }

    $linkPath = Join-Path $report.desktopFolder "ANOMALIA'Z PRIGIMALIA - JOUER (version valide).lnk"
    if (Test-Path -LiteralPath $linkPath) {
        $existing = $shell.CreateShortcut($linkPath)
        if (-not [string]::Equals([string]$existing.TargetPath, $bootstrap, [StringComparison]::OrdinalIgnoreCase)) {
            $report.result = 'Name collision: shortcut exists and targets a different file; existing shortcut preserved.'
            Write-Host 'PRIGIMALIA_DESKTOP_LAUNCHER_NAME_COLLISION=true'
            return
        }
        $report.createdShortcut = $linkPath
        $report.result = 'Existing good shortcut verified; no change needed.'
        Write-Host ('PRIGIMALIA_DESKTOP_LAUNCHER_VERIFIED=' + $linkPath)
        return
    }

    # Only a NEW .lnk is created. Old .lnk/.exe/.uproject and all original
    # installed archives/saves remain untouched.
    $newLink = $shell.CreateShortcut($linkPath)
    $newLink.TargetPath = $bootstrap
    $newLink.WorkingDirectory = $packageRoot
    $newLink.IconLocation = $bootstrap + ',0'
    $newLink.Description = "Lancer ANOMALIA'Z PRIGIMALIA depuis son dossier de jeu Windows complet sur D:"
    $newLink.Save()
    if (-not (Test-Path -LiteralPath $linkPath -PathType Leaf)) { throw 'New shortcut not written' }
    $verify = $shell.CreateShortcut($linkPath)
    if (-not [string]::Equals([string]$verify.TargetPath, $bootstrap, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'New shortcut target did not match validated Windows game'
    }
    $report.createdShortcut = $linkPath
    $report.result = 'New desktop shortcut created and validated. Click the new shortcut, not the stray desktop EXE.'
    Write-Host ('PRIGIMALIA_DESKTOP_LAUNCHER_CREATED=' + $linkPath)
    Write-Host 'PRIGIMALIA_EXISTING_DESKTOP_FILES_PRESERVED=true'
    Write-Host 'PRIGIMALIA_ORIGINAL_PROJECT_SAVES_PRESERVED=true'
} finally {
    Write-Audit
}
