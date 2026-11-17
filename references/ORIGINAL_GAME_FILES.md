# Original Etherlords II material consulted

These game/editor resources were provided for analysis. They are **not included** in this public repository because game resources and documentation may be copyrighted. Use your own legitimately obtained local installation.

| Local resource | Purpose |
|---|---|
| `MapEditor/ReadMe.txt` | Map editor basics; matching map and `.scp` names; Lua scripting |
| `MapEditor/Script functions.pdf` | Engine adventure functions, commands and callback signatures |
| `MapEditor/adventure_lib.txt` | Original adventure library's documented interface, local hooks and helpers |
| `Tutorial/Adventure/e2tutorial.scp` | Readable example of original developer scripting |
| `scripts.res` | Original compiled Lua 4 mission scripts; used to inspect Mission 14 |
| `e2mission14.map` / `e2mission14.ebm` | Original campaign map data for the Walking Horror encounter |

## Walking Horror finding
The Mission 14 battle-finishing branch was analyzed and found to reposition the Walking Horror at (62,55), reposition the hero at (62,50), reset the gate state and close the gate after a non-winning outcome. The Bee Queen experiment adapted that style of reset. The player **confirmed in game** that declining the Bee Queen's native battle prompt triggers a reset in the Lesson 19 encounter. That observed result is more important than assumptions about generic callback behavior.

## Not yet proven
We have **not** established that arbitrary extra scripts can be loaded by custom maps at runtime or that repacking `scripts.res` is necessary. For now, produce one script per map using offline build tooling.
