cmake_minimum_required(VERSION 3.22)
project(CallOut VERSION 1.0.0)

# ── JUCE path resolution ──────────────────────────────────────────────────────
# Priority:
#   1. JUCE_PATH cmake variable  (-DJUCE_PATH=... on command line)
#   2. Well-known local install locations (developer machines)
#   3. FetchContent download (GitHub Actions / clean environments)
# ─────────────────────────────────────────────────────────────────────────────
set(JUCE_TAG "7.0.12")

if(DEFINED JUCE_PATH AND EXISTS "${JUCE_PATH}/CMakeLists.txt")
    message(STATUS "[JUCE] Using override path: ${JUCE_PATH}")
    add_subdirectory("${JUCE_PATH}" JUCE)
elseif(EXISTS "C:/JUCE/CMakeLists.txt")
    message(STATUS "[JUCE] Found at C:/JUCE")
    add_subdirectory("C:/JUCE" JUCE)
elseif(EXISTS "C:/dev/JUCE/CMakeLists.txt")
    message(STATUS "[JUCE] Found at C:/dev/JUCE")
    add_subdirectory("C:/dev/JUCE" JUCE)
elseif(EXISTS "C:/Users/user/OneDrive/Desktop/開発/ShoutBuck/JUCE/CMakeLists.txt")
    message(STATUS "[JUCE] Found at legacy ShoutBuck path")
    add_subdirectory("C:/Users/user/OneDrive/Desktop/開発/ShoutBuck/JUCE" JUCE)
else()
    message(STATUS "[JUCE] No local install found — fetching JUCE ${JUCE_TAG} via FetchContent")
    include(FetchContent)
    FetchContent_Declare(
        JUCE
        GIT_REPOSITORY https://github.com/juce-framework/JUCE.git
        GIT_TAG        ${JUCE_TAG}
        GIT_SHALLOW    TRUE
    )
    FetchContent_MakeAvailable(JUCE)
endif()

juce_add_plugin(CallOut
    COMPANY_NAME                "Naughty"
    PLUGIN_MANUFACTURER_CODE    "Nght"
    PLUGIN_CODE                 "CaOu"
    FORMATS                     VST3
    PRODUCT_NAME                "CALL OUT"
    IS_SYNTH                    FALSE
    NEEDS_MIDI_INPUT            FALSE
    NEEDS_MIDI_OUTPUT           FALSE
    IS_MIDI_EFFECT              FALSE
    EDITOR_WANTS_KEYBOARD_FOCUS FALSE
    COPY_PLUGIN_AFTER_BUILD     FALSE
)

juce_add_binary_data(CallOutBinaryData
    SOURCES
        Resources/background.png
        Resources/knob.png
)

juce_generate_juce_header(CallOut)

target_sources(CallOut
    PRIVATE
        Source/PluginProcessor.cpp
        Source/PluginProcessor.h
        Source/PluginEditor.cpp
        Source/PluginEditor.h
        Source/KnobLookAndFeel.cpp
        Source/KnobLookAndFeel.h
)

target_compile_definitions(CallOut
    PUBLIC
        JUCE_WEB_BROWSER=0
        JUCE_USE_CURL=0
        JUCE_VST3_CAN_REPLACE_VST2=0
)

# /utf-8: MSVC が日本語コメントを SJIS と誤認するのを防ぐ (docs/08 trust=1.0)
if(MSVC)
    target_compile_options(CallOut PRIVATE /utf-8)
endif()

target_link_libraries(CallOut
    PRIVATE
        CallOutBinaryData
        juce::juce_audio_utils
        juce::juce_audio_processors
        juce::juce_gui_basics
    PUBLIC
        juce::juce_recommended_config_flags
        juce::juce_recommended_lto_flags
        juce::juce_recommended_warning_flags
)
