# Maintainer / assistant instructions

## Purpose
Develop modular Lua 4-compatible scripted encounters for Etherlords II custom adventure maps. The game/editor is the runtime authority.

## Before changing code
1. Read `README.md`, `docs/PROJECT_STRUCTURE.md` and `docs/TESTING_GUIDE.md`.
2. Review the relevant lesson's README and state whether it was game-tested or experimental.
3. Preserve a known-working backup of Lesson 19. Do not silently overwrite a proven version.
4. Work on a branch and review a diff before merging.

## Code conventions
- Only **one** global `Hook_*` implementation per mission, in a central router.
- Give encounter functions and persistent variables unique prefixes.
- Use `ExGetVariable`/`ExSetVariable` for encounter state. Avoid Lua 5+ syntax and capturing outer local variables in Lua 4.
- Distinguish runtime object IDs from permanent editor IDs. Identify mapped objects reliably.
- Be conservative with `Hook_OnStep`, command queues, dialogue hooks and battle-result return values.
- Generated `.scp` files are outputs: edit modules, rebuild, then test the generated result in the game.
- Validate duplicate function declarations before producing a build; remember that concatenation is **not** a full Lua parser or runtime validation.

## Original game references
Prefer `Script functions.pdf`, `adventure_lib.txt`, `ReadMe.txt`, `e2tutorial.scp`, and the original Mission 14 Walking Horror code when available locally. Don't claim bytecode reconstruction proves behavior that has not been game-tested.

## Release criteria
Record test version, in-game environment, dialogue YES/NO, reward, battle decline/return/rearm, and win outcome. Keep any future experimental change explicitly marked unverified. Never upload third-party game binaries or archives here without authorization.
