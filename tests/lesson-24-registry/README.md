# Lesson 24 — Self-registering encounter manager

**Experimental hotfix — NOT YET VERIFIED IN GAME.** The original Lesson 24 game-test crashed after saving/loading: `attempt to call field 'on_step' (a nil value)`. This corrected build stores callback names as serializable strings, resolving them via Lua 4 `getglobal(name)` when called.

## What changes
- The original Lesson 23 **Bee Queen and Grumble functions are copied byte-for-byte**, with only a **single registration statement appended** at the end of each encounter file.
- A new `encounter_registry.lua` stores **callback function names as strings** (not Lua function references) and the names of each encounter's existing `ExGetVariable` keys. It resolves functions at runtime via `getglobal(name)`. It routes OnStep, question responses, battle-finish, PreUse and intercept events.
- The five engine hooks in `hook_router.lua` no longer contain any encounter-specific names.
- `build.py` automatically discovers `src/encounters/*.lua` and produces one combined `build/TestMap.scp`. Modules must register themselves at file load.
- Lesson 23 passive diagnostic messages are preserved.

The registry itself holds callback **names** instead of non-serializable function references; **persistent progression continues to use existing ExSetVariable values**, not the registry.

## Map setup
Unchanged from Lesson 22/23: P1 hero, bluhblah P2 at (7,5), Grumble P2 at (15,10), P2 tower present, no P3 tower. Preserve your previous `TestMap.scp` as backup.

## Regression test
1. Start new map. Visit Bee, choose **YES**, receive **one** spell. Click Bee afterward: friendly greeting, no attack (native attack cursor may remain).
2. Visit Grumble, choose **NO**, decline the battle; watch reset and rearm. Revisit to trigger the opening dialogue.
3. Start new map. Visit Grumble, choose **YES**; verify repeated peaceful greeting. Visit Bee, choose **NO** and decline; verify Bee resets.
4. Start new map. Win a fight against Grumble and verify normal completion.
5. Save after a Bee truce, reload, check greeting and no duplicate reward. Approach Grumble afterward and confirm he still works.
6. If any step fails, report exactly which NPC, choice, and observable behavior, and revert to the working Lesson 23 backup.

## Important limits
This is a structural refactor, not a solution to the hostile native cursor. The cursor may remain the attack icon for peaceful P2 monsters. The earlier implementation stored actual Lua function references in a table and **crashed on loading saves**. This hotfix stores function-name strings instead, but needs fresh in-game validation. **Start a new map and make new saves with this hotfix; old broken Lesson 24 saves are not guaranteed compatible.**

## Add another encounter
Create a new uniquely named `src/encounters/<name>.lua` with its `OnStep`, `OnCloseMessageBox`, `OnBattleFinishing` and `OnPreUse` functions. At the end, register those callback functions with the existing persistent runtime-ID and state keys. Build again. **No edits to the shared engine router are needed.**

## Hotfix verification priority
1. Start a **new** scenario using this fixed TestMap.scp; greet Bee, choose YES and receive the spell.
2. Save **under a new save filename**. Reload it. Confirm no registry crash; Bee greeting still works and reward cannot duplicate.
3. If step 2 succeeds, test Grumble truce/save/load and Bee battle refusal/rearm/save/load.
4. For remaining encounter/quest regressions, follow the original checklist above.
