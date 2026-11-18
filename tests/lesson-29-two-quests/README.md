# Lesson 29 — Two Independent Quests / Missable Spores

**Game-tested success (2026-11-18).** Player confirmed both quests function independently, save/load retains state at every tested stage, and the revised Bramble spore-handover dialogue plays correctly. Lesson 28 remains an earlier verified fallback. This folder is self-contained and lives on `main`.

## Map Editor setup

Use the existing 20×20 map (only 19×19 tiles accessible), same P1 hero and existing P2 tower:

| NPC | Position | Faction | Purpose |
|---|---|---|---|
| bluhblah | (7,5) | P2 | Missing Honey quest giver |
| Grumble | (15,10) | P2 | Honey quest |
| Moss | (10,16) | P2 | Honey quest and Stolen Spores quest giver |
| **Bramble** | **(1,16)** | **P2** | Hidden, very powerful spore thief |

Bramble's position was supplied by the player: **X:1 Y:16, behind a rock**, deliberately easy to miss. Give her a valid battle deck for all difficulty levels. The user has already designed her to be **effectively unbeatable at this stage**, so **peaceful negotiation** is the intended side-quest solution. Confirm the player's hero can approach within **three tiles** of (1,16) despite the rock.

No additional faction tower; all NPCs stay P2. Avoid changing existing Bee, Grumble or Moss properties.

## Quest 1 — The Queen's Missing Honey

The existing Lesson 28 main quest is preserved: apologize to Bee, click again to start, resolve Grumble and Moss peacefully or by victory, then return to Bee. Original honey journal milestones and one-time reward are separate from side quest state.

## Quest 2 — The Stolen Mushroom Spores

1. Make peace with Moss (**YES** to protect the mushrooms). **Click her again** to receive the side quest. Moss asks you to find Bramble behind the western rocks.
2. Find Bramble at **(1,16)**, then choose **YES = Negotiate for spores**. Bramble is extremely strong; **NO = Challenge** is intended as a dangerous/missable choice, not a required battle.
3. After resolving Bramble peacefully, the spore quest advances when the hero is physically **within 3 tiles of (1,16)**. A spore recovery journal entry appears.
4. Return to Moss, click her to turn in the spores and receive **one** spell reward (`ALST`) plus a completion journal entry.

## Missable consequences

- **Moss defeated before making peace:** No side quest giver exists; side quest cannot be started or turned in. Honey quest may still be completed using combat.
- **Bramble defeated before or during the spores quest:** Negotiation becomes impossible; the spore quest is marked **failed** instead of being completed by looting. This design intentionally prioritizes diplomacy because Bramble has an overpowered deck.
- **Bramble battle declined:** Existing encounter cooling/reset/rearm remains intact; does not complete or fail the spores quest. You may retry and negotiate.
- **Bramble already peaceful before accepting quest:** Revisiting her hideout after taking Moss's quest advances spore recovery. There is no remote dialogue from Moss's location.
- **Moss killed after becoming peaceful:** Not normally available in this tested framework because `Hook_OnPreUse` blocks combat against peaceful NPCs. The new quest nevertheless checks for `MossChoiceState == "Completed"` to fail gracefully if future mission mechanics allow it.

`SporeQuestStage` values: nil inactive; 1 search for Bramble; 2 spores recovered/return to Moss; 3 completed; 4 failed. All other flags, including one-time journal and reward guards, are independent from `HoneyQuest*`.

## Regression checklist

1. Honey quest first, then spores quest; ensure both complete, no duplicate rewards, journal milestones remain meaningful.
2. Start spores before accepting honey; complete either in different orders. Both must progress independently.
3. Peace with Moss, accept spores, negotiate Bramble, return to Moss. Save/load at stages 1, 2, 3.
4. Challenge Bramble then **decline** combat to verify reset/rearm and no spore progress; retry with peace. Do **not** risk a real unwinnable fight without a disposable save.
5. Kill Moss before peace: side quest unavailable, honey quest still works.
6. If feasible in a disposable save, defeat Bramble: side quest fails, never grants spores reward. This is not required given her intentionally overwhelming deck.
7. Pre-resolve Bramble peacefully, then accept side quest from Moss: revisit her location to obtain spores, not immediately upon acceptance.
8. On the Edge: ensure Bramble at (1,16) is in reachable trigger range. If no encounter, check walkability and possible interference from the rock.

## Technical notes

- A fourth NPC self-registers through the Lua-4/save-safe callback-name registry; no extra engine `Hook_*` functions.
- `SporeQuest_OnStep` is called from the existing `Hook_OnStep`, after `HoneyQuest_OnStep`.
- Journal writes use `ExMessageBoxStandard` and one-time saved flags. Ordinary dialogue uses `ExAddCommandText(..., 0)` except meaningful quest-giving and completion dialogue.
- `build.py` assembles the game-ready **single** `build/TestMap.scp`; individual `.lua` files are only developer sources.
- The entire lesson is **experimental until the player tests it**. Keep a copy of verified Lesson 28.

## In-game test report (2026-11-18)

Player confirms both honey and spores quests work, including save/load at every tested stage. One minor issue: Bramble repeated her final spore-related dialogue. The quest's additional spoken line was removed because her peaceful encounter already agrees to hand over the spores. The spore recovery state, journal update, and rewards are unchanged. **Final recheck passed:** player confirmed the corrected Bramble dialogue now works as intended.

## Final confirmation — 2026-11-18

The player verified the corrected Bramble dialogue no longer repeats, all dual-quest mechanics work, and save/load at different quest stages remains functional. The player additionally observed that changing the .scp script and loading older saves can work in this configuration. **This is observed compatibility for these edits, not a guarantee for future script or save-data changes.** Lesson 29 is the verified baseline for the upcoming first campaign map.
