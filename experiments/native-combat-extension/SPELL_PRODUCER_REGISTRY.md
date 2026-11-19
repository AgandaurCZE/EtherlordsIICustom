# Spell producer initialization and E3TC

## Registration and ownership

The earlier static scan counted 343 direct calls to `0x746580`. Those calls all sit in initializer `0x73e2a0`. The same initializer has another 20 inlined insertion paths, identifiable by calls to `0x7465e0` before the first direct registration. The first two inline keys are `WLIL` and `BRAB`, loaded as four bytes from `0x99c098` and `0x99db74`. The runtime guard sees 363 stock entries after the final stock assignment. The debugger then sees 364 with E3TC inserted.

The map at `0x9cd998` holds a sentinel and a count. `0x4d6ab0` searches an unsigned four-byte key in the tree rooted at sentinel +4. Each node has left/right pointers at +8/+12, key at +16, and producer value at +20. `0x746580` takes the map in ECX and a pointer to the key on the stack, inserts if absent, and returns the address of the value slot. The insertion path allocates tree nodes internally. It is a dynamic structure even though the stock calls run at initialization.

At shutdown the destructor `0x746410` walks entries and invokes each non-null object's deleting destructor at vtable slot 0. For GRUN, `0x7463c0` calls the game deallocator when invoked with flag 1. Storing the same producer pointer under two keys would create duplicate ownership and risk a double free. Two independently allocated four-byte objects can instead share vtable `0x8c22b4`, with the same factory implementation at `0x74be40`.

## Probe

After the last stock insertion in the initializer, the trampoline at `0x744d80` completes the original final assignment, requires a 363-entry map, allocates four bytes with engine operator new `0x82b410`, calls GRUN's producer constructor `0x745ca0`, and asks the original map to insert the new key `E3TC`. The game owns the object from that point. The probe never writes GRUN's own producer slot.

The startup breakpoint immediately after initializer return reads both keys. The first successful run found `E3TC=0x2f4f7d8`, `GRUN=0x2f4c838`, 364 entries and the same expected vtable. These heap addresses are specific to that run.

The common factory writes the requested ID at object +4 at `0x74655f` after native creation. The debit-site trace directly read `E3TC` from the native spell object inside GRUN's cast path. An additional card kept its own runtime identity while taking the donor's native behavior. The tester observed the donor's return-to-hand effect and Kinets-style visuals after casting with creatures present on both sides.

The resource pair defines a Chaots card with base cost 1. GRUN's original behavior also assigns a surcharge of one Ether per eligible creature via `0x6cccd9`, so a crowded battlefield can require more than one Ether. The first traced cast had zero eligible targets. The field report of a populated-board cast verifies effect and animation, with the exact debit treated separately in the results. The experimental old description says enemy-only, while the probe intentionally retains the donor's behavior on both sides.

A separate `alias-flat` profile checks the runtime spell ID at the surcharge affordability and debit sites. It skips the extra check only for `E3TC` and substitutes zero for its extra debit while preserving the actual eligible-creature count and the return effect. Original `GRUN` takes the displaced affordability branch and pays the original count. The base cost still comes from the card record. See [results](EXPERIMENT_RESULTS.md) for the populated-board test.

This establishes hand and cast compatibility for the tested Duel route. Save/load and long-running allocation behavior require separate validation.
