-- LESSON 25: Moss sample encounter built from the tested Grumble pattern
-- Map position (10,16). Moss belongs to P2, alongside Bee and Grumble.
-- All runtime global scratch variables and stored state are Moss-prefixed.

function Moss_OnStep()
    moss_state = ExGetVariable("MossChoiceState")
    moss_hero = ExGetMainHeroID()

    if moss_state == "Cooling" then
        if CalcDistanceObjectPoint(moss_hero, 10, 16) >= 3 then
            ExSetVariable("MossChoiceState", "Ready")
            ExMessageToScreen("MOSS RESET: Encounter rearmed")
        end
        return
    end
    if moss_state ~= nil and moss_state ~= "Ready" then
        return
    end
    if CalcDistanceObjectPoint(moss_hero, 10, 16) >= 3 then
        return
    end

    -- Guard against overlapping scripted cinematics.
    moss_bee_state = ExGetVariable("BeeChoiceState")
    if moss_bee_state == "Intro" or moss_bee_state == "Question"
       or moss_bee_state == "Hostile" or moss_bee_state == "Charging" then
        return
    end
    moss_grumble_state = ExGetVariable("GrumbleChoiceState")
    if moss_grumble_state == "Intro" or moss_grumble_state == "Question"
       or moss_grumble_state == "Hostile" or moss_grumble_state == "Charging" then
        return
    end

    moss_id = nil
    moss_distance = 9999
    for moss_index = 0, ExGetMobCount() - 1 do
        moss_candidate = ExGetMobByIndex(moss_index)
        moss_current_distance = CalcDistanceObjectPoint(
            moss_candidate, 10, 16
        )
        if moss_current_distance < moss_distance then
            moss_id = moss_candidate
            moss_distance = moss_current_distance
        end
    end
    if moss_id == nil or moss_distance > 2 then
        ExSetVariable("MossChoiceState", "NotFound")
        ExMessageToScreen("MOSS ERROR: Cannot find monster near (10,16)")
        return
    end

    moss_home_x, moss_home_y = ExGetPos(moss_id)
    moss_start_x, moss_start_y = ExGetPos(moss_hero)
    ExSetVariable("MossRuntimeId", moss_id)
    ExSetVariable("MossHomeX", moss_home_x)
    ExSetVariable("MossHomeY", moss_home_y)
    ExSetVariable("MossHeroStartX", moss_start_x)
    ExSetVariable("MossHeroStartY", moss_start_y)
    ExSetVariable("MossChoiceState", "Intro")

    ExSoftAbortCmd(moss_hero)
    ExAbortAllCommand()
    ExAddCommandText(moss_id, "Oh! Someone's walking through my mushroom patch!", 1)
    ExAddCommandText(moss_hero, "I didn't mean to disturb your garden.", 1)
    ExAddCommandText(moss_id, "Will you protect these mushrooms, or trample them?", 1)
    ExAddCommandExecuteScriptFunction("Moss_AskQuestion")
end

function Moss_AskQuestion()
    ExSetVariable("MossChoiceState", "Question")
    ExAddCommandQuestion(
        ExGetMainHeroID(),
        "What do you promise Moss?\n\nYES = Protect the mushrooms\nNO = Trample the mushrooms",
        0
    )
end

function Moss_OnCloseMessageBox(callback)
    if ExGetVariable("MossChoiceState") ~= "Question" then
        return
    end
    if callback == "OK" then
        ExSetVariable("MossChoiceState", "Peaceful")
        -- Shared P2 faction stays hostile; peaceful state is object-specific.
        ExAddCommandText(ExGetMainHeroID(), "I'll leave every mushroom untouched.", 1)
        ExAddCommandText(
            ExGetVariable("MossRuntimeId"),
            "Oh, wonderful! The mushrooms thank you!",
            1
        )
    else
        ExSetVariable("MossChoiceState", "Hostile")
        -- Shared P2 faction stays hostile; do not change faction hostility.
        ExAddCommandText(ExGetMainHeroID(), "These mushrooms look like excellent stepping stones!", 1)
        ExAddCommandText(
            ExGetVariable("MossRuntimeId"),
            "Not one step further! Defend the mushroom kingdom!",
            1
        )
        ExAddCommandExecuteScriptFunction("Moss_LaunchAttack")
    end
end

function Moss_LaunchAttack()
    moss_id = ExGetVariable("MossRuntimeId")
    moss_hero = ExGetMainHeroID()
    if moss_id == nil then
        return
    end
    ExSetVariable("MossChoiceState", "Charging")
    ExAddCommandMobOrientToObject(moss_id, moss_hero)
    ExAddCommandCameraToObject(moss_id, 0)
    moss_attack_id = ExAddCommandMoveAndUseObject(
        moss_id, moss_hero
    )
    ExSetVariable("MossAttackCommand", moss_attack_id)
end

function Moss_IsBattle(attacker_id, target_id)
    moss_id = ExGetVariable("MossRuntimeId")
    if moss_id == nil then
        return 0
    end
    if attacker_id == moss_id or target_id == moss_id then
        return 1
    end
    return 0
end

function Moss_OnBattleFinishing(attacker_id, target_id, winner_id)
    moss_id = ExGetVariable("MossRuntimeId")
    moss_hero = ExGetMainHeroID()
    if moss_id == nil then
        return 1
    end
    if ExGetVariable("MossChoiceState") ~= "Charging" then
        return 1
    end

    ExMessageToScreen(
        "MOSS BATTLE: W=" .. tostring(winner_id)
    )
    if winner_id == moss_hero then
        ExSetVariable("MossChoiceState", "Completed")
        ExMessageToScreen("MOSS: Hero won the battle")
        return 1
    end

    -- Same confirmed battle-refusal reset pattern as Lesson 19.
    ExSetVariable("MossChoiceState", "Cooling")
    moss_home_x = ExGetVariable("MossHomeX")
    moss_home_y = ExGetVariable("MossHomeY")
    moss_start_x = ExGetVariable("MossHeroStartX")
    moss_start_y = ExGetVariable("MossHeroStartY")

    if moss_home_x ~= nil and moss_home_y ~= nil then
        ExJumpToPos(moss_id, moss_home_x, moss_home_y)
        ExMessageToScreen("MOSS RESET: Returned home")
    end
    if moss_start_x ~= nil and moss_start_y ~= nil then
        ExJumpToPos(moss_hero, moss_start_x, moss_start_y)
    end
    ExAddCommandCameraToObject(moss_hero, 0)
    return 0
end

function Moss_OnPreUse(object_id, hero_id)
    if ExGetVariable("MossChoiceState") ~= "Peaceful" then
        return nil
    end
    if object_id == ExGetVariable("MossRuntimeId") then
        ExMessageToScreen("MOSS TEST: Peaceful PreUse intercepted")
        ExAddCommandText(
            object_id, "Welcome back, careful traveler. My mushrooms are safe.", 1
        )
        return 0
    end
    return nil
end

-- Lesson 25: self-register by callback names (save/load-safe).
EncounterRegistry_Register("Moss", "MossRuntimeId", "MossChoiceState",
    "Moss_OnStep", "Moss_OnCloseMessageBox",
    "Moss_OnBattleFinishing", "Moss_OnPreUse")
