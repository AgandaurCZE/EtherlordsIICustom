# Etherlords III campaign UI @VERSION@

Package ID `@PACKAGE_ID@`.

This package was built against the pinned English Windows 1.03 research baseline. That baseline already contains the project's custom localization. Use a separate, working game copy with matching source hashes. Close the game before installation or rollback. Extract this ZIP into its own folder outside the game copy. Keep this document with the package.

Copy the PowerShell script below into a file named `install-campaign-ui.ps1` at the root of the extracted package. From PowerShell, pass the absolute path of the disposable game copy. The script uses the package beside itself.

```powershell
.\install-campaign-ui.ps1 -GameCopy 'E:\EtherlordsIII-Test' -Action Install
```

The script verifies the package and all affected game archives before changing any of them. It backs up source files under `.etherlords-iii-ui-backup` in the game copy and verifies each backup before use. It replaces each archive atomically. If the operation is interrupted between archives, rerun the same action to finish or run rollback. Unexpected hashes stop the operation. For a newer package, roll back the current package first and then run the newer package's installer.

Open **Single → Campaign → New Campaign** and check the Green title and portrait alongside Chaots. Continue to the overview to check the map, the current marker and the hover labels. Advance through Chapter 1 to check the next route segment. The stock game supplies the unlock sequence and marker sprites.

Roll back with the same script and game copy. The backup is retained and the script checks the restored files against the source hashes.

```powershell
.\install-campaign-ui.ps1 -GameCopy 'E:\EtherlordsIII-Test' -Action Rollback
```

| Archive | Source SHA-256 | Modified SHA-256 |
| --- | --- | --- |
@SHA256_TABLE@

## Copy this script

```powershell
param(
    [Parameter(Mandatory)][string]$GameCopy,
    [Parameter(Mandatory)][ValidateSet('Install', 'Rollback')][string]$Action
)

$ErrorActionPreference = 'Stop'
$archives = [ordered]@{
@ARCHIVE_RECORDS@
}

function Assert-Hash([string]$Path, [string]$Expected) {
    if ((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash -ne $Expected) {
        throw "SHA-256 mismatch for $Path"
    }
}

function Publish-Archive([string]$From, [string]$To, [string]$Expected, [string]$Previous) {
    $temp = Join-Path (Split-Path -Parent $To) ('.campaign-ui-' + [Guid]::NewGuid() + '.tmp')
    try {
        [IO.File]::Copy($From, $temp)
        Assert-Hash $temp $Expected
        if ($Previous) {
            Assert-Hash $To $Previous
            [IO.File]::Replace($temp, $To, [NullString]::Value)
        } else {
            [IO.File]::Move($temp, $To)
        }
        Assert-Hash $To $Expected
    } finally {
        if ([IO.File]::Exists($temp)) { [IO.File]::Delete($temp) }
    }
}

$game = (Resolve-Path -LiteralPath $GameCopy).ProviderPath
if (!(Test-Path -LiteralPath (Join-Path $game 'Etherlords2.exe') -PathType Leaf)) {
    throw 'GameCopy must point to a separate Etherlords II game copy.'
}
if (Test-Path -LiteralPath (Join-Path $game '.git')) {
    throw 'Use a separate game copy outside the research checkout.'
}
if (Get-Process -Name Etherlords2 -ErrorAction SilentlyContinue) {
    throw 'Close Etherlords II before changing its resources.'
}
$backupRoot = Join-Path $game '.etherlords-iii-ui-backup'
$backup = Join-Path $backupRoot '@PACKAGE_ID@'
$gameResources = Join-Path $game 'Resources'
$packageResources = Join-Path $PSScriptRoot 'Resources'
foreach ($path in $game, $gameResources, $backupRoot, $backup) {
    if ((Test-Path -LiteralPath $path) -and
        ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw "Use a disposable copy with regular directories. Found a redirected path at $path"
    }
}
[void][IO.Directory]::CreateDirectory($backupRoot)
$lockPath = Join-Path $backupRoot 'archive-transaction.lock'
$lock = [IO.File]::Open($lockPath, 'OpenOrCreate', 'ReadWrite', 'None')
try {
    $current = @{}
    foreach ($name in $archives.Keys) {
        $target = Join-Path $gameResources $name
        $saved = Join-Path $backup $name
        $expected = $archives[$name]
        $current[$name] = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
        if ($current[$name] -ne $expected.Source -and $current[$name] -ne $expected.Patched) {
            throw "Unrecognized archive at $target. Restore the pinned baseline first."
        }
        if (Test-Path -LiteralPath $saved) {
            Assert-Hash $saved $expected.Source
        } elseif ($current[$name] -eq $expected.Patched) {
            throw "Original backup is missing for $target"
        }
        if ($Action -eq 'Install') {
            Assert-Hash (Join-Path $packageResources $name) $expected.Patched
        }
    }

    if ($Action -eq 'Install') {
        [void][IO.Directory]::CreateDirectory($backup)
        foreach ($name in $archives.Keys) {
            $saved = Join-Path $backup $name
            if (!(Test-Path -LiteralPath $saved)) {
                Publish-Archive (Join-Path $gameResources $name) $saved $archives[$name].Source ''
            }
        }
    }

    foreach ($name in $archives.Keys) {
        $target = Join-Path $gameResources $name
        $expected = $archives[$name]
        if ($Action -eq 'Install' -and $current[$name] -eq $expected.Source) {
            Publish-Archive (Join-Path $packageResources $name) $target $expected.Patched $expected.Source
        }
        if ($Action -eq 'Rollback' -and $current[$name] -eq $expected.Patched) {
            Publish-Archive (Join-Path $backup $name) $target $expected.Source $expected.Patched
        }
    }
    foreach ($name in $archives.Keys) {
        $digest = if ($Action -eq 'Install') { $archives[$name].Patched } else { $archives[$name].Source }
        Assert-Hash (Join-Path $gameResources $name) $digest
    }
    Write-Output "$Action complete. All archive checksums verified."
} finally {
    $lock.Dispose()
}
```
