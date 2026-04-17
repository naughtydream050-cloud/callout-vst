#pragma once
#include <JuceHeader.h>

/**
 * CALLOUT Plugin – KnobLookAndFeel
 *
 * Rotary knob renderer:
 *   Layer 1: LED value arc — green (low) → amber (mid) → red (high)
 *            3-layer glow effect
 *   Layer 2: knob.png image rotated via AffineTransform::rotation
 *            Fallback: plain dark circle when image is unavailable
 *   Layer 3: Amber indicator dot with glow halos
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
    juce::Image knobImage;   // loaded once from BinaryData in constructor

    // sliderPos drives the colour gradient: 0→green, 0.5→amber, 1.0→red
    void drawValueArc     (juce::Graphics& g, float cx, float cy,
                           float arcRadius, float arcThickness,
                           float startAngle, float currentAngle,
                           float sliderPos) const;

    void drawIndicatorDot (juce::Graphics& g, float cx, float cy,
                           float knobRadius, float angle) const;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (KnobLookAndFeel)
};
