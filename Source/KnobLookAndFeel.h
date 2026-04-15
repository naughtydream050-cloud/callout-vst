#pragma once
#include <JuceHeader.h>

/**
 * CALLOUT Plugin – KnobLookAndFeel
 *
 * Rotary knob renderer:
 *   Layer 1: Amber value arc (glow ring)
 *   Layer 2: knob.png image rotated via AffineTransform::rotation
 *            Fallback: plain dark circle when image is unavailable
 *   Layer 3: Amber indicator dot with glow halos
 *
 * Spec: docs/02_knob_implementation_skill.md
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

    void drawValueArc     (juce::Graphics& g, float cx, float cy,
                           float arcRadius, float arcThickness,
                           float startAngle, float currentAngle) const;

    void drawIndicatorDot (juce::Graphics& g, float cx, float cy,
                           float knobRadius, float angle) const;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (KnobLookAndFeel)
};
