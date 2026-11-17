#!/usr/bin/env python3
"""Generate a single Lua 4 TestMap.scp with a self-registering encounter registry."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
ENCOUTERS_DIR = ROOT / "src/encounters"
MODULES = ([ROOT / "src/shared/encounter_registry.lua"]
           + sorted(ENCOUTERS_DIR.glob("*.lua"))
           + [ROOT / "src/shared/save_load_diagnostics.lua",
              ROOT / "src/shared/hook_router.lua"])
OUT = ROOT / "build/TestMap.scp"

def main():
    chunks = []
    functions = {}
    for path in MODULES:
        content = path.read_text(encoding="utf-8")
        for match in re.finditer(r"^function\s+([A-Za-z_][A-Za-z_0-9]*)\s*\(", content, re.M):
            name = match.group(1)
            if name in functions:
                sys.exit("Duplicate function: " + name)
            functions[name] = path
        # Lua 4 supports local variables, but existing project policy avoids
        # local upvalue capture in nested functions.
        if re.search(r"\blocal\b", re.sub(r"--[^\n]*", "", content)):
            sys.exit("Unexpected Lua local keyword: " + str(path))
        chunks.append("-- BEGIN " + str(path.relative_to(ROOT)) + "\n"
                      + content.rstrip() + "\n-- END")

    hooks = {x for x in functions if x.startswith("Hook_")}
    expected_hooks = {"Hook_OnStep", "Hook_OnPreUse", "Hook_OnIntercept",
                      "Hook_OnCloseMessageBox", "Hook_OnBattleFinishing"}
    if hooks != expected_hooks:
        sys.exit("Unexpected engine hooks: " + repr(hooks))

    encounter_paths = sorted(ENCOUTERS_DIR.glob("*.lua"))
    if not encounter_paths:
        sys.exit("No encounter modules found")
    for path in encounter_paths:
        content = path.read_text(encoding="utf-8")
        if "EncounterRegistry_Register(" not in content:
            sys.exit("Encounter does not self-register: " + str(path))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("-- GENERATED: Lesson 24 registry test (Lua 4)\n\n"
                   + "\n\n".join(chunks) + "\n", encoding="utf-8")
    print("Generated", OUT, "with", len(functions),
          "functions and", len(encounter_paths), "encounters")

if __name__ == "__main__":
    main()
