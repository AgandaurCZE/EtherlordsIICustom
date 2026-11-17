# Lesson 23 — Save/load persistence investigation

**Experimental, not yet verified in-game.**

This build preserves the **exact encounter source modules** used in Lesson 22 and adds only a passive observer to the central `Hook_OnStep()`.

## Map configuration

Use the **same map as Lesson 22**: player hero P1, bluhblah P2 at (7,5), Grumble P2 at (15,10), P2 tower present, P3 tower absent. No editor changes.

## What the diagnostic reports

`L23 START Bee=<state> Grumble=<state> Gift=<0/1>` is printed when the script's transient globals initialize (often on scenario start or reload). `L23 STATE Bee=...` and `L23 STATE Grumble=...` print on state changes observed by the script.

This is intentionally *observational*. It does not change battle logic, reward logic or persisted variables.

The official manual documents `ExSetVariable(name, value[, permanent])`, where `permanent` is for **between missions**. Save/load behavior of current-mission state needs real testing. Engine save/load may restore Lua globals too: absence of a new `L23 START` after loading is not by itself evidence of failure.

## Tests

**A. Bee truce save/load**
1. Start new scenario. Approach bee, choose YES, collect spell.
2. Save the game **after the reward window closes** (make a new named save).
3. Reload that save. Move back to bee, click her. Does the greeting occur rather than the opening dialogue or battle? Does the gift duplicate?
4. After loading, approach Grumble, choose NO, decline; does he reset and rearm?

**B. Grumble truce save/load**
1. Start *new scenario*. Offer Grumble a truce.
2. Save, reload. Click Grumble to verify peaceful greeting.
3. Approach Bee, select NO, decline; does her attack and reset still work?

**C. Refusal/rearm save/load**
1. Start *new scenario*. Challenge Bee, decline battle, walk outside the bee trigger and observe the `Ready` state.
2. Save and reload. Reapproach. Does the **initial** Bee dialogue reappear and can you choose YES or NO again?
3. Repeat with Grumble if A/B work.

**D. Optional victory save/load**
1. Start new scenario, win an accepted battle against Grumble.
2. Save/reload. Confirm victory remains completed; do not expect defeated monsters to respawn.

Report the messages you happen to see, but prioritize **observable behavior after reload**: greeting, choice repetition, reward count and battle reset.

## Important: preserve rollback
Keep Lesson 22 `TestMap.scp` as the tested baseline. The new script has not been run in the game.

Build with `python build.py`; install `build/TestMap.scp` beside the map's `TestMap.smp`, then restart the scenario.
