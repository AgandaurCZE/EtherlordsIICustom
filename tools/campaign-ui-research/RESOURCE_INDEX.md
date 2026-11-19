# Campaign UI resource index

Offsets are hexadecimal byte offsets in the source archives listed in [TESTING.md](TESTING.md). Rows are zero-based directory positions for inspection. The engine-facing names are the archive member paths, registry labels and localization keys. Use backslashes or slashes in the inspector.

## Textures

| Archive | Row | Offset | Member | Use |
| --- | ---: | ---: | --- | --- |
| `textures.res` | 999 | `0x1ab1fc60` | `Interface\compain_panel_01.mmp` | Green upper portrait, `CAMPAIGN_PANEL_01`, registry section `267` |
| `textures.res` | 1591 | `0x1ab3fcb0` | `Interface\compain_panel_012.mmp` | Green and Red lower strips, `CAMPAIGN_PANEL_012`, section `268` |
| `textures.res` | 1000 | `0x1ab5fd00` | `Interface\compain_panel_02.mmp` | Chaots upper portrait, `CAMPAIGN_PANEL_02`, section `269` |
| `textures.res` | 1001 | `0x1ab7fd50` | `Interface\compain_panel_03.mmp` | Dark portrait, `CAMPAIGN_PANEL_03`, section `270` |
| `textures.res` | 70 | `0x1ab9fda0` | `Interface\compain_panel_034.mmp` | Three lower portrait strips, `CAMPAIGN_PANEL_034`, section `271` |
| `textures.res` | 1002 | `0x1abbfdf0` | `Interface\compain_panel_04.mmp` | Blue portrait, `CAMPAIGN_PANEL_04`, section `272` |
| `textures.res` | 1003 | `0x1abdfe40` | `Interface\compain_panel_05.mmp` | Diamanda portrait artwork, `CAMPAIGN_PANEL_05`, section `273` |
| `textures.res` | 1299 | `0x184b1c20` | `Interface\black\compain_panel_19.mmp` | Similar Green portrait asset, `CAMPAIGN_PANEL_19`. The initial replacement of this tile had no effect on the tested selection card. |
| `textures.res` | 1419 | `0x1dd87a50` | `Interface\GlobalMap\GlobalMap.mmp` | Shared overview illustration |
| `textures.res` | 1278 | `0x1ed5aa70` | `Interface\world_symbols_map.mmp` | Base marker and overview UI atlas, `WORLD_SYMBOLS_MAP` |
| `textures002.res` | 1 | `0x400b0` | `Interface\world_symbols_map.mmp` | Active patch atlas in the tested setup |
| `textures.res` | 503, 504 | `0x1e664bc0`, `0x1e70f410` | `Interface\selection00.mmp`, `Interface\selection01.mmp` | Colored selection effects, visually distinct from the campaign portraits |

The on-disk spelling is `compain`. The Green artwork occupies columns 0–222 in both tiles. The upper tile uses rows 0–255. The lower strip uses rows 0–84 in `compain_panel_012.mmp`, followed by a separator on row 85 and the Chaots strip on rows 86–170. The tool's `green_portrait` input fits both tiles from a single 223 × 341 image and copies all remaining bytes of the shared tile. The `a6-int-campaign1-*`, `a6-int-campaign2-*`, `a6-int-camp-mission-*` and `a6-int-camp-text-*` families decode as UI frame or panel art.

## Overview data and localization

| Archive | Row | Offset | Member | Contents |
| --- | ---: | ---: | --- | --- |
| `regs.res` | 57 | `0x2719e0` | `GlobalMap\Green1.reg` | 1 point, `(222,236)` |
| `regs.res` | 58 | `0x2719f0` | `GlobalMap\Green2.reg` | 12 points, `(221,252)` to `(247,370)` |
| `regs.res` | 59 | `0x271a60` | `GlobalMap\Green3.reg` | 8 points, `(232,366)` to `(267,306)` |
| `regs.res` | 60 | `0x271ab0` | `GlobalMap\Green4.reg` | 6 points, `(281,294)` to `(322,235)` |
| `regs.res` | 38 | `0x2714c0` | `GlobalMap\GlobalMap.reg` | 31 keyed location rectangles. Example `(210,214,226,232)` → `MT_GMAP_TT_BLACKTHORN_FORTRESS` |
| `regs.res` | 22 | `0x2be4f0` | `InterfaceTextures.reg` | Texture aliases, file paths, and color flags |
| `regs.res` | 32 | `0x6f950` | `Controls.reg` | UI tree and control geometry |
| `regs.res` | 21, 24, 29 | `0x1ca0f0`, `0x3677a0`, `0x14baf0` | `ELKTexts.reg`, `Texts.reg`, `ELKIDs.reg` | Additional registry-form text resources. The tested selection heading was loaded from the text archive below. |
| `text.res` | 0 | `0x10` | `ELKTexts.txt` | UTF-16LE with BOM and `#KEY` headers. Relevant families are `T_SC_CAMP_*`, `MT_E2C_*` and `MT_GMAP_TT_*`. |

