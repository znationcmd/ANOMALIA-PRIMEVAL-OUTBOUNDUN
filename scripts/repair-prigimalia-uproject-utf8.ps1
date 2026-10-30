# Repairs ONLY the staged AnomaliaZPrigimalia.uproject when its
# exact bytes prove a UTF-16 BOM + valid UE JSON. The original
# D:\ANOMALIA, assets, maps, Fab/Sketchfab and packaged game are read-only.
$ErrorActionPreference = 'Stop'
$root = 'D:\ANOMALIAZ-PRIGIMALIA\unreal'
$project = Join-Path $root 'AnomaliaZPrigimalia.uproject'
$original = 'D:\ANOMALIA\unreal\AnomaliaPrimeval.uproject'
$marker = Join-Path $root 'Saved\BrandMigration\verified-source-backup.marker'
$reportDir = Join-Path $root 'Saved\BrandMigration'
$reportPath = Join-Path $reportDir 'project-encoding-repair-report.json'
$state = [ordered]@{
  status = 'NOT_STARTED'
  project = $project
  originalPresent = $false
  originalUnchanged = $false
  beforeEncoding = ''
  afterEncoding = ''
  beforeLength = 0
  afterLength = 0
  beforeSHA256 = ''
  afterSHA256 = ''
  backupPath = ''
  repairApplied = $false
  projectFilesGenerated = $false
  packagedGamePreserved = $false
  error = ''
}
$originalHash = $null
try {
  if (-not (Test-Path -LiteralPath $project -PathType Leaf)) { throw 'Staged .uproject absent' }
  if (-not (Test-Path -LiteralPath $original -PathType Leaf)) { throw 'D original .uproject absent' }
  if (-not (Test-Path -LiteralPath $marker -PathType Leaf)) { throw 'Staged backup marker missing' }
  foreach ($r in @('D:\ANOMALIA', 'D:\ANOMALIAZ-PRIGIMALIA', $root)) {
    $item = Get-Item -LiteralPath $r -Force
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Junction/symlink root refused: $r" }
  }
  if ((Get-Item -LiteralPath $project -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
    throw 'Symlinked .uproject refused'
  }
  if (@(Get-Process -Name UnrealEditor,UnrealEditor-Cmd,UnrealBuildTool,AnomaliaPrimeval,AnomaliaZPrigimalia,robocopy -ErrorAction SilentlyContinue).Count -gt 0) {
    throw 'An Unreal/editor/build or stage-copy process is active; refusing concurrent repair'
  }
  $originalHash = (Get-FileHash -LiteralPath $original -Algorithm SHA256).Hash
  $state.originalPresent = $true
  $bytes = [IO.File]::ReadAllBytes($project)
  $state.beforeLength = $bytes.Length
  $state.beforeSHA256 = (Get-FileHash -LiteralPath $project -Algorithm SHA256).Hash
  if ($bytes.Length -lt 4) { throw '.uproject too short to be valid Unreal JSON' }
  $state.beforeBytesPrefix = [BitConverter]::ToString($bytes, 0, [Math]::Min(8, $bytes.Length))
  $strictUtf8 = [System.Text.UTF8Encoding]::new($false, $true)
  $needsFix = $false
  if ($bytes[0] -eq 0xFF -and $bytes[1] -eq 0xFE) {
    if ($bytes.Length % 2 -ne 0) { throw 'Invalid UTF-16 LE byte length' }
    $decoded = [System.Text.UnicodeEncoding]::new($false, $true, $true).GetString($bytes,2,$bytes.Length-2)
    $state.beforeEncoding = 'UTF-16 LE BOM'
    $needsFix = $true
  } elseif ($bytes[0] -eq 0xFE -and $bytes[1] -eq 0xFF) {
    if ($bytes.Length % 2 -ne 0) { throw 'Invalid UTF-16 BE byte length' }
    $decoded = [System.Text.UnicodeEncoding]::new($true, $true, $true).GetString($bytes,2,$bytes.Length-2)
    $state.beforeEncoding = 'UTF-16 BE BOM'
    $needsFix = $true
  } elseif ($bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
    $decoded = $strictUtf8.GetString($bytes,3,$bytes.Length-3)
    $state.beforeEncoding = 'UTF-8 BOM'
  } else {
    $decoded = $strictUtf8.GetString($bytes)
    $state.beforeEncoding = 'UTF-8 no BOM'
  }
  $parsed = $decoded | ConvertFrom-Json -ErrorAction Stop
  if ($parsed.FileVersion -ne 3) { throw "Unexpected Unreal .uproject FileVersion: $($parsed.FileVersion)" }
  if (@($parsed.Modules | Where-Object { $_.Name -eq 'AnomaliaZPrigimalia' }).Count -ne 1) {
    throw 'Unreal descriptor does not contain the expected AnomaliaZPrigimalia game module'
  }
  if ($needsFix) {
    $utf8Bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($decoded)
    if ($utf8Bytes.Length -lt 10 -or $utf8Bytes[0] -ne 0x7B) {
      throw 'Unexpected project JSON first byte after UTF-8 conversion'
    }
    $rechecked = $strictUtf8.GetString($utf8Bytes) | ConvertFrom-Json -ErrorAction Stop
    if (@($rechecked.Modules | Where-Object { $_.Name -eq 'AnomaliaZPrigimalia' }).Count -ne 1) {
      throw 'UTF-8 roundtrip changed the native game descriptor'
    }
    $backup = Join-Path $reportDir ('AnomaliaZPrigimalia.uproject.before-utf8-' + $state.beforeSHA256 + '.bak')
    if (Test-Path -LiteralPath $backup) { throw 'Existing project backup collision; refusing to overwrite' }
    $temp = Join-Path $root 'AnomaliaZPrigimalia.uproject.utf8-fix.tmp'
    if (Test-Path -LiteralPath $temp) { throw 'Pre-existing temporary descriptor; refusing overwrite' }
    [IO.File]::WriteAllBytes($temp, $utf8Bytes)
    # Atomic NTFS replace: creates the original-byte backup in Saved/BrandMigration.
    [IO.File]::Replace($temp, $project, $backup, $false)
    $state.backupPath = $backup
    $state.repairApplied = $true
    Write-Host 'PRIGIMALIA_UTF16_PROJECT_CONVERTED_TO_UTF8_NO_BOM=true'
  } else {
    Write-Host 'PRIGIMALIA_PROJECT_ALREADY_VALID_UTF8=true'
  }
  $after = [IO.File]::ReadAllBytes($project)
  $state.afterLength = $after.Length
  $state.afterSHA256 = (Get-FileHash -LiteralPath $project -Algorithm SHA256).Hash
  if ($after[0] -eq 0xFF -or $after[0] -eq 0xFE) { throw 'Project still starts with invalid UTF-16 byte' }
  $afterText = $strictUtf8.GetString($after)
  $afterParsed = $afterText | ConvertFrom-Json -ErrorAction Stop
  if (@($afterParsed.Modules | Where-Object { $_.Name -eq 'AnomaliaZPrigimalia' }).Count -ne 1) { throw 'Post-repair JSON validation failed' }
  $state.afterEncoding = 'UTF-8'
  $packaged = 'D:\ANOMALIAZ-PRIGIMALIA\PackagedWindows\NativeValidated\Windows\AnomaliaZPrigimalia.exe'
  $state.packagedGamePreserved = (Test-Path -LiteralPath $packaged -PathType Leaf)
  if (-not $state.packagedGamePreserved) { throw 'Previously verified Windows executable is unexpectedly missing; stop and investigate' }
  if ([string]::IsNullOrWhiteSpace($env:UE_ROOT)) { throw 'UE_ROOT unavailable' }
  $genBat = Join-Path $env:UE_ROOT 'Engine\Build\BatchFiles\GenerateProjectFiles.bat'
  if (-not (Test-Path -LiteralPath $genBat -PathType Leaf)) { throw 'UE5.8 GenerateProjectFiles.bat unavailable' }
  # IMPORTANT: the system dotnet.exe only has .NET 9, while UE5.8 UBT requires
  # .NET 10. Use the engine's own batch launcher and its bundled runtime instead.
  # This is the same native project-file generation invoked by the selector.
  & $genBat "-Project=$project" '-Game' '-Progress'
  if ($LASTEXITCODE -ne 0) { throw "UE5.8 bundled GenerateProjectFiles failed (exit $LASTEXITCODE); inspect the job log" }
  $state.projectFilesGenerated = $true
  $state.status = 'SUCCESS'
  Write-Host 'PRIGIMALIA_NATIVE_GENERATE_PROJECT_FILES_SUCCESS=true'
} catch {
  $state.status = 'FAILED'
  $state.error = $_.Exception.Message
  Write-Host ('PRIGIMALIA_DESCRIPTOR_REPAIR_FAILED=' + $state.error)
  throw
} finally {
  if ($originalHash -and (Test-Path -LiteralPath $original)) {
    $state.originalUnchanged = ((Get-FileHash -LiteralPath $original -Algorithm SHA256).Hash -eq $originalHash)
  }
  if (Test-Path -LiteralPath $root) {
    New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
    $state | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $reportPath -Encoding UTF8
    Write-Host ('PRIGIMALIA_DESCRIPTOR_REPORT=' + $reportPath)
  }
}
