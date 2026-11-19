# Controlled Duel crash analysis

Both decks containing `E3TC` failed in the same native hand-creation routine. The stock decks reached the battlefield and drew hands with both sets of archives. This isolates the trigger to creating the new spell ID rather than opening Duel or loading the modified archives.

## Matrix

Tests ran on 19 November 2026 in two disposable Windows 1.03 copies under the same debugger, with one round and the default random arena. The tested executable SHA-256 was `d3ed30f840b3325b1f03c01aa486e7f44328a7d6993964c409950a65e86a158b`. The observer reported image base `0x400000` in all five runs. The archive hashes are recorded in [TEST_RESULTS.md](TEST_RESULTS.md).

| Case | Archives and Duel presets | Last verified stage | Process result |
| --- | --- | --- | --- |
| 01 | Baseline archives. Chaot Beginner Deck vs. Kinet Beginner Deck, resource level 1. | Battlefield with both opening hands and Attack/Cast Phase. | Tester closed with Alt+F4. Exit `0x00000000`. |
| 02 | Probe archives. Same stock decks and resource level. | Battlefield with both opening hands and Attack/Cast Phase. | Tester closed the game. Exit `0x00000000`. |
| 03 | Probe archives. Red fixture with **one** `E3TC` vs. Kinet Beginner Deck, resource level 3. | Preset selected and full Duel start requested. The next visible battlefield or card was never confirmed. The debugger reached the command that creates the hand entry. | Read access violation at `0x746554`, then exit `0x0000dead`. |
| 04 | Probe archives. Matching Red fixture with **three** `E3TC` vs. Kinet Beginner Deck, resource level 3. | Tester last saw the Duel setup screen and clicked Start. The same hand-creation command faulted. | Read access violation at `0x746554`, then exit `0x0000dead`. |
| 05 | Probe archives. Blue fixture with three original `GRUN` vs. Chaot Beginner Deck, resource level 3. | Battlefield and original Greater Unsummoning tooltip with base cost 2. Two copies were visible in hand. Tester confirmed a successful cast. | No access violation recorded. Tester closed the game. Exit `0x00000000`. |

The Red fixtures each contain 16 cards. Case 03 fills the two extra experimental slots with the already-present stock `FRWA`, leaving the other 14 slots identical to case 04. Case 05 uses a Kinets deck with 13 registered stock cards and three copies of the untouched Kinets donor. The control faction follows the donor's original card data. The random arenas and draw orders were allowed to vary, so the matrix establishes the failure path rather than a deterministic card order.

## Exception evidence

The following is the relevant, sanitized data from the two local JSONL logs. Times are Prague time.

| Case | Exception time | SEH exception and address | Fault parameters | Registers and stack | Exit |
| --- | --- | --- | --- | --- | --- |
| 03 | 03:18:26.592 | First-chance `0xc0000005` at `0x00746554` (RVA `0x346554`) | Read (`0`) of address `0x0` | `EAX=0`, `ESI=0x009cd998`, spell argument `E3TC` | `0x0000dead`, about 49 ms later |
| 04 | 03:19:10.048 | First-chance `0xc0000005` at `0x00746554` | Read (`0`) of address `0x0` | Same relevant registers and `E3TC` argument | `0x0000dead`, about 48 ms later |

Both stacks contained the two checked return addresses below. These are identified frames from the pinned calling sequence, with no claim of a full symbolized stack.

1. `0x007541ef` returns from calling the `AddSpellToHand` routine at `0x7541ea`.
2. `0x007332e2` returns from that routine's factory call at `0x7332dd`.
3. `0x00746554` is `mov edx, [eax]`, the first dereference of the missing producer. The factory argument at fault-time `[esp+0x18]` was the little-endian four-byte `E3TC` value `0x43543345`. The loaded producer pointer was zero.

The fault happens while constructing the combat spell for the hand, before successful display or casting. The evidence cannot establish whether the arena had already loaded internally. It does establish why these two processes closed. The debugger passed the access violation back to Windows. Neither run emitted a second-chance access violation, and both ended with the application's nonzero exit code. The executable contains an exception recovery path returning `0xDEAD` at `0x4a2860`. A failure handled before a second-chance event can therefore look like a silent close. The controls also emitted handled first-chance notifications during startup or rendering, which is why an exception alone was insufficient without the fault type, call site and exit. [Microsoft's debugger exception-handling documentation](https://learn.microsoft.com/en-us/windows/win32/debug/debugger-exception-handling)

The previous observation from commit `81d7084` lacked a debugger trace. This matrix reproduces the same user-visible symptom and identifies the failure in these runs. It cannot retroactively identify the instruction in that earlier session.

## Reproduction tools

[prepare_duel_matrix.py](prepare_duel_matrix.py) verifies the exact baseline and probe archives, makes two disposable copies, and generates the three named presets. [observe_duel.py](observe_duel.py) collects Windows debug events, the x86 register context and a short stack excerpt only on a fault. It passes game exceptions through and sets no breakpoints, writes no target memory, and leaves the executable unchanged. Logs and copied game files remain local. See [INSTALL.md](INSTALL.md) for the matrix commands.
