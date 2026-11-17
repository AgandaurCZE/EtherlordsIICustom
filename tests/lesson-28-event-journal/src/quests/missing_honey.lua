-- LESSON 27: The Queen's Missing Honey.
-- Quest coordination only. Encounter combat/reward functions stay unchanged.
-- All durable quest state lives in ExSetVariable (not Lua tables/functions).
--
-- Stages: nil = not started, 1 = investigate Grumble,
--         2 = recover honey from Moss, 3 = return to Bee, 4 = complete.
-- Peaceful OR Completed (hero won combat) counts as resolved.
-- Refusing a battle / Cooling / Ready does NOT count.

function HoneyQuest_BeeInteraction(object_id, hero_id)
    honey_stage = ExGetVariable("HoneyQuestStage")
    if honey_stage == nil then
        ExSetVariable("HoneyQuestStage", 1)
        ExAddCommandText(object_id,
            "BZZ! I need your help. Someone stole my royal honey!", 1)
        ExAddCommandText(object_id,
            "Question Grumble. He was seen by my hive!", 1)
        ExAddCommandText(hero_id,
            "I will investigate the missing honey, Your Buzziness.", 1)
        ExMessageToScreen("QUEST: Missing Honey - Question Grumble")
        ExAddCommandExecuteScriptFunction("HoneyJournal_Stage1")
        return 0
    end
    if honey_stage == 1 then
        ExAddCommandText(object_id,
            "BZZ! Grumble knows something. Please question him!", 0)
        return 0
    end
    if honey_stage == 2 then
        ExAddCommandText(object_id,
            "BZZ! Find Moss! My royal honey is still missing!", 0)
        return 0
    end
    if honey_stage == 3 then
        -- Mark paid before triggering reward commands to prevent duplicates
        -- across interrupted dialogs, saving/loading, or repeated clicks.
        ExSetVariable("HoneyQuestStage", 4)
        ExAddCommandText(hero_id,
            "Moss had the honey. I have brought it back!", 1)
        ExAddCommandText(object_id,
            "BZZZZ! The hive is saved! Accept my royal reward!", 1)
        ExAddCommandExecuteScriptFunction("HoneyQuest_Reward")
        ExAddCommandExecuteScriptFunction("HoneyJournal_Stage3")
        ExMessageToScreen("QUEST COMPLETE: The Queen's Missing Honey")
        return 0
    end
    if honey_stage == 4 then
        ExAddCommandText(object_id,
            "BZZ! My royal honey is safe, thanks to you!", 0)
        return 0
    end
    return nil
end

function HoneyQuest_Reward()
    if ExGetVariable("HoneyQuestRewardReceived") == 1 then
        return
    end
    ExSetVariable("HoneyQuestRewardReceived", 1)
    -- A known working spell reward API, separate from BeeGiftReceived.
    ExAddSpell(ExGetMainHeroID(), "ASLT")
    ExStartLootMessage()
    ExAddLootMessageSpell("ASLT")
    ExSendLootMessage()
end

function HoneyQuest_Resolved(state)
    if state == "Peaceful" or state == "Completed" then
        return 1
    end
    return 0
end

function HoneyQuest_OnStep()
    honey_stage = ExGetVariable("HoneyQuestStage")
    if honey_stage == nil or honey_stage == 3 or honey_stage == 4 then
        return
    end

    -- Do not enqueue quest narration in the middle of an encounter's
    -- scripted dialogue, charge or battle transition.
    if ExGetCommandQueueSize() > 0 then
        return
    end
    honey_bee_state = ExGetVariable("BeeChoiceState")
    honey_grumble_state = ExGetVariable("GrumbleChoiceState")
    honey_moss_state = ExGetVariable("MossChoiceState")
    if honey_bee_state == "Intro" or honey_bee_state == "Question"
       or honey_bee_state == "Hostile" or honey_bee_state == "Charging"
       or honey_grumble_state == "Intro" or honey_grumble_state == "Question"
       or honey_grumble_state == "Hostile" or honey_grumble_state == "Charging"
       or honey_moss_state == "Intro" or honey_moss_state == "Question"
       or honey_moss_state == "Hostile" or honey_moss_state == "Charging" then
        return
    end

    -- A previously resolved NPC does not remotely deliver quest clues.
    -- The hero must visit the NPC's area after the quest reaches this stage.
    if honey_stage == 1 and HoneyQuest_Resolved(honey_grumble_state) == 1
       and CalcDistanceObjectPoint(ExGetMainHeroID(), 15, 10) < 3 then
        ExSetVariable("HoneyQuestStage", 2)
        honey_grumble_id = ExGetVariable("GrumbleRuntimeId")
        if honey_grumble_state == "Peaceful" and honey_grumble_id ~= nil then
            -- The movement click which brought the hero here may still
            -- invoke OnPreUse after this queued quest narration.
            -- Consume that extra greeting once, not permanently.
            ExSetVariable("HoneyQuestSkipGrumbleGreeting", 1)
            ExAddCommandText(honey_grumble_id,
                "I traded the Queen's honey to Moss for rare mushrooms!", 1)
        else
            ExAddCommandText(ExGetMainHeroID(),
                "Grumble's belongings reveal a honey trade with Moss.", 1)
        end
        ExMessageToScreen("QUEST: Clue found - Find Moss")
        ExAddCommandExecuteScriptFunction("HoneyJournal_Stage2")
        return
    end

    if honey_stage == 2 and HoneyQuest_Resolved(honey_moss_state) == 1
       and CalcDistanceObjectPoint(ExGetMainHeroID(), 10, 16) < 3 then
        ExSetVariable("HoneyQuestStage", 3)
        ExSetVariable("HoneyQuestHoneyRecovered", 1)
        honey_moss_id = ExGetVariable("MossRuntimeId")
        if honey_moss_state == "Peaceful" and honey_moss_id ~= nil then
            ExSetVariable("HoneyQuestSkipMossGreeting", 1)
            ExAddCommandText(honey_moss_id,
                "The honey? Of course! Please return it to the Queen.", 1)
        else
            ExAddCommandText(ExGetMainHeroID(),
                "I recovered the Queen's honey among Moss's belongings.", 1)
        end
        ExMessageToScreen("QUEST: Honey recovered - Return to Bee")
        ExAddCommandExecuteScriptFunction("HoneyJournal_StageRecovered")
        return
    end
end
