-- Bee Queen encounter, extracted from working Lesson 19.
-- Only Bee_* functions are defined here; engine hooks live in hook_router.lua.
-- IMPORTANT: keep variable persistence through ExSetVariable/ExGetVariable.

function Bee_OnStep()
    state = ExGetVariable("BeeChoiceState")
    hero_id = ExGetMainHeroID()

    if state == "Cooling" then
        if CalcDistanceObjectPoint(hero_id, 7, 5) >= 3 then
            ExSetVariable("BeeChoiceState", "Ready")
            ExMessageToScreen("BEE RESET: Encounter rearmed")
        end
        return
    end

    if state ~= nil and state ~= "Ready" then
        return
    end

    if CalcDistanceObjectPoint(hero_id, 7, 5) >= 3 then
        return
    end

    bee_id = nil
    bee_distance = 9999
    for i = 0, ExGetMobCount() - 1 do
        mob_id = ExGetMobByIndex(i)
        mob_distance = CalcDistanceObjectPoint(mob_id, 7, 5)
        if mob_distance < bee_distance then
            bee_distance = mob_distance
            bee_id = mob_id
        end
    end

    if bee_id == nil or bee_distance > 2 then
        ExSetVariable("BeeChoiceState", "NotFound")
        ExMessageToScreen("Bee not found!")
        return
    end

    bee_x, bee_y = ExGetPos(bee_id)
    hero_x, hero_y = ExGetPos(hero_id)
    ExSetVariable("BeeRuntimeId", bee_id)
    ExSetVariable("BeeHomeX", bee_x)
    ExSetVariable("BeeHomeY", bee_y)
    ExSetVariable("BeeHeroStartX", hero_x)
    ExSetVariable("BeeHeroStartY", hero_y)
    ExSetVariable("BeeChoiceState", "Intro")

    ExSoftAbortCmd(hero_id)
    ExAbortAllCommand()
    ExAddCommandText(bee_id, "BZZ! You dare enter my sacred kingdom?", 1)
    ExAddCommandText(hero_id, "I was just passing through!", 1)
    ExAddCommandText(bee_id, "Then show some respect to your Queen!", 1)
    ExAddCommandExecuteScriptFunction("Bee_AskQuestion")
end

function Bee_AskQuestion()
    ExSetVariable("BeeChoiceState", "Question")
    ExAddCommandQuestion(
        ExGetMainHeroID(),
        "Will you apologize to the Queen of Bees?\n\nYES = Apologize\nNO = Insult",
        0
    )
end

function Bee_OnCloseMessageBox(callback)
    if ExGetVariable("BeeChoiceState") ~= "Question" then
        return
    end

    if callback == "OK" then
        ExSetVariable("BeeChoiceState", "Peaceful")
        -- Lesson 22: no faction-wide change; keep P1/P2 hostile.
        ExAddCommandText(ExGetMainHeroID(), "Forgive me, Your Buzziness!", 1)
        ExAddCommandText(ExGetVariable("BeeRuntimeId"), "BZZ! Your apology is accepted!", 1)
        ExAddCommandText(ExGetVariable("BeeRuntimeId"), "Take this magical gift from my hive!", 1)
        ExAddCommandExecuteScriptFunction("Bee_GiveGift")
    else
        ExSetVariable("BeeChoiceState", "Hostile")
        -- Lesson 22: P1/P2 remains hostile for native battle initiation.
        ExAddCommandText(ExGetMainHeroID(), "Your honey tastes like swamp water!", 1)
        ExAddCommandText(ExGetVariable("BeeRuntimeId"), "BZZZZ! NOBODY INSULTS MY HONEY!", 1)
        ExAddCommandExecuteScriptFunction("Bee_LaunchAttack")
    end
end

function Bee_GiveGift()
    if ExGetVariable("BeeGiftReceived") == 1 then
        return
    end
    ExSetVariable("BeeGiftReceived", 1)
    gift_roll = 1
    if random ~= nil then
        gift_roll = random(2)
    end
    gift_code = "ALST"
    if gift_roll == 2 then
        gift_code = "ASLT"
    end
    ExAddSpell(ExGetMainHeroID(), gift_code)
    ExStartLootMessage()
    ExAddLootMessageSpell(gift_code)
    ExSendLootMessage()
end

function Bee_LaunchAttack()
    bee_id = ExGetVariable("BeeRuntimeId")
    hero_id = ExGetMainHeroID()
    if bee_id == nil then
        return
    end
    ExSetVariable("BeeChoiceState", "Charging")
    ExAddCommandMobOrientToObject(bee_id, hero_id)
    ExAddCommandCameraToObject(bee_id, 0)
    attack_id = ExAddCommandMoveAndUseObject(bee_id, hero_id)
    ExSetVariable("BeeAttackCommand", attack_id)
end

-- Returns engine 'accept' value (0/1) for this bee battle,
-- or nil if the battle is unrelated. Keep Lesson 19 outcome logic.
function Bee_OnBattleFinishing(attacker_id, target_id, winner_id)
    ExMessageToScreen(
        "BATTLE HOOK: A=" .. tostring(attacker_id) ..
        " T=" .. tostring(target_id) ..
        " W=" .. tostring(winner_id)
    )

    bee_id = ExGetVariable("BeeRuntimeId")
    hero_id = ExGetMainHeroID()

    if bee_id == nil then
        return 1
    end
    if attacker_id ~= bee_id and target_id ~= bee_id then
        return 1
    end
    if ExGetVariable("BeeChoiceState") ~= "Charging" then
        return 1
    end
    if winner_id == hero_id then
        ExSetVariable("BeeChoiceState", "Completed")
        ExMessageToScreen("BEE: Hero won the battle")
        return 1
    end

    ExMessageToScreen("BEE RESET: Beginning rollback")
    ExSetVariable("BeeChoiceState", "Cooling")
    home_x = ExGetVariable("BeeHomeX")
    home_y = ExGetVariable("BeeHomeY")
    start_x = ExGetVariable("BeeHeroStartX")
    start_y = ExGetVariable("BeeHeroStartY")

    if home_x ~= nil and home_y ~= nil then
        ExJumpToPos(bee_id, home_x, home_y)
        ExMessageToScreen("BEE RESET: Queen returned home")
    end
    if start_x ~= nil and start_y ~= nil then
        ExJumpToPos(hero_id, start_x, start_y)
        ExMessageToScreen("BEE RESET: Hero repositioned")
    end
    ExAddCommandCameraToObject(hero_id, 0)
    return 0
end

-- Return nil for unrelated objects. Return 0/1 for handled bee interactions.
function Bee_OnPreUse(object_id, hero_id)
    if ExGetVariable("BeeChoiceState") ~= "Peaceful" then
        return nil
    end
    if object_id == ExGetVariable("BeeRuntimeId") then
        ExMessageToScreen("BEE TEST: Peaceful PreUse intercepted")
        ExAddCommandText(object_id, "BZZ BZZ! Welcome back, friend of the Hive!", 1)
        return 0
    end
    return nil
end
