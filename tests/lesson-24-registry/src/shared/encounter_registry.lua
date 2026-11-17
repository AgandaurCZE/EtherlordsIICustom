-- LESSON 24: Lua 4 compatible encounter registry.
-- Store only callback names (strings), NOT function references in tables.
-- Lua 4 save/load can restore registry data without restoring function fields.
-- Resolve global functions dynamically with Lua 4 getglobal(name).
-- Load this module BEFORE any encounter source registers itself.
EncounterRegistry_Entries = {}
EncounterRegistry_Count = 0

function EncounterRegistry_Register(name, runtime_key, state_key,
    on_step_name, on_close_name, on_battle_name, on_preuse_name)
    EncounterRegistry_Count = EncounterRegistry_Count + 1
    EncounterRegistry_Entries[EncounterRegistry_Count] = {
        name = name,
        runtime_key = runtime_key,
        state_key = state_key,
        on_step_name = on_step_name,
        on_close_name = on_close_name,
        on_battle_name = on_battle_name,
        on_preuse_name = on_preuse_name
    }
end

-- Never store a function in an encounter entry: retrieve it from the global
-- function namespace at the moment it is needed.
function EncounterRegistry_Call(name, a, b, c)
    registry_callback = getglobal(name)
    if type(registry_callback) ~= "function" then
        ExMessageToScreen("REGISTRY ERROR: " .. tostring(name))
        return nil
    end
    return registry_callback(a, b, c)
end

function EncounterRegistry_OnStep()
    for registry_index = 1, EncounterRegistry_Count do
        registry_entry = EncounterRegistry_Entries[registry_index]
        EncounterRegistry_Call(registry_entry.on_step_name)
    end
end

function EncounterRegistry_OnCloseMessageBox(callback)
    -- Keep former behavior: each handler ignores callbacks unless
    -- its own state is "Question".
    for registry_index = 1, EncounterRegistry_Count do
        registry_entry = EncounterRegistry_Entries[registry_index]
        EncounterRegistry_Call(registry_entry.on_close_name, callback)
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
            return EncounterRegistry_Call(registry_entry.on_battle_name, attacker_id, target_id, winner_id)
        end
    end
    return 1
end

function EncounterRegistry_OnPreUse(object_id, hero_id)
    -- Preserve Lesson 23 dispatch priority: Bee before Grumble.
    for registry_index = 1, EncounterRegistry_Count do
        registry_entry = EncounterRegistry_Entries[registry_index]
        registry_answer = EncounterRegistry_Call(registry_entry.on_preuse_name, object_id, hero_id)
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
