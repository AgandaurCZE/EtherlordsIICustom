# Etherlords III — Card Creator

A Windows desktop editor for building additive Etherlords II 1.03 cards. The editor uses Tk with Pillow for image previews and conversion. The local test launcher reuses the game's existing native producer registry and checks the exact executable build.

## Start

1. Install 64-bit Python 3.11 or newer with Tcl/Tk enabled. Keep this tools directory together with the repository’s `experiments` and `tools/campaign-ui-research` directories.
2. Double-click **Launch Card Creator.cmd**. The first launch sets up a local Python environment and installs Pillow. Later launches open the window directly.
3. In **Settings**, choose a stock English Etherlords II 1.03 folder as the source. The app checks the executable hash plus the registry, text, model, animation and texture archives.
4. Use **Card Library** to open the included example, start a new project, or add, duplicate and edit cards. **Save** writes a project JSON. The help panel follows the selected control.
5. In **Build & Install**, click **Build Mod**. The app verifies every card, preserves the original rows, builds the local archives and reports the versioned package path.
6. Click **Create Disposable Copy**, then **Launch Test Game** in **Testing & Diagnostics**. In Single → Duel, choose a generated **Card Creator** deck for the relevant faction at resource level 3. Use the application launcher for any game that has the installed custom definitions.

`example-project.json` contains TESTING Rat and TESTING CARD. `five-card-test-project.json` adds Testing Guard, Testing Shaman and Testing Recall. The PNG example gives Testing Guard an original gold shield, and the schema describes the on-disk format. Artwork paths may be absolute or relative to the saved project. [PNG example](examples/custom-portrait-project.json) · [Project schema](project.schema.json)

For development, run `python app.py` from this directory after installing the requirements. Optional arguments select a project, source game and workspace. The default workspace is under Local AppData. Build outputs, test games and diagnostic logs are local.

## What the editors support

| Feature | Scope |
|---|---|
| New creatures | Original four-character ID, four playable factions, fixed base Ether cost, attack, health, rarity and real native family. The source catalog lists 136 stock model rows with matching mesh and animation entries and 41 family names. |
| Abilities | Standard summon, Kobold Shaman Zap, or Doom Rat Brotherhood. Each creature can select one implementation. Models retain their stock animation and sound set. Untested model and ability combinations deserve a Duel before campaign use. |
| New spells | Greater Unsummoning is the supported additive donor. Its stock effect returns eligible creatures from both sides with Kinets visuals. Choose either the stock per-creature surcharge or a flat project-defined base cost. |
| Artwork | Stock small illustration references and stock creature detail portraits. For custom creature detail art, choose a 384 × 512 PNG. The builder converts it to three MMP tiles. An already packed 768 × 256 PNG sheet is also accepted. |
| Preview | Editor approximation of the selected faction, cost, illustration, stats and effect. The game remains authoritative for rendering. |
| Scale | Each custom ID gets a distinct native allocation. Duel fixtures page sets of up to 16 definitions by faction. The builder checks the signed registry index capacity. The maximum stable runtime card count remains unmeasured. |

Arbitrary meshes and animations, custom small-icon atlases, custom spell detail artwork, multiple attached abilities, arbitrary damage or target overrides, and ordered effects on additive cards are outside this release. The earlier stock Zap experiments remain available in their own branch. The utility guides users toward implemented configurations.

## Install and roll back

**Build Mod** only writes a package under the local workspace. It includes the generated archives, test presets, runtime configuration and a checksummed manifest. The package carries neither a game executable nor a complete installation.

**Create Disposable Copy** copies the stock game without saves or replays and installs the package there. **Install into a Game Copy** requests a separate folder and confirmation. Both check for running Etherlords II processes, validate the executable and stock hashes, refuse occupied generated file paths, and verify backups before replacing anything. Native changes are applied only to the launched test process.

Close the game, then choose **Roll Back a Game Copy**. The app restores the original registry and text archives, removes the generated portrait overlay and presets, and verifies the restored checksums. If a target file changed outside the app, rollback reports the file and retains the backups. Manually inspect the verified copies under `.card-creator-backup` before deciding how to reconcile a changed file. User-created presets, replays and saves stay in the copy. A preset containing custom IDs needs its matching project installed and launched.

See [TESTING.md](TESTING.md) for recorded results and compatibility limits.

## Screenshots

[Card Library](screenshots/creator-library.jpg) · [Creature Editor and contextual help](screenshots/creator-editor.jpg)
