#include "PluginEditor.h"
#include "BinaryData.h"

CallOutAudioProcessorEditor::CallOutAudioProcessorEditor(CallOutAudioProcessor& p)
    : AudioProcessorEditor(&p), audioProcessor(p)
{
    backgroundImage = juce::ImageCache::getFromMemory(
        BinaryData::background_png, BinaryData::background_pngSize);

    int w = backgroundImage.getWidth();
    int h = backgroundImage.getHeight();
    if (w > 1200) { h = h * 1200 / w; w = 1200; }
    setSize(w > 0 ? w : 1093, h > 0 ? h : 612);
}

void CallOutAudioProcessorEditor::paint(juce::Graphics& g)
{
    g.drawImage(backgroundImage, getLocalBounds().toFloat());
}
