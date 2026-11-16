# Etherlords II Custom — Etherlords III experiments

A source-controlled workshop for building original adventure-map encounters and a future fan campaign with **Etherlords II 1.03** (Steam/Windows), using the map editor and **Lua 4** scripting.

## Start here

- [Project structure](docs/PROJECT_STRUCTURE.md) — why we keep editable modules separate from generated game scripts.
- [Testing and rollback](docs/TESTING_GUIDE.md) — how to test without losing the proven Bee Queen encounter.
- [Script references](references/ORIGINAL_GAME_FILES.md) — descriptions of the original editor documentation and campaign files studied.
- [Lesson 19](tests/lesson-19-working/README.md) — successful in-game behavior; save the player's exact original working script as the authoritative baseline.
- [Lesson 20](tests/lesson-20-modular/README.md) — **not yet verified in game**; modular refactor and script builder.

## Status

- **Lesson 19: game-tested success.** Bee Queen dialogue, peaceful reward, hostile automatic charge, declining combat and rearming, and victory were confirmed by the player.
- **Lesson 20: generated prototype; requires regression testing.** Keep the working Lesson 19 backup until all branches are tested.

## Safety and ownership

This repository is public. Do not upload proprietary Etherlords II executables, `.res` archives, commercial campaign maps, or entire copies of bundled documentation without verifying permission. Keep these original resources locally; project notes explain what was learned from them. Do not commit personal game-installation paths or large diagnostic logs.

## Quick test

Copy a **generated** `TestMap.scp` beside the map `TestMap.smp` in the local game installation, then restart the scenario. Do not replace the only working Lesson 19 backup.

*BZZZZ! Long live bluhblah, our first properly scripted encounter.* 🐝
