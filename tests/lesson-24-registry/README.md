# Lesson 24 — Self-registering encounter manager

**Experimental — NOT YET VERIFIED IN GAME.**

## What changes
- The original Lesson 23 **Bee Queen and Grumble functions are copied byte-for-byte**, with only a **single registration statement appended** at the end of each encounter file.
- A new `encounter_registry.lua` stores callbacks and the names of each encounter's existing `ExGetVariable` keys. It routes OnStep, question responses, battle-finish, PreUse and intercept events.
- The five engine hooks in `hook_router.lua` no longer contain any encounter-specific names.
- `build.py` automatically discovers `src/encounters/*.lua` and produces one combined `build/TestMap.scp`. Modules must register themselves at file load.
- Lesson 23 passive diagnostic messages are preserved.

The registry itself holds Lua callback references for the current script; **persistent progression continues to use existing ExSetVariable values**, not the registry.

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
This is a structural refactor, not a solution to the hostile native cursor. The cursor may remain the attack icon for peaceful P2 monsters. The registry uses in-memory Lua function references created on script initialization; test actual saved games, since engine serialization has not been independently proven for this new registry.

## Add another encounter
Create a new uniquely named `src/encounters/<name>.lua` with its `OnStep`, `OnCloseMessageBox`, `OnBattleFinishing` and `OnPreUse` functions. At the end, register those callback functions with the existing persistent runtime-ID and state keys. Build again. **No edits to the shared engine router are needed.**
