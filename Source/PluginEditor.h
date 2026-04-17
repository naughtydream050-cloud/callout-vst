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
    CallOutAudioProcessor& audioProcessor;
    juce::Image backgroundImage;

    // LookAndFeel must be declared before Sliders (destruction order)
    KnobLookAndFeel knobLAF;

    juce::Slider buckKnob { juce::Slider::RotaryVerticalDrag, juce::Slider::NoTextBox };
    juce::Slider gritKnob { juce::Slider::RotaryVerticalDrag, juce::Slider::NoTextBox };

    // [10] LCD + SELECT button
    juce::TextButton selectButton { "SEL" };

    // [11] Clip LED state
    bool leftClip  = false;
    bool rightClip = false;

    std::unique_ptr<juce::AudioProcessorValueTreeState::SliderAttachment> buckAttachment, gritAttachment;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (CallOutAudioProcessorEditor)
};
