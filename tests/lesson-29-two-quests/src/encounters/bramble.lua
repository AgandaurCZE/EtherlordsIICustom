-- LESSON 29: Bramble, dangerous hidden spore thief. Based on verified encounter mechanics
-- Map position (1, 16). Bramble belongs to P2 with Bee, Grumble and Moss.
-- All runtime global scratch variables and stored state are Bramble-prefixed.

function Bramble_OnStep()
    bramble_state = ExGetVariable("BrambleChoiceState")
    bramble_hero = ExGetMainHeroID()

    if bramble_state == "Cooling" then
        if CalcDistanceObjectPoint(bramble_hero, 1, 16) >= 3 then
            ExSetVariable("BrambleChoiceState", "Ready")
            ExMessageToScreen("BRAMBLE RESET: Encounter rearmed")
        end
        return
    end
    if bramble_state ~= nil and bramble_state ~= "Ready" then
        return
    end
    if CalcDistanceObjectPoint(bramble_hero, 1, 16) >= 3 then
        return
    end

    -- Guard against overlapping scripted cinematics.
    bramble_bee_state = ExGetVariable("BeeChoiceState")
    if bramble_bee_state == "Intro" or bramble_bee_state == "Question"
       or bramble_bee_state == "Hostile" or bramble_bee_state == "Charging" then
        return
    end
    bramble_grumble_state = ExGetVariable("GrumbleChoiceState")
    if bramble_grumble_state == "Intro" or bramble_grumble_state == "Question"
       or bramble_grumble_state == "Hostile" or bramble_grumble_state == "Charging" then
        return
    end

    bramble_moss_state = ExGetVariable("MossChoiceState")
    if bramble_moss_state == "Intro" or bramble_moss_state == "Question"
       or bramble_moss_state == "Hostile" or bramble_moss_state == "Charging" then
        return
    end

    bramble_id = nil
    bramble_distance = 9999
    for bramble_index = 0, ExGetMobCount() - 1 do
        bramble_candidate = ExGetMobByIndex(bramble_index)
        bramble_current_distance = CalcDistanceObjectPoint(
            bramble_candidate, 1, 16
        )
        if bramble_current_distance < bramble_distance then
            bramble_id = bramble_candidate
            bramble_distance = bramble_current_distance
        end
    end
    if bramble_id == nil or bramble_distance > 2 then
        ExSetVariable("BrambleChoiceState", "NotFound")
        ExMessageToScreen("BRAMBLE ERROR: Cannot find monster near (1, 16)")
        return
    end

    bramble_home_x, bramble_home_y = ExGetPos(bramble_id)
    bramble_start_x, bramble_start_y = ExGetPos(bramble_hero)
    ExSetVariable("BrambleRuntimeId", bramble_id)
    ExSetVariable("BrambleHomeX", bramble_home_x)
    ExSetVariable("BrambleHomeY", bramble_home_y)
    ExSetVariable("BrambleHeroStartX", bramble_start_x)
    ExSetVariable("BrambleHeroStartY", bramble_start_y)
    ExSetVariable("BrambleChoiceState", "Intro")

    ExSoftAbortCmd(bramble_hero)
    ExAbortAllCommand()
    ExAddCommandText(bramble_id, "You found my hideout? Not many travelers get this far.", 0)
    ExAddCommandText(bramble_hero, "Moss says you've stolen some rare mushroom spores.", 0)
    ExAddCommandText(bramble_id, "You'll never overpower me. Will you negotiate, or challenge me?", 0)
    ExAddCommandExecuteScriptFunction("Bramble_AskQuestion")
end

function Bramble_AskQuestion()
    ExSetVariable("BrambleChoiceState", "Question")
    ExAddCommandQuestion(
        ExGetMainHeroID(),
        "What will you do?\n\nYES = Negotiate for the spores\nNO = Challenge Bramble",
        0
    )
end

