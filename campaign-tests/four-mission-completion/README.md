# Four-mission Vitals campaign completion test

**Experimental, not yet game-tested.** Full installable package delivered in chat as `EtherlordsIII_FourMission_CompletionTest.zip`.

**Objective:** Check whether four normal `ExAddCommandWin()` victories through the native Vitals campaign slots produce the game engine's ordinary Good-side follow-on campaign selection / Kinets unlock.

- Mission 1: user's Chapter01 converted terrain, victory by entering fort at (21,14); uses the previously tested `E3_Chapter01.scp`.
- Mission 2: user's Chapter02 converted terrain, hero starts (9,3), walk near (9,8) to win.
- Mission 3: reused Chapter02 map and binary terrain under registered e2mission13 resource; walk near (9,8) to win.
- Mission 4: reused Chapter02 map and binary terrain under registered e2mission14 resource; walk near (9,8) to win.
- Each stage checks the previous stage's persistent completion flag and writes its own flag. Hero progression remains under native engine control, not manually reconstructed.
- Hook_OnBattleFinishing returns 1 as already game-tested to preserve post-battle XP while bypassing the original invalid hero ID specialization handler.

**Safety:** Back up Campaigns/Green.cpg AND all 8 original mission map/binary files (`e2mission11`, `e2mission12_52`, `e2mission13`, `e2mission14` .map/.ebm). The original e2mission13 assets are not present in our reference uploads, so user MUST preserve their own backups. Also back up saves. Installation in main `Maps/` folder only. Restore original files after testing.

**Limitations:** This occupies the existing Vitals campaign slot, doesn't create a sixth campaign or customize selection art/overview UI. Whether normal campaign-end advancement works depends on the engine and possibly profile state; awaiting direct in-game test.
