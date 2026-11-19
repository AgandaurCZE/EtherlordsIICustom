# Etherlords II 1.03 card mechanics

| Layer | Local source | What the experiment established |
|---|---|---|
| Card identity and UI metadata | `Resources/regs.res::CombatSpells.reg` | Four-character keys identify cards and map to labels, icons, faction, costs and ability descriptors. Copying a descriptor does not construct an activated ability. |
| Creature definitions | `Resources/regs.res::CombatCreatures.reg` | The stock Stink Rat definition supplies real starting power and toughness. Its model and texture references can stay intact through a stat change. |
| Card text | `Resources/text.res::ELKTexts.txt` | Localized keys include `STRTNm`, `Ab62`, `ZAPPNm` and `ZAPPTt`. These describe mechanics separately from native effect code. |
| Native producer | `Etherlords2.exe` | The earlier [producer investigation](../new-spell-proof-of-concept/PRODUCER_ARCHITECTURE.md) tracks lookup by registered ID. This experiment retains all original IDs and studies what their producers read or attach. |
| Combat instance | Registered summon implementation | Stink Rat uses shared instance creation. Doom Rat extends it by attaching a specialized ability object. |
| Effect playback | `Resources/Effects.xml`, `pfx.res`, `sfx.res` | Zap’s native cast dispatches `RedZap`. The XML defines links, lights, `RedZap.pfx` and `Magic\\RedZap.wav`. The native cast separately decides damage and target handling. |
| Encounter scripting | Bundled Map Editor `Script functions.pdf`, pp. 10–11 | Scenario scripts can set enumerated summon stats and request additional registered spell casts. The documented post-spell hook runs after the original cast and other triggers. |

The read-only addresses in this experiment use the 32-bit executable with SHA-256 `d3ed30f840b3325b1f03c01aa486e7f44328a7d6993964c409950a65e86a158b`, preferred image base `0x400000`. They are virtual addresses for this build. No executable, shipped resource or extracted artwork is included in the branch.

See [Rat tests](RAT_TESTS.md), [Zap tests](ZAP_TESTS.md), [observed combat results](COMBAT_RESULTS.md) and [technical limitations](TECHNICAL_LIMITATIONS.md).
