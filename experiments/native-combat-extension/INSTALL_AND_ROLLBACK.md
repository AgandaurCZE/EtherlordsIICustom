# Prepare, run and roll back

Use 64-bit Python 3.11 or newer on Windows. Start with a legally obtained unmodified copy of the pinned build. From this directory, prepare one local profile per game copy. The preparer validates the supplied baseline and copies it without existing saves or replays.

```powershell
$baseline = 'E:\EtherlordsII-Baseline'
python prepare_probe.py zap-three $baseline zap-three-01
python combat_probe.py zap-three local/zap-three-01 local/zap-three-01.jsonl
```

The `alias` profile takes the hash-pinned additive archive pair from the [earlier builder](../new-spell-proof-of-concept/INSTALL.md). Build that pair first. Its default output path is discovered automatically. If using a different output directory, use `--metadata`.

```powershell
python prepare_probe.py alias $baseline alias-01
python combat_probe.py alias local/alias-01 local/alias-01.jsonl
```

Substitute `zap-mass`, `zap-chain` or `rat-brotherhood` in both commands for other independent games. Each command takes a new directory or log name. The runner monitors only the child it launches. Close the game to end the probe. If the launcher is interrupted, the debug session terminates its dedicated child. Start a new process to unload the gameplay changes.

## Duel fixtures

| Profile | Fixture and observation |
|---|---|
| `alias` | Use **Matrix 04 - Three E3TC** (Red, resource level 3) against a stock deck. Confirm the ID in the saved preset and draw the card. Cast with eligible creatures on both sides and record hand contents, animation and Ether. In a separate Duel use **Matrix 05 - GRUN Control** to check the original. |
| `alias-flat` | Prepare and launch using `alias-flat` in place of `alias`. Use the same fixture with at least one eligible creature on the battlefield. Compare the casting hero's Ether on the same turn and confirm it drops by 1 while the creatures still return. |
| `zap-three` | Use **Mechanics Zap** (or Chaot Beginner Deck) against **Mechanics Wall Target** or a stock deck. Cast on a hero, a creature above 3 health and a creature at or below 3 health. Record health within the same turn. Add a shield/prevention fixture before treating that case as verified. |
| `zap-mass` | Use the same presets. Put creatures on both sides, preferably two each at different health. Cast without selecting a target. Record surviving health, deaths and both heroes' health. Use original Lightning Storm as a separate control for the donor. |
| `zap-chain` | Use the same presets. Cast on an enemy creature above 1 health, an enemy creature at 1 health, a friendly creature and a hero in separate controlled cases. Check damage, each destination, animation order, and one normal Ether debit. Then test invalidated targets and changes of control before promoting this profile. |
| `rat-brotherhood` | Use **Mechanics Rat Ability** and summon Stink Rat. Put a Rat in your graveyard, keep the acting Rat ready and have 2 Ether. Use Brotherhood and confirm its target arrives in your hand. Repeat with original Doom Rat. |

The presets reuse [the new-spell fixtures](../new-spell-proof-of-concept/prepare_duel_matrix.py) and [the previously committed mechanics fixtures](../card-mechanics/duel-presets). This directory contains no game archives or executable. The JSONL event stream identifies image, writes, relevant breakpoints, exceptions and process exit. Ordinary handled first-chance exceptions during startup also occur under the stock debugger control.

## Rollback of disk resources

The original executable is never overwritten. Close the probe, leave its disposable folder unused or restore modified archives there from the pinned baseline, then compare SHA-256. The `alias` test stages `regs.res` and `text.res`. The `rat-brotherhood` test stages only `regs.res`. Zap profiles use stock archives. Keep experimental presets and saves in disposable copies, since the E3TC preset expects the extra registration. For a clean rerun, make a new copy with `prepare_probe.py`.

```powershell
$game = (Resolve-Path local/alias-01).Path
if (-not (Test-Path -LiteralPath (Join-Path $game '.native-combat-test'))) {
    throw 'Select the disposable test copy.'
}
$stock = @{
    'regs.res' = 'e38ed76d8fcde2aeee1e22a89771e9eb05d95f3364e122a3024db929975970d7'
    'text.res' = '0360ed75214fc2565fef1e3bb67b096323d6a9d5a4e17a87a72b38b7d6f9af6b'
}
foreach ($name in $stock.Keys) {
    $source = Join-Path $baseline "Resources/$name"
    $target = Join-Path $game "Resources/$name"
    if ((Get-FileHash -LiteralPath $source).Hash -ne $stock[$name]) { throw 'Wrong baseline.' }
    Copy-Item -LiteralPath $source -Destination $target
    if ((Get-FileHash -LiteralPath $target).Hash -ne $stock[$name]) { throw 'Restore failed.' }
}
```
