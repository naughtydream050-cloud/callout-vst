# Knob Implementation Skill — JUCE 技術仕様書
> **System Prompt / Internal Harness v1.0**
> ノブ実装は開発の最難関。このドキュメントの手順・数式から外れた実装は行わないこと。

---

## 1. クラス構造の規約

### 1.1 ファイル構成

必ず **独立したヘッダー＋実装ファイル** として切り出す。`PluginEditor.h` へのインライン定義は禁止。

```
Source/
├── KnobLookAndFeel.h    ← クラス宣言のみ
└── KnobLookAndFeel.cpp  ← 実装（drawRotarySlider を含む）
```

### 1.2 クラス宣言テンプレート

```cpp
// KnobLookAndFeel.h
#pragma once
#include <JuceHeader.h>

class KnobLookAndFeel : public juce::LookAndFeel_V4
{
public:
    KnobLookAndFeel();
    ~KnobLookAndFeel() override = default;

    void drawRotarySlider(juce::Graphics& g,
                          int x, int y, int width, int height,
                          float sliderPosProportional,
                          float rotaryStartAngle,
                          float rotaryEndAngle,
                          juce::Slider& slider) override;

private:
    juce::Image knobImage;  // BinaryData から1回だけロード

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(KnobLookAndFeel)
};
```

### 1.3 コンストラクタでの画像ロード

```cpp
KnobLookAndFeel::KnobLookAndFeel()
{
    // BinaryData から1回だけロード（キャッシュされる）
    int dataSize = 0;
    const char* data = BinaryData::getNamedResource("knob_png", dataSize);
    if (data && dataSize > 0)
        knobImage = juce::ImageCache::getFromMemory(data, dataSize);
}
```

**規約**:
- `ImageCache::getFromMemory` を使うこと（`Image::fromData` は非推奨）
- ロードはコンストラクタで1回のみ。`drawRotarySlider` 内でのロードは禁止
- `knobImage.isValid()` を常にチェックし、フォールバック描画を用意する

---

## 2. 画像回転方式（標準）

### 2.1 方針: スプライトシートは使わない

フレーム分割方式（スプライトシート）は採用しない。**1枚の画像を `AffineTransform::rotation` で回転させる**方式を標準とする。

理由:
- 画像1枚の管理で済む
- 任意の角度に対応できる（フレーム数の制約がない）
- JUCEの `drawImage` + `ScopedSaveState` で実装が完結する

### 2.2 回転描画の実装パターン

```cpp
if (knobImage.isValid())
{
    const float kd = knobRadius * 2.0f;
    const float kx = cx - kd * 0.5f;
    const float ky = cy - kd * 0.5f;

    // ① 現在のグラフィクス状態を保存
    juce::Graphics::ScopedSaveState savedState(g);

    // ② ノブ中心を軸に回転変換を適用
    //    angle は drawRotarySlider の引数から算出した「現在の回転角」
    g.addTransform(juce::AffineTransform::rotation(angle, cx, cy));

    // ③ 画像を描画（変換済み座標系で）
    g.drawImage(knobImage,
                (int)kx, (int)ky, (int)kd, (int)kd,
                0, 0, knobImage.getWidth(), knobImage.getHeight(),
                false);
    // ScopedSaveState のスコープを抜けると状態が自動復元される
}
```

**重要**: `g.addTransform()` は現在の変換に**累積**するため、必ず `ScopedSaveState` で囲むこと。

---

## 3. 回転角の標準マッピング

### 3.1 JUCE の角度規約

JUCE の `rotaryStartAngle` / `rotaryEndAngle` は **ラジアン、12時方向が 0、時計回りが正** ではなく、**3時方向から反時計回り** の数学的慣行に注意。

`juce::Slider::setRotaryParameters()` で設定する推奨値:

```cpp
// ±150度 = 合計300度の範囲（標準的なノブ）
slider.setRotaryParameters(
    juce::MathConstants<float>::pi * 1.25f,   // 開始: 225度 (7時方向)
    juce::MathConstants<float>::pi * 2.75f,   // 終了: 495度 (5時方向)
    true                                       // 時計回りで値が増加
);
```

