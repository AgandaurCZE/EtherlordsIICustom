# Native combat experiment results

The player drove the Duels in isolated copies on 19 November 2026. The runner checked the exact build and recorded runtime evidence independently. The reported before-and-after observations come from the player.

| Feature | Classification | Evidence |
|---|---|---|
| E3TC uses Greater Unsummoning | **VERIFIED SUCCESS** | A separate Chaots spell appeared in hand and cast. Creatures on both sides returned to their respective heroes' hands with the familiar Kinets visual. A native debit-site trace read `E3TC` inside Greater Unsummoning's path. The registry had 364 entries and distinct producer pointers. |
| Zap deals 3 damage | **VERIFIED SUCCESS** | The hero took exactly 3 damage and a 2/3 Aviak Scout died. Both target branches reached their expected native damage calls. |
| Zap damages all creatures | **VERIFIED SUCCESS** | The player confirmed exactly 3 damage to all creatures. The debugger hit the donor loop's creature-damage site. |
| Zap damages and Unsummons | **VERIFIED SUCCESS** | Enemy 0/7 wall took 1 damage and immediately returned to hand from the same cast. A friendly wall took 1 and remained on the battlefield. The trace recorded 1 damage on `SLWL` before entering the Unsummon call. |
| 3/3 Stink Rat gains Brotherhood | **VERIFIED SUCCESS** | The debugger recorded attachment for spell ID `STRT`. The player activated Brotherhood on a surviving 3/3 Stink Rat and confirmed the dead Stink Rat returned to hand. |

## Debugger evidence

| Profile | Runtime site and result |
|---|---|
| `alias` | `0x73e27a` at initializer return: 364 entries; distinct `E3TC` and `GRUN` objects, both using vtable `0x8c22b4`. `0x6cccd9` passed by an `E3TC` instance on an empty-board cast. A later populated-board cast supplied the visible gameplay check. |
| `alias-flat` | In the debit trampoline, ID `E3TC`, one eligible creature and a surcharge argument of 0. The tester measured Ether dropping from 4/4 to 3/4 and returned both summoned Stink Rats to hand. The tester saw a temporary freeze and recovered without restarting. The debugger saw no access violation and recorded exit code 0. The cause of the pause was not established. |
| `zap-three` | Damage call sites observed at `0x6f22a2` (hero) and `0x6f22f0` (creature). |
| `zap-mass` | Damage call observed in the Lightning Storm loop at `0x6f4c2d`. |
| `zap-chain` | Original creature damage at `0x6f22f0` received 1. The wrapper reached the Unsummon call for `SLWL` with one point of accumulated damage. |
| `rat-brotherhood` | Ability attachment call observed at `0x6f0572` with `STRT`. |

The first E3TC launch attempt used the earlier static count of 343 as its guard and stopped when the new binding did not appear. Comparing the initializer against the live registry exposed 20 earlier inlined insertions. With the guard corrected to 363, E3TC registered and cast. The five gameplay profiles exited with code 0 and produced no access violations. A zero exit code establishes a clean application exit. Match completion is tracked separately from exiting.

## Pinned inputs

| File / variant | SHA-256 |
|---|---|
| Stock executable | `d3ed30f840b3325b1f03c01aa486e7f44328a7d6993964c409950a65e86a158b` |
| Stock `regs.res` | `e38ed76d8fcde2aeee1e22a89771e9eb05d95f3364e122a3024db929975970d7` |
| Stock `text.res` | `0360ed75214fc2565fef1e3bb67b096323d6a9d5a4e17a87a72b38b7d6f9af6b` |
| E3TC `regs.res` | `26592e61ae3b78b372deadd15546af63cf743ae41eb7168567c233cee3ed69e3` |
| E3TC `text.res` | `ff90849e81172c47505b7be90e5f5aa31f390bf713d7196296b66ebcce8f185f` |
| Stink Rat `regs.res` | `1c86758929e6dde3ab5dd72f8695322d5f1f9b0b98f2a5e31a7e60c6174e9aba` |

E3TC metadata sets a base cost of 1 Red Ether. The original `alias` profile retains Greater Unsummoning's per-creature charge. The distinct `alias-flat` profile verified a total cost of 1 Ether on a populated battlefield. The stock GRUN cast was verified in the earlier control matrix. This run independently confirmed that its registry slot was untouched and that the flat-cost gate is keyed to E3TC. A fresh stock GRUN cast under the flat-cost profile was not observed. A stock Doom Rat activation, shields and damage prevention, lethal and controller-change cases for the chain, full match completion for each profile, a combat save/load round trip, and multiplayer remain release checks.

After the sessions ended, the E3TC and Stink Rat test archives were restored from the pinned baseline. Hash checks matched both stock archives and the stock executable in every disposable copy. No runtime changes survived process exit.
