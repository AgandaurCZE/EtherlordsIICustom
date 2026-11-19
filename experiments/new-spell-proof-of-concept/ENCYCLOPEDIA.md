# Encyclopedia registration

The normal Chaots **Sorcery** table accepted `E3TC` from added resource records. The displayed row had the intended title, icon, cost and description. Call Lightning, Comet, Ether Vortex, Tremor, Ethereal Resonance and Firestorm remained visible alongside it. The Sorcery table displayed its details inline. Any separate panel opened by clicking the row remains unverified.

| Resource | Addition |
| --- | --- |
| `regs.res/CombatSpells.reg` | One section keyed by `E3TC`. The faction, class, icon and cost come from this section. |
| `regs.res/ELKIDs.reg` and `Texts.reg` | Two additional Sorcery localization descriptors, `E3TCNm` and `E3TCTt`. |
| `regs.res/ELKTexts.reg` | Fallback translation records for the two keys. |
| `text.res/ELKTexts.txt` | Two UTF-16LE text blocks appended after the existing data. |

The full set above is the tested recipe. The experiment did not isolate which fallback files can be omitted. The `Encyclopaedia` panel already exists in `Controls.reg` and required no customization. `CombatSpells.reg` grew from 377 to 378 records, and its Red records grew from 66 to 67. All 377 original record payloads compared exactly with their source. These are archive record counts; the entire UI list was not counted by hand.

The tested build has no 377-entry cap on the Sorcery listing. The separate native producer map, described in [FINDINGS.md](FINDINGS.md), is the actual combat limitation.
