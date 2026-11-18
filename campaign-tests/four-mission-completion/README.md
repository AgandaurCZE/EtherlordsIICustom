# Four-mission Vitals campaign completion test

**GAME-TESTED: PASSED (2026-11-18).** Full installable package delivered in chat as `EtherlordsIII_FourMission_CompletionTest.zip`.

**Objective:** Check whether four normal `ExAddCommandWin()` victories through the native Vitals campaign slots produce the game engine's ordinary Good-side follow-on campaign selection / Kinets unlock.

- Mission 1: user's Chapter01 converted terrain, victory by entering fort at (21,14); uses the previously tested `E3_Chapter01.scp`.
- Mission 2: user's Chapter02 converted terrain, hero starts (9,3), walk near (9,8) to win.
- Mission 3: reused Chapter02 map and binary terrain under registered e2mission13 resource; walk near (9,8) to win.
- Mission 4: reused Chapter02 map and binary terrain under registered e2mission14 resource; walk near (9,8) to win.
- Each stage checks the previous stage's persistent completion flag and writes its own flag. Hero progression remains under native engine control, not manually reconstructed.
- Hook_OnBattleFinishing returns 1 as already game-tested to preserve post-battle XP while bypassing the original invalid hero ID specialization handler.

**Safety:** Back up Campaigns/Green.cpg AND all 8 original mission map/binary files (`e2mission11`, `e2mission12_52`, `e2mission13`, `e2mission14` .map/.ebm). The original e2mission13 assets are not present in our reference uploads, so user MUST preserve their own backups. Also back up saves. Installation in main `Maps/` folder only. Restore original files after testing.

**Limitations:** This occupies the existing Vitals campaign slot, doesn't create a sixth campaign or customize selection art/overview UI. Whether normal campaign-end advancement works depends on the engine and possibly profile state; awaiting direct in-game test.

## Game-test confirmation — 2026-11-18

The player completed all four successive replacement Vitals missions. Mission 4 ended via the normal campaign victory command and the engine transitioned to the **next campaign selection screen**, displaying **Synthets** in the supplied screenshot. This establishes that completing all four native slots advances to the next campaign selection phase, even when the missions/maps/scripts are replaced with user-created content.

Important nuance: the post-completion screenshot shows **Synthets**, not Kinets. The source of that choice (profile progression, campaign route, or engine-specific branching) is not yet established; do **not** claim that a particular Good/Evil branch was validated by this test. The chapter UI still displays stock campaign graphics and overview, and an extra sixth campaign entry has not been achieved.

**Next engineering workstream:** campaign-selection UI, campaign overview/background images, campaign header/briefing localization and slot limitations, with backups and reversible changes. Story and maps can proceed in parallel; no more basic native four-mission unlock probes needed.
