# Build the Etherlords III campaign UI

From the repository root, with Python 3.11 or newer and Pillow available, run one command. Point it at your own local resource baseline.

```powershell
python tools/campaign-ui-research/build_campaign_ui.py --source-resources 'E:\EtherlordsIII-Baseline\Resources'
```

Install Pillow once with `python -m pip install Pillow` if needed. The command uses [campaign_ui.py](campaign_ui.py) to encode and stage replacements. It checks all three source SHA-256 hashes against [release.json](release.json), validates input manifests and checks the output archives and ZIP before publishing. It opens source archives read-only. The pinned baseline is the English Windows 1.03 research copy, including the project's previously customized `text.res`. A clean retail or Steam text archive may differ. See [TESTING.md](TESTING.md) for the source hashes.

The output is `tools/campaign-ui-research/.campaign-ui-local/packages/etherlords-iii-campaign-ui-<version>-<content-id>.zip`. The ZIP contains `INSTALL.md` and only archives whose member bytes changed. The default template build contains `textures.res`, `regs.res` and `text.res`. These are complete replacement archives because the game reads the native containers. Keep them local. The installer instructions include a PowerShell script that checks both baseline and package hashes, retains verified backups, supports resuming an interrupted install, and restores by checksum. Use a separate game copy for installation.

## Replace the template artwork

The included PNGs are original editing guides. The overview guide marks the endpoints used in the example route and tooltip manifests. Replace these guides with your own finished artwork before packaging a release.

| Input | What to edit |
| --- | --- |
| [portrait.json](portrait.json) | Point to a 223 × 341 PNG inside the project. The encoder splits it at row 256. |
| [overview.json](overview.json) | Point to a 736 × 444 PNG inside the project. Map coordinates start at the upper left. |
| [mission-routes.json](mission-routes.json) | Edit the ordered pixel pairs for Green stages 1–4. The required counts are 1, 12, 8 and 6. Preserve the order, with each stage's destination last. |
| [hover-locations.json](hover-locations.json) | Assign existing map keys to rectangles in `[left, top, right, bottom]` pixel coordinates. |
| [localization.json](localization.json) | Edit `T_SC_CAMP_GREEN` for the visible selection heading. Add Green campaign name, chapter or briefing keys as needed. Rename hover labels using the keys in the location manifest. Existing strings outside the requested keys are preserved. |
| [release.json](release.json) | Increment the version when preparing a release. Keep the source hashes pinned to the verified baseline. |

For local art or extracted references, copy the project into the ignored work area and edit that copy. The source archives can also be specified explicitly.

```powershell
Set-Location tools/campaign-ui-research
$project = '.campaign-ui-local/etherlords-iii'
New-Item -ItemType Directory -Force $project | Out-Null
Get-ChildItem -File -Filter '*.json' | Copy-Item -Destination $project
Copy-Item -LiteralPath templates -Destination $project -Recurse
python build_campaign_ui.py --project $project --source-resources 'E:\EtherlordsIII-Baseline\Resources'
```

Keep image paths relative to the project. Set an image manifest's value to `null` to leave that image alone. Omit individual Green route keys to keep those source routes. Use an empty object in a data manifest to skip that group. Rebuild after each edit. The package filename changes with its version or staged contents, and a repeat build verifies and reuses an identical package.

Keep extracted game art, backups, staged archives and packages under the ignored `.campaign-ui-local/` directory or in a private folder outside the repository. The PNGs committed under `templates/` are original guides.

## Shared UI and Green-specific UI

| Scope | Components |
| --- | --- |
| Green campaign | Selection heading, Green portrait pixels, Green chapter and briefing keys, and the four Green route entries. The build validates both portrait tiles, including the neighboring Chaots pixels in the shared lower tile. |
| Shared across campaigns | The illustrated overview BMP and the hover location rectangles and labels. Renaming or moving those locations affects any campaign using `GlobalMap`. For a Green-only build, skip the overview image and location edits and remove the `MT_GMAP_TT_*` overrides. |
| Native behavior | The existing marker atlas, unlock sequence, mission transitions, gameplay scripts and save data stay in use. The package only changes route positions and presentation data. |

For archive formats and in-game verification details, see [FINDINGS.md](FINDINGS.md), [RESOURCE_INDEX.md](RESOURCE_INDEX.md) and [TESTING.md](TESTING.md).
