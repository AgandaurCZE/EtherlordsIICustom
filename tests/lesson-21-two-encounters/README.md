# Lesson 21 — Two independent encounters

**Status: experimental; awaiting in-game verification.**

This lesson keeps the game-tested Lesson 20 Bee Queen module unchanged, adds Grumble as a second encounter, and dispatches engine callbacks through one shared router.

## Mandatory Map Editor setup

- Bee Queen **bluhblah** remains at **(7,5)** on **P2**, with the existing P2 Main Tower.
- **Grumble** stays at **(15,10)**, but **change his player assignment from P2 to P3**.
- Place **one P3 Main Tower** in an unobtrusive, valid location and set its owner to P3 (the editor's player definitions are anchored by Main Towers).
- Keep the hero on **P1** and its Main Tower.
- Ensure Grumble has a valid combat deck for all difficulty settings.

**Why P3?** The engine's documented `ExSetHostility(1, player, ...)` affects a whole player faction, not one monster. Putting both encounters on P2 would cause apologizing to the bee to change Grumble's hostility as well. P3 isolates their diplomacy. Do not test independent encounters without this map change.

## Source layout

- `src/encounters/bee_queen.lua` — byte-preserved copy of Lesson 20's game-tested Bee source.
- `src/encounters/grumble.lua` — Grumble dialogue/choices/attack/reset.
- `src/shared/hook_router.lua` — exactly one copy of each engine Hook_*.
- `build.py` — combines the source to `build/TestMap.scp`.
- `build/TestMap.scp` — copy this completed output next to your TestMap.smp.

Run `python build.py` from this lesson folder to regenerate.

## Focused regression sequence

1. Restart the map. Visit **Bee Queen** first and apologize, receive randomized spell. Now visit **Grumble**: his dialogue must still trigger; choose NO to challenge and verify native battle prompt.
2. Decline Grumble's battle: he should return to (15,10). Walk away and back: the opening dialogue should repeat.
3. Restart the map. Visit Grumble and choose YES for truce; then visit Bee and choose NO: her hostile charge and native battle must still work.
4. Restart the map. Test Bee NO/decline/rearm again as in Lesson 20.
5. Win an accepted Grumble battle and confirm normal continuation.

Log any odd interactions between encounters. In particular, if either encounter starts during the other's dialogue/cinematic, report it. Do not replace your verified Lesson 20 backup until this lesson passes.

This is an **architecture isolation test**, not a claim that P2/P3 diplomacy is monster-specific.
