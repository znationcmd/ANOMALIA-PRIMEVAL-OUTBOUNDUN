# Read-only audit. Never modifies ANOMALIA or City Sample native files.
[CmdletBinding()]
param(
 [string]$CitySampleProject='',
 [string]$StagedProject='D:\ANOMALIAZ-PRIGIMALIA\unreal\AnomaliaZPrigimalia.uproject',
 [string]$ReportPath=''
)
$ErrorActionPreference='Stop'
function IsFile([string]$p) { return [bool]($p -and (Test-Path -LiteralPath $p -PathType Leaf)) }
$candidates=@()
if($CitySampleProject){$candidates+= $CitySampleProject}
$candidates+=@(
 'D:\CitySample\CitySample.uproject',
 'D:\Unreal Projects\CitySample\CitySample.uproject',
 'D:\ANOMALIA\CitySample\CitySample.uproject',
 'D:\ANOMALIA\FabImports\CitySample\CitySample.uproject',
 'C:\Unreal Projects\CitySample\CitySample.uproject'
)
if(Test-Path 'C:\Users'){
 foreach($u in @(Get-ChildItem 'C:\Users' -Directory -ErrorAction SilentlyContinue)){
  $candidates+= (Join-Path $u.FullName 'Documents\Unreal Projects\CitySample\CitySample.uproject')
 }
}
$source=$null
foreach($c in $candidates){
 if(Test-Path -LiteralPath $c -PathType Container){$c=Join-Path $c 'CitySample.uproject'}
 if(IsFile $c){$source=(Resolve-Path -LiteralPath $c).Path;break}
}
$big=$null;$external=$null
if($source){
 $root=Split-Path -Parent $source
 foreach($filename in @('Big_City_LLV.umap','Big_City_LVL.umap')){
  $candidate=Join-Path $root ('Content\Map\'+$filename)
  if(IsFile $candidate){$big=$candidate;break}
 }
 $dir=Join-Path $root 'Content\__ExternalActors__'
 if(Test-Path -LiteralPath $dir -PathType Container){$external=$dir}
}
$stage=IsFile $StagedProject
$stagedMap=$null;$sm5=$false
if($stage){
 $stageRoot=Split-Path -Parent $StagedProject
 $candidate=Join-Path $stageRoot 'Content\Maps\ANOMALIA_Archipelago_v2.umap'
 if(IsFile $candidate){$stagedMap=$candidate}
 $ini=Join-Path $stageRoot 'Config\DefaultEngine.ini'
 if(IsFile $ini){$sm5=[bool](Select-String -LiteralPath $ini -Pattern 'PCD3D_SM5' -Quiet)}
}
$preservedOriginal='D:\ANOMALIA\unreal\Content\Maps\ANOMALIA_Archipelago_v2.umap'
$originalPresent=IsFile $preservedOriginal
$status='BLOCKED_SOURCE_CITY_SAMPLE_NOT_FOUND'
if($source -and !$big){$status='BLOCKED_BIG_CITY_MAP_NOT_FOUND'}
if($source -and $big -and !$external){$status='BLOCKED_EXTERNAL_ACTORS_NOT_FOUND'}
if($source -and $big -and $external -and !$stage){$status='BLOCKED_STAGED_PROJECT_NOT_FOUND'}
if($source -and $big -and $external -and $stage -and !$stagedMap){$status='BLOCKED_STAGED_SKARVIK_NOT_FOUND'}
if($source -and $big -and $external -and $stage -and $stagedMap){$status='READY_FOR_MANUAL_NATIVE_MIGRATION_REVIEW'}
$freeGb=$null
if(Test-Path 'D:\'){try{$freeGb=[math]::Round(([System.IO.DriveInfo]::new('D')).AvailableFreeSpace/1GB,1)}catch{}}
$report=[ordered]@{
 status=$status;sourceCitySampleProject=$source;sourceBigCityMap=$big
 externalActorDirectory=$external;stagedAnomaliaExists=$stage
 stagedSkarvikMap=$stagedMap;originalSkarvikPreserved=$originalPresent
 stagedSm5TargetPresent=$sm5;freeDiskD_GB=$freeGb
 cityImported=$false;playtested=$false;trafficDisabled=$false;crowdsDisabled=$false
 originalFilesModified=$false
 guidance='Keep SKARVIK 48x48 backup and other maps. City Sample Big City is ~4x4km. Never switch world catalog until native SM5 tests pass.'
}
$json=$report|ConvertTo-Json -Depth 5
Write-Output $json
if($ReportPath){
 $folder=Split-Path -Parent $ReportPath
 if($folder -and !(Test-Path -LiteralPath $folder)){New-Item -ItemType Directory -Path $folder -Force|Out-Null}
 Set-Content -LiteralPath $ReportPath -Value $json -Encoding UTF8
}
