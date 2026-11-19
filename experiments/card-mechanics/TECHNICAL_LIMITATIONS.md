# Technical limits and usable paths

- **Creature balance.** Edit verified scalar fields in `CombatCreatures.reg` for existing creature IDs. Stink Rat’s 3/3 variant was exercised in Duel. Keep the original spell ID, model and other registry fields.
- **Activated creature skills.** The Doom Rat transfer test reached Duel with the donor metadata in Stink Rat’s spell row and exposed no new ability. The ability is allocated and attached by Doom Rat’s native summon override. The documented scenario API exposes base flags such as flying, regeneration and first strike through `ExSetNewCreatureBaseStat` during the summon hook. Those flags do not attach Rat’s Brotherhood.
- **Zap damage and targets.** The native cast uses two literal damage operands and one selected target. No checked registry field or documented scenario hook changes its damage or expands the original cast’s targeting. For a custom encounter that requires three damage to both sides, start with the stock `LGST` mass-damage effect.
- **Multiple spell effects.** The inspected Zap producer has no editable effect list. A scenario-level scripted second cast is a separate command with its own timing. See [B4](ZAP_TESTS.md) for the documented interface and the remaining questions.
- **Visuals.** `Effects.xml` configures playback for known effect names. It does not implement combat damage, ability attachment or target selection.

For Etherlords III, existing creature records and stock effects are practical starting points. Use encounter scripts for scenario-specific behavior and validate each hook in an isolated test encounter before using it in the campaign.
