#pragma once
#include <JuceHeader.h>
#include "PluginProcessor.h"

class CallOutAudioProcessorEditor : public juce::AudioProcessorEditor
{
public:
    explicit CallOutAudioProcessorEditor(CallOutAudioProcessor&);
    ~CallOutAudioProcessorEditor() override = default;

    void paint(juce::Graphics&) override;
    void resized() override {}

private:
    juce::Image backgroundImage;
    CallOutAudioProcessor& audioProcessor;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(CallOutAudioProcessorEditor)
};
