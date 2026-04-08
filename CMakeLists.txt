cmake_minimum_required(VERSION 3.22)
project(CallOut VERSION 1.0.0)

add_subdirectory("C:/Users/user/OneDrive/Desktop/開発/ShoutBuck/JUCE" JUCE)

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
