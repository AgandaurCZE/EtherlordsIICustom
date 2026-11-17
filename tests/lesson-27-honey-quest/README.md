# Lesson 27 — The Queen's Missing Honey

**Partially game-tested; proximity fix awaiting verification.** Player confirmed peaceful and combat quest completion, mixed resolutions, one-time reward, and saving/loading. A bug in pre-resolved NPCs triggered remote dialogue; the corrected build now requires visiting each NPC's location. Lesson 25 remains the verified fallback.

This lesson adds an interconnected quest across **bluhblah, Grumble, and Moss**, using the same **20×20 editor map / 19×19 accessible tiles** and the same **P2** faction. No Map Editor changes.

## Architecture

- `src/encounters/grumble.lua` and `src/encounters/moss.lua` are **unchanged** from the tested Lesson 25.
- `src/encounters/bee_queen.lua` has one integration in `Bee_OnPreUse`, routing Bee's peaceful repeat-click to the quest coordinator.
- `src/quests/missing_honey.lua` owns persistent `HoneyQuestStage`, `HoneyQuestHoneyRecovered`, and `HoneyQuestRewardReceived` variables. It reads existing encounter states without altering their combat, reward or reset logic.
- `src/shared/hook_router.lua` adds one call to `HoneyQuest_OnStep`, retaining exactly the same five engine `Hook_*` definitions.
- The save/load-safe encounter registry remains unchanged (function **name strings**, never function values).
- The `build.py` includes all modules and produces one `build/TestMap.scp` for the game.

## Quest flow (start NEW SCENARIO)

1. Visit **Bee at (7,5)**. Say **YES** to her original apology choice and collect her original one-time spell. **Click Bee again** to receive the honey quest. (Starting it requires an existing peaceful Bee; choosing NO starts her old fight instead.)
2. Visit **Grumble at (15,10)**. Resolve his encounter by **YES (peace)** or **NO followed by a won battle**. Declining combat does **not** count. When his outcome is resolved, the quest reveals he traded honey to Moss.
3. Visit **Moss at (10,16)**. Resolve his encounter by **YES (peace)** or **NO followed by a won battle**. Declining combat does **not** count. The quest advances to recovered honey.
4. **Return to peaceful Bee and click her.** She thanks you and gives a **one-time bonus spell ASLT**. Bee's initial random spell and the quest reward have **different one-time flags**.
5. Click Bee a further time. You should only get the finished-quest dialogue — **no repeat reward**.

Quest stages: `nil` not started, `1` investigate Grumble, `2` seek Moss, `3` return to Bee, `4` complete. It uses a logical honey quest flag; **there is no physical honey inventory item** in this test.

Players may resolve Grumble or Moss before formally starting the quest: a valid earlier peaceful/completed state can satisfy the corresponding stage **only after the hero revisits the relevant NPC's coordinates**. Clue at Grumble (15,10), honey at Moss (10,16); being near Bee is not sufficient.

## Important regression: pre-resolved characters

1. In a fresh scenario, resolve Grumble and Moss before accepting the Queen's quest (peace or victory, mixed choices are fine).
2. Return to Bee, apologize and receive her original gift, then click again to start the quest. **No Grumble clue and no Moss dialogue must trigger while standing by Bee.**
3. Walk to Grumble's position at (15,10). His previously resolved encounter can now reveal the clue without requiring a second truce/fight.
4. Walk to Moss's position at (10,16). Only there should the honey be recovered.
5. Return to Bee to complete the quest once. Save/load between stages and verify proximity gating still works after reloading.
6. Normal quest order should still automatically show clue/recovery narration shortly after the original peaceful dialogue or battle ends, without needing another click.

## Save/load tests

- After accepting quest at Bee, save, reload, then proceed to Grumble. No repeated quest start.
- After Grumble resolves (stage 2), save/reload and continue to Moss. His interaction must still function.
- After recovering honey (stage 3), save/reload; return to Bee and turn in. Quest should finish.
- After turn-in (stage 4), save/reload and click Bee again: no duplicate bonus spell.
- Refuse a Grumble or Moss battle and confirm it does not satisfy the quest; their old reset/rearm still works.

## Known limitations / deliberate scope

- Quest only starts from a **peaceful** Bee; killing Bee or never accepting her apology prevents turn-in. This is explicit for this first prototype.
- The honey itself is a **saved quest flag**, not a tradeable inventory object.
- The native attack cursor can remain for peaceful monsters on hostile P2.
- The quest coordinator uses a small `Hook_OnStep` observer. It waits for the native command queue to empty before advancing quest stages so it should not interrupt existing dialogue, but **in-game verification is required**.
- The reward uses the known working `ExAddSpell` API, with `ASLT` as a fixed bonus. If Bee's random initial reward happened to be `ASLT`, this quest can award the same spell code again; the once-only quest flag still prevents repeated claims.

## Installation
Use the generated `build/TestMap.scp` alongside `TestMap.smp`. Start a **new scenario** after replacing the script; use fresh saves for this build. Keep Lesson 25's working generated script backed up.
