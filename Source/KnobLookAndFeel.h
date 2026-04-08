#pragma once
#include <JuceHeader.h>

/**
 * CALLOUT Plugin – KnobLookAndFeel
 *
 * Rotary knob renderer with:
 *   - BinaryData (knob.png) image-based rendering when the resource is present
 *   - Procedural dark-mahogany wood-grain fallback when the image is absent
 *   - Glowing amber arc ring (value indicator)
 *   - Glowing amber indicator dot
 *
 * Drop this file next to PluginEditor.h and add both to the Projucer source list.
 * knob.png must be registered in the Projucer Resources tab for image-based rendering.
 */
class KnobLookAndFeel : public juce::LookAndFeel_V4
{
public:
    KnobLookAndFeel();
    ~KnobLookAndFeel() override = default;

    void drawRotarySlider (juce::Graphics& g,
                           int x, int y, int width, int height,
                           float sliderPosProportional,
                           float rotaryStartAngle,
                           float rotaryEndAngle,
                           juce::Slider& slider) override;

private:
    // Loaded once in the constructor from BinaryData (may be invalid)
    juce::Image knobImage;

    // Sub-draw helpers ---------------------------------------------------
    void drawValueArc    (juce::Graphics& g, float cx, float cy,
                          float arcRadius, float arcThickness,
                          float startAngle, float currentAngle) const;

    void drawKnobBody    (juce::Graphics& g, float cx, float cy,
                          float knobRadius) const;

    void drawIndicatorDot(juce::Graphics& g, float cx, float cy,
                          float knobRadius, float angle) const;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (KnobLookAndFeel)
};