### 3.2 sliderPos → angle の変換式

```cpp
// drawRotarySlider の引数から現在角度を算出
const float angle = rotaryStartAngle
                  + sliderPos * (rotaryEndAngle - rotaryStartAngle);
```

| `sliderPos` | 角度（ラジアン） | 見た目 |
|-------------|----------------|--------|
| 0.0         | π × 1.25 ≈ 3.93 | 7時方向 |
| 0.5         | π × 2.00 ≈ 6.28 | 12時方向 |
| 1.0         | π × 2.75 ≈ 8.64 | 5時方向 |

### 3.3 インジケータードット/マーカーの座標計算

```cpp
// ノブ中心から半径 dotDist の位置にドットを描画
const float dotDist = knobRadius * 0.68f;
const float dotX    = cx + dotDist * std::sin(angle);
const float dotY    = cy - dotDist * std::cos(angle);
```

**証明**: JUCE の angle 0 は「上（12時）」でなく「右（3時）」起点の場合がある。
上記の `sin/cos` 式は「12時が中央値」になるよう調整済み（実測で検証すること）。

---

## 4. `drawRotarySlider` のレイヤー構造（ベストプラクティス）

描画は**背面 → 前面**の順に行う。以下の順序を標準とする。

```
Layer 0: ドロップシャドウ（最背面）
Layer 1: アーク・リング（バリューインジケーター）
Layer 2: ノブ本体（画像またはプロシージャル）
Layer 3: インジケータードット / グロー（最前面）
```

### 4.1 実装テンプレート

```cpp
void KnobLookAndFeel::drawRotarySlider(
    juce::Graphics& g,
    int x, int y, int width, int height,
    float sliderPos,
    float rotaryStartAngle, float rotaryEndAngle,
    juce::Slider&)
{
    const float cx     = x + width  * 0.5f;
    const float cy     = y + height * 0.5f;
    const float radius = juce::jmin(width, height) * 0.5f;
    const float angle  = rotaryStartAngle
                       + sliderPos * (rotaryEndAngle - rotaryStartAngle);

    // ---- Layer 0: Drop shadow (optional) ----
    // g.setColour(juce::Colour(0x99000000));
    // g.fillEllipse(cx - radius + 3, cy - radius + 4, radius * 2, radius * 2);

    // ---- Layer 1: Value arc ----
    drawValueArc(g, cx, cy, radius * 0.90f, radius * 0.10f,
                 rotaryStartAngle, angle);

    // ---- Layer 2: Knob body ----
    const float knobRadius = radius * 0.74f;
    if (knobImage.isValid())
    {
        const float kd = knobRadius * 2.0f;
        juce::Graphics::ScopedSaveState s(g);
        g.addTransform(juce::AffineTransform::rotation(angle, cx, cy));
        g.drawImage(knobImage,
                    (int)(cx - kd * 0.5f), (int)(cy - kd * 0.5f),
                    (int)kd, (int)kd,
                    0, 0, knobImage.getWidth(), knobImage.getHeight(), false);
    }
    else
    {
        drawFallbackKnob(g, cx, cy, knobRadius);
    }

    // ---- Layer 3: Indicator dot ----
    drawIndicatorDot(g, cx, cy, knobRadius, angle);
}
```

### 4.2 アーク（バリューインジケーター）の描画

