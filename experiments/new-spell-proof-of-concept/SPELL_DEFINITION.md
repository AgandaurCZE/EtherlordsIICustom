# TESTING CARD definition

The build consumes [spell-probe.json](spell-probe.json). `E3TC` is the new experimental ID, checked for absence in the original spell database, text keys and native producer registrations. All stock donor IDs and field values below were read from the local 1.03 files.

| Property | Probe metadata | Runtime status |
| --- | --- | --- |
| ID | `E3TC` | Separate resource record and Duel deck reference |
| Name | `E3TCNm` resolves to **TESTING CARD** | Displayed in the Chaots Encyclopedia |
| Faction and type | `Color=Red`, `Class=Sorcery` | Displayed under Chaots → Sorcery |
| Displayed cost | `Cost=1`, `OriginalCost=1` | Displayed as 1. No cast or Ether debit observed. |
| Description | `E3TCTt` resolves to **Vanishes all enemy creatures.** | Displayed as specified, describes the intended effect |
| Illustration | `Icon=674` from `GRUN` | Rendered in the new row and Duel editor using the original installed art |
| Remaining metadata | Inherited from `GRUN`, including `Use=+`, `UseIn=Both`, `Rarity=Unique` | The inherited deck-builder price is 30 Root, 5 Ruby and 9 Stone per copy. Use resource level 3 for the three-copy preset. |
| Effect and animation | Intended enemy-only removal using the Kinets disappearance effect | No native producer for `E3TC`. Neither effect nor animation executed. |

## Stock Kinets effects inspected

| Stock card | ID | Source and behavior |
| --- | --- | --- |
| **Greater Unsummoning** | `GRUN` | `CombatSpells.reg` section at member offset `0x1769d`, `Color=Blue`, `Class=Sorcery`, base cost 2, icon 674. `GRUNTt` in `text.res` describes returning creatures on both sides to their controllers' hands with an added Ether cost per affected creature. The bound native method at `0x6ccc50` iterates both sides and passes the eligible-creature count into the additional cost check. |
| **Unsummon** | `UNSM` | Section at `0x37c46`, Blue Sorcery, cost 1, icon 698. `UNSMTt` describes returning one target creature to its controller's hand. |
| **Lesser Unsummoning** | `LSUS` | Section at `0x1d80f`, Blue Sorcery, cost 1, icon 695. `LSUSTt` describes returning a target creature with casting cost 3 or less. |

`GRUN` is the nearest verified mass-removal donor; returning to hand is its stock behavior. In its native loop the effect dispatch at `0x6ccee6` receives `BlueDeath`. The effect is defined in `Resources/Effects.xml` and is also present as `BlueDeath.fx` in `fx.res` (row 76). The XML references model `ef14`, `EffectsObjects\bluesummon.mmp`, `BlueSummon.pfx` in reverse, and `Magic\BlueDeath.wav`. These assets already exist in the original game. The experiment reuses the icon by reference and copies no artwork. Effect dispatch remains available to the original `GRUN` only.
