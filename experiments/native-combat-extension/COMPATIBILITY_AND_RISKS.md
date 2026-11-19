# Compatibility and risks

- The probes target one x86 Windows executable SHA-256, loaded at preferred base `0x400000`, with specific archive pairs. A matching version label alone is insufficient. Windows runs the child under the established `WIN2000` compatibility setting. The runner requires 64-bit Python and Windows WOW64 debugger APIs.
- The runner starts a marked test copy and writes only its new process memory. Breakpoints on gameplay sites are one-shot and removed when hit. Trampolines are written to new process pages that change from writable to executable. Unexpected original bytes, image base, hashes or observed registry ownership abort the test.
- Shutdown normally destroys one producer per key. Each added producer must come from the engine allocator and have its own lifetime. A pointer alias shared by multiple owned entries is unsafe. The probe uses a second instance of the same implementation and leaves it owned by the registry.
- Mixing profiles is intentionally unavailable. A single executable site or vtable slot can affect multiple execution paths. Donor redirection can change target descriptors, AI behavior, effect placement and native cost rules. The displayed card metadata should be brought into agreement before a release.
- Runtime changes expire on process exit. An in-session unload could leave active spells and ability instances with stale assumptions. Restart the process instead. Use test-only saves and keep them paired with the profile that produced them.
- Save/load, replay compatibility, broader card interactions, modified controller relationships and multiplayer are outside the verified release envelope. Normal exit of a few Duels does not establish long-session memory safety.

The gameplay findings justify more development on this pinned build. A public Etherlords III release needs reproducible compatibility checks, a narrower startup hook with diagnostics, matched UI data, and repeatable regression tests. The debugger launcher is a research tool for local Duels.

## Original gameplay bytes

| Profile | Virtual address | Original bytes | Replacement |
|---|---|---|---|
| `alias` | `0x744d80` | `8b 4c 24 30 89 38` | Relative jump and one NOP. The trampoline performs the displaced operations. |
| `alias-flat` | `0x6cccb1`, `0x6cccd7` | `8b 57 14 39 6a 20 7d 07`, `55 50 e8 d2 75 08 00` | Two jumps to surcharge gates. Only the E3TC path changes. This profile also installs the alias registry trampoline. |
| `zap-three` | `0x6f229f`, `0x6f22ed` | `6a 01` at each site | `6a 03` at each site. |
| `zap-mass` | `0x8c1d78` | `30 9a 74 00` | `90 8f 74 00`. |
| `zap-chain` | `0x8bff30` | `60 21 6f 00` | The address of the new per-process wrapper. |
| `rat-brotherhood` | `0x8c2c24` | `b0 80 73 00` | `80 04 6f 00`. |

The runner additionally lists any one-shot trace sites and their original first byte in its source. Their breakpoint bytes are restored on hit. Process exit discards all runtime changes.
