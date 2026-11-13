param([Parameter(Mandatory=$true)][string]$Script,[Parameter(Mandatory=$true)][string]$LogName,[int]$Seconds=1200)
$ErrorActionPreference='Stop'
$root='D:\ANOMALIAZ\01_Projet_Principal\unreal'
$effect=Join-Path $root 'Content\Effect\Vehicle\Niagara\VehicleDamageSystem_Runtime.uasset'
$held=Join-Path $env:SCENE_REPAIR_OUT ($LogName+'.held-effect.uasset')
$expected='6958C967A29C644C51B8C30D76308AB9A80C87FA716BEC7ED7ABB1766E96D6BF'
$moved=$false
$process=$null
try{
 if(Test-Path -LiteralPath $effect){
  if((Get-FileHash -LiteralPath $effect).Hash -ne $expected){throw 'Known traffic effect changed; preserve original'}
  Move-Item -LiteralPath $effect -Destination $held
  $moved=$true
 }
 $editor=Join-Path $env:UE_ROOT 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
 $log=Join-Path $env:SCENE_REPAIR_OUT ($LogName+'.log')
 $process=Start-Process -FilePath $editor -ArgumentList @((Join-Path $root 'AnomaliaPrimeval.uproject'),'/Engine/Maps/Entry',('-ExecutePythonScript="'+$Script+'"'),'-NullRHI','-unattended','-nopause','-nosound',('-abslog="'+$log+'"')) -PassThru
 $handle=$process.Handle
 $started=Get-Date
 $next=30
 while(-not $process.WaitForExit(3000)){
  $elapsed=((Get-Date)-$started).TotalSeconds
  if($elapsed -gt $Seconds -or -not(Test-Path -LiteralPath (Join-Path $root 'AnomaliaPrimeval.uproject'))){throw 'Owned editor reached its time budget or principal disk became unavailable'}
  foreach($drive in @('C','D')){if(([IO.DriveInfo]::new($drive)).AvailableFreeSpace -lt 1GB){throw ('Editor stopped before exhausting '+$drive+': disk reserve')}}
  if($elapsed -gt $next){Write-Host ($LogName+' active '+[int]$elapsed+'s');$next+=30}
 }
 if($process.ExitCode -ne 0){throw ('Principal editor exited '+$process.ExitCode)}
}finally{
 if($process -and -not $process.HasExited){& taskkill.exe /PID $process.Id /T /F|Out-Null;$process.WaitForExit(15000)|Out-Null}
 if($moved){
  if(Test-Path -LiteralPath $effect){throw 'Unexpected traffic effect replacement; held original preserved'}
  Move-Item -LiteralPath $held -Destination $effect
  if((Get-FileHash -LiteralPath $effect).Hash -ne $expected){throw 'Original effect restoration mismatch'}
 }
}
