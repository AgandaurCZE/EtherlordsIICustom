# Project structure and architecture

The map editor's `ReadMe.txt` describes a map and its matching script filename, e.g. `TestMap.smp` and `TestMap.scp`.

## Directories
- `tests/lesson-19-working/`: documented, game-confirmed Bee Queen baseline. The authoritative exact script is the player's local working backup.
- `tests/lesson-20-modular/`: standalone experiment with editable modules and an offline concatenating builder.
- `docs/`: workflow and troubleshooting.
- `references/`: notes identifying original editor and campaign resources, not redistributing them.
- `src/`: reserved for promoted, repeatedly tested production modules.

## Runtime model
The game gets one generated mission `.scp`. Developer source can contain one file per encounter and a centralized router for the engine's global `Hook_*` callbacks. Do not assume custom maps automatically load other `.scp` files. We have not verified runtime loading of arbitrary external scripts.

## Current router
Lesson 20 forwards step, close-message, battle-finish, and pre-use callbacks to the Bee Queen. As more encounters are added, battle callbacks must dispatch by the actual runtime attacker/target IDs, with exactly one handler per battle. Dialogue interactions also need explicit ownership routing.

## Known Lua 4 concerns
Avoid Lua 5 language features, outer-local captures, and duplicate global functions. The current prototype still contains short-lived global scratch names; namespacing these is a future change to test independently.

## Change strategy
1. Archive and preserve the current known-good build.
2. Refactor **one** encounter; test every branch in-game.
3. Add a second encounter only after confirming that the router and rebuild process preserve the first.
4. Maintain a per-lesson changelog and a rollback path.
