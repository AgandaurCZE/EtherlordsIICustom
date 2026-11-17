-- LESSON 21: one global event-hook router, two encounter modules.
-- This script is concatenated after Bee and Grumble modules.

function Hook_OnStep()
    Bee_OnStep()
    Grumble_OnStep()
end

function Hook_OnCloseMessageBox(callback)
    -- Only a module in its Question state handles this callback.
    Bee_OnCloseMessageBox(callback)
    Grumble_OnCloseMessageBox(callback)
end

function Hook_OnBattleFinishing(attacker_id, target_id, winner_id)
    -- Dispatch only the affected monster; do not run both reset handlers.
    grumble_router_id = ExGetVariable("GrumbleRuntimeId")
    if grumble_router_id ~= nil and
       (attacker_id == grumble_router_id or target_id == grumble_router_id) then
        return Grumble_OnBattleFinishing(attacker_id, target_id, winner_id)
    end

    bee_router_id = ExGetVariable("BeeRuntimeId")
    if bee_router_id ~= nil and
       (attacker_id == bee_router_id or target_id == bee_router_id) then
        return Bee_OnBattleFinishing(attacker_id, target_id, winner_id)
    end

    return 1
end

function Hook_OnPreUse(object_id, hero_id)
    router_answer = Bee_OnPreUse(object_id, hero_id)
    if router_answer ~= nil then
        return router_answer
    end
    router_answer = Grumble_OnPreUse(object_id, hero_id)
    if router_answer ~= nil then
        return router_answer
    end
    return 1
end
