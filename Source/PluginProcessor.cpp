#include "PluginProcessor.h"
#include "PluginEditor.h"

juce::AudioProcessorValueTreeState::ParameterLayout CallOutAudioProcessor::createParameterLayout()
{
    juce::AudioProcessorValueTreeState::ParameterLayout layout;
    layout.add(std::make_unique<juce::AudioParameterFloat>(
        juce::ParameterID("buck", 1), "Buck", 0.0f, 1.0f, 0.5f));
    layout.add(std::make_unique<juce::AudioParameterFloat>(
        juce::ParameterID("grit", 1), "Grit", 0.0f, 1.0f, 0.5f));
    layout.add(std::make_unique<juce::AudioParameterFloat>(
        juce::ParameterID("drive", 1), "Drive", 0.0f, 1.0f, 0.55f));
    layout.add(std::make_unique<juce::AudioParameterFloat>(
        juce::ParameterID("saturation", 1), "Saturation", 0.0f, 1.0f, 0.50f));
    layout.add(std::make_unique<juce::AudioParameterFloat>(
        juce::ParameterID("lpf", 1), "LPF Freq", 20.0f, 20000.0f, 8000.0f));
    layout.add(std::make_unique<juce::AudioParameterFloat>(
        juce::ParameterID("gain", 1), "Gain", -12.0f, 12.0f, 0.0f));
    return layout;
}

CallOutAudioProcessor::CallOutAudioProcessor()
    : AudioProcessor(BusesProperties()
          .withInput("Input",   juce::AudioChannelSet::stereo(), true)
          .withOutput("Output", juce::AudioChannelSet::stereo(), true)),
      apvts(*this, nullptr, "Parameters", createParameterLayout())
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

void CallOutAudioProcessor::prepareToPlay(double sampleRate, int /*samplesPerBlock*/)
{
    currentSampleRate = sampleRate;
    lpfZ[0] = lpfZ[1] = 0.0f;

    const double smoothTime = 0.02;
    driveSmooth.reset(sampleRate, smoothTime);
    gritSmooth .reset(sampleRate, smoothTime);
    satSmooth  .reset(sampleRate, smoothTime);
    gainSmooth .reset(sampleRate, smoothTime);
    lpfSmooth  .reset(sampleRate, smoothTime);

    driveSmooth.setCurrentAndTargetValue(*apvts.getRawParameterValue("drive"));
    gritSmooth .setCurrentAndTargetValue(*apvts.getRawParameterValue("grit"));
    satSmooth  .setCurrentAndTargetValue(*apvts.getRawParameterValue("saturation"));
    gainSmooth .setCurrentAndTargetValue(*apvts.getRawParameterValue("gain"));
    lpfSmooth  .setCurrentAndTargetValue(*apvts.getRawParameterValue("lpf"));
}

// [10] Preset table
const std::array<CallOutAudioProcessor::Preset, 4> CallOutAudioProcessor::kPresets = {{
    { "ODD SPICE",  0.55f, 0.30f, 0.50f,  8000.0f,  0.0f },
    { "DARK SOUL",  0.85f, 0.20f, 0.80f,  5000.0f, -2.0f },
    { "GRIT GRIND", 0.70f, 0.85f, 0.60f, 12000.0f,  1.0f },
    { "CLEAN PUSH", 0.25f, 0.05f, 0.20f, 18000.0f,  3.0f }
}};

void CallOutAudioProcessor::selectNextPreset()
{
    currentPreset = (currentPreset + 1) % (int)kPresets.size();
    const auto& p = kPresets[(size_t)currentPreset];

    if (auto* d  = apvts.getRawParameterValue("drive"))     d ->store(p.drive,      std::memory_order_relaxed);
    if (auto* g  = apvts.getRawParameterValue("grit"))      g ->store(p.grit,       std::memory_order_relaxed);
    if (auto* s  = apvts.getRawParameterValue("saturation"))s ->store(p.saturation, std::memory_order_relaxed);
    if (auto* l  = apvts.getRawParameterValue("lpf"))       l ->store(p.lpf,        std::memory_order_relaxed);
    if (auto* gn = apvts.getRawParameterValue("gain"))      gn->store(p.gain,       std::memory_order_relaxed);
}

