# TESTING Rat verification

| Check | Evidence |
|---|---|
| Additive archives | Both registry payloads contain one added `E3RT` row. The original sections were verified byte for byte. The two localization keys were added to each text lookup registry; the original text bank bytes remain an exact prefix. |
| Producer ownership | At initializer return the game had 364 producers. E3RT and stock KBSH had distinct live pointers (first run `0x2fcf798` and `0x2fc8bb8`) with the same vtable `0x8c1a98`. |
| Summon and stats | Breakpoint `0x6ed7eb` recorded E3RT with power 5 and toughness 5 during native ability attachment. The second Duel showed two 5/5 Mantis models on the battlefield. Original 1/1 Stink Rats were visible separately. |
| Family and return to hand | The runtime family index returned `Rat` for E3RT. In the Lifecycle Duel, the player used the original Doom Rat's Brotherhood to recover the new creature from the graveyard and confirmed it was back in hand. |
| Native activation and damage dispatch | Breakpoint `0x6ed960` recorded the Shaman ability on a 5/5 E3RT instance. The repeat logged damage argument 1 for E3RT at both the hero receiver and the creature receiver. These traces record native calls. Final target health is a separate observation. |
| Model and animations | The player confirmed the Mantis animations looked correct in the Duels. Individual animation clips were not separately timed or logged. |
| Duel completion | The player completed both Duels normally. Both processes exited with code 0. |
| Encyclopedia | The player confirmed the additional Chaots entry and effect text. The first build had a blank large portrait even though the card artwork reference was present. In a fresh copy with the overlay, the player confirmed the complete large image appeared on the right in the same position as the original Mantis Patriarch portrait. |

Normal combat saves are unavailable through the shipped combat UI. Replay playback and a freshly saved preset round trip remain unverified. The observed graveyard-to-hand return is a separate gameplay check from direct battlefield Unsummon.

The portrait-check process also exited with code 0. Both generated registries were restored from stock in the disposable copies and their archive hashes verified. The added portrait overlay was removed, and both original texture archives and the executable matched the baseline.

## Version and hashes

| Input | Stock SHA-256 | TESTING Rat SHA-256 |
|---|---|---|
| `Etherlords2.exe` | `d3ed30f840b3325b1f03c01aa486e7f44328a7d6993964c409950a65e86a158b` | Same stock file. The producer is registered in memory. |
| `regs.res` | `e38ed76d8fcde2aeee1e22a89771e9eb05d95f3364e122a3024db929975970d7` | `006651c76291c40d76b17b5d417764d35f842044f5dc7dba46aff4c1b50d4950` |
| `text.res` | `0360ed75214fc2565fef1e3bb67b096323d6a9d5a4e17a87a72b38b7d6f9af6b` | `f74a61a8a370f895ad0d9f3f1b507289697d40d5a02c183bcd913965f38b66ae` |
| `textures001.res` | Empty archive slot in baseline | `d11cced416af2de46b8fdbea63ac091fb98a5c9792fa55c269e65280819f149f` |
