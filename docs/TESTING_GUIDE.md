# Testing and rollback

## Safeguards
- Keep a separate untouched local copy of the **actual** Lesson 19 game-tested `TestMap.scp`.
- Never copy a source module (`.lua`) directly over the active map script.
- Keep the map `TestMap.smp` and the game installation unchanged while testing script refactors.
- Restart the scenario after changing `TestMap.scp`.

## Bee Queen regression checklist
1. Approach the bee near (7,5). Introductory dialogue appears only once per encounter.
2. Select **YES**: player apologizes, bee turns peaceful, randomized `ALST`/`ASLT` spell reward appears in the native loot UI; friendly interaction works.
3. Restart scenario, select **NO**: bee turns hostile, camera moves, bee charges, native Accept Battle prompt opens.
4. Decline battle: bee returns home; after moving away from the trigger, approach again and verify the beginning dialogue and choices recur.
5. Restart scenario, select **NO**, accept battle and **win**: battle completes and normal gameplay continues.
6. Verify no unexpected extra encounters, duplicate rewards, frozen command queues or error messages.

## Test record template
- Lesson / commit:
- Game version:
- Script filename:
- YES / reward:
- NO / camera / charge:
- Declined / bee reset:
- Rearmed dialogue:
- Accepted battle / victory:
- Unexpected messages / errors:
- Status: **game-tested** or **experimental**

If the modular refactor regresses, immediately restore the Lesson 19 backup and investigate the diff between modules and generated code. Code generation success is not a substitute for game testing.
