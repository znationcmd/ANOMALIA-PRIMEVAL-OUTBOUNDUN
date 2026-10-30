Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

function Test-AnomaliaZPrigimaliaExcludedPath {
    param([string]$RelativePath,[string[]]$ExcludePaths)
    $relative = $RelativePath.Replace([char]47,[char]92).TrimStart([char[]]@([char]92,[char]47))
    foreach($raw in $ExcludePaths) {
        if([string]::IsNullOrWhiteSpace($raw)){continue}
        $exclude = $raw.Replace([char]47,[char]92).Trim([char[]]@([char]92,[char]47))
        if($relative.Equals($exclude,[StringComparison]::OrdinalIgnoreCase)){return $true}
        if($exclude.Contains('\')) {
            if($relative.StartsWith($exclude+'\',[StringComparison]::OrdinalIgnoreCase)){return $true}
        } elseif(@($relative.Split([char]92)) -contains $exclude) { return $true }
    }
    return $false
}

function Get-AnomaliaZPrigimaliaManagedFiles {
    param([Parameter(Mandatory=$true)][string]$Root,[string[]]$ExcludePaths=@())
    $rootFull=[IO.Path]::GetFullPath($Root).TrimEnd([char[]]@([char]92,[char]47))
    if(!(Test-Path -LiteralPath $rootFull -PathType Container)){throw "Managed directory missing: $rootFull"}
    $pending=New-Object System.Collections.Stack
    $pending.Push($rootFull)
    while($pending.Count -gt 0) {
        $directory=[string]$pending.Pop()
        foreach($entry in [IO.Directory]::EnumerateFileSystemEntries($directory)) {
            $item=Get-Item -LiteralPath $entry -Force
            if(($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){continue}
            $relative=$entry.Substring($rootFull.Length).TrimStart([char[]]@([char]92,[char]47))
            if(Test-AnomaliaZPrigimaliaExcludedPath -RelativePath $relative -ExcludePaths $ExcludePaths){continue}
            if($item.PSIsContainer){$pending.Push($entry)}else{Write-Output $item}
        }
    }
}

if(-not ('AnomaliaZPrigimaliaDifferential.Native' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;
namespace AnomaliaZPrigimaliaDifferential {
    public struct BY_HANDLE_FILE_INFORMATION {
        public uint FileAttributes;
        public System.Runtime.InteropServices.ComTypes.FILETIME CreationTime;
        public System.Runtime.InteropServices.ComTypes.FILETIME LastAccessTime;
        public System.Runtime.InteropServices.ComTypes.FILETIME LastWriteTime;
        public uint VolumeSerialNumber;
        public uint FileSizeHigh;
        public uint FileSizeLow;
        public uint NumberOfLinks;
        public uint FileIndexHigh;
        public uint FileIndexLow;
    }
    public static class Native {
        [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
        public static extern bool CreateHardLink(string newFileName, string existingFileName, IntPtr securityAttributes);
        [DllImport("kernel32.dll", SetLastError=true)]
        public static extern bool GetFileInformationByHandle(SafeFileHandle file, out BY_HANDLE_FILE_INFORMATION info);
        public static uint GetHardLinkCount(string path) {
            using (FileStream stream = File.OpenRead(path)) {
                BY_HANDLE_FILE_INFORMATION info;
                if (!GetFileInformationByHandle(stream.SafeFileHandle, out info)) {
                    throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
                }
                return info.NumberOfLinks;
            }
        }
    }
}
'@
}

function Invoke-AnomaliaZPrigimaliaDifferentialVersionStage {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$SourceRoot,
        [Parameter(Mandatory=$true)][string]$StagePath,
        [string]$BaseVersionRoot,
        [string[]]$ExcludePaths=@()
    )
    $source=[IO.Path]::GetFullPath($SourceRoot)
    $stage=[IO.Path]::GetFullPath($StagePath)
    if(!(Test-Path -LiteralPath $source -PathType Container)){throw "Update source missing: $source"}
    if(Test-Path -LiteralPath $stage){throw "Stage path already exists; preserving it: $stage"}
    $parent=Split-Path -Parent $stage
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    $base=$null
    if($BaseVersionRoot) {
        $base=[IO.Path]::GetFullPath($BaseVersionRoot)
        if(!(Test-Path -LiteralPath $base -PathType Container)){throw "Base version missing: $base"}
        if(-not ([IO.Path]::GetPathRoot($base).Equals([IO.Path]::GetPathRoot($stage),[StringComparison]::OrdinalIgnoreCase))){throw 'Hard-link snapshots require the same NTFS volume.'}
    }
    $report=[ordered]@{state='FAILED';source=$source;stage=$stage;base=$base;files=0;hardlinksCreated=0;unchanged=0;replaced=0;added=0;removed=0;bytesCopied=0}
    try {
        New-Item -ItemType Directory -Path $stage | Out-Null
        $baseFiles=@()
        if($base) {
            $baseFiles=@(Get-AnomaliaZPrigimaliaManagedFiles -Root $base -ExcludePaths $ExcludePaths)
            foreach($file in $baseFiles) {
                $relative=$file.FullName.Substring($base.Length).TrimStart([char[]]@([char]92,[char]47))
                $destination=Join-Path $stage $relative
                New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
                if(-not [AnomaliaZPrigimaliaDifferential.Native]::CreateHardLink($destination,$file.FullName,[IntPtr]::Zero)) {
                    $code=[Runtime.InteropServices.Marshal]::GetLastWin32Error()
                    throw "Cannot create base snapshot hard link ($code): $relative"
                }
                $report.hardlinksCreated++
            }
        }
        $sourceFiles=@(Get-AnomaliaZPrigimaliaManagedFiles -Root $source -ExcludePaths $ExcludePaths)
        $sourceSet=@{}
        foreach($file in $sourceFiles) {
            $relative=$file.FullName.Substring($source.Length).TrimStart([char[]]@([char]92,[char]47))
            $sourceSet[$relative]=$true
            $destination=Join-Path $stage $relative
            New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
            $sourceHash=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
            if(Test-Path -LiteralPath $destination -PathType Leaf) {
                $destinationHash=(Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash
                if($destinationHash -eq $sourceHash){$report.unchanged++;continue}
            }
            $temporary=$destination+'.anomalia-'+[Guid]::NewGuid().ToString('N')+'.tmp'
            Copy-Item -LiteralPath $file.FullName -Destination $temporary
            if((Get-FileHash -LiteralPath $temporary -Algorithm SHA256).Hash -ne $sourceHash) {
                Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue
                throw "Differential staged hash mismatch: $relative"
            }
            if(Test-Path -LiteralPath $destination -PathType Leaf) {
                $replacementBackup=$destination+'.anomalia-old-'+[Guid]::NewGuid().ToString('N')+'.tmp'
                [IO.File]::Replace($temporary,$destination,$replacementBackup,$true)
                if(Test-Path -LiteralPath $replacementBackup){Remove-Item -LiteralPath $replacementBackup -Force}
                $report.replaced++
            } else {
                [IO.File]::Move($temporary,$destination)
                $report.added++
            }
            $report.bytesCopied += [int64]$file.Length
        }
        foreach($file in $baseFiles) {
            $relative=$file.FullName.Substring($base.Length).TrimStart([char[]]@([char]92,[char]47))
            if(-not $sourceSet.ContainsKey($relative)) {
                $destination=Join-Path $stage $relative
                if(Test-Path -LiteralPath $destination -PathType Leaf){Remove-Item -LiteralPath $destination -Force}
                $report.removed++
            }
        }
        $report.files=$sourceFiles.Count
        foreach($file in $sourceFiles) {
            $relative=$file.FullName.Substring($source.Length).TrimStart([char[]]@([char]92,[char]47))
            $destination=Join-Path $stage $relative
            if(!(Test-Path -LiteralPath $destination -PathType Leaf)){throw "Staged file missing: $relative"}
            if((Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash){throw "Staged verification mismatch: $relative"}
        }
        $report.state='DIFFERENTIAL_STAGE_VERIFIED'
        [pscustomobject]$report
    } catch {
        if(Test-Path -LiteralPath $stage){Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue}
        throw
    }
}
