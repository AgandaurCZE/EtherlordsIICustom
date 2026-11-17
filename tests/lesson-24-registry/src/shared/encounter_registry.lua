-- LESSON 24: Lua 4 compatible encounter registry.
-- Keep function references in Lua memory; gameplay state remains in ExSetVariable.
-- Load this module BEFORE any encounter source registers itself.
EncounterRegistry_Entries = {}
EncounterRegistry_Count = 0

function EncounterRegistry_Register(name, runtime_key, state_key,
    on_step, on_close, on_battle, on_preuse)
    EncounterRegistry_Count = EncounterRegistry_Count + 1
    EncounterRegistry_Entries[EncounterRegistry_Count] = {
        name = name,
        runtime_key = runtime_key,
        state_key = state_key,
        on_step = on_step,
        on_close = on_close,
        on_battle = on_battle,
        on_preuse = on_preuse
    }
end

function EncounterRegistry_OnStep()
    for registry_index = 1, EncounterRegistry_Count do
        registry_entry = EncounterRegistry_Entries[registry_index]
        registry_entry.on_step()
    end
end

function EncounterRegistry_OnCloseMessageBox(callback)
    -- Keep former behavior: each handler ignores callbacks unless
    -- its own state is "Question".
    for registry_index = 1, EncounterRegistry_Count do
        registry_entry = EncounterRegistry_Entries[registry_index]
        registry_entry.on_close(callback)
    end
end

function EncounterRegistry_OnBattleFinishing(attacker_id, target_id, winner_id)
    -- Preserve Lesson 23 dispatch priority: Grumble (registered second)
    -- before Bee. Only one battle handler is allowed to handle a fight.
    for registry_index = EncounterRegistry_Count, 1, -1 do
        registry_entry = EncounterRegistry_Entries[registry_index]
        registry_id = ExGetVariable(registry_entry.runtime_key)
        if registry_id ~= nil and
           (attacker_id == registry_id or target_id == registry_id) then
            return registry_entry.on_battle(attacker_id, target_id, winner_id)
        end
    end
    return 1
end

function EncounterRegistry_OnPreUse(object_id, hero_id)
    -- Preserve Lesson 23 dispatch priority: Bee before Grumble.
    for registry_index = 1, EncounterRegistry_Count do
        registry_entry = EncounterRegistry_Entries[registry_index]
        registry_answer = registry_entry.on_preuse(object_id, hero_id)
        if registry_answer ~= nil then
            return registry_answer
        end
    end
    return 1
end

function EncounterRegistry_OnIntercept(hero_id, interceptor_id)
    if hero_id ~= ExGetMainHeroID() then
        return 1
    end

    for registry_index = 1, EncounterRegistry_Count do
        registry_entry = EncounterRegistry_Entries[registry_index]
        registry_id = ExGetVariable(registry_entry.runtime_key)
        if registry_id ~= nil and interceptor_id == registry_id and
           ExGetVariable(registry_entry.state_key) == "Peaceful" then

            registry_debug_key = registry_entry.name .. "InterceptDebug"
            if ExGetVariable(registry_debug_key) ~= 1 then
                ExSetVariable(registry_debug_key, 1)
                ExMessageToScreen(
                    registry_entry.name ..
                    " TEST: Peaceful intercept blocked"
                )
            end
            return 0
        end
    end
    return 1
end
