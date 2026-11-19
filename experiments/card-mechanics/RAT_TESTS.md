# Stink Rat tests

## A1. Stock Chaots Rats

| Card | ID | Power / toughness | Ether | Activated ability |
|---|---|---:|---:|---|
| Stink Rat | `STRT` | 1/1 | 1 | None |
| Disease Rat | `DRAT` | 1/2 | 2 | Ghoul. Rest and pay 1 Ether to remove a creature from the target hero’s graveyard. |
| Plague Rat | `PRAT` | 3/4 | 4 | Ravenous Ghoul. Rest and pay X Ether to remove X creatures from the target hero’s graveyard. |
| Doom Rat | `DMRT` | 4/5 | 6 | Rat’s Brotherhood. Rest and pay 2 Ether to return a target Rat from the controller’s graveyard to the controller’s hand. |

The rows come from `CombatCreatures.reg` and `CombatSpells.reg` in `Resources/regs.res`. The names and ability descriptions come from `Resources/text.res::ELKTexts.txt`. All four use model `cr212` with separate Red Rat textures numbered 00–03. Disease Rat, Plague Rat and Doom Rat enter distinct native summon implementations at `0x6ed200`, `0x6ef300` and `0x6f0480`, respectively.

## A2. Base statistics

The probe changed two bytes in stock `regs.res`, setting only `STRT.Power` and `STRT.Toughness` to 3. The Duel deck editor displayed **Stink Rat 3/3** at 1 Ether. The battlefield showed a freshly summoned 3/3. The tester reported an unblocked hit for exactly 3 against the enemy hero, a Rat dying after taking exactly 3 damage, and normal Duel completion. No separate healing or combat save/load test was recorded.

## A3. Activated ability

The second copy was built independently from stock resources. It used the verified A2 stat edit and copied Doom Rat’s `Ability=62`, `AbilityIcon=711`, and `AbilityText=Ab62` to the Stink Rat spell row. The tester found no additional ability in the Encyclopedia, deck editor or Duel. No ability execution was observed. Doom Rat’s original row and producer were preserved.

Read-only disassembly explains the result. Stink Rat’s registered class uses the shared summon implementation at `0x7380b0`. Doom Rat’s override calls that implementation at `0x6f04a8`, then constructs a `DoomRat::RatAbility` object, assigns its vtable at `0x6f0531` and inserts it into the instance’s ability container via `0x6f0572`. The three copied fields do not run this constructor for Stink Rat. The documented scenario stat API provides some built-in flags and does not expose an attachment operation for this activated ability.
