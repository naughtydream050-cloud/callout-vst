#include "PluginEditor.h"

namespace Layout {
    constexpr int kWidth    = 700;
    constexpr int kHeight   = 420;
    constexpr int kKnobSize = 230;
    constexpr int kBuckX    = 38;
    constexpr int kBuckY    = 80;
    constexpr int kGritX    = 432;
    constexpr int kGritY    = 80;
    constexpr int kNLW      = 120;
    constexpr int kNLH      = 24;
    constexpr int kNLYOff   = -28;
    constexpr int kVLW      = 120;
    constexpr int kVLH      = 22;
    constexpr int kVLYOff   = 8;
}

CallOutAudioProcessorEditor::CallOutAudioProcessorEditor (CallOutAudioProcessor& p)
    : AudioProcessorEditor (&p), audioProcessor (p)
{
    // Background image from BinaryData
    {
        int sz = 0;
        const char* d = BinaryData::getNamedResource ("background_png", sz);
        if (d && sz > 0)
            backgroundImage = juce::ImageCache::getFromMemory (d, sz);
    }

    const juce::Font bf (14.0f, juce::Font::bold);
    const juce::Font nf (13.0f);
    const juce::Colour org (0xFFFF9900), dim (0xFFCC7700);

    // Apply KnobLookAndFeel to both sliders
    buckKnob.setLookAndFeel (&knobLAF);
    gritKnob.setLookAndFeel (&knobLAF);

    // Slider setup helper
    auto sk = [&](juce::Slider& k)
    {
        k.setSliderStyle  (juce::Slider::RotaryVerticalDrag);
        k.setTextBoxStyle (juce::Slider::NoTextBox, false, 0, 0);
        k.setRange        (0.0, 1.0, 0.001);
        k.setValue        (0.5, juce::dontSendNotification);
        k.setRotaryParameters (juce::MathConstants<float>::pi * 1.25f,
                               juce::MathConstants<float>::pi * 2.75f, true);
        addAndMakeVisible (k);
    };
    sk (buckKnob);
    sk (gritKnob);

    // Name label helper
    auto snl = [&](juce::Label& l, const juce::String& t)
    {
        l.setText             (t, juce::dontSendNotification);
        l.setFont             (bf);
        l.setColour           (juce::Label::textColourId, org);
        l.setJustificationType(juce::Justification::centred);
        l.setInterceptsMouseClicks (false, false);
        addAndMakeVisible (l);
    };
    snl (buckNameLabel, "BUCK");
    snl (gritNameLabel, "GRIT");

    // Value label helper
    auto svl = [&](juce::Label& l)
    {
        l.setFont             (nf);
        l.setColour           (juce::Label::textColourId, dim);
        l.setJustificationType(juce::Justification::centred);
        l.setInterceptsMouseClicks (false, false);
        addAndMakeVisible (l);
    };
    svl (buckValueLabel);
    svl (gritValueLabel);

    // APVTS attachments
    buckAttachment = std::make_unique<juce::AudioProcessorValueTreeState::SliderAttachment>(
        audioProcessor.apvts, "buck", buckKnob);
    gritAttachment = std::make_unique<juce::AudioProcessorValueTreeState::SliderAttachment>(
        audioProcessor.apvts, "grit", gritKnob);

    setSize (Layout::kWidth, Layout::kHeight);
    updateValueLabels();
    startTimerHz (10);
}

CallOutAudioProcessorEditor::~CallOutAudioProcessorEditor()
{
    // Must reset before Sliders are destroyed to avoid dangling LAF pointer
    buckKnob.setLookAndFeel (nullptr);
    gritKnob.setLookAndFeel (nullptr);
    stopTimer();
}

void CallOutAudioProcessorEditor::paint (juce::Graphics& g)
{
    g.fillAll (juce::Colour (0xFF1A1A1A));
    if (backgroundImage.isValid())
        g.drawImage (backgroundImage,
                     0, 0, getWidth(), getHeight(),
                     0, 0, backgroundImage.getWidth(), backgroundImage.getHeight(), false);
}

void CallOutAudioProcessorEditor::resized()
{
    using namespace Layout;
    buckKnob.setBounds (kBuckX, kBuckY, kKnobSize, kKnobSize);
    gritKnob.setBounds (kGritX, kGritY, kKnobSize, kKnobSize);

    const int bCX = kBuckX + kKnobSize / 2;
    const int gCX = kGritX + kKnobSize / 2;

    buckNameLabel .setBounds (bCX - kNLW / 2, kBuckY + kNLYOff,             kNLW, kNLH);
    gritNameLabel .setBounds (gCX - kNLW / 2, kGritY + kNLYOff,             kNLW, kNLH);
    buckValueLabel.setBounds (bCX - kVLW / 2, kBuckY + kKnobSize + kVLYOff, kVLW, kVLH);
    gritValueLabel.setBounds (gCX - kVLW / 2, kGritY + kKnobSize + kVLYOff, kVLW, kVLH);
}

void CallOutAudioProcessorEditor::timerCallback()
{
    updateValueLabels();
}

void CallOutAudioProcessorEditor::updateValueLabels()
{
    auto fmt = [](const juce::Slider& s)
    {
        return "~" + juce::String (juce::roundToInt (s.getValue() * 100.0)) + "%";
    };
    buckValueLabel.setText (fmt (buckKnob), juce::dontSendNotification);
    gritValueLabel.setText (fmt (gritKnob), juce::dontSendNotification);
}
