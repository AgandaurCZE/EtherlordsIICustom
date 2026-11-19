# Etherlords II 1.03 additive spell experiment

**Partial success.** `E3TC` is a genuinely additional Chaots spell record. Etherlords II displayed it in the Encyclopedia and saved it in a new Duel deck. The first Duel attempt with the new card crashed before a successful draw or cast. Read-only inspection identified a separate native producer lookup that has no entry for `E3TC`.

## Database and native code

- `Resources/regs.res` member `CombatSpells.reg` holds display and deck-building metadata keyed by four-byte IDs. The source member is row 20 at `0x328d0`, 249,975 bytes. Fields include `Color`, `Class`, `Cost`, `OriginalCost`, `Icon`, `Name`, `ToolTip`, `Use`, `UseIn`, and resource prices. No effect selector, script binding, animation name, or target-side field was found in the tested records.
- The REG section and key directories use six-byte entries containing a signed 16-bit collision link and unsigned 32-bit offset. The bucket is the lowercase byte sum modulo count, with byte values sign-extended and the sum interpreted as unsigned 32-bit for the remainder. The builder verifies all source hash chains and rehashes the expanded section directories. Every original raw section remains byte-identical, including the original card metadata and localization records.
- `CombatDecks.reg` and `DuelPresets.reg` describe stock decks and their allowed resource level, faction, skills, and specialization. A custom Duel preset was saved as loose XML in `Duel/test1.prs` and referenced `E3TC` by code. The experiment leaves the stock decks, specialties, and scenario files alone.
- `scripts.res` contains compiled Lua, including adventure scripts, the adventure library and battlefield modifier assets such as `EtherStir.sobj`. The main executable contains script entry points for granting or removing a spell. The tested spell metadata has no field connecting a newly declared spell to a Lua implementation or to an existing producer. Granting an ID via script would still leave combat to resolve that ID through the native factory.

## Exact combat limitation

The addresses below are virtual addresses in the pinned executable with image base `0x400000` and SHA-256 `d3ed30f840b3325b1f03c01aa486e7f44328a7d6993964c409950a65e86a158b`. The executable was read only.

| Address | Evidence |
| --- | --- |
| `0x7392e7` | Metadata loader references `CombatSpells.reg` and enumerates its sections. |
| `0x73e270` | Native startup initializes a separate spell producer map at `0x9cd998`. |
| `0x742cb6`, `0x742cfd`, `0x74371d` vicinity | Native registration loads literal four-byte IDs for `UNSM`, `GRUN`, and `LSUS` and adds producer objects via `0x746580`. |
| `0x742d19` | `GRUN` registers a producer whose RTTI is `SpellProducer<BlueSpells::GreaterUnsummon>`. Its virtual factory at `0x74be40` constructs the native spell. |
| `0x746500` | Combat factory looks up the requested four-byte card ID in the producer map. The missing-key path constructs a node with a zero producer at `0x746532`. At `0x746551` the function loads that producer, then dereferences it at `0x746554` with no fallback. |
| `0x7332dd`, `0x73341d` | Combat paths pass the requested spell ID into the same factory. |

`native_producers.py` recovered 343 unique literal IDs at calls to the native registration routine. The three stock Kinets candidates are registered and `E3TC` is absent. This is a missing native producer binding, distinct from the number of rows the resource registry or Encyclopedia accepts. The read-only trace predicts a null dereference if combat tries to instantiate the new ID. No crash dump tied the observed Duel exit to a particular instruction.

The largest working data-only result is the additive Encyclopedia and deck-editor record. An independently castable `E3TC` would require a supported producer extension or another legitimate engine interface that can bind a distinct ID. No such hook was verified. The metadata file has no supported way to borrow `GRUN`'s producer or configure its target loop. Reusing the original `GRUN` spell as an unchanged stock control remains possible in an isolated Kinets Duel, but it is a different card with different mechanics.

The local result is consistent with the earlier community report that new IDs work in menus and decks and fail in combat. The binary REG format description provided an independent structural reference. [Original modder's report](https://www.gog.com/forum/etherlords_series/there_needs_to_be_a_modding_community/post17) · [Nival hashed REG format analysis](https://habr.com/ru/articles/434802/)
