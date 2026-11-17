# Lesson 22 — Independent scripted truces in a shared faction

**STATUS: EXPERIMENTAL, NOT GAME-TESTED.** Preserve the successful Lesson 21 backup and map.

## Map Editor
- Hero P1 + its Main Tower.
- Bee Queen bluhblah at (7,5) on P2 + existing P2 Main Tower.
- Grumble at (15,10) ALSO ON P2.
- No P3 tower required.
- Keep both enemies' existing valid combat decks.

## Hypothesis, not yet a verified solution
`ExSetHostility` is **player-to-player**, so we removed every faction-wide peace/hostility call from both encounter choices. Faction P2 remains at the map's original hostility with P1. Instead, individual `BeeChoiceState` / `GrumbleChoiceState` and object-ID checks in `Hook_OnPreUse` block manual use of a peaceful encounter and show its scripted greeting. `Hook_OnIntercept` attempts to block automatic interceptions involving the peaceful individual. These hooks do **not** change the engine's attack cursor and may not prevent every attack path. Their behavior is the purpose of the test.

**Do not interpret a changed cursor or a blocked movement command as full success.** If native interactions bypass both hooks, we need a different design. We do not use `ExSetUsability` yet because the editor documentation says full support is only for corpses.

## Test checklist
1. Restart scenario; approach Bee and select YES. Her reward/dialogue should remain intact. Note whether her cursor is still an attack icon.
2. Click Bee after truce. Does she deliver the friendly greeting, display `BEE TEST: Peaceful PreUse intercepted`, or open a battle confirmation? **Report exactly.**
3. Approach Grumble and choose NO. Verify the camera, automatic charge, battle prompt; decline and check reset/rearm. His hostile behavior must work even while Bee is peaceful.
4. Restart scenario: choose Grumble YES; click him after the truce. Note any `GRUMBLE TEST: Peaceful PreUse intercepted` message and whether the cursor remains hostile.
5. Challenge Bee and check that the hostile battle still works while Grumble is at peace. Optionally move around peaceful NPCs to see whether `Peaceful intercept blocked` appears.
6. Restart and win a battle to confirm no regressions.

Known issue: Because the map has only one shared P2 faction, a peaceful monster may still display the native attack cursor. The test is about the scripted interaction and interception gate, not cursor customization.

## Build
Run `python build.py` from this directory and use `build/TestMap.scp` next to `TestMap.smp`. This builder checks duplicate functions and hook list but is not a Lua 4 parser.
