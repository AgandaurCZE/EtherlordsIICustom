# Build, verify and roll back campaign UI changes

Use Windows PowerShell from the repository root and set `$baseline` to the local game copy containing the resources in the checksum table. The tool requires Python 3.11 or newer and uses Pillow for image decoding and encoding. Listing, binary extraction, structured inspection and text or registry staging use the Python standard library.

```powershell
python -m pip install Pillow
Set-Location tools/campaign-ui-research
$baseline = (Resolve-Path 'E:\EtherlordsIII-Baseline').Path
$resources = Join-Path $baseline 'Resources'
New-Item -ItemType Directory -Force .campaign-ui-local | Out-Null
python campaign_ui.py "$resources/textures.res" list --match 'compain_panel|world_symbols|globalmap'
python campaign_ui.py "$resources/textures.res" preview 'Interface/GlobalMap/GlobalMap.mmp' .campaign-ui-local/stock-overview.png
python campaign_ui.py "$resources/textures002.res" preview 'Interface/world_symbols_map.mmp' .campaign-ui-local/active-atlas.png
python campaign_ui.py "$resources/regs.res" inspect 'GlobalMap/Green2.reg'
python campaign_ui.py "$resources/regs.res" inspect 'GlobalMap/GlobalMap.reg'
python campaign_ui.py "$resources/text.res" inspect 'ELKTexts.txt'
python campaign_ui.py "$resources/regs.res" extract 'Controls.reg' .campaign-ui-local/Controls.reg
```

The `inspect` output is JSON. A route or localization inspection can be redirected into a manifest and trimmed to the entries you want to change. Location inspection returns a list of records. To edit rectangles, use the key-to-bounds object shown below. `extract` returns the exact member bytes. `preview` saves a PNG. Both require a new output filename. Keep extracted artwork, staged game archives and the disposable game copy local. The repository ignores `.campaign-ui-local/`.

## Stage a portrait, map and route

Place your own `green-portrait.png` (223 × 341) and `overview.png` (736 × 444) in `.campaign-ui-local`. Save the following JSON files alongside the images. Image paths are relative to the manifest. JSON keys can use forward slashes. The input images may use any format supported by Pillow.

`textures.json`

```json
{
  "green_portrait": "green-portrait.png",
  "Interface/GlobalMap/GlobalMap.mmp": "overview.png"
}
```

`regs.json`

```json
{
  "GlobalMap/Green1.reg": [[100, 100]],
  "GlobalMap/Green2.reg": [[100, 100], [115, 100], [130, 100], [145, 100], [160, 100], [175, 100], [190, 100], [205, 100], [220, 100], [235, 100], [250, 100], [265, 100]],
  "GlobalMap/GlobalMap.reg": {
    "MT_GMAP_TT_BLACKTHORN_FORTRESS": [80, 80, 125, 130]
  }
}
```

`text.json`

```json
{
  "ELKTexts.txt": {
    "T_SC_CAMP_GREEN": "ECHOES OF THE ETHER",
    "MT_GMAP_TT_BLACKTHORN_FORTRESS": "Campaign Probe Location"
  }
}
```

For a marker-art test, edit the previewed 256 × 256 patch atlas, preserving its alpha and each sprite's atlas position. Save it as `.campaign-ui-local/symbols.png` and use this optional `textures002.json` manifest. The game uses the atlas for several UI elements and campaigns. Keep unrelated regions intact.

```json
{
  "Interface/world_symbols_map.mmp": "symbols.png"
}
```

```powershell
python campaign_ui.py "$resources/textures.res" stage .campaign-ui-local/textures.json .campaign-ui-local/output/textures.res
python campaign_ui.py "$resources/regs.res" stage .campaign-ui-local/regs.json .campaign-ui-local/output/regs.res
python campaign_ui.py "$resources/text.res" stage .campaign-ui-local/text.json .campaign-ui-local/output/text.res
# Optional marker art
python campaign_ui.py "$resources/textures002.res" stage .campaign-ui-local/textures002.json .campaign-ui-local/output/textures002.res
```

Omit files and JSON entries you do not need. Staging writes a new archive under its original basename, prints both hashes, and verifies the changed members by reading them back. Existing files are refused. Use a fresh staging subdirectory for each revision. The tool leaves equal-length entries at their original offsets. If a text edit changes the byte length, it appends the new text payload before the relocated directory and updates the relevant offset and size. Route edits keep the original point counts. The `green_portrait` input preserves the Chaots strip. Advanced use can replace the two full 256 × 256 portrait tiles by explicit member name.

## Install into a disposable copy

Close the game. Run this from `tools/campaign-ui-research` with the same `$baseline`. The destination must be new. Use the local working 1.03 game tree with the custom missions and matching archives as the source. This copies the executable and support files byte for byte for use with your normal licensed launch method.

```powershell
$scratch = (Resolve-Path .campaign-ui-local).Path
$testGame = Join-Path $scratch 'verify-game'
if (Test-Path -LiteralPath $testGame) { throw "Use a new disposable directory." }
robocopy $baseline $testGame /E /XD .git .campaign-ui-local tools /XF shot*.bmp /NJH /NJS /NFL /NDL /NP
if ($LASTEXITCODE -ge 8) { throw "Could not create the test copy." }

$backup = New-Item -ItemType Directory (Join-Path $scratch 'verify-original')
$staged = Get-ChildItem -LiteralPath (Join-Path $scratch 'output') -Filter '*.res' -File
if (-not $staged) { throw "No staged archives." }
foreach ($file in $staged) {
    $target = Join-Path $testGame ('Resources\' + $file.Name)
    $saved = Join-Path $backup.FullName $file.Name
    Copy-Item -LiteralPath $target -Destination $saved -ErrorAction Stop
    if ((Get-FileHash -LiteralPath $target).Hash -ne (Get-FileHash -LiteralPath $saved).Hash) {
        throw "Backup checksum mismatch for $($file.Name)."
    }
    Copy-Item -LiteralPath $file.FullName -Destination $target -ErrorAction Stop
    if ((Get-FileHash -LiteralPath $target).Hash -ne (Get-FileHash -LiteralPath $file.FullName).Hash) {
        throw "Installed test checksum mismatch for $($file.Name)."
    }
}
Get-ChildItem -LiteralPath $backup.FullName -File | Get-FileHash
```

