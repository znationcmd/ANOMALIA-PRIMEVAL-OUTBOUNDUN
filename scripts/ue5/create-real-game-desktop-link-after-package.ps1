# Create ONE Windows "JOUER" desktop shortcut only after a genuine UE5 Win64
# package and a headless load of the actual SKARVIK world have passed.
# Never pretend that a C++ build target or an editor launcher is a playable game.
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$PackageStatusPath,
  [string]$ReportPath=(Join-Path $env:RUNNER_TEMP 'anomaliaz-genuine-game-desktop.json')
)
$ErrorActionPreference='Stop'
$report=[ordered]@{
 state='NOT_PACKAGED'
 playShortcutCreated=$false
 playableGamePackageFound=$false
 nativeSkarvikSmokePassed=$false
 fullVisualGameTestPassed=$false
 autoUpdaterShipped=$false
 realGameExe=$null
 packagingStatus=$null
 error=$null
}
function SaveReport{
 ($report|ConvertTo-Json -Depth 6)|Set-Content -LiteralPath $ReportPath -Encoding UTF8
}
try {
 if(!(Test-Path -LiteralPath $PackageStatusPath -PathType Leaf)){throw 'Native package receipt absent'}
 $status=Get-Content -LiteralPath $PackageStatusPath -Raw | ConvertFrom-Json
 $report.packagingStatus=[string]$status.state
 if($status.state -ne 'NATIVE_SKARVIK_ALPHA_PACKAGED_NOT_YET_PLAYTESTED' -or !$status.packagedExeExists){
   $report.state='WAITING_FOR_REAL_COOKED_WINDOWS_GAME_AND_SAFE_NTFS_STORAGE'
   Write-Host 'ANOMALIAZ_DESKTOP_PLAY_BUTTON_NOT_YET_CREATED_NO_REAL_PACKAGE=true'
   return
 }
 $exe=[string]$status.executablePath
 if(!(Test-Path -LiteralPath $exe -PathType Leaf)){throw 'Claimed native Windows executable does not exist'}
 $exeItem=Get-Item -LiteralPath $exe
 if($exeItem.Length -lt 40000){throw 'Packaged Win64 executable implausibly small'}
 if($exe -notmatch '[\\/]ANOMALIAZ_NATIVE_ALPHA_WIN64_RELEASES[\\/]run-[0-9]+[\\/]'){throw 'Game exe not inside an owned/versioned output folder'}
 $top=($exe -split '(?i)\\ANOMALIAZ_NATIVE_ALPHA_WIN64_RELEASES\\run-\d+\\')[0]
 $runRoot=[regex]::Match($exe,'(?i)^.+?\\ANOMALIAZ_NATIVE_ALPHA_WIN64_RELEASES\\run-\d+\\').Value.TrimEnd('\')
 if(!$runRoot -or !(Test-Path -LiteralPath $runRoot -PathType Container)){throw 'Native owned package output directory missing'}
 $packs=@(Get-ChildItem -LiteralPath $runRoot -Recurse -File -ErrorAction Stop|
   Where-Object {$_.Extension -in @('.pak','.utoc','.ucas') -and $_.Length -gt 1048576})
 if(!(@($packs|Where-Object Extension -eq '.pak').Count -gt 0 -or
     (@($packs|Where-Object Extension -eq '.utoc').Count -gt 0 -and
      @($packs|Where-Object Extension -eq '.ucas').Count -gt 0))){
   throw 'No real cooked .pak or paired .utoc/.ucas game contents: never create a fake Play button'
 }
 $report.playableGamePackageFound=$true
 $report.realGameExe=$exe
 # The packaged exe can be launched in unattended NullRHI mode to exercise
 # genuine package/module/map startup; no simulated game or local HTML wrapper.
 $log=Join-Path $env:RUNNER_TEMP ('anomaliaz-skarvik-smoke-'+$env:GITHUB_RUN_ID+'.log')
 $args=@('-nullrhi','-unattended','-nosplash','-nosound','-log',"-abslog=$log",'-ExecCmds=quit')
 $p=Start-Process -FilePath $exe -ArgumentList $args -PassThru -ErrorAction Stop
 try {
   if(!$p.WaitForExit(90000)){
     $p.Kill();throw 'Packaged native game did not exit within 90-second map startup smoke test'
   }
   if($p.ExitCode -ne 0){throw ('Packaged native game exited nonzero '+$p.ExitCode)}
 }finally{
   if(!$p.HasExited){Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue}
 }
 if(!(Test-Path -LiteralPath $log -PathType Leaf)){throw 'Game emitted no Unreal startup log; cannot verify real map'}
 $content=Get-Content -LiteralPath $log -Raw -ErrorAction Stop
 if($content -notmatch '(?i)PRIGIMALIA_SKARVIK_FINAL_v1' -or
    $content -notmatch '(?i)(LoadMap|Bringing World|WorldPartition|GameMode)' -or
    $content -match '(?i)(Fatal error|EXCEPTION_ACCESS_VIOLATION|Failed to load (?:Map|Package))'){
   throw 'Real SKARVIK Win64 world startup not independently proven by Unreal log'
 }
 $report.nativeSkarvikSmokePassed=$true
 $desk=[Environment]::GetFolderPath('Desktop')
 if(!(Test-Path -LiteralPath $desk -PathType Container)){throw 'Interactive user desktop not found'}
 $shells=@(Get-CimInstance Win32_Process -Filter "name='explorer.exe'" -ErrorAction Stop)
 $identity=[System.Security.Principal.WindowsIdentity]::GetCurrent().Name.Split('\')[-1]
 $isDesktopOwner=$false
 foreach($x in $shells){
   try{$owner=Invoke-CimMethod -InputObject $x -MethodName GetOwner
       if($owner.User -ieq $identity){$isDesktopOwner=$true;break}
   }catch{}
 }
 if(!$isDesktopOwner){throw 'Runner does not own the interactive Desktop; do not create shortcut in wrong account'}
 $link=Join-Path $desk 'ANOMALIAZ - JOUER (ALPHA TEST).lnk'
 if(Test-Path -LiteralPath $link -PathType Leaf){
   $old=(New-Object -ComObject WScript.Shell).CreateShortcut($link)
   if($old.TargetPath -ine $exe){
     $archive=Join-Path $desk 'ANOMALIAZ - anciens raccourcis (sauvegardes)'
     if(!(Test-Path -LiteralPath $archive)){New-Item -ItemType Directory -Path $archive -Force|Out-Null}
     $oldCopy=Join-Path $archive ('ANOMALIAZ-JOUER-before-'+$env:GITHUB_RUN_ID+'.lnk')
     if(Test-Path -LiteralPath $oldCopy){throw 'Old desktop link backup already exists'}
     Copy-Item -LiteralPath $link -Destination $oldCopy
   }
 }
 $w=New-Object -ComObject WScript.Shell
 $tmp=Join-Path $desk ('ANOMALIAZ-JOUER-'+$env:GITHUB_RUN_ID+'.lnk')
 if(Test-Path -LiteralPath $tmp){throw 'Pending shortcut with same run name already exists'}
 $shortcut=$w.CreateShortcut($tmp)
 $shortcut.TargetPath=$exe
 $shortcut.WorkingDirectory=Split-Path -Parent $exe
 $shortcut.Description="ANOMALIA'Z - vrai jeu Unreal Engine Win64, version alpha de test"
 $shortcut.IconLocation=$exe+',0'
 $shortcut.Save()
 if(!(Test-Path -LiteralPath $tmp)){throw 'Shortcut save failed'}
 Move-Item -LiteralPath $tmp -Destination $link -Force
 $saved=$w.CreateShortcut($link)
 if($saved.TargetPath -ine $exe){throw 'Created play link points to wrong binary'}
 $report.playShortcutCreated=$true
 $report.state='GENUINE_PACKAGED_UE5_GAME_BOOT_SMOKE_PASSED_DESKTOP_ALPHA_LINK_CREATED'
 Write-Host ('ANOMALIAZ_REAL_PLAY_LINK='+$link)
 Write-Host ('ANOMALIAZ_REAL_PLAY_EXE='+$exe)
 Write-Host 'ANOMALIAZ_PLAY_BUTTON_IS_NOT_EDITOR_OR_FAKE_DEMO=true'
 Write-Host 'ANOMALIAZ_FULL_VISUAL_PLAYTEST_NOT_YET_PROVEN=true'
}catch{
 $report.state='NO_DESKTOP_PLAY_LINK_UNLESS_GENUINE_GAME_STARTS'
 $report.error=$_.Exception.Message
 Write-Host ('ANOMALIAZ_NATIVE_PLAY_LINK_SAFETY_BLOCKER='+$report.error)
}finally{
 SaveReport
 Write-Host ('ANOMALIAZ_NATIVE_PLAY_LINK_STATE='+$report.state)
}
# If packaging is simply blocked by space, leave the main compile workflow
# successful and do NOT make a shortcut. On a real but faulty package, stop.
if($report.state -eq 'WAITING_FOR_REAL_COOKED_WINDOWS_GAME_AND_SAFE_NTFS_STORAGE'){exit 0}
if(!$report.playShortcutCreated){exit 2}
