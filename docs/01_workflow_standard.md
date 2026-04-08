# Plugin Development Workflow Standard
> **System Prompt / Internal Harness v1.1**
> このファイルはAIエージェントへの指示書として機能する。新規プラグイン開発を開始する際は必ずこの定義に従うこと。

---

## 原則

- **トークン効率最優先**: 各ステップは独立して完結可能なタスクとして定義する。前ステップが完了・承認されるまで次ステップに着手しない。
- **画像完全再現を最重要目標とする**: 特に Step 1・2 において、設計図（blueprint）の画像と1px単位で一致することをゴールとする。
- **ステップ間にチェックポイントを置く**: 各ステップ完了後、スクリーンショットまたはコードレビューを挟んで人間の承認を得る。
- **🛡️ Gemmaプレ検閲が必須**: Windsurfを起動する前に、必ずGemma（ローカルAI）のレビューを通す。詳細は `docs/07_gemma_local_assistant.md` を参照。

---

## ⚡ Gemmaプレ検閲ゲート（Step開始前の必須手順）

> **鉄則: Windsurfを起動する前に、必ずGemmaの承認を得ること。**
> 理由: Windsurfの無料枠は有限。ミスだらけの設計でWinsdurfを起動すると枠を浪費する。

```
【Gemmaゲートの流れ】

1. blueprint.md（または修正コード・エラーログ）を準備する
         ↓
2. gemma_bridge.py を実行して、Gemma用プロンプトを生成・クリップボードコピー
   python scripts/gemma_bridge.py --mode design  ← 設計検証
   python scripts/gemma_bridge.py --mode debug   ← エラーログ診断
         ↓
3. Gemmaにプロンプトを貼り付けて結果を受け取る
         ↓
4a. [PASS] → Windsurfに実装指示を出す ✅
4b. [FAIL] → 指摘を修正 → 2に戻る 🔄
```

**Gemmaを使う具体的なタイミング**:

| タイミング | チェック内容 |
|-----------|------------|
| Step 1 開始前 | blueprint.md の座標・キャンバス境界チェック |
| Step 2 開始前 | KnobLookAndFeel 仕様の確認 |
| ビルドエラー時 | エラーログの初期診断（タイポ・include漏れ） |
| リリース前 | SNS告知文の生成 |

---

## 4ステップ開発フロー（各Step前にGemmaゲートを通ること）

### Step 1 — UI Perfect Build
**目標**: 背景画像とすべてのコンポーネントの配置を完全再現する。

**入力物**:
- `blueprint.md`（設計図テンプレート: `03_plugin_blueprint_template.md` 参照）
- 背景画像ファイル（PNG/JPG）
- コンポーネント配置リスト（座標・サイズ）

**実施内容**:
1. `PluginEditor.cpp` の `paint()` で背景画像を `drawImage` でフルサイズ描画する
2. 各 `Slider`・`Button` を `setBounds(x, y, w, h)` で設計図通りに配置する
3. `addAndMakeVisible()` の呼び出し順序を描画レイヤー順（背面→前面）に合わせる
4. ウィンドウサイズを `setSize(width, height)` で blueprint に合わせる

**完了条件**:
- DAW上での表示が背景画像と目視で一致する
- リサイズ後も座標ズレが発生しない（固定サイズが原則）

**禁止事項**:
- この段階でDSP・パラメータロジックに手をつけない
- LookAndFeel のカスタマイズをここで始めない

---

### Step 2 — Custom Knob Implementation ⭐ **最重要**
**目標**: すべての可動パーツ（ノブ・スライダー等）に画像を適用し、物理的に正確な動作を実現する。

**入力物**:
- 各ノブの画像ファイル（`knob.png` など）
- 発光・アーク等のデザイン仕様（色コード・太さ）

**実施内容**:
- `KnobLookAndFeel.h/.cpp` を `02_knob_implementation_skill.md` の仕様に従って実装する
- 各 `Slider` に `setLookAndFeel(&knobLAF)` を適用する
- デストラクタで `setLookAndFeel(nullptr)` を必ず呼ぶ

**完了条件**:
- ノブを操作したとき画像が正確に回転する
- アーク・グロー等のプロシージャル演出がデザイン仕様と一致する

**技術仕様**: → `docs/02_knob_implementation_skill.md` を参照

---

### Step 3 — Core Logic
**目標**: DSP処理・パラメータ処理・プリセット等の「中身」を実装する。

**実施内容**:
1. `PluginProcessor.cpp` の `processBlock()` にDSPを実装する
2. `AudioProcessorValueTreeState`（APVTS）でパラメータを定義する
3. UIとの接続: `SliderAttachment` で値を双方向バインドする
4. 必要に応じてプリセット保存・読み込みを実装する

**完了条件**:
- 音が正しくルーティングされ、ノブ操作が音に反映される
- DAW のオートメーションレーンにパラメータが表示される

**注意**:
- このステップでUIレイアウトを変更しない（Step 1 の成果を壊さない）

---

### Step 4 — QA & Refinement
**目標**: 品質保証と最終調整。

**チェックリスト**:
- [ ] 異なるサンプルレート（44100 / 48000 / 96000）で動作確認
- [ ] バッファサイズ最小（32サンプル）で確認
- [ ] DAWでの起動・終了・セッション再読み込みが正常
- [ ] パラメータをオートメーション → ノイズ・クリック音がない
- [ ] `valgrind` または JUCE の leak detector で未解放メモリがない
- [ ] GitHub Release に .vst3 を添付してバージョンタグを打つ

---

## ステップ間コミュニケーション規則

| 状況 | AIへの指示形式 |
|------|---------------|
| 次ステップに進む | `「Step N を開始してください」` と明示する |
| 手戻りが発生した | `「Step N に戻ります。理由: ...」` と明示する |
| 設計変更が生じた | `blueprint.md` を先に更新してから指示を出す |

---

## ファイル構成規約

```
ProjectName/
├── Source/
│   ├── PluginProcessor.h/.cpp
│   ├── PluginEditor.h/.cpp
│   └── KnobLookAndFeel.h/.cpp   ← Step 2 で作成
├── Resources/
│   ├── background.png
│   └── knob.png                 ← Projucer で登録必須
├── scripts/
│   └── gemma_bridge.py          ← Gemmaプレ検閲ブリッジスクリプト
├── docs/
│   ├── 01_workflow_standard.md  ← このファイル
│   ├── 02_knob_implementation_skill.md
│   ├── 03_plugin_blueprint_template.md
│   ├── 04_agent_workflow.md
│   ├── 05_ai_common_protocol.md
│   ├── 07_gemma_local_assistant.md  ← Gemma活用定義
│   └── blueprint.md             ← プロジェクトごとの設計図
└── CMakeLists.txt
```
