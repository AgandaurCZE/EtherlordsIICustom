# Reproduce and roll back

Use Windows and 64-bit Python 3.11 or newer with a stock copy of the same English Etherlords II 1.03 build used by the [native combat extension](../native-combat-extension/COMPATIBILITY_AND_RISKS.md). The build checks the executable and original archives before copying the game. The new copy omits existing saves and replays.

```powershell
python testing_rat.py prepare E:\EtherlordsII-Baseline test-rat-01
python testing_rat.py run local/test-rat-01 local/test-rat-01.jsonl
```

1. Check **Encyclopedia → Chaots → Creatures** for TESTING Rat. Verify the cost, 5/5 stats and description, then check Stink Rat and Kobold Shaman still appear separately.
2. Start **Single → Duel** with the **Testing Rat - E3RT** preset at resource level 3 against a stock Kinets deck. The fixture contains four new cards and four original Stink Rats for comparison. Confirm the name, 1-Ether cost and artwork in hand and summon each separately.
3. Observe the Mantis idle, attack, hit and death animations. Note whether the new creature survives returning to hand and summoning again.
4. Once the creature can act, select its Zap ability and use it on a hero and a creature. Record health immediately before and after and check that the user must rest.
5. Save and reopen a disposable Duel preset to check the ID round trip. If the Duel completes, save its replay and open it again with the same profile. Record campaign save/load separately. Live combat saves are unavailable through the normal combat menu.

The optional **Testing Rat - Lifecycle** deck adds stock Lightning Storm and Doom Rat. Two Lightning Storms in one turn apply 6 damage to all creatures. Keep the 4/5 Doom Rat in hand until after that test, then summon it and, once ready, use Brotherhood with 2 Ether to try returning E3RT from the graveyard. A stock Kinets opponent can separately test direct battlefield removal and return to hand.

Logs and generated files stay under ignored `local/`. Exiting discards the native change. To restore the disposable copy to stock after it exits, copy `Resources/regs.res` and `Resources/text.res` from the original baseline and compare their hashes with the [results](TEST_RESULTS.md). Verify the SHA-256 of `Resources/textures001.res` against the generated overlay hash in the results, then remove that added overlay from the disposable copy. The stock baseline leaves this archive slot empty. Keep the experimental Duel presets and logs under `local/`. Launch this card only through the profile while the additive archives are present.
