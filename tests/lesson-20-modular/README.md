# Lesson 20 — modular Bee Queen encounter prototype

**Status: generated, but not yet verified in Etherlords II.** Preserve Lesson 19 as the fallback.

Files:
- `src/encounters/bee_queen.lua`: encounter-specific dialogue, reward and battle logic.
- `src/shared/hook_router.lua`: the sole engine-level Hook_* definitions.
- `build.py`: Python 3 standard-library-only offline builder.
- `build/TestMap.scp`: generated mission script; copy it next to TestMap.smp for testing.
- `reference/LESSON19_BASELINE.md`: game-test observations and provenance.

Build:
```sh
cd tests/lesson-20-modular
python build.py
```

The script builder checks for duplicate global functions and expected hooks; it is not a full Lua 4 syntax checker. Confirm dialogue, reward, decline/reset/rearm and victory in game before calling this version verified.

Do not edit `build/TestMap.scp` directly. This prototype intentionally retains some Lesson 19 debug screen messages and global scratch names.
