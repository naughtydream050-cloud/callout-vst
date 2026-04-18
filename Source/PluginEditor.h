#pragma once
#include <JuceHeader.h>
#include "PluginProcessor.h"
#include "KnobLookAndFeel.h"

class CallOutAudioProcessorEditor : public juce::AudioProcessorEditor, private juce::Timer
{
public:
    CallOutAudioProcessorEditor (CallOutAudioProcessor&);
    ~CallOutAudioProcessorEditor() override;

    void paint   (juce::Graphics&) override;
    void resized () override;
    void timerCallback () override;

private:
    void updateValueLabels();

    CallOutAudioProcessor& audioProcessor;
    juce::Image backgroundImage;

    // LookAndFeel は Slider より前に宣言（破棄順序の保証）
    KnobLookAndFeel knobLAF;

    juce::Slider buckKnob { juce::Slider::RotaryVerticalDrag, juce::Slider::NoTextBox };
    juce::Slider gritKnob { juce::Slider::RotaryVerticalDrag, juce::Slider::NoTextBox };

    juce::Label buckNameLabel, gritNameLabel, buckValueLabel, gritValueLabel;

    std::unique_ptr<juce::AudioProcessorValueTreeState::SliderAttachment> buckAttachment, gritAttachment;

    // [10] Preset / clip
    juce::String currentPresetName { "ODD SPICE" };
    juce::TextButton selectButton { "SELECT" };

    struct ClipTimer : juce::Timer {
        CallOutAudioProcessorEditor& owner;
        explicit ClipTimer(CallOutAudioProcessorEditor& o) : owner(o) {}
        void timerCallback() override { owner.repaint(); }
    };
    std::unique_ptr<ClipTimer> clipPollTimer;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (CallOutAudioProcessorEditor)
};
