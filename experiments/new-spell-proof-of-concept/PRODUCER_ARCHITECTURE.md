# Native spell registration and resolution

**C. Fundamentally blocked within the permitted modification methods.** The existing additive UI and deck entry works. The tested 1.03 build lacks a verified interface for binding that distinct ID to a native combat producer. The controlled Duel runs confirm that the missing binding is reached and faults. See [CRASH_ANALYSIS.md](CRASH_ANALYSIS.md).

All addresses below apply to the executable SHA-256 and observed image base recorded there. The analysis used only on-disk inspection and read-only debugger observations.

## Two independent registries

| Stage | Registry and behavior |
| --- | --- |
| Metadata | At `0x7392e7`, the loader reads `CombatSpells.reg`. The registry at `0x9cd910` supports metadata lookup and ID checks. The metadata is sufficient for the Encyclopedia and the saved Duel preset. All 377 original sections were inspected. Their keys cover type, color, cost, localization, display, eligibility and creature ability data. None identifies an alternate spell producer. |
| Registration | A startup entry at `0x73e270`, referenced from the static initializer table at `0x97b64c`, calls initializer `0x73e2a0` on the producer map at `0x9cd998`. Its only identified direct caller is the startup entry. All 343 direct calls to producer-map insertion `0x746580` are in the initializer's literal-ID block, from `0x73ed96` through `0x744d7b`. Each registered key comes from a literal read by `0x5246f0`, which simply loads the first four bytes of the string. |
| Draw and hand creation | The caller at `0x7541ea` prepares the add-to-hand log record. Its `AddSpellToHand` path at `0x7332d0` takes the record's exact ID and calls `0x746500` at `0x7332dd`. A return-to-hand variant at `0x733410` makes the same factory call. The live faults used the ordinary add-to-hand route. |
| Instantiation | At `0x74650b` the factory searches using the passed key. The missing branch initializes a map value with a zero producer. At `0x746551` it loads the value and at `0x746554` reads the producer vtable. With a valid entry it invokes the virtual factory at `0x746558`, then writes the original requested ID to the instance at `0x74655f`. Both faulting calls used the unchanged key `E3TC`. |
| Donor | The initialization call at `0x742d19` binds `GRUN` to its own producer, built by `0x745ca0`. The producer's factory at `0x74be40` creates the native Greater Unsummoning object. Its existing behavior and animation are documented in [SPELL_DEFINITION.md](SPELL_DEFINITION.md). Case 05 verified it can enter the hand and cast with the probe archives loaded. |

## Where an alias could be supported

- **A second key is structurally possible.** The map is keyed by a four-byte ID and stores a producer pointer. The factory writes the requested ID to a freshly constructed object. That structure could in principle represent multiple IDs backed by the same implementation, but the 343 observed registrations each had a distinct producer-constructor call target. This does not establish that a shared producer object would have safe lifetime semantics or that the donor would behave identically under another ID.
- **Resource paths checked.** The metadata record, the stock combat decks, and the loose Duel preset format carry IDs or fields about them. The tested `E3TC` key survived these stages and reached the factory unmodified. No ID translation or alias in that pipeline was found. The metadata alone leaves the draw path with a missing producer.
- **Lua validation is separate.** The combat `ExAddSpellToHand` wrapper at `0x7f9410` reaches `0x7dc6d0`. At `0x7dc71b` it checks metadata membership via `0x73b770` on `0x9cd910`. An adventure wrapper follows a similar metadata check at `0x7e933a`. These checks establish that the ID is a known card record. They do not install a producer or prevent the native hand factory from seeing an unregistered record. No Lua binding to the producer insertion path was found.
- **Native interfaces checked.** The executable's ten named exports expose no spell-registration entry point. The three identified `LoadLibraryA` / `GetProcAddress` paths resolve `GetGraphicsProcessor` or `GetTLPipeline`. They are renderer interfaces. No supported spell plugin route was found in the executable interfaces or shipped game resources inspected. This is a bounded finding for this build and its normal data/script paths.

Changing metadata to resemble `GRUN` more closely, or adding the card with Lua, leaves the producer key unchanged. Reusing the actual `GRUN` ID would execute the original spell and would give up the distinct ID. Keep the Encyclopedia probe isolated and shift campaign development toward custom encounters and compositions of existing spell IDs. Reopen native card registration only if a supported interface for inserting a new producer binding becomes available.

Run `native_producers.py <Etherlords2.exe> GRUN UNSM LSUS E3TC --constructors` to reproduce the registration locations and constructor count from the pinned file.
