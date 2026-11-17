-- LESSON 21: Grumble independent encounter
-- Map position (15,10), Grumble belongs to P3 (with P3 Main Tower).
-- All runtime global scratch variables and stored state are Grumble-prefixed.

function Grumble_OnStep()
    grumble_state = ExGetVariable("GrumbleChoiceState")
    grumble_hero = ExGetMainHeroID()

    if grumble_state == "Cooling" then
        if CalcDistanceObjectPoint(grumble_hero, 15, 10) >= 3 then
            ExSetVariable("GrumbleChoiceState", "Ready")
            ExMessageToScreen("GRUMBLE RESET: Encounter rearmed")
        end
        return
    end
    if grumble_state ~= nil and grumble_state ~= "Ready" then
        return
    end
    if CalcDistanceObjectPoint(grumble_hero, 15, 10) >= 3 then
        return
    end

    -- Guard against overlapping scripted cinematics.
    grumble_bee_state = ExGetVariable("BeeChoiceState")
    if grumble_bee_state == "Intro" or grumble_bee_state == "Question"
       or grumble_bee_state == "Hostile" or grumble_bee_state == "Charging" then
        return
    end

    grumble_id = nil
    grumble_distance = 9999
    for grumble_index = 0, ExGetMobCount() - 1 do
        grumble_candidate = ExGetMobByIndex(grumble_index)
        grumble_current_distance = CalcDistanceObjectPoint(
            grumble_candidate, 15, 10
        )
        if grumble_current_distance < grumble_distance then
            grumble_id = grumble_candidate
            grumble_distance = grumble_current_distance
        end
    end
    if grumble_id == nil or grumble_distance > 2 then
        ExSetVariable("GrumbleChoiceState", "NotFound")
        ExMessageToScreen("GRUMBLE ERROR: Cannot find monster near (15,10)")
        return
    end

    grumble_home_x, grumble_home_y = ExGetPos(grumble_id)
    grumble_start_x, grumble_start_y = ExGetPos(grumble_hero)
    ExSetVariable("GrumbleRuntimeId", grumble_id)
    ExSetVariable("GrumbleHomeX", grumble_home_x)
    ExSetVariable("GrumbleHomeY", grumble_home_y)
    ExSetVariable("GrumbleHeroStartX", grumble_start_x)
    ExSetVariable("GrumbleHeroStartY", grumble_start_y)
    ExSetVariable("GrumbleChoiceState", "Intro")

    ExSoftAbortCmd(grumble_hero)
    ExAbortAllCommand()
    ExAddCommandText(grumble_id, "GRRR! Who stomps across my territory?", 1)
    ExAddCommandText(grumble_hero, "I am just exploring.", 1)
    ExAddCommandText(grumble_id, "Then choose! A friendly truce, or a proper duel?", 1)
    ExAddCommandExecuteScriptFunction("Grumble_AskQuestion")
end

function Grumble_AskQuestion()
    ExSetVariable("GrumbleChoiceState", "Question")
    ExAddCommandQuestion(
        ExGetMainHeroID(),
        "How do you answer Grumble?\n\nYES = Offer a truce\nNO = Challenge him",
        0
    )
end

function Grumble_OnCloseMessageBox(callback)
    if ExGetVariable("GrumbleChoiceState") ~= "Question" then
        return
    end
    if callback == "OK" then
        ExSetVariable("GrumbleChoiceState", "Peaceful")
        -- Lesson 22: no faction-wide change; Grumble is on P2.
        ExAddCommandText(ExGetMainHeroID(), "How about we call it a truce?", 1)
        ExAddCommandText(
            ExGetVariable("GrumbleRuntimeId"),
            "Hmph. Fine. You may pass without a fight.",
            1
        )
    else
        ExSetVariable("GrumbleChoiceState", "Hostile")
        -- Lesson 22: Grumble shares hostile P2 faction with Bee.
        ExAddCommandText(ExGetMainHeroID(), "I challenge you, Grumble!", 1)
        ExAddCommandText(
            ExGetVariable("GrumbleRuntimeId"),
            "HA! Finally, a worthy opponent! Prepare yourself!",
            1
        )
        ExAddCommandExecuteScriptFunction("Grumble_LaunchAttack")
    end
end

function Grumble_LaunchAttack()
    grumble_id = ExGetVariable("GrumbleRuntimeId")
    grumble_hero = ExGetMainHeroID()
    if grumble_id == nil then
        return
    end
    ExSetVariable("GrumbleChoiceState", "Charging")
    ExAddCommandMobOrientToObject(grumble_id, grumble_hero)
    ExAddCommandCameraToObject(grumble_id, 0)
    grumble_attack_id = ExAddCommandMoveAndUseObject(
        grumble_id, grumble_hero
    )
    ExSetVariable("GrumbleAttackCommand", grumble_attack_id)
end

function Grumble_IsBattle(attacker_id, target_id)
    grumble_id = ExGetVariable("GrumbleRuntimeId")
    if grumble_id == nil then
        return 0
    end
    if attacker_id == grumble_id or target_id == grumble_id then
        return 1
    end
    return 0
end

function Grumble_OnBattleFinishing(attacker_id, target_id, winner_id)
    grumble_id = ExGetVariable("GrumbleRuntimeId")
    grumble_hero = ExGetMainHeroID()
    if grumble_id == nil then
        return 1
    end
    if ExGetVariable("GrumbleChoiceState") ~= "Charging" then
        return 1
    end

    ExMessageToScreen(
        "GRUMBLE BATTLE: W=" .. tostring(winner_id)
    )
    if winner_id == grumble_hero then
        ExSetVariable("GrumbleChoiceState", "Completed")
        ExMessageToScreen("GRUMBLE: Hero won the battle")
        return 1
    end

    -- Same confirmed battle-refusal reset pattern as Lesson 19.
    ExSetVariable("GrumbleChoiceState", "Cooling")
    grumble_home_x = ExGetVariable("GrumbleHomeX")
    grumble_home_y = ExGetVariable("GrumbleHomeY")
    grumble_start_x = ExGetVariable("GrumbleHeroStartX")
    grumble_start_y = ExGetVariable("GrumbleHeroStartY")

    if grumble_home_x ~= nil and grumble_home_y ~= nil then
        ExJumpToPos(grumble_id, grumble_home_x, grumble_home_y)
        ExMessageToScreen("GRUMBLE RESET: Returned home")
    end
    if grumble_start_x ~= nil and grumble_start_y ~= nil then
        ExJumpToPos(grumble_hero, grumble_start_x, grumble_start_y)
    end
    ExAddCommandCameraToObject(grumble_hero, 0)
    return 0
end

function Grumble_OnPreUse(object_id, hero_id)
    if ExGetVariable("GrumbleChoiceState") ~= "Peaceful" then
        return nil
    end
    if object_id == ExGetVariable("GrumbleRuntimeId") then
        ExMessageToScreen("GRUMBLE TEST: Peaceful PreUse intercepted")
        ExAddCommandText(
            object_id, "Hmph. A deal is a deal. Pass in peace.", 1
        )
        return 0
    end
    return nil
end

-- Lesson 24: self-register at script initialization.
EncounterRegistry_Register("Grumble", "GrumbleRuntimeId", "GrumbleChoiceState",
    Grumble_OnStep, Grumble_OnCloseMessageBox,
    Grumble_OnBattleFinishing, Grumble_OnPreUse)
