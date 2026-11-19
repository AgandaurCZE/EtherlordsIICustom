# Card Creator verification

Tested with the pinned English Windows 1.03 executable `d3ed30f840b3325b1f03c01aa486e7f44328a7d6993964c409950a65e86a158b`.

## Reproducible checks

- Open both example projects. The two-card project and the five-card project must build independently from the stock input. Build again and check the package directory name and file hashes match.
- Try an existing card ID, a repeated custom ID, an invalid health value, and a PNG with the wrong dimensions. The validation view should identify each invalid input before producing a package.
- Use **Build Mod**, **Create Disposable Copy** and **Launch Test Game** for the five-card fixture. Its package must include all five metadata entries, the corresponding producer definitions, and the four-faction-aware preset layout. A stock game is only used as a read-only source.
- In Duel mode, start the generated Chaots deck against a stock deck. Summon E3RT and activate Shaman Zap, and cast E3TC with creatures present. Check the in-game Encyclopedia and save a new test preset if verifying deck round trips.
- While the test game is running, installation and rollback should refuse to proceed. Close the game and roll back. The preexisting files must match the original SHA-256 values, and the generated portrait archive and test preset must be absent.

Developers can run `python verify_build.py <stock-game-folder>` for the deterministic builds, stock record preservation, validation failures and artwork conversion checks. The command never stages to a game folder.

## Recorded evidence

| Check | Result |
|---|---|
| Desktop workflow | The editor loaded the stock catalog, built the five-card project, created package `card-creator-0.1.0-3f360e6cf7d9`, installed it into a disposable copy and launched the game through the Diagnostics page. A separate editor smoke test created a creature, edited its health, saved the project and reopened the resulting data. |
| Native ownership and scope | The log verified 368 producers and distinct allocations for `E3RT`, `E3TC`, `E3TG`, `E3TS` and `E3TU`. All stock combat records compared byte for byte. |
| Actual combat | The player used the generated deck in a Duel, confirmed the custom cards’ stats and effects, and completed the match. TESTING CARD returned creatures to hand in the same match that used TESTING Rat. The debugger recorded E3RT at 5/5 during Shaman attachment and activation. |
| Exit | The installed five-card process exited with code 0 and emitted no access violation. Longer-running stress and cleanup tests remain open. |
| GUI rollback | With the game closed, **Roll Back a Game Copy** restored both stock resource hashes, removed the generated preset, overlay and backup, and kept the stock executable and artwork hashes intact. The Windows process guard separately detected the running game before rollback. |
| Build verification | The two-card and five-card projects rebuilt deterministically. The negative checks rejected duplicate and stock IDs and invalid health. The converter packed a 384 × 512 PNG into three MMP tiles. |
| In-game artwork and Encyclopedia | A separate `card-creator-0.1.0-d8f585418bf6` package used an original gold-shield PNG for `E3TG`. The player confirmed the large image on the right side, stock-model portraits for the other creatures, and the additional spell entries under Chaots. The spell detail panes follow stock behavior. The portrait test copy was also restored and hash-verified. |

The game’s normal combat menu lacks a live save facility. The generated Duel preset loaded successfully. A newly saved Duel deck, replay playback and campaign save/load remain separate compatibility checks. The launcher detects installed metadata without a matching producer definition and reports missing card IDs in a Duel preset before starting the game.
