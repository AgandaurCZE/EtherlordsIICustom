# Lesson 28 — Native Events List / Notebook Experiment

**Partially game-tested (2026-11-17):** User confirmed that custom quest popup text appears in the native Events List with hero portrait/day, and that normal dialogue and battles are also recorded. Further save/load verification is still needed. A follow-up experimental update adds Moss's missing fourth milestone and suppresses journal entries for repeatable greetings using `ExAddCommandText(..., 0)`. Lesson 27 is the proven fallback. This builds on Lesson 27 without modifying its folder or map.

## Goal
Find out whether the game's **Events List** is backed by the scripting API's documented **notebook**, and if event entries survive saving/loading.

The supplied original editor documentation, `Script functions.pdf`, says:
- `ExMessageBoxStandard(message, hero_id)` displays an OK message and adds a notebook entry when a hero is supplied.
- `ExMessageBoxDialogHero(hero_id, message, script_info, note)` supports an optional notebook flag, but `script_info` is obsolete.

We use **only** `ExMessageBoxStandard(message, ExGetMainHeroID())` for this first controlled experiment, because its notebook behavior is explicitly documented. It may create an extra OK popup; that is part of this experiment. No claim is made yet that this function populates the visible Events List in version 1.03.

## No Map Editor changes

Keep the existing 20x20 map (19x19 accessible) with:
- Hero P1; Bee **P2 (7,5)**; Grumble **P2 (15,10)**; Moss **P2 (10,16)**.
- Same towers, decks, and encounter models.

## What should happen

Copy `build/TestMap.scp` to the game's `Maps/Custom/TestMap.scp` next to `TestMap.smp`, and **start a fresh scenario**.

1. Apologize to Bee; collect her initial spell; click her again to start **The Queen's Missing Honey**. After the usual text, a new OK popup should say **The Queen's Missing Honey: Investigate Grumble**.
2. Open **Events List**. Check whether that entry appears, its day, its details panel, and if it survives closing/reopening the list.
3. Resolve Grumble via peace or combat. After the original clue dialogue, a second OK popup should say **A Suspicious Trade: Find Moss**.
4. Check **Events List** again. Are the first and second entries visible together? Is the mission filter affecting visibility?
5. Resolve Moss via peace or combat, return to Bee, turn in quest, and claim the bonus spell. After the completion sequence, a third OK popup should say **The Royal Honey Returned: Quest complete**.
6. After resolving Moss, a fourth milestone popup should appear: **Royal Honey Recovered: Return to the Queen**. Check the log for all four entries: initial quest, Grumble clue, Moss recovery, and completion.
7. Save and load after each stage where practical, checking whether notebook entries persist, duplicate, or disappear. The one-time quest reward and encounter states must remain intact.

## Implementation
- `src/journal/honey_journal.lua`: three callback-name functions, each with its own `ExSetVariable` one-time flag.
- `src/quests/missing_honey.lua`: queues `ExAddCommandExecuteScriptFunction("HoneyJournal_StageN")` immediately after existing milestone dialogue. No quest state transitions, proximity requirements, or battle hooks were changed.
- Everything else was copied from Lesson 27, including the tested one-use greeting suppression.

## Watch for these edge cases
- A journal popup appearing at the wrong time or **before** the previous dialogue.
- A blank Events List despite the popup.
- Events recorded but with unexpected or missing hero portraits/details.
- Notebook entries not surviving reload even though `HoneyJournalEntryN` is saved. Flags suppress repeated popups; they do not themselves recreate engine journal entries.
- Any Lua script error or new issue with the dialogue sequence. If one appears, restore Lesson 27 and report the exact error.

This experiment does not implement an editable active-objectives list; it first establishes whether the native event log can be written at all.

## Journal discovery and follow-up test

In-game screenshots confirm the game's Events List records all dialogue scripted with `ExAddCommandText(..., 1)`, plus combat summaries, and that `ExMessageBoxStandard(message, ExGetMainHeroID())` adds custom journal text with hero portrait and day. These are native event-log entries, not a separate active quest-objectives UI.

**New experimental adjustment:** repeatable peaceful greetings for Grumble and Moss, and repeatable Bee reminder/completion greetings, now use `ExAddCommandText(..., 0)` to request no journal record. Initial story dialogue remains logged. The official `Script functions.pdf` identifies that argument as `bNote`; this behavior should be tested directly. A new save-safe `HoneyJournalRecovered` guard records Moss's honey recovery via a fourth standard popup.

Please test that repeated peaceful interactions remain visible in gameplay **but stop adding Events List entries**, while journal milestones still appear and persist across saving/loading. Previous lesson 27 remains unchanged and verified.
