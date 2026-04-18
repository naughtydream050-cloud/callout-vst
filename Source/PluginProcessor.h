#pragma once
#include <JuceHeader.h>

class CallOutAudioProcessor : public juce::AudioProcessor
{
public:
    CallOutAudioProcessor();
    ~CallOutAudioProcessor() override = default;

    void prepareToPlay(double sampleRate, int samplesPerBlock) override;
    void releaseResources() override {}
    void processBlock(juce::AudioBuffer<float>&, juce::MidiBuffer&) override;

    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override { return true; }

    const juce::String getName() const override { return JucePlugin_Name; }
    bool acceptsMidi() const override { return false; }
    bool producesMidi() const override { return false; }
    bool isMidiEffect() const override { return false; }
    double getTailLengthSeconds() const override { return 0.0; }

    int getNumPrograms() override { return 1; }
    int getCurrentProgram() override { return 0; }
    void setCurrentProgram(int) override {}
    const juce::String getProgramName(int) override { return {}; }
    void changeProgramName(int, const juce::String&) override {}

    void getStateInformation(juce::MemoryBlock& destData) override;
    void setStateInformation(const void* data, int sizeInBytes) override;

    bool isBusesLayoutSupported(const BusesLayout& layouts) const override;

    juce::AudioProcessorValueTreeState apvts;

    // [10] Preset system
    struct Preset {
        juce::String name;
        float drive, grit, saturation, lpf, gain;
    };
    static const std::array<Preset, 4> kPresets;
    int currentPreset { 0 };

    void selectNextPreset();
    bool isLeftClipping()  const noexcept { return leftClipping.load(); }
    bool isRightClipping() const noexcept { return rightClipping.load(); }
    void resetClipLEDs()   noexcept { leftClipping = false; rightClipping = false; }

private:
    static juce::AudioProcessorValueTreeState::ParameterLayout createParameterLayout();

    double currentSampleRate { 44100.0 };
    float  lpfZ[2] { 0.0f, 0.0f };

    juce::SmoothedValue<float> driveSmooth, gritSmooth, satSmooth, gainSmooth, lpfSmooth;

    // [11] Clip detection (atomic for thread-safety)
    std::atomic<bool> leftClipping  { false };
    std::atomic<bool> rightClipping { false };

    // [12] Asymmetric saturation helper
    static float asymSat (float x, float driveAmt) noexcept;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(CallOutAudioProcessor)
};
