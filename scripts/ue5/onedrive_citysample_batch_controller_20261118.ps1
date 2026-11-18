param(
    [Parameter(Mandatory=$true)][string]$Python,
    [Parameter(Mandatory=$true)][string]$CopyScript
)
$ErrorActionPreference='Stop'
$root=$env:OneDriveConsumer
if (!$root -or !(Test-Path -LiteralPath $root -PathType Container)) {throw 'Personal OneDrive root unavailable'}
if (!(Test-Path -LiteralPath $Python -PathType Leaf)) {throw 'Unreal Engine embedded Python unavailable'}
if (!(Test-Path -LiteralPath $CopyScript -PathType Leaf)) {throw 'City Sample safe copy script unavailable'}
$dstRoot=Join-Path $root 'ANOMALIAZ_PRIGIMALIA\Backups\CitySample'
$out=$env:CITYSAMPLE_ONEDRIVE_OUT
if (!$out) {throw 'Report directory unavailable'}
New-Item -ItemType Directory -Path $out -Force | Out-Null
$deadline=(Get-Date).ToUniversalTime().AddMinutes(205)
$minClientFree=7GB
$minimumStart=6GB
$cumulative=0L
$cumulativeFiles=0
$completed=0
$stopReason='STOPPED_TIME_BUDGET'
function Write-ControllerReport {
    param([string]$status)
    $rec=[ordered]@{
        state=$status
        onlyClientSyncReceipts=$true
        remoteServerVerifiedViaMicrosoftAPI=$false
        sourceDeletedCount=0
        cumulativeFilesStagedThisController=$cumulativeFiles
        cumulativeBytesStagedThisController=$cumulative
        batchesCompleted=$completed
        timestampUTC=(Get-Date).ToUniversalTime().ToString('o')
        freeCBytes=([IO.DriveInfo]::new([IO.Path]::GetPathRoot($root))).AvailableFreeSpace
    }
    $rec|ConvertTo-Json -Depth 4|Set-Content -LiteralPath (Join-Path $out 'controller-summary.json') -Encoding UTF8
    Write-Host ('ONEDRIVE_CONTROLLER_STATUS '+($rec|ConvertTo-Json -Compress))
}
for ($i=1; $i -le 64; $i++) {
    if ((Get-Date).ToUniversalTime() -ge $deadline) {break}
    if (@(Get-Process -Name OneDrive -ErrorAction SilentlyContinue).Count -eq 0) {
        $stopReason='STOPPED_ONEDRIVE_PROCESS_ABSENT';break
    }
    $free=([IO.DriveInfo]::new([IO.Path]::GetPathRoot($root))).AvailableFreeSpace
    if ($free -lt $minimumStart) {$stopReason='STOPPED_LOW_C_SPACE';break}
    Write-Host ("ONEDRIVE_CONTROLLER_BEGIN_BATCH=$i FREE_C_BYTES=$free")
    & $Python -B $CopyScript
    if ($LASTEXITCODE -ne 0) {$stopReason='STOPPED_PYTHON_BATCH_ERROR';break}
    $reportPath=Join-Path $out 'onedrive-batch-summary.json'
    if (!(Test-Path -LiteralPath $reportPath -PathType Leaf)) {$stopReason='STOPPED_NO_BATCH_RECEIPT';break}
    $receipt=Get-Content -LiteralPath $reportPath -Raw -Encoding UTF8 | ConvertFrom-Json
    Copy-Item -LiteralPath $reportPath -Destination (Join-Path $out ("batch-{0:d3}.json" -f $i))
    if ([long]$receipt.copiedFiles -eq 0) {
        $stopReason=('STOPPED_NO_NEW_FILES_'+$receipt.state);break
    }
    $completed+=1
    $cumulative+=[long]$receipt.copiedBytes
    $cumulativeFiles+=[long]$receipt.copiedFiles
    Write-ControllerReport 'WAITING_FOR_ONEDRIVE_ONLINE_ONLY'
    $samples=@($receipt.samples)
    if ($samples.Count -eq 0) {$stopReason='STOPPED_NO_SAMPLES_FOR_SYNC_GUARD';break}
    $waitUntil=(Get-Date).ToUniversalTime().AddMinutes(22)
    $ready=$false
    while ((Get-Date).ToUniversalTime() -lt $waitUntil -and (Get-Date).ToUniversalTime() -lt $deadline) {
        if (@(Get-Process -Name OneDrive -ErrorAction SilentlyContinue).Count -eq 0) {break}
        $offline=0
        foreach($sample in $samples) {
            $p=Join-Path $dstRoot $sample.relative
            if (Test-Path -LiteralPath $p -PathType Leaf) {
                $item=Get-Item -LiteralPath $p -Force
                if (([int]$item.Attributes -band 0x1000) -ne 0 -and ([int]$item.Attributes -band 0x100000) -ne 0) {
                    $offline++
                }
            }
        }
        $free=([IO.DriveInfo]::new([IO.Path]::GetPathRoot($root))).AvailableFreeSpace
        if($offline -eq $samples.Count -and $free -ge $minClientFree){$ready=$true;break}
        Start-Sleep -Seconds 20
    }
    Write-Host "ONEDRIVE_BATCH_SYNC_GUARD batch=$i samples=$($samples.Count) freeC=$free ready=$ready"
    if (!$ready) {$stopReason='STOPPED_SYNC_NOT_READY_OR_LOW_DISK';break}
    $stopReason='BATCHES_SUCCEEDED_CAN_RESUME'
}
Write-ControllerReport $stopReason
Write-Host 'CRITICAL Original D:\ANOMALIA\FabImports\CitySample was never deleted or changed'
