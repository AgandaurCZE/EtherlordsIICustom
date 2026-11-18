# Campaign UI localization probe — Etherlords III

This is a **real, prepared, but not yet in-game-verified** binary text resource patch.

Using the user's uploaded `text.res` (911,634 bytes), we located 10 UTF-16LE text records referenced by Green.cpg:

- `MT_E2C_GREEN_NAME` → `Etherlords III / Echoes of the Ether` (two lines)
- `MT_E2C_GREEN_DESC` → a new campaign description
- `MT_E2C_M11_NAME` → Echoes Awaken
- `MT_E2C_M12_NAME` → Beyond the Border
- `MT_E2C_M13_NAME` → Uncharted Territory
- `MT_E2C_M14_NAME` → Endgame!
- All four `MT_E2C_M1{1,2,3,4}_DESC` briefing values → provisional custom descriptions

**Validation:** preserved original 16-byte resource header, exact payload size, entire resource length, and every byte outside the UTF-16 payload; replaced each entry exactly once and padded shorter values with spaces, so existing payload offsets remain unchanged. A repeat execution produced byte-identical output. The ready-to-test package `EtherlordsIII_Campaign_UI_Text_Probe.zip` is delivered in the ChatGPT conversation with patched resource, original backup, patch script, changes report and checksums.

**Install:** only replace an actual installed `text.res` with your own backed-up original; first verify the source SHA256. Do not overwrite .cab/.rar archives or exe. Restart and check campaign selector text and mission briefing. Restore original resource afterward. If original text.res was *extracted* from an archive, investigate its archive resource path before attempting injection.

**Unchanged:** stock artwork, selection portrait/headings if texture-baked, campaign overview map markers, five campaign slots. This step isolates *localization*, not full UI visuals. **Do not claim the patch is game-tested.**

**Decision:** Keep the proven four-mission native campaign mod as the gameplay foundation; handle selection screen resources in a separate reversible asset pipeline.