```cpp
void KnobLookAndFeel::drawValueArc(
    juce::Graphics& g,
    float cx, float cy,
    float arcRadius, float arcThickness,
    float startAngle, float currentAngle) const
{
    // トラック（暗色）
    juce::Path track;
    track.addCentredArc(cx, cy, arcRadius, arcRadius,
                        0.0f, startAngle,
                        startAngle + juce::MathConstants<float>::twoPi * 0.833f,
                        true);
    g.setColour(juce::Colour(0xFF111111));
    g.strokePath(track, juce::PathStrokeType(arcThickness,
                 juce::PathStrokeType::curved,
                 juce::PathStrokeType::rounded));

    if (currentAngle <= startAngle + 0.001f) return;

    // バリューアーク（グロー多層 → ソリッド）
    for (float wm : { 3.5f, 2.2f, 1.4f })
    {
        float alpha = (wm > 3.0f) ? 0.06f : (wm > 2.0f) ? 0.14f : 0.30f;
        juce::Path p;
        p.addCentredArc(cx, cy, arcRadius, arcRadius,
                        0.0f, startAngle, currentAngle, true);
        g.setColour(juce::Colour(0xFFFFB800).withAlpha(alpha));
        g.strokePath(p, juce::PathStrokeType(arcThickness * wm,
                     juce::PathStrokeType::curved,
                     juce::PathStrokeType::rounded));
    }

    // ソリッドアーク
    juce::Path solid;
    solid.addCentredArc(cx, cy, arcRadius, arcRadius,
                        0.0f, startAngle, currentAngle, true);
    g.setColour(juce::Colour(0xFFFFB800));
    g.strokePath(solid, juce::PathStrokeType(arcThickness * 0.55f,
                 juce::PathStrokeType::curved,
                 juce::PathStrokeType::rounded));
}
```

---

## 5. PluginEditor への適用ルール

### 5.1 宣言順序（必須）

```cpp
// PluginEditor.h
private:
    // ① LookAndFeel を Slider より先に宣言（破棄順序の保証）
    KnobLookAndFeel knobLAF;

    // ② Slider
    juce::Slider gainKnob;
```

### 5.2 コンストラクタでの適用

```cpp
// PluginEditor.cpp
gainKnob.setLookAndFeel(&knobLAF);
gainKnob.setRotaryParameters(
    juce::MathConstants<float>::pi * 1.25f,
    juce::MathConstants<float>::pi * 2.75f,
    true);
gainKnob.setSliderStyle(juce::Slider::RotaryVerticalDrag);
gainKnob.setTextBoxStyle(juce::Slider::NoTextBox, false, 0, 0);
```

### 5.3 デストラクタでの解除（必須）

```cpp
// PluginEditor.cpp
CallOutAudioProcessorEditor::~CallOutAudioProcessorEditor()
{
    gainKnob.setLookAndFeel(nullptr);
    // 全ての Slider に対して実施すること
}
```

---

## 6. よくある失敗と対策

| 症状 | 原因 | 対策 |
|------|------|------|
| ノブが回転しない | `drawRotarySlider` の `angle` 計算ミス | `rotaryStartAngle + sliderPos * (rotaryEndAngle - rotaryStartAngle)` を再確認 |
| 起動時にアサート | デストラクタで `nullptr` を忘れた | 全 Slider に `setLookAndFeel(nullptr)` を追加 |
| juceaide クラッシュ | パスに日本語・OneDrive | プロジェクトを `C:\dev\` 以下に移動してリビルド |
| 日本語コメントでコンパイルエラー | MSVC のエンコーディング誤認 | CMakeLists.txt に `/utf-8` フラグを追加 |
| 画像が描画されない | `knobImage.isValid()` が false | BinaryData に画像が登録されているか確認。Projucer の Resources タブを要確認 |
| 回転中心がズレる | `ScopedSaveState` なしで `addTransform` | 必ず `ScopedSaveState` で囲む |

---

## 7. CMakeLists.txt 必須設定

```cmake
# /utf-8 フラグ（日本語コメント対策）
target_compile_options(${PROJECT_NAME} PRIVATE
    $<$<CXX_COMPILER_ID:MSVC>:/utf-8>
)

# KnobLookAndFeel をソースリストに追加
target_sources(${PROJECT_NAME} PRIVATE
    Source/PluginProcessor.cpp
    Source/PluginEditor.cpp
    Source/KnobLookAndFeel.cpp   # ← 必須
)
```
