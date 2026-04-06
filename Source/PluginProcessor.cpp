#include "PluginProcessor.h"
#include "PluginEditor.h"

CallOutAudioProcessor::CallOutAudioProcessor()
    : AudioProcessor(BusesProperties()
          .withInput("Input",   juce::AudioChannelSet::stereo(), true)
          .withOutput("Output", juce::AudioChannelSet::stereo(), true))
{
}

bool CallOutAudioProcessor::isBusesLayoutSupported(const BusesLayout& layouts) const
{
    if (layouts.getMainOutputChannelSet() != juce::AudioChannelSet::stereo())
        return false;
    if (layouts.getMainInputChannelSet() != juce::AudioChannelSet::stereo())
        return false;
    return true;
}

void CallOutAudioProcessor::prepareToPlay(double /*sampleRate*/, int /*samplesPerBlock*/)
{
}

void CallOutAudioProcessor::processBlock(juce::AudioBuffer<float>& buffer,
                                          juce::MidiBuffer& /*midiMessages*/)
{
    juce::ScopedNoDenormals noDenormals;
    // Stereo pass-through: nothing to do
    (void)buffer;
}

juce::AudioProcessorEditor* CallOutAudioProcessor::createEditor()
{
    return new CallOutAudioProcessorEditor(*this);
}

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter()
{
    return new CallOutAudioProcessor();
}
