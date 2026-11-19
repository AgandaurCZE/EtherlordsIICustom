# Controlled Duel results

Each probe ran in its own disposable copy of the Windows 1.03 baseline. Both Rat copies changed only `regs.res`. The Zap copy changed only `text.res`. The tester drove the menus and turns. These observations combine the game views checked during the session with the tester's before-and-after measurements.

| Phase | Expected behavior | Observed result | Classification |
|---|---|---|---|
| A2. Stink Rat 1/1 → 3/3 | Real starting attack and health increase | Deck editor showed 3/3, and the battlefield showed a summoned 3/3. The tester reported an unblocked 3-damage hit against the enemy hero, a Rat dying after taking exactly 3 damage, and a normal Duel finish. | **SUCCESS** |
| A3. Rat’s Brotherhood | An activated Stink Rat ability can return a Rat from the graveyard | The game reached combat. The tester found no added ability in the Encyclopedia, deck editor or Duel. Read-only inspection identified Doom Rat’s separate ability construction and attachment. | **BLOCKED** |
| B2. Zap 1 → 3 | A selected creature or hero loses 3 health | Card text said 3. Aviak Scout went from 1/2 to 1/1, and the enemy hero went from 19 to 18. Both native target paths dealt 1. | **BLOCKED** |
| B3. Zap damages all creatures | Both sides’ creatures lose 3 health from one Zap | The conditional cast test did not start because B2 failed. Zap’s native branch resolves a single selected object. The stock Lightning Storm effect is separate. | **BLOCKED** |
| B4. Zap plus Unsummon | One Zap damages a creature and returns it to hand if it survives | Read-only inspection found separate native producers and no data-driven sequence in Zap. No same-resolution runtime variant was built. | **BLOCKED** |

Separate A2 Encyclopedia observation, healing and combat save/load were unverified. In B2 the recorded creature had 2 health before the cast. Separate high-health and lethal-damage cases were unverified. The reported Zap damage outcomes are surviving-target observations.

## Archive checks

| Phase | Archive | Modified SHA-256 |
|---|---|---|
| A2 | `regs.res` | `39b654623184bf783c043711172bb8b3660e6b0be4d22d99fd3a06a81b4c45d2` |
| A3 | `regs.res` | `1c86758929e6dde3ab5dd72f8695322d5f1f9b0b98f2a5e31a7e60c6174e9aba` |
| B2 | `text.res` | `b3bf8356e168628a24bea35544c20deaebb6bc3d87a8125554c30283c0cd27e2` |

The A2 and A3 copies were restored to stock `regs.res` SHA-256 `e38ed76d8fcde2aeee1e22a89771e9eb05d95f3364e122a3024db929975970d7`. B2 was restored to stock `text.res` SHA-256 `0360ed75214fc2565fef1e3bb67b096323d6a9d5a4e17a87a72b38b7d6f9af6b`.