Launch the copy with its working directory set to `verify-game`. This workspace's `Run.cmd` normally sets the `WIN2000` compatibility layer. The runtime test started the unchanged executable with the equivalent command below. The disposable settings used 1024 × 768, the bundled graphics wrapper, and `Video=0` to skip intros.

```powershell
$env:__COMPAT_LAYER = 'WIN2000'
Start-Process -FilePath (Join-Path $testGame 'Etherlords2.exe') -WorkingDirectory $testGame
```

## Verify in game

1. Confirm **Version 1.03** on the main menu. Use **Single → Campaign → New Campaign**. Check the left heading, both sections of the Green portrait and both sections of the neighboring Chaots portrait. Select each card in turn to check its normal and dimmed rendering.
2. Select the left campaign and click the lower-right checkmark. Check the new illustration underneath the Chapter 1 briefing and compare the current marker against `(100,100)` on your map. Clicking the briefing's small × exposes the full map. If you edited the atlas, inspect the current marker's sprite or color.
3. With the briefing closed and mouse-over tooltips enabled, hover within `[80,80,125,130]` in map-local pixels, just outside the marker sprite, and test the former Blackthorn Fortress region as a control. Record whether the expected tooltip appears. The location labels are separate from the mission header.
4. Start Chapter 1 at the desired difficulty and finish it normally. Look for the horizontal point series on the Chapter 2 overview. Finish Chapters 2–4 to verify the later route segments, the briefing text, and the native transition to the next selection screen. Compare a new campaign with a copied existing save as needed. An autosave after the full Green campaign resumes at the subsequent campaign selection, so it is not a Chapter 2 checkpoint.

## Rollback

Close the disposable game. From the same PowerShell session, restore its copied resources and compare each restored hash with its backup. The repository source and any installed copy can be kept outside this workflow.

```powershell
foreach ($file in Get-ChildItem -LiteralPath $backup.FullName -Filter '*.res' -File) {
    $target = Join-Path $testGame ('Resources\' + $file.Name)
    Copy-Item -LiteralPath $file.FullName -Destination $target -ErrorAction Stop
    if ((Get-FileHash -LiteralPath $target).Hash -ne (Get-FileHash -LiteralPath $file.FullName).Hash) {
        throw "Rollback checksum mismatch for $($file.Name)."
    }
}
```

## Source checksums and verification record

These are SHA-256 hashes for the local research inputs. The tested `Green.cpg` and `text.res` already contained the project's prior custom edits.

| Source | SHA-256 |
| --- | --- |
| `Resources/textures.res` | `0b6a82b36aad5f4d1ed819f74bae81cd59ad6f67e7ec80c50a5b7ddf5b077cfb` |
| `Resources/textures002.res` | `e8861810751a63480fe752180f393bb6ae2ef6c767ed19df4f17259c04597b50` |
| `Resources/regs.res` | `e38ed76d8fcde2aeee1e22a89771e9eb05d95f3364e122a3024db929975970d7` |
| `Resources/text.res` | `0360ed75214fc2565fef1e3bb67b096323d6a9d5a4e17a87a72b38b7d6f9af6b` |
| `Campaigns/Green.cpg` | `04faaaf4537d0271ef49acbdc633b8f9b867066a47ee585897834b3afeef4d41` |
| `Etherlords2.exe` | `d3ed30f840b3325b1f03c01aa486e7f44328a7d6993964c409950a65e86a158b` |

The local verification parsed all 15 RES directories and all 24 numbered route payloads, decoded all six DXT1 textures and compared every archive member of the staged outputs against its source. The intended changed members were the two portrait tiles, the overview image, the two atlas copies used for the precedence test, the two stage routes, the location record and the main text bank. The overview's decoded staged pixels matched the grid input, and the Chaots strip in the shared tile compared byte for byte with its source. In-game checks confirmed the heading, the two portrait tiles, the shared overview image, the first marker position, the active atlas, the altered Chapter 2 path after completing Chapter 1 and **Campaign Probe Location** at its moved hover region.

After the runtime checks, all four modified archives in the disposable copy were restored from backup. Their SHA-256 hashes matched both the backups and the repository source files. The repository executable and campaign definition also matched their recorded hashes.

## Versioned package acceptance

The [package workflow](README.md) reuses those verified replacements. The 0.1.0 template build checked every staged member and compared protected portrait bytes with the pinned source. ZIP verification confirmed that only the three changed archives and installation instructions were included. A text-only build included just `text.res` and the instructions. Rejected inputs included a source checksum mismatch, an incorrectly sized PNG, an invalid route point count, an out-of-scope localization key, and a manifest with no payload changes.

The generated PowerShell installer rejected both the research checkout as an installation target and a tampered package archive. Installation and rollback succeeded in the disposable game copy, including repeat calls with the earlier package build. All three restored SHA-256 hashes matched the baseline. The packaged editing guides were verified at the archive level. The in-game comparisons above used the earlier visual probes.
