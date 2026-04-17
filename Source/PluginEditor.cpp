#include "PluginEditor.h"

namespace Layout {
    constexpr int kWidth    = 420;
    constexpr int kHeight   = 420;
    constexpr int kKnobSize = 160;
    constexpr int kBuckX    =  48;   // centre 128 - radius 80
    constexpr int kBuckY    = 125;   // centre 205 - radius 80
    constexpr int kGritX    = 212;   // centre 292 - radius 80
    constexpr int kGritY    = 125;
}

// ============================================================================
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

    // SELECT button
    addAndMakeVisible (selectButton);
    selectButton.setColour (juce::TextButton::buttonColourId,   juce::Colour (0xFF333333));
    selectButton.setColour (juce::TextButton::buttonOnColourId, juce::Colour (0xFF555555));
    selectButton.setColour (juce::TextButton::textColourOffId,  juce::Colour (0xFF00FF44));
    selectButton.setColour (juce::TextButton::textColourOnId,   juce::Colour (0xFF00FF44));

    // APVTS attachments
    buckAttachment = std::make_unique<juce::AudioProcessorValueTreeState::SliderAttachment>(
        audioProcessor.apvts, "buck", buckKnob);
    gritAttachment = std::make_unique<juce::AudioProcessorValueTreeState::SliderAttachment>(
        audioProcessor.apvts, "grit", gritKnob);

    setSize (Layout::kWidth, Layout::kHeight);
    startTimerHz (10);
}

// ============================================================================
CallOutAudioProcessorEditor::~CallOutAudioProcessorEditor()
{
    // Must reset before Sliders are destroyed to avoid dangling LAF pointer
    buckKnob.setLookAndFeel (nullptr);
    gritKnob.setLookAndFeel (nullptr);
    stopTimer();
}

// ============================================================================
void CallOutAudioProcessorEditor::paint (juce::Graphics& g)
{
    // -- Background ----------------------------------------------------------
    g.fillAll (juce::Colour (0xFF1A1208));
    if (backgroundImage.isValid())
        g.drawImage (backgroundImage,
                     0, 0, getWidth(), getHeight(),
                     0, 0, backgroundImage.getWidth(), backgroundImage.getHeight(), false);

    // -- LCD area ------------------------------------------------------------
    g.setColour (juce::Colour (0xFF0A1A08));
    g.fillRoundedRectangle (60.0f, 316.0f, 300.0f, 40.0f, 4.0f);
    g.setColour (juce::Colour (0xFF00FF44));
    g.setFont   (juce::Font (18.0f, juce::Font::bold));
    g.drawText  ("ODD SPICE", 75, 318, 270, 36, juce::Justification::centred);

    // -- Clip LEDs (top-right corner) ----------------------------------------
    const auto clipCol = leftClip ? juce::Colour (0xFFFF2200) : juce::Colour (0xFF330000);
    g.setColour (clipCol);
    g.fillEllipse (365.0f, 25.0f, 12.0f, 12.0f);
    g.fillEllipse (381.0f, 25.0f, 12.0f, 12.0f);

    // -- Knob labels ---------------------------------------------------------
    g.setColour (juce::Colours::white.withAlpha (0.85f));
    g.setFont   (juce::Font (11.0f));
    g.drawText  ("DARK MELODY", 48,  285, 160, 20, juce::Justification::centred);
    g.drawText  ("GRIT",        212, 285, 160, 20, juce::Justification::centred);

    // -- Mini knob (decorative, lower-right) ---------------------------------
    {
        constexpr float mx = 390.0f, my = 345.0f, mr = 12.0f;
        g.setColour (juce::Colour (0xFF222222));
        g.fillEllipse (mx - mr, my - mr, mr * 2.0f, mr * 2.0f);
        g.setColour (juce::Colour (0xFF444444));
        g.drawEllipse (mx - mr, my - mr, mr * 2.0f, mr * 2.0f, 1.5f);
        // 12-o'clock indicator dot
        g.setColour (juce::Colour (0xFFFFAA30));
        g.fillEllipse (mx - 1.5f, my - mr * 0.72f - 1.5f, 3.0f, 3.0f);
    }
}

// ============================================================================
void CallOutAudioProcessorEditor::resized()
{
    using namespace Layout;
    buckKnob.setBounds (kBuckX, kBuckY, kKnobSize, kKnobSize);
    gritKnob.setBounds (kGritX, kGritY, kKnobSize, kKnobSize);

    selectButton.setBounds (20, 316, 38, 38);
}

// ============================================================================
void CallOutAudioProcessorEditor::timerCallback()
{
    // Refresh clip LED state (reads peak from processor in future iterations)
    leftClip  = false;
    rightClip = false;
    repaint();
}
