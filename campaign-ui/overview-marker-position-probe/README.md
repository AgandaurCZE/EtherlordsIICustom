# Campaign overview marker position test

**Status:** prepared, not yet game-tested. Package in chat: `EtherlordsIII_Campaign_UI_MarkerPosition_Test.zip`.

## Verified UI observations
The user tested the `text.res` patch and confirmed new campaign description and all four chapter headers and briefings appear, while the original Vitals selection portrait and global map picture remain. This is expected: the patch only altered localized text.

## New test
Modify only `map_x` and `map_y` on the four `<scenario>` tags in the working four-mission `Green.cpg`:

| Mission | Previous position | Test position |
|---|---|---|
| 1 | (201,191) | (410,175) |
| 2 | (201,314) | (410,230) |
| 3 | (263,253) | (410,285) |
| 4 | (263,191) | (410,340) |

No scripts, maps, binaries, `text.res`, or artwork are changed. Back up your installed `Campaigns/Green.cpg` before temporarily replacing it with the ZIP's `Campaigns/Green.cpg`; retain the tested four-mission mod. Restore original after checking whether mission markers move. New locations are diagnostic, **not final**.

## Open UI engineering question
Identify where stock Vitals campaign card artwork, 'VITALS' top header and 'GlobalMap' world artwork are sourced (texture archives, UI resources, or executable). Nothing uploaded to date grounds an actual texture replacement path. Do not guess resource paths or edit executable blindly. Build an asset replacement only after original texture and loader are identified.
