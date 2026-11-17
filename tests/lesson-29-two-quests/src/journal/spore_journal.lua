-- LESSON 29 side quest journal: native Events List, once per stage.
-- Each ExMessageBoxStandard writes a save-persistent event for the player.

function SporeJournal_Accepted()
    if ExGetVariable("SporeJournalAccepted") == 1 then
        return
    end
    ExSetVariable("SporeJournalAccepted", 1)
    ExMessageBoxStandard(
        "The Stolen Mushroom Spores: Find Bramble. "
        .. "Moss needs rare spores stolen by a powerful thief. "
        .. "Bramble hides behind rocks to the west. Negotiate; do not fight.",
        ExGetMainHeroID()
    )
end

function SporeJournal_Recovered()
    if ExGetVariable("SporeJournalRecovered") == 1 then
        return
    end
    ExSetVariable("SporeJournalRecovered", 1)
    ExMessageBoxStandard(
        "Spores Recovered: Return to Moss. "
        .. "Bramble agreed to surrender the spores peacefully. "
        .. "Bring them back to Moss to finish the side quest.",
        ExGetMainHeroID()
    )
end

function SporeJournal_Completed()
    if ExGetVariable("SporeJournalCompleted") == 1 then
        return
    end
    ExSetVariable("SporeJournalCompleted", 1)
    ExMessageBoxStandard(
        "The Stolen Mushroom Spores: Completed. "
        .. "Moss received her rare spores and rewarded your diplomacy.",
        ExGetMainHeroID()
    )
end

function SporeJournal_Failed()
    if ExGetVariable("SporeJournalFailed") == 1 then
        return
    end
    ExSetVariable("SporeJournalFailed", 1)
    ExMessageBoxStandard(
        "The Stolen Mushroom Spores: Failed. "
        .. "The peaceful path was lost. The rare spores cannot be returned.",
        ExGetMainHeroID()
    )
end
