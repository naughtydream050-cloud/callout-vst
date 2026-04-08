#include "KnobLookAndFeel.h"

// ============================================================================
//  Constructor – try to load knob.png from BinaryData
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

    // Proportions
    const float arcRadius    = radius * 0.90f;
    const float arcThickness = radius * 0.10f;
    const float knobRadius   = radius * 0.74f;

    // ------------------------------------------------------------------
    // 1. Amber arc ring (behind everything)
    // ------------------------------------------------------------------
    drawValueArc (g, cx, cy, arcRadius, arcThickness, rotaryStartAngle, angle);

    // ------------------------------------------------------------------
    // 2. Knob body
    // ------------------------------------------------------------------
    if (knobImage.isValid())
    {
        // Image-based: rotate the PNG around the knob centre.
        // The image's "top" (12 o'clock) maps to value = 0.5 (centre angle).
        // rotaryStartAngle for this project is pi*1.25; centre = pi*2.0 = 2π.
        // We subtract pi*2 so that 12 o'clock of the image lines up with the
        // centre knob position, then add the current angle offset.
        const float centreAngle = (rotaryStartAngle + rotaryEndAngle) * 0.5f;
        const float rotAngle    = angle - centreAngle;

        const float kd = knobRadius * 2.0f;
        const float kx = cx - kd * 0.5f;
        const float ky = cy - kd * 0.5f;

        juce::Graphics::ScopedSaveState savedState (g);
        g.addTransform (juce::AffineTransform::rotation (rotAngle, cx, cy));
        g.drawImage (knobImage,
                     (int) kx, (int) ky, (int) kd, (int) kd,
                     0, 0, knobImage.getWidth(), knobImage.getHeight(), false);
    }
    else
    {
        // Procedural dark-mahogany fallback
        drawKnobBody (g, cx, cy, knobRadius);
    }

    // ------------------------------------------------------------------
    // 3. Glowing indicator dot (always drawn on top)
    // ------------------------------------------------------------------
    drawIndicatorDot (g, cx, cy, knobRadius, angle);
}

// ============================================================================
//  drawValueArc
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

    // Glow layers (outermost → innermost)
    struct Layer { float widthMult; float alpha; };
    static constexpr Layer layers[] = {
        { 4.5f, 0.04f },
        { 3.0f, 0.08f },
        { 2.0f, 0.15f },
        { 1.4f, 0.28f },
    };

    for (auto& l : layers)
    {
        juce::Path p;
        p.addCentredArc (cx, cy, arcRadius, arcRadius,
                         0.0f, startAngle, currentAngle, true);

        // Orange → yellow gradient matching the existing style
        juce::ColourGradient grad (juce::Colour (0xFFFF4400), cx - arcRadius, cy,
                                   juce::Colour (0xFFFFCC00), cx + arcRadius, cy, false);
        g.setGradientFill (grad);
        g.strokePath (p, juce::PathStrokeType (arcThickness * l.widthMult,
                      juce::PathStrokeType::curved,
                      juce::PathStrokeType::rounded));
    }

    // Solid arc on top
    {
        juce::Path p;
        p.addCentredArc (cx, cy, arcRadius, arcRadius,
                         0.0f, startAngle, currentAngle, true);
        juce::ColourGradient grad (juce::Colour (0xFFFF4400), cx - arcRadius, cy,
                                   juce::Colour (0xFFFFCC00), cx + arcRadius, cy, false);
        g.setGradientFill (grad);
        g.strokePath (p, juce::PathStrokeType (arcThickness * 0.6f,
                      juce::PathStrokeType::curved,
                      juce::PathStrokeType::rounded));
    }
}

