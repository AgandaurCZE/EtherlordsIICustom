#!/usr/bin/env python3
"""Generate Etherlords II Lua 4 .scp from a save/load-safe encounter registry."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
ENCOUNTERS = ROOT / "src/encounters"
MODULES = ([ROOT / "src/shared/encounter_registry.lua"]
           + sorted(ENCOUNTERS.glob("*.lua"))
           + [ROOT / "src/shared/save_load_diagnostics.lua",
              ROOT / "src/shared/hook_router.lua"])
OUT = ROOT / "build/TestMap.scp"

def main():
    chunks = []
    functions = {}
    registrations = []
    for path in MODULES:
        source = path.read_text(encoding="utf-8")
        for match in re.finditer(r"^function\s+([A-Za-z_][A-Za-z_0-9]*)\s*\(", source, re.M):
            name = match.group(1)
            if name in functions:
                sys.exit("Duplicate Lua function: " + name)
            functions[name] = path
        # Keep the project's Lua 4 constraints: no local captures.
        if re.search(r"\blocal\b", re.sub(r"--[^\n]*", "", source)):
            sys.exit("Unexpected 'local' in " + str(path))
        if path.parent == ENCOUNTERS:
            reg = re.findall(r'^EncounterRegistry_Register\("([A-Za-z_][A-Za-z_0-9]*)"', source, re.M)
            if len(reg) != 1:
                sys.exit("Expected one registration in " + str(path))
            registrations += reg
            # No Lua function objects can be registered: use callback names as strings.
            registration = source[source.rfind("EncounterRegistry_Register("):]
            if re.search(r'\b[A-Za-z_][A-Za-z_0-9]*_On(?:Step|CloseMessageBox|BattleFinishing|PreUse)\b(?!")', registration):
                sys.exit("Possible non-string callback in " + str(path))
        chunks.append("-- BEGIN " + str(path.relative_to(ROOT)) + "\n"
                      + source.rstrip() + "\n-- END")

    hooks = {name for name in functions if name.startswith("Hook_")}
    required = {"Hook_OnStep", "Hook_OnCloseMessageBox", "Hook_OnBattleFinishing",
                "Hook_OnPreUse", "Hook_OnIntercept"}
    if hooks != required:
        sys.exit("Incorrect engine hooks: " + repr(hooks))
    if len(registrations) != len(set(registrations)):
        sys.exit("Duplicate encounter registration name")
    if not registrations:
        sys.exit("No encounters registered")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("-- GENERATED: Lesson 25, registry + 3 encounters (Lua 4)\n\n"
                   + "\n\n".join(chunks) + "\n", encoding="utf-8")
    print("Generated", OUT, "with", len(registrations),
          "encounters and", len(functions), "functions")

if __name__ == "__main__":
    main()
