-- LESSON 29: A second, independent, missable quest.
-- Moss must be peaceful/alive. Bramble at (1,16) is intentionally overwhelming.
-- Durable flags ONLY via ExSetVariable; no Lua function objects in saved state.
-- SporeQuestStage: nil unavailable/not offered, 1 find Bramble,
--   2 return to Moss, 3 complete, 4 failed.
-- Bramble peaceful negotiation is REQUIRED. Victory is not a substitute.

function SporeQuest_MossInteraction(object_id, hero_id)
    spore_stage = ExGetVariable("SporeQuestStage")
    spore_moss_state = ExGetVariable("MossChoiceState")
    spore_bramble_state = ExGetVariable("BrambleChoiceState")

    if spore_moss_state ~= "Peaceful" then
        return nil
    end
    if spore_stage == nil then
        if spore_bramble_state == "Completed" then
            ExSetVariable("SporeQuestStage", 4)
            ExAddCommandText(object_id,
                "Oh no! Bramble is gone. My rare spores are lost forever.", 0)
            ExAddCommandExecuteScriptFunction("SporeJournal_Failed")
            return 0
        end
        ExSetVariable("SporeQuestStage", 1)
        ExAddCommandText(object_id,
            "Bramble stole my rare mushroom spores! Please bring them home.", 1)
        ExAddCommandText(hero_id,
            "I'll search for Bramble. Where is she hiding?", 0)
        ExAddCommandText(object_id,
            "Far to the west, behind the rocks. Please do not fight her!", 0)
        ExAddCommandExecuteScriptFunction("SporeJournal_Accepted")
        ExMessageToScreen("SIDE QUEST: The Stolen Mushroom Spores")
        return 0
    end
    if spore_stage == 1 then
        ExAddCommandText(object_id,
            "Please find Bramble. She hides west behind the rocks.", 0)
        return 0
    end
    if spore_stage == 2 then
        if ExGetVariable("SporeQuestSporesRecovered") ~= 1 then
            return 0
        end
        ExSetVariable("SporeQuestStage", 3)
        ExAddCommandText(hero_id,
            "I convinced Bramble to return your stolen mushroom spores.", 0)
        ExAddCommandText(object_id,
            "My spores! Thank you. These are precious beyond words.", 1)
        ExAddCommandExecuteScriptFunction("SporeQuest_Reward")
        ExAddCommandExecuteScriptFunction("SporeJournal_Completed")
        ExMessageToScreen("SIDE QUEST COMPLETE: The Stolen Mushroom Spores")
        return 0
    end
    if spore_stage == 3 then
        ExAddCommandText(object_id,
            "My mushroom spores are safe. Thank you again!", 0)
        return 0
    end
    if spore_stage == 4 then
        ExAddCommandText(object_id,
            "The spores are lost. There is nothing more we can do.", 0)
        return 0
    end
    return 0
end

function SporeQuest_Reward()
    if ExGetVariable("SporeQuestRewardReceived") == 1 then
        return
    end
    ExSetVariable("SporeQuestRewardReceived", 1)
    -- Known working Etherlords II spell + loot notification.
    ExAddSpell(ExGetMainHeroID(), "ALST")
    ExStartLootMessage()
    ExAddLootMessageSpell("ALST")
    ExSendLootMessage()
end

function SporeQuest_OnStep()
    spore_stage = ExGetVariable("SporeQuestStage")
    if spore_stage == nil or spore_stage == 3 or spore_stage == 4 then
        return
    end

    -- If later campaign mechanics ever allow Moss to die after a truce,
    -- fail gracefully without touching the independent honey quest.
    if ExGetVariable("MossChoiceState") == "Completed" then
        ExSetVariable("SporeQuestStage", 4)
        ExAddCommandExecuteScriptFunction("SporeJournal_Failed")
        ExMessageToScreen("SIDE QUEST FAILED: Moss is gone")
        return
    end

    if ExGetCommandQueueSize() > 0 then
        return
    end

    spore_bramble_state = ExGetVariable("BrambleChoiceState")
    spore_moss_state = ExGetVariable("MossChoiceState")
    spore_bee_state = ExGetVariable("BeeChoiceState")
    spore_grumble_state = ExGetVariable("GrumbleChoiceState")
    if spore_bee_state == "Intro" or spore_bee_state == "Question"
       or spore_bee_state == "Hostile" or spore_bee_state == "Charging"
       or spore_grumble_state == "Intro" or spore_grumble_state == "Question"
       or spore_grumble_state == "Hostile" or spore_grumble_state == "Charging"
       or spore_moss_state == "Intro" or spore_moss_state == "Question"
       or spore_moss_state == "Hostile" or spore_moss_state == "Charging"
       or spore_bramble_state == "Intro" or spore_bramble_state == "Question"
       or spore_bramble_state == "Hostile" or spore_bramble_state == "Charging" then
        return
    end

    if spore_stage == 1 and spore_bramble_state == "Completed" then
        ExSetVariable("SporeQuestStage", 4)
        ExAddCommandText(ExGetMainHeroID(),
            "Bramble was defeated. The fragile spores cannot be recovered.", 0)
        ExAddCommandExecuteScriptFunction("SporeJournal_Failed")
        ExMessageToScreen("SIDE QUEST FAILED: The spores were destroyed")
        return
    end

    if spore_stage == 1 and spore_bramble_state == "Peaceful"
       and CalcDistanceObjectPoint(ExGetMainHeroID(), 1, 16) < 3 then
        ExSetVariable("SporeQuestStage", 2)
        ExSetVariable("SporeQuestSporesRecovered", 1)
        spore_bramble_id = ExGetVariable("BrambleRuntimeId")
        if spore_bramble_id ~= nil then
            ExSetVariable("SporeQuestSkipBrambleGreeting", 1)
            ExAddCommandText(spore_bramble_id,
                "Take the spores back to Moss. Keep our bargain secret.", 0)
        end
        ExAddCommandExecuteScriptFunction("SporeJournal_Recovered")
        ExMessageToScreen("SIDE QUEST: Spores recovered - Return to Moss")
        return
    end
end
