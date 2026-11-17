#!/usr/bin/env python3
"""Deterministic assembler for Lesson 22 (original Lua 4 target)."""
from pathlib import Path
import re
import sys
ROOT = Path(__file__).resolve().parent
MODULES = [ROOT / "src/encounters/bee_queen.lua",
           ROOT / "src/encounters/grumble.lua",
           ROOT / "src/shared/hook_router.lua"]
OUT = ROOT / "build/TestMap.scp"

def main():
    chunks = []
    functions = {}
    for path in MODULES:
        source = path.read_text(encoding="utf-8")
        for match in re.finditer(r"^function\s+([A-Za-z_][A-Za-z_0-9]*)\s*\(", source, re.M):
            name = match.group(1)
            if name in functions:
                sys.exit("ERROR duplicate function " + name)
            functions[name] = path
        if re.search(r"\blocal\b", re.sub(r"--[^\n]*", "", source)):
            sys.exit("Unexpected local variable in " + str(path))
        chunks.append("-- ===== BEGIN " + str(path.relative_to(ROOT)) + " =====\n" +
                      source.rstrip() + "\n-- ===== END =====")
    required = {"Hook_OnStep", "Hook_OnPreUse", "Hook_OnCloseMessageBox",
                "Hook_OnBattleFinishing", "Hook_OnIntercept"}
    hooks = {name for name in functions if name.startswith("Hook_")}
    if hooks != required:
        sys.exit("Unexpected hooks " + repr(sorted(hooks)))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("-- GENERATED LESSON 22 (Lua 4); edit modules, not generated file.\n\n"
                   + "\n\n".join(chunks) + "\n", encoding="utf-8")
    print("Generated", OUT, "with", len(functions), "functions")

if __name__ == "__main__":
    main()
