#include "KnobLookAndFeel.h"

// ============================================================================
//  Constructor – load knob.png from BinaryData once
// ============================================================================
KnobLookAndFeel::KnobLookAndFeel()
{
    int dataSize = 0;
    const char* data = BinaryData::getNamedResource ("knob_png", dataSize);
    if (data != nullptr && dataSize > 0)
        knobImage = juce::ImageCache::getFromMemory (data, dataSize);
}

// ============================================================================
//  drawRotarySlider
// ============================================================================
void KnobLookAndFeel::drawRotarySlider (
        juce::Graphics& g,
        int x, int y, int width, int height,
        float sliderPos,
        float rotaryStartAngle,
        float rotaryEndAngle,
        juce::Slider& /*slider*/)
{
    const float cx     = x + width  * 0.5f;
    const float cy     = y + height * 0.5f;
    const float radius = juce::jmin (width, height) * 0.5f;
    const float angle  = rotaryStartAngle + sliderPos * (rotaryEndAngle - rotaryStartAngle);

    const float knobRadius = juce::jmin (width, height) * 0.5f * 0.90f;

    // ------------------------------------------------------------------
    // Layer 1: Value arc (amber glow behind knob body)
    // ------------------------------------------------------------------
    drawValueArc (g, cx, cy, radius * 0.90f, radius * 0.10f,
                  rotaryStartAngle, angle);

    // ------------------------------------------------------------------
    // Layer 2: Knob body
    // ------------------------------------------------------------------
    if (knobImage.isValid())
    {
        const float kd = knobRadius * 2.0f;

        juce::Graphics::ScopedSaveState savedState (g);
        g.addTransform (juce::AffineTransform::rotation (angle, cx, cy));
        g.drawImage (knobImage,
                     (int) (cx - kd * 0.5f), (int) (cy - kd * 0.5f),
                     (int) kd, (int) kd,
                     0, 0, knobImage.getWidth(), knobImage.getHeight(), false);
    }
    else
    {
        // Fallback: plain dark circle
        g.setColour (juce::Colour (0xFF222222));
        g.fillEllipse (cx - knobRadius, cy - knobRadius,
                       knobRadius * 2.0f, knobRadius * 2.0f);
    }

    // ------------------------------------------------------------------
    // Layer 3: Indicator dot (always on top)
    // ------------------------------------------------------------------
    drawIndicatorDot (g, cx, cy, knobRadius, angle);
}

// ============================================================================
//  drawValueArc  — amber glow ring
// ============================================================================
void KnobLookAndFeel::drawValueArc (
        juce::Graphics& g,
        float cx, float cy,
        float arcRadius, float arcThickness,
        float startAngle, float currentAngle) const
{
    // Dark background track (full sweep)
    {
        juce::Path track;
        track.addCentredArc (cx, cy, arcRadius, arcRadius,
                             0.0f, startAngle,
                             startAngle + juce::MathConstants<float>::twoPi * 0.833f,
                             true);
        g.setColour (juce::Colour (0xFF111111));
        g.strokePath (track, juce::PathStrokeType (arcThickness,
                      juce::PathStrokeType::curved,
                      juce::PathStrokeType::rounded));
    }

    if (currentAngle <= startAngle + 0.001f)
        return;

    // Glow layers (outermost to innermost)
    for (float wm : { 3.5f, 2.2f, 1.4f })
    {
        const float alpha = (wm > 3.0f) ? 0.06f : (wm > 2.0f) ? 0.14f : 0.30f;
        juce::Path p;
        p.addCentredArc (cx, cy, arcRadius, arcRadius,
                         0.0f, startAngle, currentAngle, true);
        g.setColour (juce::Colour (0xFFFFB800).withAlpha (alpha));
        g.strokePath (p, juce::PathStrokeType (arcThickness * wm,
                      juce::PathStrokeType::curved,
                      juce::PathStrokeType::rounded));
    }

    // Solid amber arc on top
    {
        juce::Path solid;
        solid.addCentredArc (cx, cy, arcRadius, arcRadius,
                             0.0f, startAngle, currentAngle, true);
        g.setColour (juce::Colour (0xFFFFB800));
        g.strokePath (solid, juce::PathStrokeType (arcThickness * 0.55f,
                      juce::PathStrokeType::curved,
                      juce::PathStrokeType::rounded));
    }
}

// ============================================================================
//  drawIndicatorDot
// ============================================================================
void KnobLookAndFeel::drawIndicatorDot (
        juce::Graphics& g,
        float cx, float cy,
        float knobRadius,
        float angle) const
{
    const float dotRadius = knobRadius * 0.072f;
    const float dotDist   = knobRadius * 0.68f;

    const float dotX = cx + dotDist * std::sin (angle);
    const float dotY = cy - dotDist * std::cos (angle);

    // Glow halos
    struct Halo { float radiusMult; float alpha; };
    static constexpr Halo halos[] = {
        { 7.0f, 0.03f },
        { 5.0f, 0.06f },
        { 3.4f, 0.11f },
        { 2.3f, 0.21f },
        { 1.6f, 0.36f },
    };

    for (auto& h : halos)
    {
        const float r = dotRadius * h.radiusMult;
        g.setColour (juce::Colour (0xFFFF8800).withAlpha (h.alpha));
        g.fillEllipse (dotX - r, dotY - r, r * 2.0f, r * 2.0f);
    }

    // Core dot
    g.setColour (juce::Colour (0xFFFFAA30));
    g.fillEllipse (dotX - dotRadius, dotY - dotRadius,
                   dotRadius * 2.0f, dotRadius * 2.0f);

    // Specular fleck
    const float specR = dotRadius * 0.42f;
    g.setColour (juce::Colour (0x60FFFFFF));
    g.fillEllipse (dotX - dotRadius * 0.48f, dotY - dotRadius * 0.58f,
                   specR * 2.0f, specR * 2.0f);
}