// ============================================================================
//  drawKnobBody  (procedural – used when knob.png is not in BinaryData)
// ============================================================================
void KnobLookAndFeel::drawKnobBody (
        juce::Graphics& g,
        float cx, float cy,
        float knobRadius) const
{
    const juce::Rectangle<float> bounds (cx - knobRadius, cy - knobRadius,
                                          knobRadius * 2.0f, knobRadius * 2.0f);

    // --- Drop shadow ---
    {
        const float off = knobRadius * 0.09f;
        g.setColour (juce::Colour (0xAA000000));
        g.fillEllipse (bounds.translated (off, off * 1.5f).expanded (off * 0.4f));
    }

    // --- Outer metallic rim ---
    {
        juce::ColourGradient rim (
            juce::Colour (0xFF525252), cx - knobRadius * 0.5f, cy - knobRadius * 0.55f,
            juce::Colour (0xFF0E0E0E), cx + knobRadius * 0.5f, cy + knobRadius * 0.55f,
            false);
        g.setGradientFill (rim);
        g.fillEllipse (bounds);
    }

    // --- Main body: dark mahogany radial gradient ---
    {
        const juce::Rectangle<float> body = bounds.reduced (2.0f);

        juce::ColourGradient wood (
            juce::Colour (0xFF502B15), cx - knobRadius * 0.30f, cy - knobRadius * 0.38f,
            juce::Colour (0xFF080503), cx + knobRadius * 0.30f, cy + knobRadius * 0.48f,
            true /* radial */);
        wood.addColour (0.30, juce::Colour (0xFF2E1709));
        wood.addColour (0.65, juce::Colour (0xFF130C04));
        g.setGradientFill (wood);
        g.fillEllipse (body);

        // Wood grain lines clipped to the knob ellipse
        {
            juce::Path clip;
            clip.addEllipse (body);

            juce::Graphics::ScopedSaveState state (g);
            g.reduceClipRegion (clip);

            for (int i = -10; i <= 10; ++i)
            {
                const float t      = (float) i / 10.0f;
                const float lineY  = cy + t * knobRadius * 0.95f;
                const float drift  = (float) i * 0.28f;
                const float alpha  = 0.022f + std::abs (t) * 0.014f;

                const auto colour = (std::abs (i) % 3 == 0)
                    ? juce::Colour (0xFF3D1F0A).withAlpha (alpha * 1.7f)
                    : juce::Colour (0xFF000000).withAlpha (alpha);

                g.setColour (colour);
                g.drawLine (cx - knobRadius * 1.1f, lineY + drift,
                            cx + knobRadius * 1.1f, lineY - drift, 0.8f);
            }

            // Subtle depth rings
            for (float frac : { 0.45f, 0.78f })
            {
                const float r = knobRadius * frac;
                g.setColour (juce::Colour (0x09000000));
                g.drawEllipse (cx - r, cy - r, r * 2.0f, r * 2.0f, 1.2f);
            }
        }
    }

    // --- Specular highlight (top-left) ---
    {
        juce::ColourGradient spec (
            juce::Colour (0x22FFFFFF), cx - knobRadius * 0.20f, cy - knobRadius * 0.35f,
            juce::Colour (0x00FFFFFF), cx + knobRadius * 0.15f, cy + knobRadius * 0.18f,
            false);
        g.setGradientFill (spec);
        g.fillEllipse (bounds.reduced (3.0f));
    }

    // --- Rim highlight arc (top-left catch light) ---
    {
        juce::Path rimArc;
        rimArc.addCentredArc (cx, cy,
                              knobRadius - 1.5f, knobRadius - 1.5f,
                              0.0f,
                              juce::MathConstants<float>::pi * 1.05f,
                              juce::MathConstants<float>::pi * 1.65f,
                              true);
        g.setColour (juce::Colour (0x45888888));
        g.strokePath (rimArc, juce::PathStrokeType (1.1f));
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

    // Core
    g.setColour (juce::Colour (0xFFFFAA30));
    g.fillEllipse (dotX - dotRadius, dotY - dotRadius,
                   dotRadius * 2.0f, dotRadius * 2.0f);

    // Specular fleck
    const float specR = dotRadius * 0.42f;
    g.setColour (juce::Colour (0x60FFFFFF));
    g.fillEllipse (dotX - dotRadius * 0.48f, dotY - dotRadius * 0.58f,
                   specR * 2.0f, specR * 2.0f);
}
