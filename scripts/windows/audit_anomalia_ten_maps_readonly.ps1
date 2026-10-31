# Read-only 10-map inventory. All outputs go to RUNNER_TEMP, not game projects.
$ErrorActionPreference='Stop'
$reportDir=Join-Path $env:RUNNER_TEMP ('ANOMALIA_MAP_AUDIT_'+$env:GITHUB_RUN_ID)
New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
$catalog=Join-Path $env:GITHUB_WORKSPACE 'public\config\anomalia-map-catalog.json'
$data=Get-Content -LiteralPath $catalog -Raw -Encoding UTF8|ConvertFrom-Json
if(@($data.maps).Count -ne 10){throw 'Expected ten map entries'}
$projects=@(
 @{name='stage';root='D:\ANOMALIAZ-PRIGIMALIA\unreal';project='AnomaliaZPrigimalia.uproject'},
 @{name='original';root='D:\ANOMALIA\unreal';project='AnomaliaPrimeval.uproject'},
 @{name='runnerWorkspace';root=(Join-Path $env:GITHUB_WORKSPACE 'unreal');project='AnomaliaZPrigimalia.uproject'}
)
$all=@{}
foreach($entry in $projects){
 $content=Join-Path $entry.root 'Content'
 $valid=(Test-Path -LiteralPath (Join-Path $entry.root $entry.project) -PathType Leaf)
 $items=@()
 if(Test-Path -LiteralPath $content -PathType Container){
   $files=@(Get-ChildItem -LiteralPath $content -Filter '*.umap' -File -Recurse -ErrorAction Stop)
   foreach($f in $files){
     $relative=$f.FullName.Substring($content.TrimEnd('\').Length+1).Replace('\','/')
     $package='/Game/'+($relative -replace '\.umap$','')
     $items+=@{file=$f.FullName;package=$package;bytes=[int64]$f.Length;lastWriteUtc=$f.LastWriteTimeUtc.ToString('o')}
   }
 }
 $all[$entry.name]=@{root=$entry.root;projectPresent=$valid;worldFiles=@($items|Sort-Object package);mapCount=$items.Count}
 Write-Host ('ANOMALIA_MAP_FILES_'+$entry.name.ToUpperInvariant()+'='+$items.Count)
}
$outMaps=@()
foreach($world in $data.maps){
 $name=[string]$world.displayName
 $id=[string]$world.id
 $expected=[string]$world.originalUnrealPackage
 $worldProjects=@{}
 foreach($entry in $projects){
   $matches=@()
   foreach($f in @($all[$entry.name].worldFiles)){
      $leaf=[IO.Path]::GetFileNameWithoutExtension([string]$f.file)
      $normal=$name.Replace('.','').Replace(' ','')
      $matchByName=($leaf -eq ('PRIGIMALIA_'+$normal)) -or ($leaf -eq $normal)
      $matchByAlias=($f.package -eq $expected)
      if($id -eq 'inhabited-v2'){
         $matchByAlias=$matchByAlias -or $leaf -eq 'ANOMALIA_DrazoviaTopo_NewReferenceV3_Candidate'
      }
      if($matchByName -or $matchByAlias){
         $matches+=@{package=$f.package;file=$f.file;bytes=$f.bytes;exactConfiguredPackage=($f.package -eq $expected);candidateV3=($leaf -eq 'ANOMALIA_DrazoviaTopo_NewReferenceV3_Candidate')}
      }
   }
   $worldProjects[$entry.name]=@{projectPresent=$all[$entry.name].projectPresent;exactPackagePresent=(@($matches|Where-Object {$_.exactConfiguredPackage}).Count -gt 0);nativeFiles=@($matches)}
 }
 $outMaps+=@{id=$id;displayName=$name;configuredPackage=$expected;sizeKm=@([double]$world.widthKm,[double]$world.heightKm);catalogValidation=[string]$world.validation;projects=$worldProjects}
 Write-Host ('MAP_STAGE '+$name+' NATIVE_LEVEL_FILES='+@($worldProjects.stage.nativeFiles).Count+' CATALOG='+[string]$world.validation)
}
$report=@{schemaVersion=1;generatedUtc=[DateTime]::UtcNow.ToString('o');mode='read-only-file-inventory';runId=$env:GITHUB_RUN_ID;engineNativeLoadVerified=$false;gameplayTested=$false;stages=$all;maps=$outMaps;warning='File presence does not prove native World load, partition streaming, or playability'}
$path=Join-Path $reportDir 'map-file-inventory.json'
$report|ConvertTo-Json -Depth 20|Set-Content -LiteralPath $path -Encoding UTF8
Write-Host ('MAP_AUDIT_REPORT='+$path)
Write-Host 'READ_ONLY_MAP_FILE_INVENTORY_COMPLETE=true'