function Bramble_OnCloseMessageBox(callback)
    if ExGetVariable("BrambleChoiceState") ~= "Question" then
        return
    end
    if callback == "OK" then
        ExSetVariable("BrambleChoiceState", "Peaceful")
        -- Shared P2 faction stays hostile; peaceful state is object-specific.
        ExAddCommandText(ExGetMainHeroID(), "Give Moss her spores back. No one needs to fight.", 0)
        ExAddCommandText(
            ExGetVariable("BrambleRuntimeId"),
            "Hah. Sensible. Take the spores, but keep my secret.", 0
        )
    else
        ExSetVariable("BrambleChoiceState", "Hostile")
        -- Shared P2 faction stays hostile; do not change faction hostility.
        ExAddCommandText(ExGetMainHeroID(), "I won't negotiate with a thief!", 0)
        ExAddCommandText(
            ExGetVariable("BrambleRuntimeId"),
            "Then face my strongest spells. I warned you!", 0
        )
        ExAddCommandExecuteScriptFunction("Bramble_LaunchAttack")
    end
end

function Bramble_LaunchAttack()
    bramble_id = ExGetVariable("BrambleRuntimeId")
    bramble_hero = ExGetMainHeroID()
    if bramble_id == nil then
        return
    end
    ExSetVariable("BrambleChoiceState", "Charging")
    ExAddCommandMobOrientToObject(bramble_id, bramble_hero)
    ExAddCommandCameraToObject(bramble_id, 0)
    bramble_attack_id = ExAddCommandMoveAndUseObject(
        bramble_id, bramble_hero
    )
    ExSetVariable("BrambleAttackCommand", bramble_attack_id)
end

function Bramble_IsBattle(attacker_id, target_id)
    bramble_id = ExGetVariable("BrambleRuntimeId")
    if bramble_id == nil then
        return 0
    end
    if attacker_id == bramble_id or target_id == bramble_id then
        return 1
    end
    return 0
end

function Bramble_OnBattleFinishing(attacker_id, target_id, winner_id)
    bramble_id = ExGetVariable("BrambleRuntimeId")
    bramble_hero = ExGetMainHeroID()
    if bramble_id == nil then
        return 1
    end
    if ExGetVariable("BrambleChoiceState") ~= "Charging" then
        return 1
    end

    ExMessageToScreen(
        "BRAMBLE BATTLE: W=" .. tostring(winner_id)
    )
    if winner_id == bramble_hero then
        ExSetVariable("BrambleChoiceState", "Completed")
        ExMessageToScreen("BRAMBLE: Hero won the battle")
        -- Spore quest requires negotiation. Killing the thief destroys that route.
        return 1
    end

    -- Same confirmed battle-refusal reset pattern as Lesson 19.
    ExSetVariable("BrambleChoiceState", "Cooling")
    bramble_home_x = ExGetVariable("BrambleHomeX")
    bramble_home_y = ExGetVariable("BrambleHomeY")
    bramble_start_x = ExGetVariable("BrambleHeroStartX")
    bramble_start_y = ExGetVariable("BrambleHeroStartY")

    if bramble_home_x ~= nil and bramble_home_y ~= nil then
        ExJumpToPos(bramble_id, bramble_home_x, bramble_home_y)
        ExMessageToScreen("BRAMBLE RESET: Returned home")
    end
    if bramble_start_x ~= nil and bramble_start_y ~= nil then
        ExJumpToPos(bramble_hero, bramble_start_x, bramble_start_y)
    end
    ExAddCommandCameraToObject(bramble_hero, 0)
    return 0
end

function Bramble_OnPreUse(object_id, hero_id)
    if ExGetVariable("BrambleChoiceState") ~= "Peaceful" then
        return nil
    end
    if object_id == ExGetVariable("BrambleRuntimeId") then
        if ExGetVariable("SporeQuestSkipBrambleGreeting") == 1 then
            ExSetVariable("HoneyQuestSkipBrambleGreeting", 0)
            return 0
        end
        ExMessageToScreen("BRAMBLE TEST: Peaceful PreUse intercepted")
        ExAddCommandText(
            object_id, "We have an understanding. Keep my hiding place secret.", 0
        )
        return 0
    end
    return nil
end

-- Lesson 25: self-register by callback names (save/load-safe).
EncounterRegistry_Register("Bramble", "BrambleRuntimeId", "BrambleChoiceState",
    "Bramble_OnStep", "Bramble_OnCloseMessageBox",
    "Bramble_OnBattleFinishing", "Bramble_OnPreUse")
