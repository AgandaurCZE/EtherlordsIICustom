# Etherlords III — Native campaign foundation (Vitals slot)

**Status:** Previous native campaign build game-tested; these renamed/cleaned scripts are a new experimental revision awaiting a quick regression test.

## Verified discoveries (Nov 18, 2026)
- User-created .smp and .sbm can be adapted to the stock campaign's existing map resource names: e2mission11.map/.ebm and e2mission12_52.map/.ebm.
- Both *distinct* editor-created landscapes load in sequence through a modified Green.cpg.
- Native campaign progression retains hero EXP/level, skills, specialization, resources, deck, reserve spells, artifacts, including a player-picked-up artifact.
- Returning 1 from Hook_OnBattleFinishing avoids the stock specialization error 'Hero not found: 0' while the battle still grants the game-reported 2,300 EXP.
- Permanent variables saved using ExSetVariable(key, value, 1) persist between those linked campaign missions.
- Adding a new E3Test.cpg did not make a sixth selectable campaign. Using newly invented map resource names crashed; existing known resource names worked.

## Decision
Develop this project as a **native campaign replacement/mod**, not disconnected standalone custom missions. This reuses genuine character persistence and campaign mission progression. It **currently occupies the Vitals slot**. Never distribute as a sixth campaign; that was not verified. The selection art, descriptions, overview/map markers and stock mission roster are **not** replaced yet. They are a separate resource/UI discovery workstream.

## Package and files
The ready-to-install package is delivered in chat as EtherlordsIII_Campaign_Foundation.zip. The verified XML and EBMs derive from the user's Chapter01/Chapter02 .smp/.sbm and are included in that ZIP. This GitHub folder archives source Lua and decisions. The ZIP modifies Campaigns/Green.cpg and the e2mission11/e2mission12_52 map resources; install only after backing up originals, and use the ZIP's rollback instructions.

- `Maps/E3_Chapter01.scp`: fort at (21,14) triggers victory and permanent completion flag, plus native-battle safe override.
- `Maps/E3_Chapter02.scp`: checks completion flag and native campaign transfer, refuses progression if missing; chapter 2 story/ending not yet implemented.

## Future work
1. Author a real Chapter 01 story, encounters and quest journal using our verified modular quest architecture.
2. Author Chapter 02 content and a proper chapter-ending condition; later map slots must be mapped explicitly.
3. Investigate safe modding/replacement of Vitals campaign title/portraits, campaign overview/minimap and localization text IDs.
4. Provide an installer/uninstaller that validates original resource versions and restores backed-up files. Do not overwrite installed Vitals content without warning.
