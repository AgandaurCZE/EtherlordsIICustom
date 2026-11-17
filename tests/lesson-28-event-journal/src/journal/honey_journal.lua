-- LESSON 28 EXPERIMENT: native notebook / Events List.
-- Official editor documentation says ExMessageBoxStandard(message, hero_id)
-- adds an event to the notebook when the hero_id is supplied.
-- This also displays an OK-message: observe whether the user sees both.
-- Save-safe once-only flags; no function/table values in ExSetVariable.

function HoneyJournal_Stage1()
    if ExGetVariable("HoneyJournalEntry1") == 1 then
        return
    end
    ExSetVariable("HoneyJournalEntry1", 1)
    ExMessageBoxStandard(
        "The Queen's Missing Honey: Investigate Grumble. "
        .. "Bluhblah's royal honey has disappeared. "
        .. "Question Grumble about the theft.",
        ExGetMainHeroID()
    )
end

function HoneyJournal_Stage2()
    if ExGetVariable("HoneyJournalEntry2") == 1 then
        return
    end
    ExSetVariable("HoneyJournalEntry2", 1)
    ExMessageBoxStandard(
        "A Suspicious Trade: Find Moss. "
        .. "Grumble traded the Queen's honey to Moss for rare mushrooms. "
        .. "Find Moss and recover the royal honey.",
        ExGetMainHeroID()
    )
end

function HoneyJournal_StageRecovered()
    if ExGetVariable("HoneyJournalRecovered") == 1 then
        return
    end
    ExSetVariable("HoneyJournalRecovered", 1)
    ExMessageBoxStandard(
        "Royal Honey Recovered: Return to the Queen. "
        .. "Moss has surrendered the missing honey. "
        .. "Bring it back to bluhblah for your reward.",
        ExGetMainHeroID()
    )
end

function HoneyJournal_Stage3()
    if ExGetVariable("HoneyJournalEntry3") == 1 then
        return
    end
    ExSetVariable("HoneyJournalEntry3", 1)
    ExMessageBoxStandard(
        "The Royal Honey Returned: Quest complete. "
        .. "The honey has been recovered and returned to bluhblah. "
        .. "The Queen has rewarded her Royal Investigator.",
        ExGetMainHeroID()
    )
end
