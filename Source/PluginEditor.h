#pragma once
#include <JuceHeader.h>
#include "PluginProcessor.h"
#include "KnobLookAndFeel.h"   // ← 新しいカスタムノブ

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

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (CallOutAudioProcessorEditor)
};
