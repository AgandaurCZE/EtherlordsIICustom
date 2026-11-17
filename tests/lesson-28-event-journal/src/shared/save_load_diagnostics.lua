-- LESSON 23: passive save/load diagnostics.
-- Temporary Lua globals are not placed into ExSetVariable.
-- This detects initial script execution and observed state transitions.
Lesson23_LastBee = nil
Lesson23_LastGrumble = nil
Lesson23_Initialized = nil

function Lesson23_DiagnosticStep()
    lesson23_bee = ExGetVariable("BeeChoiceState")
    lesson23_grumble = ExGetVariable("GrumbleChoiceState")

    if Lesson23_Initialized == nil then
        Lesson23_Initialized = 1
        ExMessageToScreen(
            "L23 START Bee=" .. tostring(lesson23_bee)
            .. " Grumble=" .. tostring(lesson23_grumble)
            .. " Gift=" .. tostring(ExGetVariable("BeeGiftReceived"))
        )
    end

    if lesson23_bee ~= Lesson23_LastBee then
        Lesson23_LastBee = lesson23_bee
        ExMessageToScreen("L23 STATE Bee=" .. tostring(lesson23_bee))
    end

    if lesson23_grumble ~= Lesson23_LastGrumble then
        Lesson23_LastGrumble = lesson23_grumble
        ExMessageToScreen("L23 STATE Grumble=" .. tostring(lesson23_grumble))
    end
end
