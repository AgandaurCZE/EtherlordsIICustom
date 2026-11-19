# Build, test and restore

Use the pinned Windows 1.03 baseline from the previous spell experiment. Keep all generated archives, copied games and backups under an ignored local folder or outside the repository.

From this experiment directory, build a phase independently with Python 3.11 or newer.

```powershell
$baseline = (Resolve-Path 'E:\EtherlordsII-Baseline').Path
$phase = 'rat-stats'
python mechanics_probe.py --resources (Join-Path $baseline 'Resources') $phase
```

`rat-stats` writes a verified replacement `regs.res` and creates `local/rat-stats/rat-3x3-local.zip` with the archive, hashes and these instructions. The ZIP is local only. `rat-ability` applies the proven stat edit plus the three donor metadata fields from a stock input. `zap-ui-control` writes a deliberately labeled diagnostic tooltip to `text.res`, with the original mechanics intact. Use `--output local/new-test` to rebuild without replacing prior output.

## Apply in a fresh copy

Close the game and use PowerShell 7. This example expects the phase output above.

```powershell
$ErrorActionPreference = 'Stop'
$scratch = (Resolve-Path local).Path
$game = Join-Path $scratch ("game-" + $phase)
$stage = Join-Path $scratch $phase
if (Test-Path -LiteralPath $game) { throw 'Choose a new disposable game directory.' }
robocopy $baseline $game /E /XD .git .campaign-ui-local local /XF shot*.bmp /NJH /NJS /NFL /NDL /NP
if ($LASTEXITCODE -ge 8) { throw 'Game copy failed.' }
$sums = Get-Content -LiteralPath (Join-Path $stage 'checksums.json') -Raw | ConvertFrom-Json
$name = $sums.archive
if ($name -notin 'regs.res', 'text.res') { throw 'Unexpected archive name.' }
$target = Join-Path $game "Resources/$name"
$patch = Join-Path $stage $name
if ((Get-FileHash -LiteralPath $target).Hash -ne $sums.original -or
    (Get-FileHash -LiteralPath $patch).Hash -ne $sums.modified) {
    throw 'Input checksum mismatch.'
}
$backup = New-Item -ItemType Directory (Join-Path $game '.mechanics-backup')
$original = Join-Path $backup.FullName $name
Copy-Item -LiteralPath $target -Destination $original
if ((Get-FileHash -LiteralPath $original).Hash -ne $sums.original) { throw 'Backup hash mismatch.' }
Copy-Item -LiteralPath $patch -Destination $target
if ((Get-FileHash -LiteralPath $target).Hash -ne $sums.modified) { throw 'Staged hash mismatch.' }

$env:__COMPAT_LAYER = 'WIN2000'
Start-Process -FilePath (Join-Path $game 'Etherlords2.exe') -WorkingDirectory $game
```

If applying a previously built Rat ZIP, extract it to a new local directory, point `$stage` at that directory, and set `$patch = Join-Path $stage "Resources/$name"` in the same procedure.

For the Rat tests, the stock Chaot Beginner Deck contains Stink Rat. Choose Kinet Beginner Deck as the opponent. The optional **Mechanics Rat Ability** fixture includes both Stink Rat and the original Doom Rat. For the Zap test, copy `mechanics-zap.prs` and `mechanics-wall-target.prs` from [Duel presets](duel-presets) into the disposable game's `Duel` directory before launch. At resource level 3 use **Mechanics Zap** versus **Mechanics Wall Target**. If the game offers only its built-in decks, use the Chaot Beginner Deck for Zap. Measure the target's health before the cast and again in the same turn.

## Roll back

Close the disposable game. In the same shell, verify the backup and restore the original archive.

```powershell
if ((Get-FileHash -LiteralPath $original).Hash -ne $sums.original) { throw 'Backup hash mismatch.' }
if ((Get-FileHash -LiteralPath $target).Hash -ne $sums.modified) { throw 'Installed archive changed since staging.' }
Copy-Item -LiteralPath $original -Destination $target
if ((Get-FileHash -LiteralPath $target).Hash -ne $sums.original) { throw 'Rollback hash mismatch.' }
```
