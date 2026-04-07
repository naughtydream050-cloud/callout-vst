#pragma once
#include <JuceHeader.h>
#include "PluginProcessor.h"

class CallOutLookAndFeel : public juce::LookAndFeel_V4
{
public:
    CallOutLookAndFeel()
    {
        int dataSize = 0;
        const char* data = BinaryData::getNamedResource("knob_png", dataSize);
        if (data && dataSize > 0)
            knobImage = juce::ImageCache::getFromMemory(data, dataSize);
    }
    ~CallOutLookAndFeel() override = default;

    void drawRotarySlider(juce::Graphics& g, int x, int y, int width, int height,
                          float sliderPos, float rotaryStartAngle, float rotaryEndAngle,
                          juce::Slider&) override
    {
        const float cx = x + width * 0.5f, cy = y + height * 0.5f;
        const float radius = juce::jmin(width, height) * 0.5f;
        const float angle = rotaryStartAngle + sliderPos * (rotaryEndAngle - rotaryStartAngle);
        const juce::Colour glowColour(0xFFFF8800);

        for (int i = 6; i > 0; --i) {
            const float extra = static_cast<float>(i) * 4.0f;
            g.setColour(glowColour.withAlpha(0.10f * static_cast<float>(i)));
            g.fillEllipse(cx-radius-extra, cy-radius-extra, (radius+extra)*2.0f, (radius+extra)*2.0f);
        }

        const float arcT = radius * 0.10f, arcR = radius + arcT;
        {
            juce::Path tp;
            tp.addArc(cx-arcR, cy-arcR, arcR*2, arcR*2, rotaryStartAngle, rotaryEndAngle, true);
            g.setColour(juce::Colour(0xFF1A1A1A));
            g.strokePath(tp, juce::PathStrokeType(arcT, juce::PathStrokeType::curved, juce::PathStrokeType::rounded));
        }

        if (sliderPos > 0.001f) {
            juce::Path vp;
            vp.addArc(cx-arcR, cy-arcR, arcR*2, arcR*2, rotaryStartAngle, angle, true);
            juce::PathStrokeType st(arcT, juce::PathStrokeType::curved, juce::PathStrokeType::rounded);
            juce::ColourGradient grad(juce::Colour(0xFFFF4400), cx-arcR, cy,
                                      juce::Colour(0xFFFFCC00), cx+arcR, cy, false);
            g.setGradientFill(grad);
            g.strokePath(vp, st);
            g.setColour(glowColour.withAlpha(0.25f));
            g.strokePath(vp, juce::PathStrokeType(arcT*2.5f, juce::PathStrokeType::curved, juce::PathStrokeType::rounded));
        }

        if (knobImage.isValid()) {
            const float kd = radius * 1.85f, kx = cx - kd * 0.5f, ky = cy - kd * 0.5f;
            juce::Graphics::ScopedSaveState s(g);
            g.addTransform(juce::AffineTransform::rotation(angle, cx, cy));
            g.drawImage(knobImage, (int)kx, (int)ky, (int)kd, (int)kd,
                        0, 0, knobImage.getWidth(), knobImage.getHeight(), false);
        } else {
            juce::ColourGradient grad(juce::Colour(0xFF555555), cx-radius*0.5f, cy-radius*0.5f,
                                      juce::Colour(0xFF222222), cx+radius*0.5f, cy+radius*0.5f, false);
            g.setGradientFill(grad);
            g.fillEllipse(cx-radius, cy-radius, radius*2, radius*2);
            g.setColour(glowColour);
            g.drawLine(cx + std::sin(angle)*radius*0.3f, cy - std::cos(angle)*radius*0.3f,
                       cx + std::sin(angle)*radius*0.8f, cy - std::cos(angle)*radius*0.8f, 3.0f);
        }
    }

private:
    juce::Image knobImage;
};

class CallOutAudioProcessorEditor : public juce::AudioProcessorEditor, private juce::Timer
{
public:
    CallOutAudioProcessorEditor(CallOutAudioProcessor&);
    ~CallOutAudioProcessorEditor() override;

    void paint(juce::Graphics&) override;
    void resized() override;
    void timerCallback() override;

private:
    void updateValueLabels();

    CallOutAudioProcessor& audioProcessor;
    juce::Image backgroundImage;
    CallOutLookAndFeel knobLAF;

    juce::Slider buckKnob { juce::Slider::RotaryVerticalDrag, juce::Slider::NoTextBox };
    juce::Slider gritKnob { juce::Slider::RotaryVerticalDrag, juce::Slider::NoTextBox };

    juce::Label buckNameLabel, gritNameLabel, buckValueLabel, gritValueLabel;

    std::unique_ptr<juce::AudioProcessorValueTreeState::SliderAttachment> buckAttachment, gritAttachment;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(CallOutAudioProcessorEditor)
};
