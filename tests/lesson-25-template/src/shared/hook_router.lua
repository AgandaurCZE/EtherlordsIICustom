-- LESSON 24: unchanged engine API; generic registered encounter routing.
-- Five engine hooks total. No Bee or Grumble references in this file.

function Hook_OnStep()
    Lesson23_DiagnosticStep()
    EncounterRegistry_OnStep()
end

function Hook_OnCloseMessageBox(callback)
    EncounterRegistry_OnCloseMessageBox(callback)
end

function Hook_OnBattleFinishing(attacker_id, target_id, winner_id)
    return EncounterRegistry_OnBattleFinishing(
        attacker_id, target_id, winner_id
    )
end

function Hook_OnPreUse(object_id, hero_id)
    return EncounterRegistry_OnPreUse(object_id, hero_id)
end

function Hook_OnIntercept(hero_id, interceptor_id)
    return EncounterRegistry_OnIntercept(hero_id, interceptor_id)
end