`regs.res` also contains routes for Black, Blue and Red stages 1–4 and White stages 1–2 and 3a/b through 5a/b. Use `list --match GlobalMap` for their exact rows and `inspect` for full point arrays. The supplied Green chapter headings are keyed by `MT_E2C_M11_NAME` through `MT_E2C_M14_NAME`, and their briefing counterparts end in `_DESC`.

## Binary layout

- **Nival RES.** Integer fields are little-endian. The 16-byte header contains four 32-bit fields in order, magic `0x019CE23C`, member count, directory offset and name table size. The directory uses 22-byte `<iIIIHI` records in Python notation. Fields are chain link (`-1` terminator), payload size, absolute payload offset, timestamp field, name length and relative name offset. The contiguous CP1251 name table follows the last row. All 15 inspected RES directories fit this layout. Member payloads are stored verbatim and are located by their offsets and sizes.
- **Route REG.** A little-endian `uint32` count is followed by that many `int32 x, int32 y` pairs in map-local pixels. For every numbered map route the file length equaled `4 + 8 × count`.
- **Location REG.** A little-endian `uint32` count is followed by records of four `int32` coordinates `(left, top, right, bottom)` and a NUL-terminated ASCII localization key. These two flat GlobalMap formats lack the `0x45AB3EFB` header found in ordinary game registry members such as `Controls.reg` and `InterfaceTextures.reg`.
- **Portrait and atlas MMP.** These are 256 × 256 single-level `MMP\0` textures. The 76-byte header contains width, height, level count, format, bits per pixel and channel masks with shifts and bit depths in A, R, G, B order. Portraits use 16-bit RGB565 (`0x5650`), and the symbol atlas uses 16-bit ARGB4444 (`0x4444`). Other members include ARGB1555 (`0x5551`), 32-bit data (`0x8888`) and six DXT1 MMPs. The preview command decodes the first level, including DXT1.
- **Overview BMP.** `GlobalMap.mmp` has a `BM` signature, a 40-byte DIB header, pixel offset 54 and bottom-up 736 × 444 BGR24 pixels. The 980,408-byte source includes two trailing bytes after the pixel array. The staging tool retains the original header and trailing bytes.

## Archive inventory

| File | Rows | Observed content or disposition |
| --- | ---: | --- |
| `Resources/textures.res` | 1972 | Primary texture bank |
| `Resources/textures002.res` | 9 | Eight existing names and one additional member. The marker atlas duplication was tested. |
| `Resources/regs.res` | 64 | UI configuration, map geometry, and other game registries |
| `Resources/text.res` | 1 | Main localization text |
| `ar_text.res` | 1 | Separate `AR_*` UI text bank without campaign heading keys |
| `Resources/scripts.res` | 72 | Includes compiled Lua chunks and stock mission scripts |
| `Resources/sfx.res`, `sfx002.res` | 4241, 15 | RIFF audio banks, with interface and mission voice assets |
| `Resources/MEPicture.res` | 45 | Editor pictures, beginning with JPEG payloads |
| `Resources/animdb.res`, `camera.res` | 437, 61 | Animation data and camera records |
| `Resources/crfigures.res`, `figures.res`, `fx.res`, `pfx.res` | 176, 1373, 126, 1195 | Figure and effects resources. Figure archives include nested RES members. |

`tileset.tsr` has a different signature. The loose campaign XML, mission `.map` / `.ebm` files, screenshots and save pairs are also outside the RES directory format.
