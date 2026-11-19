# Zap native dispatch and effect experiments

## Stock cast

`ZAPP` is a 1-Ether Chaots Sorcery in `CombatSpells.reg`. Its producer vtable `0x8c1d74` creates a fresh Zap with factory `0x749a30` and constructor `0x6f20e0`. The constructor installs cast vtable `0x8bff2c` and pushes target category 4 into the target descriptor vector. The generic targeting path uses the descriptor vector and the spell's resource metadata to enumerate candidate configurations at `0x754820`. Zap's cast `0x6f2160` reads the first selected index from the first argument's parameter vector. Indices 0 and 1 enter the hero path. Higher indices use the creature table, with a null-check in Zap itself.

| Path | Damage operand | Combat receiver |
|---|---|---|
| Hero | `push 1` at `0x6f229f` | Hero damage via `0x751b00` |
| Creature | `push 1` at `0x6f22ed` | Creature damage via `0x752b30` |

Both paths pass a combat event context. Creature damage checks removal and prevention, records damage through an engine command, compares accumulated damage to toughness, and dispatches additional lethal or nonlethal consequences before returning. Reusing it preserves those operations. Zap emits its usual `RedZap` effects through the engine event queue. The effect files do not control the damage amount.

## B1. Three damage

The profile checks `6a 01` at both sites and changes each to `6a 03` in memory. Normal target selection, damage receivers and visuals remain in place. The resource pair is stock so the tooltip is deliberately a control. Both dispatch branches were hit in the debugger. The tester measured 3 damage to an enemy hero and killed a 2/3 Aviak Scout. Damage prevention and shield interactions need separate runtime cases.

## B2. Battlefield-wide damage

The mass profile changes the factory slot at `0x8c1d78` from Zap's factory `0x749a30` to Lightning Storm's factory `0x748f90`. The original Lightning Storm registration remains independent. The common post-factory write assigns requested ID `ZAPP`. The created donor object supplies its own no-target cast and enumeration, retaining the stock Zap metadata and native Lightning Storm visuals for this probe.

At `0x6f4930`, the Lightning Storm routine builds a snapshot containing targets from both players' creature lists, then calls the original creature damage routine with 3 at `0x6f4c2d`. The snapshots separate traversal from damage-driven removals. The tester confirmed 3 damage to all creatures. The donor loop and the runtime breakpoint were checked. This option changes the entire native target and cast implementation for Zap. A custom friendly-only or enemy-only area effect would need a separate selection policy.

## B3. Damage followed by Unsummon

The prototype redirects the Zap cast slot at `0x8bff30` to a wrapper. It saves the selected enemy creature's slot, pointer, encounter identity, controller and card identity. It runs original Zap at 1 damage, then rereads the battle table. Only a matching creature that remains alive, stays under the same controller and has matching owner and controller can reach the original `UNSM` effect method at `0x6cc9c0`. Heroes and friendly targets take stock Zap damage only. Damage remains the first engine operation. The Unsummon effect method consumes the same parameter-vector and event arguments and uses the shared caster and battle fields. No second card or casting command is issued.

The enemy-wall cast passed 1 to native damage, reached the Unsummon call with one point of damage on the target, and returned the target to hand. A friendly wall took 1 and stayed in play. The guards cover removal and identity changes. They do not reproduce the whole engine targeting service or prove that all mid-effect protection changes are handled. Stolen, morphed, replaced, killed and controller-changed creatures are cases to test explicitly. The wrapper deliberately skips mismatched owner/controller until return destination and dynamic target rules can be verified independently.
