-- LESSON 22: one router, two monsters sharing hostile P2.
-- Truce is per-monster scripted state. Native faction remains hostile.

function Hook_OnStep()
    Bee_OnStep()
    Grumble_OnStep()
end

function Hook_OnCloseMessageBox(callback)
    Bee_OnCloseMessageBox(callback)
    Grumble_OnCloseMessageBox(callback)
end

function Hook_OnBattleFinishing(attacker_id, target_id, winner_id)
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

-- The engine may ask if a monster can automatically intercept the hero.
-- This MUST NOT be mistaken for an individual hostility setter.
function Hook_OnIntercept(hero_id, interceptor_id)
    if hero_id ~= ExGetMainHeroID() then
        return 1
    end
    if interceptor_id == ExGetVariable("BeeRuntimeId") and
       ExGetVariable("BeeChoiceState") == "Peaceful" then
        if ExGetVariable("BeeInterceptDebug") ~= 1 then
            ExSetVariable("BeeInterceptDebug", 1)
            ExMessageToScreen("BEE TEST: Peaceful intercept blocked")
        end
        return 0
    end
    if interceptor_id == ExGetVariable("GrumbleRuntimeId") and
       ExGetVariable("GrumbleChoiceState") == "Peaceful" then
        if ExGetVariable("GrumbleInterceptDebug") ~= 1 then
            ExSetVariable("GrumbleInterceptDebug", 1)
            ExMessageToScreen("GRUMBLE TEST: Peaceful intercept blocked")
        end
        return 0
    end
    return 1
end