// [12] 非対称飽和ヘルパー
float CallOutAudioProcessor::asymSat (float x, float driveAmt) noexcept
{
    // 正側: tanh（ソフトサチュレーション）
    // 負側: より浅いtanh（非対称 = ハーモニックリッチ）
    if (x >= 0.0f)
        return std::tanh(driveAmt * x);
    else
        return std::tanh(0.65f * driveAmt * x);
}

void CallOutAudioProcessor::processBlock (juce::AudioBuffer<float>& buffer,
                                           juce::MidiBuffer& /*midiMessages*/)
{
    juce::ScopedNoDenormals noDenormals;
    const int numCh      = buffer.getNumChannels();
    const int numSamples = buffer.getNumSamples();

    // SmoothedValueのターゲットをAPVTSから更新
    driveSmooth.setTargetValue(*apvts.getRawParameterValue("drive"));
    gritSmooth .setTargetValue(*apvts.getRawParameterValue("grit"));
    satSmooth  .setTargetValue(*apvts.getRawParameterValue("saturation"));
    gainSmooth .setTargetValue(*apvts.getRawParameterValue("gain"));
    lpfSmooth  .setTargetValue(*apvts.getRawParameterValue("lpf"));

    bool lClip = false, rClip = false;

    for (int ch = 0; ch < numCh && ch < 2; ++ch)
    {
        float* data = buffer.getWritePointer(ch);

        for (int n = 0; n < numSamples; ++n)
        {
            const float drive = driveSmooth.getNextValue();
            const float grit  = gritSmooth .getNextValue();
            const float sat   = satSmooth  .getNextValue();
            const float gain  = gainSmooth .getNextValue();

            float x   = data[n];
            float dry = x;

            // [12] 非対称飽和 (ODD SPICE)
            float asymOut = asymSat(x, 1.0f + drive * 4.0f);

            // Soft clip（従来）
            float soft = x / (1.0f + std::abs(x));

            // Hard clip
            float hard = juce::jlimit(-1.0f, 1.0f, x);

            // GRIT: ハードクリップブレンド比
            float clipped = (1.0f - grit) * soft + grit * hard;

            // Saturation: asymSat と従来クリップのブレンド
            float y = (1.0f - sat) * dry
                    + sat * ((1.0f - drive) * clipped + drive * asymOut);

            // 1-pole LPF
            const float lpfFreq = lpfSmooth.getNextValue();
            const float rc      = 1.0f / (juce::MathConstants<float>::twoPi * lpfFreq);
            const float dt      = 1.0f / (float)currentSampleRate;
            const float alpha   = dt / (rc + dt);
            lpfZ[ch] = lpfZ[ch] + alpha * (y - lpfZ[ch]);
            y = lpfZ[ch];

            // Gain (dB)
            y *= juce::Decibels::decibelsToGain(gain);

            data[n] = y;

            // [11] クリップ検出（0dBFS超過）
            if (ch == 0 && std::abs(y) >= 1.0f) lClip = true;
            if (ch == 1 && std::abs(y) >= 1.0f) rClip = true;
        }
    }

    if (lClip) leftClipping.store(true,  std::memory_order_relaxed);
    if (rClip) rightClipping.store(true, std::memory_order_relaxed);
}

void CallOutAudioProcessor::getStateInformation(juce::MemoryBlock& destData)
{
    auto state = apvts.copyState();
    std::unique_ptr<juce::XmlElement> xml(state.createXml());
    copyXmlToBinary(*xml, destData);
}

void CallOutAudioProcessor::setStateInformation(const void* data, int sizeInBytes)
{
    std::unique_ptr<juce::XmlElement> xml(getXmlFromBinary(data, sizeInBytes));
    if (xml && xml->hasTagName(apvts.state.getType()))
        apvts.replaceState(juce::ValueTree::fromXml(*xml));
}

juce::AudioProcessorEditor* CallOutAudioProcessor::createEditor()
{
    return new CallOutAudioProcessorEditor(*this);
}

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter()
{
    return new CallOutAudioProcessor();
}
