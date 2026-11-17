# Lesson 25 — Third encounter and reusable template

**Game-tested success (2026-11-17).** User verified the Moss encounter using a Hero-checked character, with peace/hostile choices, battle refusal/reset, victory, and save/load persistence. Lesson 24 remains a rollback option.

This lesson adds **Moss**, a mushroom guardian, as a third independently registered NPC on P2. Bee Queen and Grumble encounter code is unchanged, and the save-safe registry / five engine hook router are unchanged. The builder picks up the third `moss.lua` module alphabetically without editing the router.

## Map Editor orders

- Hero P1 unchanged; Bee Queen **P2 at (7,5)** unchanged; Grumble **P2 at (15,10)** unchanged.
- Place a new monster called **Moss** at **(10,16)**, assign **P2** (no P3 tower), and give it a working battle deck on all difficulty levels.
- Ensure (10,16) is actually passable and accessible on your particular terrain, with no nearby interfering monster. This coordinate is inside the 19x19 playable grid, but terrain passability still requires a Map Editor check. If your terrain blocks that tile, adjust Moss's trigger/home coordinates in the module and rebuild before testing.
- Save as `TestMap.smp`. Do not replace the working Lesson 24 `TestMap.scp` backup.

## Moss's choices

- **YES** — promise not to trample mushrooms; Moss becomes peacefully interactive (despite the native attack cursor).
- **NO** — trample mushrooms; Moss initiates a fight. Refusal should reset him home, and walking away should rearm the encounter.
- Victory marks Moss completed.

## Regression checklist

1. Restart scenario and visit **Moss first**. Choose YES, click him afterward for his unique peaceful greeting. Then challenge Grumble and confirm his battle still works.
2. Restart; visit **Moss first**, choose NO, decline the battle, walk away and back. His opening question should reappear.
3. Restart; choose Bee YES, collect spell, then Grumble YES, then Moss NO. Moss must still be able to fight. Check both peaceful greetings.
4. Restart; fight Moss and win. Verify victory completes normally and other NPC encounters still work.
5. Save after Moss truce, reload, click Moss, confirm no script error and retained state. Save/reload after a refusal/rearm too.
6. Regression: Bee refusal/rearm, Grumble refusal/rearm, and no duplicate Bee reward.

If everything works, Lesson 25 demonstrates that a **third encounter can be added simply by adding a module and rebuilding the .scp**, without changing the engine router.

For instructions to add subsequent NPCs, see [TEMPLATE_GUIDE.md](TEMPLATE_GUIDE.md).
