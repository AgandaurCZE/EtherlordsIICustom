#!/usr/bin/env python3
"""Generate a single Lua 4 .scp from independent encounter modules."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
MODULES = [
    ROOT / "src/encounters/bee_queen.lua",
    ROOT / "src/encounters/grumble.lua",
    ROOT / "src/shared/hook_router.lua",
]
OUT = ROOT / "build/TestMap.scp"

def main():
    chunks = []
    functions = {}
    for path in MODULES:
        source = path.read_text(encoding="utf-8")
        for name in re.findall(r"^function\s+([A-Za-z_][A-Za-z_0-9]*)\s*\(", source, re.M):
            if name in functions:
                sys.exit("Duplicate Lua function: " + name)
            functions[name] = str(path)
        if re.search(r"\blocal\b", re.sub(r"--[^\n]*", "", source)):
            sys.exit("Unexpected Lua local (outer capture hazard) in " + str(path))
        chunks.append("-- ===== BEGIN " + str(path.relative_to(ROOT)) + " =====\n"
                      + source.rstrip() + "\n-- ===== END =====")

    expected_hooks = {"Hook_OnStep", "Hook_OnCloseMessageBox",
                      "Hook_OnBattleFinishing", "Hook_OnPreUse"}
    actual_hooks = {name for name in functions if name.startswith("Hook_")}
    if actual_hooks != expected_hooks:
        sys.exit("Unexpected engine hooks: " + repr(actual_hooks))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        "-- GENERATED: Lesson 21, two encounters, Lua 4.0.\n"
        "-- Edit the source modules, not this file.\n\n"
        + "\n\n".join(chunks) + "\n",
        encoding="utf-8"
    )
    print("Wrote", OUT, "with", len(functions), "functions")

if __name__ == "__main__":
    main()
