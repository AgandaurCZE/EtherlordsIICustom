#!/usr/bin/env python3
"""Build Lesson 29: four encounters, independent honey/spore quests, native journals."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
ENCOUNTERS = ROOT / "src/encounters"
QUESTS = ROOT / "src/quests"
JOURNAL = ROOT / "src/journal"
MODULES = ([ROOT / "src/shared/encounter_registry.lua"]
           + sorted(ENCOUNTERS.glob("*.lua"))
           + sorted(QUESTS.glob("*.lua"))
           + sorted(JOURNAL.glob("*.lua"))
           + [ROOT / "src/shared/save_load_diagnostics.lua",
              ROOT / "src/shared/hook_router.lua"])
OUTPUT = ROOT / "build/TestMap.scp"

def main():
    functions = {}
    chunks = []
    registrations = []
    for path in MODULES:
        source = path.read_text(encoding="utf-8")
        for m in re.finditer(r"^function\s+([A-Za-z_]\w*)\s*\(", source, re.M):
            name = m.group(1)
            if name in functions:
                sys.exit("Duplicate function: " + name)
            functions[name] = str(path)
        # Lua 4 requires return to terminate its enclosing block. Catch the
        # regression that previously prevented the mission from even loading:
        # a command statement immediately after a return at the same indent.
        for match in re.finditer(
            r"(?m)^(?P<indent>[ \t]*)return\b[^\n]*\n"
            r"(?:(?P=indent)[ \t]*--[^\n]*\n)*"
            r"(?P=indent)(?:Ex[A-Za-z_][A-Za-z_0-9]*\s*\(|return\b)",
            source
        ):
            sys.exit("Unreachable statement after return in " + str(path))
        if re.search(r"\blocal\b", re.sub(r"--[^\n]*", "", source)):
            sys.exit("Unexpected local keyword in " + str(path))
        if path.parent == ENCOUNTERS:
            found = re.findall(r'^EncounterRegistry_Register\("([A-Za-z_]\w*)"', source, re.M)
            if len(found) != 1:
                sys.exit("Exactly one registration required: " + str(path))
            registrations.extend(found)
            registration = source[source.rfind("EncounterRegistry_Register("):]
            if re.search(r'\b[A-Za-z_]\w*_On(?:Step|CloseMessageBox|BattleFinishing|PreUse)\b(?!")', registration):
                sys.exit("Function references are unsafe across saves: " + str(path))
        chunks.append("-- BEGIN " + str(path.relative_to(ROOT)) + "\n"
                      + source.rstrip() + "\n-- END")

    hooks = {name for name in functions if name.startswith("Hook_")}
    required = {"Hook_OnStep", "Hook_OnCloseMessageBox",
                "Hook_OnBattleFinishing", "Hook_OnPreUse", "Hook_OnIntercept"}
    if hooks != required:
        sys.exit("Unexpected Hook_* set: " + repr(hooks))
    if len(registrations) != 4 or len(set(registrations)) != 4:
        sys.exit("Expected four uniquely registered encounters")
    if not {"HoneyQuest_OnStep", "HoneyQuest_BeeInteraction",
            "HoneyQuest_Reward"}.issubset(functions):
        sys.exit("Honey quest functions not found")
    if not {"HoneyJournal_Stage1", "HoneyJournal_Stage2", "HoneyJournal_StageRecovered", "HoneyJournal_Stage3", "SporeJournal_Accepted", "SporeJournal_Recovered", "SporeJournal_Completed", "SporeJournal_Failed", "SporeQuest_OnStep"}.issubset(functions):
        sys.exit("Quest or journal callbacks missing")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("-- GENERATED: Lesson 29 Dual Quests (Lua 4).\n"
                      "-- Four encounters, two independent quests, native notebook.\n\n"
                      + "\n\n".join(chunks) + "\n", encoding="utf-8")
    print("Generated", OUTPUT, len(functions), "functions")

if __name__ == "__main__":
    main()
