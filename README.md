# Etherlords II Custom — Etherlords III experiments

A source-controlled workshop for creating a fan Etherlords III campaign using **Etherlords II 1.03** (Steam/Windows), its Map Editor, and **Lua 4** scripting.

## One main branch, archived lessons

**All tests and source code are now available in the `main` branch.** Each lesson has a separate directory with its source modules and a generated complete `TestMap.scp`. You only need to copy the *generated* script into the game's `Maps/Custom` folder, next to your `TestMap.smp`.

| Lesson | Folder | What it demonstrates | Status |
|---|---|---|---|
| 19 | [lesson-19-working](tests/lesson-19-working/) | Bee Queen dialogue, rewards, battle refusal/retreat | Game-tested |
| 20 | [lesson-20-modular](tests/lesson-20-modular/) | Source modules assembled into a single `.scp` | Game-tested |
| 21 | [lesson-21-two-encounters](tests/lesson-21-two-encounters/) | Grumble introduced on separate P3 faction | Game-tested historically; superseded |
| 22 | [lesson-22-shared-faction](tests/lesson-22-shared-faction/) | Bee and Grumble share P2 with separate scripted truces | Game-tested; native attack cursor remains |
| 23 | [lesson-23-save-load](tests/lesson-23-save-load/) | Choices and rewards persist across save/load | Game-tested |
| 24 | [lesson-24-registry](tests/lesson-24-registry/) | Save/load-safe callback-name registry and generic router | Game-tested **with hotfix merged** |
| 25 | [lesson-25-template](tests/lesson-25-template/) | Third encounter, Moss (Hero model), plus reusable template | **Partially game-tested**: Bee→Moss interaction choices and saves work; full regression pending |

For current three-encounter testing use [Lesson 25 generated TestMap.scp](tests/lesson-25-template/build/TestMap.scp). For the last fully verified two-encounter fallback use [Lesson 24 generated TestMap.scp](tests/lesson-24-registry/build/TestMap.scp).

The Lesson 24 fix is included in the Lesson 24 folder on `main`: callback functions are stored in the encounter registry **as strings** and looked up using Lua 4 `getglobal(name)`, rather than saving Lua function values (which caused a crash after loading).

## Documentation

- [Project structure](docs/PROJECT_STRUCTURE.md)
- [Testing and rollback](docs/TESTING_GUIDE.md)
- [Editor and original game references](references/ORIGINAL_GAME_FILES.md)
- [Reusable encounter template guide](tests/lesson-25-template/TEMPLATE_GUIDE.md)

## Current test map

- Main hero: P1
- Bee Queen bluhblah: P2, **(7,5)**
- Grumble: P2, **(15,10)**
- Moss: P2, **(10,16)** — tested using a **Hero** character model
- P1/P2 Main Towers; no P3 tower needed
- Playable map dimensions are constrained to an accessible **19×19** area inside the nominal 20×20 editor map; keep NPC positions inside accessible tiles

The engine's hostility relations are faction-wide. Peaceful interactions are controlled per character through `Hook_OnPreUse` and `Hook_OnIntercept` based on saved individual encounter states. Peaceful P2 NPCs can retain the native attack cursor even when attacking them is prevented.

## Workflow

Develop and archive new lessons as separate directories under `tests/` on `main`; preserve previous generated scripts for rollback. The modular source and builder generate a **single** `TestMap.scp` for the game. Game testing, especially save/load and independent interactions, is required before calling a lesson fully verified.

## Safety

The repository is public. Do not upload copyrighted executables, resource archives, commercial map packages, or entire game documentation without verifying permission. Keep original-game assets locally.

*BZZZZ! Long live bluhblah, and may Moss keep his mushrooms.* 🐝🍄
