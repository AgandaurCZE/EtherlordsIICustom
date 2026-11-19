# Etherlords II 1.03 campaign UI findings

The campaign selection card and the mission overview are editable through the resources of the Windows 1.03 build. The runtime comparison used a disposable game copy, which displays **Version 1.03** in its main menu. References to game files, saves and screenshots below describe the local research inputs.

| Element | Source | Evidence |
| --- | --- | --- |
| Selection heading above the Green portrait | `text.res` → `ELKTexts.txt` → `T_SC_CAMP_GREEN` | In-game replacement displayed **ECHOES OF THE ETHER** over the left card. **CHAOTS** stayed on the right. |
| Green selection portrait | `textures.res` → `Interface\compain_panel_01.mmp` and `Interface\compain_panel_012.mmp` | The magenta upper tile and yellow lower strip both rendered in-game. The lower tile also carries the lower part of the Chaots portrait, which stayed intact in the same run. |
| Illustrated overview background | `textures.res` → `Interface\GlobalMap\GlobalMap.mmp` | In-game grid replaced the illustrated map. The briefing and screen frame remained visible over the grid. |
| Chapter 1 marker position | `regs.res` → `GlobalMap\Green1.reg` | Changing the only point from `(222,236)` to `(100,100)` moved the marker to that grid intersection with the supplied CPG coordinates still in effect. |
| Marker artwork | `WORLD_SYMBOLS_MAP` → `Interface\world_symbols_map.mmp` | The main archive atlas was tinted cyan and the patch archive atlas magenta. The in-game Chapter 1 marker was magenta, establishing `textures002.res` precedence for this member with both archives installed. |
| Chapter 2–4 route geometry | `regs.res` → `GlobalMap\Green2.reg` through `Green4.reg` | The Chapter 2 overview drew the edited horizontal series after completing Chapter 1, with dots at the earlier positions and the active marker at the last point `(265,100)`. Chapters 3 and 4 decode in the same format. The supplied screenshots show the stock later route. |
| Location hover regions and names | `regs.res` → `GlobalMap\GlobalMap.reg` plus `text.res` → `MT_GMAP_TT_*` | The original Blackthorn Fortress region was moved to `[80,80,125,130]`. The new text **Campaign Probe Location** appeared on hover at the new region in-game. All 31 location keys exist in the text bank. |

## Campaign definitions, screen layout and progression

- `Campaigns/Green.cpg` is XML. The project copy uses `text_id="Green"`, `map="GlobalMap"`, and four ordered scenario records. Each points to a native map slot, a loose mission script, a briefing key, and a chapter header key. The CPG campaign name key `MT_E2C_GREEN_NAME` already resolves to `Etherlords III`. It is distinct from the selection-card heading. `T_VL_VITALS` also exists and resolves to `Vitals`. Keep the internal `Green` identifier and change `T_SC_CAMP_GREEN` for the selection heading.
- `map_x` and `map_y` are still present in the CPG and appear beside other campaign parser strings in the executable. Their destination or any other live use is unverified. The project’s earlier coordinate edit left the route in place, and the new `Green1.reg` test moved the marker independently of those values.
- `Controls.reg` defines named panels and child controls. Relevant names include `SelectCampaign`, `SCLeft`, `SCRight`, `SCCenter`, `SCHdr`, `GlobalMapA6`, `GMA6MapClip`, and `GMA6Header`. Child records include fields such as `Parent`, `Left`, `Top`, `Width` and `Height`. `InterfaceTextures.reg` separately binds texture labels to texture basenames.
- The local screenshots `shot0003.bmp` through `shot0006.bmp` show the native progression from a current marker to accumulated route dots. At the Chapter 1 overview of the fresh probe run, the Chapter 2 route was absent even with its resource staged. Positions, sprites, location strings and rectangles are data. Which stage is current is campaign state. For example, `Save/s.savc` records current campaign Green and scenario index 0, while the supplied post-campaign autosave records campaign index 1, scenario index 0 and possible campaign Black. The executable contains `CCampaignState` and `SFLB_NextCampaign` symbols. No resource record in the decoded route or location structures specifies a prerequisite, a campaign branch, or a marker-visibility rule.
- All five supplied CPGs select the same illustrated `GlobalMap` background. The marker atlas is shared UI data as well. Campaign-specific geometry is in the numbered route files. The original image contains the terrain and illustrated landmarks. With the grid in place, those landmarks disappeared while the live marker still rendered. New landmarks and permanently visible names can be painted into a custom map. Hover text can be edited independently through the location keys.

## Read-only executable evidence

These offsets are file offsets for the SHA-256 listed in [TESTING.md](TESTING.md). The strings establish the names used by this build and give entry points for further read-only tracing.

| File offset | Evidence |
| --- | --- |
| `0x5817C4–0x5817F0`, `0x58566C`, `0x590954` | Named archive strings for `textures.res`, `textures001.res`, `textures002.res`, `regs.res` and `text.res`. This copy has no `textures001.res`. |
| `0x58477C`, `0x584784`, `0x5847D8` | `map_y`, `map_x` and `.\campaigns\*.cpg` |
| `0x58C810–0x58C923` | `CGlobalMapA6`, map panel/control names, `GlobalMap\`, `.reg`, `Interface\GlobalMap\`, and file and campaign-ID error strings |
| `0x58EC08–0x58ECE8` | `CSelectCampaignScreen`, selection control names and all five `T_SC_CAMP_*` keys |
| `0x590944`, `0x591CFC`, `0x591EDC–0x591FB8` | `ELKTexts.txt`, `WORLD_SYMBOLS_MAP` and `CAMPAIGN_PANEL_*` asset labels |
| `0x5766E2`, `0x5AA350–0x5AA384` | `SFLB_NextCampaign@CCampaignState` and campaign save field names |

## Verification limits

- The tool preserves the point count of each route. It replaces coordinates in place. The Chapter 2 probe confirms progressive reveal at the normal mission transition. Chapter 3 and 4 replacements, alternate White branches, and additional progression rules were outside that runtime test. Authoring new prerequisites or replacing the native branch decision would require a verified data hook or a change to engine behavior. The known route files contain only points.
- The tooltip probe moved an existing rectangle and relocalized its key. Adding or deleting location records was outside that test. The payload contains the bounds and key for each location. The briefing should be closed when checking tooltip hit regions.
- A Green-only background would require the native loader to accept a different `map` value and matching data or to select a per-campaign asset via some other resource. The local files establish only the shared `GlobalMap` configuration. The tool does not add archive member names or provide new map IDs.
- Loose texture and registry-file override precedence was not tested. Archive replacement was used for the verified changes.

The community Etherlords modding repository helped identify `regs.res` as the configuration archive. The published Evil Islands RES layout supplied a cross-check for the header and directory, which were verified against the actual Etherlords II archives. [SomeSkull/EtherlordsModding](https://github.com/SomeSkull/EtherlordsModding) · [Original Nival RES format analysis](https://habr.com/ru/articles/434802/)
