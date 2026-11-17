# Reusable encounter template — Lesson 25

This is a **tested-pattern template**, not an engine-level helper that magically handles everything. Moss's module is our working example. Keep encounter-specific states and callback names unique and reuse the **save/load-safe string registration**.

## To create a new encounter

1. Copy `src/encounters/moss.lua` to `src/encounters/<new_slug>.lua` (e.g. `sprig.lua`).
2. Replace every `Moss`, `moss`, and `MOSS` prefix with your new unique encounter prefix.
3. Change every home/trigger coordinate (currently **10,16**) and edit each line of dialogue.
4. Set that NPC on **P2** in the Map Editor. Keep it away from the other NPCs' trigger zones.
5. Preserve the same state machine: `nil/Ready -> Intro -> Question -> Peaceful` OR `Hostile -> Charging -> Cooling -> Ready` (victory -> `Completed`).
6. Keep your `ExGetVariable/ExSetVariable` keys unique: `MossChoiceState`, `MossRuntimeId`, `MossHomeX`, etc.
7. Preserve the `OnPreUse` peaceful greeting with `return 0` to suppress native attack, and allow `Hook_OnIntercept` (through the registry) to block unwanted automatic interceptions.
8. Ensure the module ends in exactly one registration call containing callback **name strings**, never function references:

```lua
EncounterRegistry_Register("Moss", "MossRuntimeId", "MossChoiceState",
    "Moss_OnStep", "Moss_OnCloseMessageBox",
    "Moss_OnBattleFinishing", "Moss_OnPreUse")
```

9. Run `python build.py` to regenerate the sole `build/TestMap.scp` that the game reads. No changes to `src/shared/hook_router.lua` are needed.

## Why strings matter

Lesson 24 originally crashed after loading saves: `on_step` (stored as a Lua function in an encounter registry table) became nil. The player verified the fix using plain **function-name strings** resolved via Lua 4's `getglobal`. Do not revert that fix.

## Known limitations and safeguards

- `ExSetHostility` acts on whole player factions. **Do not call it for individual truces** when NPCs share P2.
- The cursor can still show the native attack icon on peaceful P2 monsters, even though manual use is safely intercepted.
- The sample identifies the closest monster to its home coordinate. **Never place different mobs within a couple of tiles of the same trigger point**, or the wrong monster might be selected. A future refinement should use stable map object IDs.
- The modules depend on one shared native command queue. Keep encounter triggers separated and test crossed/overlapping dialogue.
- Global Lua scratch variables can collide if modules reuse names; use unique prefixes.
- The current sample is a *duel-or-truce* template; optional rewards should use a separate once-only `ExSetVariable` key like the Bee gift.
- Do not assume a new script is backward compatible with an existing save. Always start a fresh scenario after replacing `TestMap.scp`, then test new saves.

## Test priorities

Run all encounter order combinations, one refused battle/rearm, one victory, peaceful re-interaction, save/load after truce and after refused battle, no duplicated rewards, no crash. Only promote a script to the working baseline once the player has tested it in Etherlords II.
