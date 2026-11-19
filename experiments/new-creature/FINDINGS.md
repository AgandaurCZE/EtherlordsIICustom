# TESTING Rat

TESTING Rat uses the new four-byte ID `E3RT`. The builder checks that the exact ID is absent from the pinned executable and original spell and creature registries. It adds independent combat metadata and creature definition records plus localization. A second build produced the same archive hashes, and all stock registry entries compare byte for byte.

## Stock donors

| Creature | Stock code | Relevant findings |
|---|---|---|
| Stink Rat | `STRT` | Chaots, 1 Ether, 1/1, `Race=Rat`, model `cr212`, artwork 422. |
| Kobold Shaman | `KBSH` | Chaots, 1 Ether, 0/1, `Race=Kobold`. Activated Zap, ability 132, icon 710, text key `Ab132`. The creature rests to deal 1 damage to a selected creature or hero. There is no additional Ether debit in the ability. |
| Mantis Patriarch | `MTPT` | Vitals, 9 Ether, 6/6, `Race=Mantis`, model `cr309`, scale 1.25, primary texture `Alpha\\GreenMantis02`, secondary texture `GreenMantisAdd02`, sound set `GreenMantis02`, artwork 478. Stock Lifetap and race-wide rest ability belong to the donor only. |

All rows were read from `regs.res::CombatSpells.reg` and `CombatCreatures.reg`, with localized labels from `text.res::ELKTexts.txt`. The model `cr309.mod` and animation data `cr309.anm` are in `crfigures.res`. `animdb.res::cr309.adb` identifies the GreenMantis animation set and includes `cidle`, `uattack`, `uhit`, `udeath`, and `uinstant`. Both textures resolve in `textures.res`. The sound set has attack, hit, death and idle members in `sfx.res`.

The new creature definition takes the Mantis rendering and sound references and sets power and toughness to 5 and race to `Rat`. It omits the donor's `Flags=Lifetap` field. The card inherits Chaots, the 1-Ether casting cost and the Shaman's ability metadata. Its illustration is the Mantis card artwork. The probe sets both Duel purchase-resource costs inherited from the Shaman to zero for fixture access. The description uses the requested damage wording and the ability tooltip retains the native rest requirement.

The large Encyclopedia image is separate from the `Icon` field. The detail pane's resource naming uses the lowercased card ID and three `_1`, `_2`, `_3` suffixes in `Interface\Encyclopaedia`. The stock archive contains the three 256×256 `mtpt_*.mmp` tiles. The local builder indexes those image payloads under `e3rt_*.mmp` in the game's optional `Resources/textures001.res` slot. Both stock texture archives remain byte-identical. The overlay remains local.

## Factory and race

Creatures and sorceries use the same native producer registry at `0x9cd998`. On the pinned executable, `KBSH` is registered at `0x73fd1e`. Its producer constructor at `0x7451d0` initializes vtable `0x8c1a98`. The factory `0x7485f0` creates the common 0x3c-byte summon spell and sets vtable `0x8c2c50`. The common dispatch subsequently writes the requested card ID into the object. E3RT owns a separately allocated producer with that same implementation, so the engine can destroy each entry independently.

The donor's summon override at `0x6ed6f0` calls the shared summon path. It creates a new Shaman ability object and attaches it at `0x6ed7eb`. The activated method at `0x6ed960` checks rest conditions and routes a literal 1 to the hero and creature damage receivers at `0x6edba0` and `0x6edcf0`. The parameters and event context come from the summoned creature and the chosen target.

`Race` is the creature’s gameplay family. At `0x739ebe` the metadata loader reads that field. The runtime index at `0x9cd91c` uses the actual creature/card code. Doom Rat's Brotherhood at `0x6f07a1`–`0x6f07cf` retrieves the candidate's family and compares it with the literal `Rat`. Rat's Tenacity also checks this family at `0x7182c5`–`0x7182f3`. Both compare race data independently of the model and producer class.

## Serialization

Duel presets store four ASCII ID characters in a `spell code` attribute. The fixture deliberately uses E3RT in that field. The shared combat return-to-hand path calls the same producer registry using the returned creature's ID, as documented in the [original producer trace](../new-spell-proof-of-concept/PRODUCER_ARCHITECTURE.md). A live return test is stronger evidence than the file format.

The shipped combat tutorial text `TUT_COMBAT_SCREEN` says saving during a fight is unavailable. Duel replays have separate save and replay controls. A fresh custom preset reload, a replay playback and campaign save/load are distinct checks. Replays, presets and saves containing E3RT should stay with the registered experimental build.
