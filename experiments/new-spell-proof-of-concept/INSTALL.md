# Build and roll back the local TESTING CARD probe

This is an Encyclopedia and deck-editor probe. The game closed after the test preset was confirmed, and the read-only trace shows a missing producer if combat attempts to instantiate `E3TC`. Use a disposable copy for any test. Keep the generated archives and copied game local.

## Build

From this experiment directory, set `$baseline` to a local 1.03 game tree with the pinned resource files, then build with Python 3.11 or newer. No third-party Python packages are needed.

```powershell
$baseline = (Resolve-Path 'E:\EtherlordsII-Baseline').Path
python spell_lab.py --resources (Join-Path $baseline 'Resources') inspect GRUN UNSM LSUS
python spell_lab.py --resources (Join-Path $baseline 'Resources') build
python native_producers.py (Join-Path $baseline 'Etherlords2.exe') GRUN UNSM LSUS E3TC
```

The build verifies source hashes, original sections, and replacement RES members. It writes only `regs.res`, `text.res`, and `checksums.json` under the ignored `local/metadata-probe/`. Use `build --output local/rebuild` for a new build; existing output directories are refused.

## Install into a new game copy

Run the following in PowerShell 7 from the experiment directory with the game closed. Keep the same session for the rollback variables. Use a baseline outside the experiment directory.

```powershell
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path local).Path
$game = Join-Path $root 'spell-test-game'
$probe = Join-Path $root 'metadata-probe'
if (Test-Path -LiteralPath $game) { throw 'The disposable target must be a new directory.' }
if (Get-Process -Name Etherlords2 -ErrorAction SilentlyContinue) { throw 'Close the game first.' }
robocopy $baseline $game /E /XD .git .campaign-ui-local local /XF shot*.bmp /NJH /NJS /NFL /NDL /NP
if ($LASTEXITCODE -ge 8) { throw 'Game copy failed.' }

$sums = Get-Content -LiteralPath (Join-Path $probe 'checksums.json') -Raw | ConvertFrom-Json -AsHashtable
$backup = New-Item -Type Directory (Join-Path $game '.spell-probe-backup')
$names = 'regs.res', 'text.res'
foreach ($name in $names) {
    $original = Join-Path $game "Resources/$name"
    $patched = Join-Path $probe $name
    if ((Get-FileHash -LiteralPath $original).Hash -ne $sums[$name].source_sha256 -or
        (Get-FileHash -LiteralPath $patched).Hash -ne $sums[$name].probe_sha256) {
        throw "Unexpected archive hash for $name"
    }
    $saved = Join-Path $backup.FullName $name
    Copy-Item -LiteralPath $original -Destination $saved
    if ((Get-FileHash -LiteralPath $saved).Hash -ne $sums[$name].source_sha256) {
        throw "Backup verification failed for $name"
    }
}
foreach ($name in $names) {
    $target = Join-Path $game "Resources/$name"
    Copy-Item -LiteralPath (Join-Path $probe $name) -Destination $target
    if ((Get-FileHash -LiteralPath $target).Hash -ne $sums[$name].probe_sha256) {
        throw "Installed probe hash mismatch for $name"
    }
}

$env:__COMPAT_LAYER = 'WIN2000'
Start-Process -FilePath (Join-Path $game 'Etherlords2.exe') -WorkingDirectory $game
```

Use **Encyclopedia → Chaots → Sorcery** to see the icon, cost, and description. For the deck editor, use **Single → Duel → New**, select Chaots and set resource level 3. Add the Greater Unsummoning illustration from Available Spells and save a new preset. The optional [Duel preset fixture](duel-testing-card.prs) can instead be copied under a new filename into the disposable game's `Duel` directory while it is closed. The in-game test used an equivalent preset saved through the editor. Use the fixture for inspecting the saved format and editor. Keep `E3TC` out of normal game and multiplayer decks because its combat producer is absent.

If Windows reports missing relative resources, launch with the game copy as the working directory. The command above does that. A separately failing installation may have a different cause.

## Roll back

Close the disposable game. Restore both backups and compare them with the build's source hashes. Move only the presets created for this probe into a local backup directory before launching with the stock archives, since those presets refer to an ID missing from the baseline.

```powershell
if (Get-Process -Name Etherlords2 -ErrorAction SilentlyContinue) { throw 'Close the game first.' }
foreach ($name in $names) {
    $saved = Join-Path $backup.FullName $name
    if ((Get-FileHash -LiteralPath $saved).Hash -ne $sums[$name].source_sha256) {
        throw "Backup verification failed for $name"
    }
}
foreach ($name in $names) {
    $target = Join-Path $game "Resources/$name"
    Copy-Item -LiteralPath (Join-Path $backup.FullName $name) -Destination $target
    if ((Get-FileHash -LiteralPath $target).Hash -ne $sums[$name].source_sha256) {
        throw "Rollback hash mismatch for $name"
    }
}
```
