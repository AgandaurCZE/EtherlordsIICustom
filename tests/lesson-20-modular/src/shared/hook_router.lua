-- The ONLY engine hook definitions for this mission.
-- New encounter modules export unique EncounterName_* functions.

function Hook_OnStep()
    Bee_OnStep()
end

function Hook_OnCloseMessageBox(callback)
    Bee_OnCloseMessageBox(callback)
end

function Hook_OnBattleFinishing(attacker_id, target_id, winner_id)
    -- When adding more encounters, dispatch based on actual attacker/target IDs.
    -- Never invoke multiple battle handlers for a single encounter.
    return Bee_OnBattleFinishing(attacker_id, target_id, winner_id)
end

function Hook_OnPreUse(object_id, hero_id)
    answer = Bee_OnPreUse(object_id, hero_id)
    if answer ~= nil then
        return answer
    end
    return 1
end
