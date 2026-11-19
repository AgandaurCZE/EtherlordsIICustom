# Native combat extension on Windows 1.03

This work builds on the [E3TC crash matrix](../new-spell-proof-of-concept/CRASH_ANALYSIS.md), the [card-mechanics experiments](../card-mechanics/FINDINGS.md), and the [original editor and encounter references](../../references/ORIGINAL_GAME_FILES.md). The Lua combat API documented by the editor can enqueue spells and adjust certain summoned stats. These experiments work one layer earlier, at native creation or dispatch.

| Stage | Source and role |
|---|---|
| Deck and Encyclopedia | `CombatSpells.reg` keys identify cards and map to cost, faction, icons and text. Duel presets store the literal ID. |
| Combat construction | The executable registers producer objects. A hand command passes its card ID into `0x746500`, which creates a fresh native object and writes the requested ID to its common header. |
| Targeting and cast | Constructors establish target requirements and the spell vtable selects a cast implementation. Economy, effects and event recording can inspect different parts of this model. |
| Creature summon | Stock summon creates the instance from the original creature definition. A subclass can attach a prepared, instance-owned ability to the result. |
| Visuals | Native casts call the combat event queue with known effect names; particles, sounds and links are resolved by the game's existing resources. |

The prototype has independent profiles for native registration, an immediate damage change, a factory substitution for targeting and mass damage, and a summon dispatch change. It checks the executable SHA-256, expected archive pair, image base and original site bytes. It launches a new child only, stages at the initial debug event, and changes no executable on disk. A profile is discarded when its process ends.

For a reusable release, represent these as distinct engine operations. A producer declaration needs a unique ID and an independently owned object. A damage override needs site or function contracts. A target mode also changes the AI and player target selection. An effect sequence needs safe effect completion boundaries and target lifetime rules. An activated ability needs a creature instance and ownership. Artwork, descriptions and faction remain resource fields. A schema alone cannot supply those native contracts.
