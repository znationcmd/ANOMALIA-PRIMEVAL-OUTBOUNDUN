# Native UE5.8 duplicate ONLY, never rename. KOLCHIEM ORIGINS is a new separate World.
# Commandlet intentionally has NO -Rename flag; this is the Epic documented duplication mode.
$ErrorActionPreference='Stop'
$root='D:\ANOMALIAZ-PRIGIMALIA\unreal'
$originalRoot='D:\ANOMALIA'
$project=Join-Path $root 'AnomaliaZPrigimalia.uproject'
$original=Join-Path $originalRoot 'unreal\AnomaliaPrimeval.uproject'
$marker=Join-Path $root 'Saved\BrandMigration\verified-source-backup.marker'
$src='/Game/Maps/ANOMALIA_Inhabited_v2'
$dst='/Game/Maps/PRIGIMALIA_KOLCHIEM_ORIGINS'
$srcMap=Join-Path $root 'Content\Maps\ANOMALIA_Inhabited_v2.umap'
$dstMap=Join-Path $root 'Content\Maps\PRIGIMALIA_KOLCHIEM_ORIGINS.umap'
$editor=Join-Path $env:UE_ROOT 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$outDir=Join-Path $env:RUNNER_TEMP ('ANOMALIA_KOLCHIEM_ORIGINS_'+$env:GITHUB_RUN_ID)
New-Item -ItemType Directory -Path $outDir -Force|Out-Null
$beforePath=Join-Path $outDir 'preflight.json'
$afterPath=Join-Path $outDir 'duplication.json'
function Assert-Exists([string]$p){
 if(-not(Test-Path -LiteralPath $p -PathType Leaf)){throw ('Missing protected file '+$p)}
}
foreach($p in @($project,$original,$marker,$srcMap,$editor)){Assert-Exists $p}
foreach($p in @($originalRoot,'D:\ANOMALIAZ-PRIGIMALIA',$root)){
 $attr=(Get-Item -LiteralPath $p).Attributes
 if($attr -band [IO.FileAttributes]::ReparsePoint){throw ('Unsafe linked project root: '+$p)}
}
$active=@(Get-Process -Name UnrealEditor,UnrealEditor-Cmd,AnomaliaPrimeval,AnomaliaZPrigimalia,UnrealBuildTool,robocopy -ErrorAction SilentlyContinue)
if($active.Count -ne 0){throw 'Native Unreal or copy process already active; refuse concurrent duplication'}
# Refuse re-running on a partial world even if its main .umap did not get saved.
$targetExternal=@(
 (Join-Path $root 'Content\__ExternalActors__\Maps\PRIGIMALIA_KOLCHIEM_ORIGINS'),
 (Join-Path $root 'Content\__ExternalObjects__\Maps\PRIGIMALIA_KOLCHIEM_ORIGINS')
)
foreach($path in @($dstMap)+$targetExternal){
 if(Test-Path -LiteralPath $path){throw ('Existing or partial KOLCHIEM target: '+$path)}
}
$receipt=Join-Path $root 'Saved\KOLCHIEM_ORIGINS\duplicate-complete.json'
if(Test-Path -LiteralPath $receipt){throw 'Existing KOLCHIEM duplication receipt; preserve native work'}
$protected=@(
 $srcMap,
 (Join-Path $root 'Content\Maps\ANOMALIA_Archipelago_v2.umap'),
 (Join-Path $root 'Content\Maps\ANOMALIA_DrazoviaTopo_NewReferenceV3_Candidate.umap'),
 $original
)
$before=@{}
foreach($path in $protected){Assert-Exists $path;$before[$path]=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash}
$originalCount=0
$sourceActors=Join-Path $root 'Content\__ExternalActors__\Maps\ANOMALIA_Inhabited_v2'
if(Test-Path -LiteralPath $sourceActors){$originalCount=@(Get-ChildItem -LiteralPath $sourceActors -File -Recurse -ErrorAction Stop).Count}
# The old 48km level contains 7583 lightweight external actor files (~86MB).
# Keep at least 6GiB free at start, or 4GiB plus 3x the measured world
# footprint, whichever is higher. Do NOT delete caches, assets or backups.
$actorBytes=[int64]0
if(Test-Path -LiteralPath $sourceActors -PathType Container){
 $actorBytes=[int64](Get-ChildItem -LiteralPath $sourceActors -File -Recurse -ErrorAction Stop | Measure-Object -Property Length -Sum).Sum
}
$sourceObjects=Join-Path $root 'Content\__ExternalObjects__\Maps\ANOMALIA_Inhabited_v2'
$objectBytes=[int64]0
if(Test-Path -LiteralPath $sourceObjects -PathType Container){
 $objectBytes=[int64](Get-ChildItem -LiteralPath $sourceObjects -File -Recurse -ErrorAction Stop | Measure-Object -Property Length -Sum).Sum
}
$sourceBytes=[int64](Get-Item -LiteralPath $srcMap).Length+$actorBytes+$objectBytes
$minimumFree=[long][Math]::Max(6GB,(4GB+3*$sourceBytes))
$drive=Get-PSDrive -Name D -ErrorAction Stop
Write-Host ('KOLCHIEM_SOURCE_FOOTPRINT_MIB='+[math]::Round($sourceBytes/1MB,2))
Write-Host ('KOLCHIEM_DISK_MINIMUM_GIB='+[math]::Round($minimumFree/1GB,2))
Write-Host ('KOLCHIEM_DISK_FREE_GIB='+[math]::Round($drive.Free/1GB,2))
if($drive.Free -lt $minimumFree){
 throw ('Insufficient safe D: capacity for measured World duplication: free '+[math]::Round($drive.Free/1GB,2)+' GiB; required '+[math]::Round($minimumFree/1GB,2)+' GiB')
}
@{
 operation='DUPLICATE_NOT_RENAME';sourcePackage=$src;targetPackage=$dst;
 sourceExternalActorFiles=$originalCount;originalHashSHA256=$before[$original];
 sourceMapSha256=$before[$srcMap];freeGB=[math]::Round($drive.Free/1GB,2)
}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $beforePath -Encoding UTF8
Write-Host 'KOLCHIEM_ORIGINS_SAFE_PREFLIGHT=true'
$state='FAILED_NOT_CERTIFIED'
$exitCode=-1
try {
 $log=Join-Path $outDir 'world-partition-duplicate.log'
 & $editor $project $src '-NullRHI' '-unattended' '-nopause' '-nosound' '-run=WorldPartitionBuilderCommandlet' '-SCCProvider=None' '-builder=WorldPartitionRenameDuplicateBuilder' "-NewPackage=$dst" "-abslog=$log"
 $exitCode=$LASTEXITCODE
 if($exitCode -ne 0){throw ('World Partition duplication commandlet failed: exit '+$exitCode)}
 if(-not(Test-Path -LiteralPath $dstMap -PathType Leaf)){throw 'Builder exited 0 but destination .umap does not exist'}
 if((Get-Item -LiteralPath $dstMap).Length -lt 1024){throw 'New KOLCHIEM .umap appears truncated'}
 $newActors=Join-Path $root 'Content\__ExternalActors__\Maps\PRIGIMALIA_KOLCHIEM_ORIGINS'
 $newActorsCount=0
 if(Test-Path -LiteralPath $newActors){$newActorsCount=@(Get-ChildItem -LiteralPath $newActors -File -Recurse -ErrorAction Stop).Count}
 if($originalCount -gt 0 -and $newActorsCount -eq 0){throw 'World Partition source has external actor files but duplicate has none'}
 $state='DISTINCT_NATIVE_UMAP_DUPLICATED_PENDING_UNREAL_RELOAD'
 Write-Host 'KOLCHIEM_ORIGINS_NEW_UMAP_CREATED=true'
} finally {
 $changed=@()
 foreach($path in $before.Keys){
  if(-not(Test-Path -LiteralPath $path -PathType Leaf) -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $before[$path]){$changed+=,$path}
 }
 @{
  status=$state;sourcePackage=$src;targetPackage=$dst;builderExitCode=$exitCode;
  targetUmapExists=(Test-Path -LiteralPath $dstMap -PathType Leaf);
  protectedMapHashChanges=$changed;
  gameplayTested=$false;worldPartitionStreamingVerified=$false;
  originalRetained=(Test-Path -LiteralPath $srcMap -PathType Leaf)
 }|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $afterPath -Encoding UTF8
 if($changed.Count -gt 0){throw ('Protected original/previous world files changed: '+($changed -join ', '))}
 Write-Host 'KOLCHIEM_PROTECTED_SOURCE_SKARVIK_DRAZOVIA_UNCHANGED=true'
}
