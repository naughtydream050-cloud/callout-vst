# Plugin Blueprint Template
> 新規プラグイン開発を開始する際に、このテンプレートをコピーして `docs/blueprint.md` として保存し、各項目を記入してください。
> AIへの指示はこの設計図を最初に渡すことを必須とします。

---

## セクション 1: 基本情報

| 項目 | 記入欄 |
|------|--------|
| **プラグイン名** | （例: CALLOUT） |
| **バージョン** | （例: 1.0.0） |
| **カテゴリ** | （例: Distortion / Dynamics / Reverb / Utility） |
| **フォーマット** | （例: VST3 / AU / AAX） |
| **ターゲットOS** | （例: Windows x64 / macOS Universal） |
| **GitHubリポジトリ** | （例: naughtydream050-cloud/callout-vst） |

---

## セクション 2: エフェクト概要

**一行説明**（30文字以内）:
> 例: ハードなサチュレーションとプリアンプシミュレーター

**詳細説明**（処理の流れ・音の特性・使用場面）:
```
（ここに記入）
例:
- 入力信号に 2段のウェーブシェーピングを適用し、アナログ的な倍音を付加する。
- BUCKノブで低域のプッシュ量を、GRITノブで歪みの荒さをコントロールする。
- ギター・ベース・ドラムバスでの使用を想定。
```

**DSPシグナルチェーン**:
```
Input → [Pre-Gain] → [Waveshaper] → [Tone Filter] → [Output Gain] → Output
```

---

## セクション 3: UIキャンバス

| 項目 | 値 |
|------|----|
| **キャンバス幅** | （例: 700 px） |
| **キャンバス高さ** | （例: 420 px） |
| **背景画像ファイル名** | （例: background.png） |
| **フォント** | （例: Helvetica Neue Bold） |
| **プライマリカラー** | （例: #FF9900） |
| **セカンダリカラー** | （例: #CC7700） |

**参考画像** （完成予想図のパスを記入）:
```
Resources/ui_reference.png
```

---

## セクション 4: コンポーネントリスト

> **記入ルール**:
> - `変数名`: コード内の `juce::Slider` / `juce::Button` メンバ変数名
> - `画像ファイル名`: BinaryDataに登録する画像ファイル名（拡張子込み）。なければ「なし（プロシージャル）」
> - `X` / `Y`: コンポーネント左上角の座標（px）
> - `W` / `H`: コンポーネントの幅・高さ（px）。ノブは W = H（正方形）にすること
> - `パラメータID`: APVTSに登録するID文字列

### 4.1 ロータリースライダー（ノブ）

| 変数名 | 画像ファイル名 | X | Y | W | H | パラメータID | 範囲(min/max/default) | 単位 |
|--------|-------------|---|---|---|---|------------|----------------------|------|
| buckKnob | knob.png | 38 | 80 | 230 | 230 | "buck" | 0.0 / 1.0 / 0.5 | % |
| gritKnob | knob.png | 432 | 80 | 230 | 230 | "grit" | 0.0 / 1.0 / 0.5 | % |
| （追加） | | | | | | | | |

### 4.2 リニアスライダー

| 変数名 | 画像ファイル名 | X | Y | W | H | パラメータID | 範囲(min/max/default) | 単位 |
|--------|-------------|---|---|---|---|------------|----------------------|------|
| （例: mixSlider） | なし（プロシージャル） | 300 | 350 | 200 | 24 | "mix" | 0.0 / 1.0 / 1.0 | % |
| （追加） | | | | | | | | |

### 4.3 ボタン・スイッチ

| 変数名 | 画像ファイル名(ON/OFF) | X | Y | W | H | パラメータID | デフォルト状態 |
|--------|--------------------|---|---|---|---|------------|--------------|
| （例: bypassBtn） | bypass_on.png / bypass_off.png | 650 | 20 | 30 | 30 | "bypass" | OFF |
| （追加） | | | | | | | |

### 4.4 ラベル

| 変数名 | 表示テキスト | X | Y | W | H | フォントサイズ | カラー | 役割 |
|--------|-----------|---|---|---|---|------------|-------|------|
| buckNameLabel | "BUCK" | 計算値 | 計算値 | 120 | 24 | 14pt Bold | #FF9900 | ノブ名 |
| buckValueLabel | 動的（"~50%"） | 計算値 | 計算値 | 120 | 22 | 13pt | #CC7700 | 現在値表示 |
| gritNameLabel | "GRIT" | 計算値 | 計算値 | 120 | 24 | 14pt Bold | #FF9900 | ノブ名 |
| gritValueLabel | 動的（"~50%"） | 計算値 | 計算値 | 120 | 22 | 13pt | #CC7700 | 現在値表示 |
| （追加） | | | | | | | | |

---

## セクション 5: オーディオ処理仕様

### パラメータ定義（APVTS）

```cpp
// PluginProcessor.cpp の createParameters() に追加する内容を記載
// 例:
juce::AudioParameterFloat("buck",  "Buck",  0.0f, 1.0f, 0.5f)
juce::AudioParameterFloat("grit",  "Grit",  0.0f, 1.0f, 0.5f)
// （追加）
```

### DSP処理メモ

```
（ここに記入）
例:
- processBlock() の中で buck の値を使って入力にプリゲインをかける
- grit の値を非線形カーブに変換してウェーブシェーパーに渡す
```

---

## セクション 6: 開発チェックリスト

### Step 1: UI Perfect Build
- [ ] 背景画像をBinaryDataに登録した
- [ ] すべてのコンポーネントをblueprintの座標通りに配置した
- [ ] ウィンドウサイズをblueprintに合わせた

### Step 2: Custom Knob Implementation
- [ ] `KnobLookAndFeel.h/.cpp` を作成した
- [ ] CMakeLists.txt にソースを追加した
- [ ] BinaryDataにknob画像を登録した
- [ ] 全ノブに `setLookAndFeel` を適用した
- [ ] デストラクタで `setLookAndFeel(nullptr)` を設定した

### Step 3: Core Logic
- [ ] APVTSにすべてのパラメータを登録した
- [ ] `processBlock()` にDSPを実装した
- [ ] SliderAttachmentでUI-パラメータを接続した

### Step 4: QA & Refinement
- [ ] 複数サンプルレートで確認した
- [ ] DAWでセッション保存・再読み込みを確認した
- [ ] GitHub Releaseにアーティファクトを添付した

---

## 記入例（CALLOUT プラグイン）

```
プラグイン名: CALLOUT
バージョン: 1.0.0
カテゴリ: Distortion
キャンバス: 700 x 420 px
背景: background.png

ノブ一覧:
- buckKnob | knob.png | (38, 80) | 230x230 | "buck" | 0.0-1.0 default 0.5
- gritKnob | knob.png | (432, 80) | 230x230 | "grit" | 0.0-1.0 default 0.5
```
