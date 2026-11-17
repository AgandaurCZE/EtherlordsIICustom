#!/usr/bin/env python3
"""Build Lesson 23 passive save/load diagnostic script for Etherlords II Lua 4."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
MODULES = [
    ROOT / "src/encounters/bee_queen.lua",
    ROOT / "src/encounters/grumble.lua",
    ROOT / "src/shared/save_load_diagnostics.lua",
    ROOT / "src/shared/hook_router.lua",
]
OUT = ROOT / "build/TestMap.scp"

def main():
    functions = {}
    chunks = []
    for path in MODULES:
        s = path.read_text(encoding="utf-8")
        for match in re.finditer(r"^function\s+([A-Za-z_][A-Za-z_0-9]*)\s*\(", s, re.M):
            name = match.group(1)
            if name in functions:
                sys.exit("ERROR: duplicate function: " + name)
            functions[name] = str(path)
        if re.search(r"\blocal\b", re.sub(r"--[^\n]*", "", s)):
            sys.exit("ERROR: unexpected local variable in " + str(path))
        chunks.append("-- BEGIN " + str(path.relative_to(ROOT)) + "\n" +
                      s.rstrip() + "\n-- END")
    hooks = {x for x in functions if x.startswith("Hook_")}
    expected = {"Hook_OnStep", "Hook_OnCloseMessageBox",
                "Hook_OnBattleFinishing", "Hook_OnPreUse", "Hook_OnIntercept"}
    if hooks != expected:
        sys.exit("ERROR: invalid hook list " + repr(hooks))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        "-- GENERATED Lesson 23 diagnostic build; edit individual source modules.\n\n"
        + "\n\n".join(chunks) + "\n", encoding="utf-8")
    print("Generated", OUT, "-", len(functions), "functions")

if __name__ == "__main__":
    main()
