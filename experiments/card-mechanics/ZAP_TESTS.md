# Chaots Zap tests

## B1. Identification

Zap is `ZAPP`, a Chaots sorcery costing 1 Ether with icon 453. `CombatSpells.reg` links its Encyclopedia metadata to name `ZAPPNm` and description `ZAPPTt` in `ELKTexts.txt`. The stock description specifies one damage to a selected creature or hero. The row has no damage amount, target selector or effect list.

On the pinned executable, the producer is registered near `0x740e09`. Its factory at `0x749a30` calls the constructor at `0x6f20e0`, setting target category 4 and vtable `0x8bff2c`. The cast routine starts at `0x6f2160` and branches on the selected target at `0x6f228f`. The hero path passes the literal 1 at `0x6f229f` to `0x751b00`. The creature path passes another literal 1 at `0x6f22ed` to `0x752b30`. Both paths use the `RedZap` visual dispatch, backed by `Resources/Effects.xml` and its matching particle and sound assets.

## B2. Damage probe

The controlled variant copies stock `text.res` and changes only `ZAPPTt` to a tooltip labeled **UI-only test: 3 damage to target creature or hero**. This distinguishes the loaded localization from the native cast. The appropriate measurement is current health immediately before and after the hit in the same turn. See [combat results](COMBAT_RESULTS.md) for observations.

## B3. All creatures

The conditional Zap mass-damage test requires successful damage modification first. The inspected Zap path resolves a single selected hero or creature and has no per-cast iteration over creatures or resource-driven targeting selector. Stock Chaots Lightning Storm (`LGST`, 2 Ether) is the closest existing mass-damage effect. Its stock tooltip specifies three damage to all creatures, and its separately registered native path passes 3 to the creature damage routine at `0x6f4c2d` inside a loop. Stock Tremor (`TREM`, 2 Ether) specifies two damage to enemy creatures. Neither card was altered.

## B4. Damage then Unsummon

Unsummon is stock Kinets `UNSM`, a 1-Ether sorcery whose description returns a target creature from play to its controller’s hand. Its independent producer is registered near `0x742cd2`; the constructor is at `0x6cc930` and the cast routine at `0x6cc9c0`. Zap’s inspected cast applies damage and queues its visuals, with no resource-configured second effect or conditional delegation to that producer.

The documented encounter hook `CHook_OnVisualPostSpellCast` receives the spell code and parameters after a successful cast and its triggers. A scenario could investigate recognizing a non-scripted Zap, tracking eligible enemy survivors, and queuing a separate registered `UNSM` via `ExCastSpellWithEffects`. Survival, ownership, timing, legal targets and scripted cost would need dedicated tests. The documented hook is post-resolution, so this route does not provide an extension to Zap’s own resolution. No combined cast is included.
