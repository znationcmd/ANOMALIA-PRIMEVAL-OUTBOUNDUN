param()
$ErrorActionPreference='Stop'
$module=Join-Path $PSScriptRoot '..\scripts\ue5\differential-version-store.ps1'
. ([IO.Path]::GetFullPath($module))
$root=Join-Path $env:TEMP ('anomalia-diff-test-'+[Guid]::NewGuid().ToString('N'))
$base=Join-Path $root 'base'
$source=Join-Path $root 'source'
$stage=Join-Path $root 'versions\candidate'
New-Item -ItemType Directory -Path $base,$source -Force|Out-Null
try {
    Set-Content -LiteralPath (Join-Path $base 'keep.txt') -Value 'same bytes' -NoNewline
    Set-Content -LiteralPath (Join-Path $base 'change.txt') -Value 'old bytes' -NoNewline
    Set-Content -LiteralPath (Join-Path $base 'obsolete.txt') -Value 'remove this' -NoNewline
    New-Item -ItemType Directory -Path (Join-Path $base 'Saved') -Force|Out-Null
    Set-Content -LiteralPath (Join-Path $base 'Saved\player.sav') -Value 'private save' -NoNewline
    Set-Content -LiteralPath (Join-Path $source 'keep.txt') -Value 'same bytes' -NoNewline
    Set-Content -LiteralPath (Join-Path $source 'change.txt') -Value 'new bytes' -NoNewline
    Set-Content -LiteralPath (Join-Path $source 'added.txt') -Value 'new file' -NoNewline
    New-Item -ItemType Directory -Path (Join-Path $source 'Saved') -Force|Out-Null
    Set-Content -LiteralPath (Join-Path $source 'Saved\player.sav') -Value 'new save must not ship in this snapshot' -NoNewline
    $pointer=Join-Path $root 'active.json'
    @{version='base';path=$base}|ConvertTo-Json|Set-Content -LiteralPath $pointer
    $result=Invoke-AnomaliaDifferentialVersionStage -SourceRoot $source -StagePath $stage -BaseVersionRoot $base -ExcludePaths @('Saved')
    if($result.state -ne 'DIFFERENTIAL_STAGE_VERIFIED'){throw 'Stage did not pass its final verification.'}
    if($result.hardlinksCreated -ne 3 -or $result.unchanged -ne 1 -or $result.replaced -ne 1 -or $result.added -ne 1 -or $result.removed -ne 1){throw ('Unexpected differential counters: '+($result|ConvertTo-Json -Compress))}
    if((Get-Content (Join-Path $stage 'change.txt') -Raw) -ne 'new bytes'){throw 'Changed file was not atomically replaced.'}
    if((Get-Content (Join-Path $base 'change.txt') -Raw) -ne 'old bytes'){throw 'Updating a hard link mutated the rollback version.'}
    if(Test-Path (Join-Path $stage 'obsolete.txt')){throw 'Obsolete file remains in the candidate.'}
    if(!(Test-Path (Join-Path $base 'obsolete.txt'))){throw 'Removing a candidate file mutated the rollback version.'}
    if(Test-Path (Join-Path $stage 'Saved')){throw 'Excluded user-data directory leaked into the version.'}
    if([AnomaliaDifferential.Native]::GetHardLinkCount((Join-Path $stage 'keep.txt')) -lt 2){throw 'Unchanged file is not shared as a hard link.'}
    $activeAfter=Get-Content $pointer -Raw|ConvertFrom-Json
    if($activeAfter.version -ne 'base' -or $activeAfter.path -ne $base){throw 'Stage creation changed the active pointer.'}
    Write-Output ($result|ConvertTo-Json -Compress)
    Write-Output 'DIFFERENTIAL INSTALLER TESTS PASSED'
} finally {
    if(Test-Path $root){Remove-Item -LiteralPath $root -Recurse -Force}
}
