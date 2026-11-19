# Test results

Tested on the English Windows build showing **Version 1.03**, using separate disposable game copies. The executable matched the pinned source SHA-256.

| Test | Result |
| --- | --- |
| Archive additions | Passed. `CombatSpells.reg` grew from 377 to 378, Red entries from 66 to 67. The only new spell ID is `E3TC`. All original sections and all unchanged RES members compare byte for byte. |
| Localization | Passed. Original `ELKTexts.txt` bytes are an exact prefix of the staged member. Two unique text records were appended. The builder rejects duplicate stock IDs. |
| Startup | Passed. The test copy launched using its own working directory and the existing `WIN2000` compatibility setting. The reported failure of the separate shared game folder was not diagnosed. |
| Encyclopedia | Passed for the Chaots Sorcery table. Name, cost 1, icon 674 artwork and requested description rendered beside stock rows. The table was stable during inspection. A separate click-through panel was not verified. |
| Duel editor | Passed. The red preset editor displayed the reused art in Available Spells and in the active deck. |
| Duel preset save | Passed at file level. The game wrote `Duel/test1.prs` with `magic="Red"` and three `E3TC` cards. The committed test fixture uses the same card counts and leaves the other decks alone. |
| Duel combat | Blocked and reproduced. One-copy and three-copy decks both reached `AddSpellToHand` and faulted instantiating `E3TC`. Windows reported a null read at `0x746554` and the game exited with `0xdead`. |
| Stock deck controls | Passed. The same beginner decks reached visible hands with both archive sets, and both processes exited zero after manual close. |
| Original `GRUN` | Passed draw and cast under the probe archives. Two copies and the cost-2 tooltip were observed in hand. The tester confirmed a successful cast. The process exited zero after manual close. The post-cast visual effect and full Duel completion were not independently recorded. |
| E3TC cast, one-Ether debit, animation, enemy removal, combat completion | Blocked at hand creation. No successful display of `E3TC` in combat or cast was observed. |
| Combat save/load | Unverified. The experiment did not reach a verified combat state containing a playable copy of the spell. Saving a custom deck is a separate check. |

## SHA-256

| File | Source | Additive probe |
| --- | --- | --- |
| `regs.res` | `e38ed76d8fcde2aeee1e22a89771e9eb05d95f3364e122a3024db929975970d7` | `26592e61ae3b78b372deadd15546af63cf743ae41eb7168567c233cee3ed69e3` |
| `text.res` | `0360ed75214fc2565fef1e3bb67b096323d6a9d5a4e17a87a72b38b7d6f9af6b` | `ff90849e81172c47505b7be90e5f5aa31f390bf713d7196296b66ebcce8f185f` |

The probe changed four registry members and one text member. It left all textures, campaign data, stock decks, specializations and the executable alone. A repeat build reproduced both hashes. After testing, both archives in the disposable copy were restored and verified against the source hashes, and the probe preset was archived with the local outputs.

The later five-case matrix used two additional disposable copies, with the exact archive pair verified for each. The current preparer made another isolated pair and reproduced all three Duel fixture hashes byte for byte. See [CRASH_ANALYSIS.md](CRASH_ANALYSIS.md) for the exception chronology and [PRODUCER_ARCHITECTURE.md](PRODUCER_ARCHITECTURE.md) for the conclusion.
