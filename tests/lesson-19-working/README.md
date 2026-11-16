# Lesson 19 — game-tested Bee Queen baseline

**Status: success confirmed in-game by the player.** The original complete Lesson 19 script was delivered in chat; the player's *actual local working* `TestMap.scp` remains the authoritative backup. Do not mistake the new Lesson 20 refactor for a separately game-tested copy.

Verified behavior:
- Proximity-based introduction, choice to apologize or insult.
- YES: peaceful bee, randomized ALST/ASLT spell, native reward message.
- NO: hostile bee, camera focus, charge and native Accept Battle confirmation.
- Decline: bee resets to its home location and the encounter can be triggered again after leaving/reapproaching.
- Accepted and won: normal game progression after battle.
- Cosmetic issues: facing direction and player position are not priorities.

## Preserve the baseline
Copy the **actual tested** local script to a safe backup and then archive it here if desired and you have the exact bytes. Never silently rewrite or replace an authoritative original with a reconstructed equivalent. See `docs/TESTING_GUIDE.md`.

Lesson 20 is a refactor of the conversation's Lesson 19 code and must be tested separately.
