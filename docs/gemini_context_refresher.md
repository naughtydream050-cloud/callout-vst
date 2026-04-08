# Gemini Context Refresher — 自己再起動マニュアル
> **このファイルを最初に読め。**
> 新しいセッションを開始したGeminiは、このドキュメントを読むことで即座にプロジェクト全容とパートナー体制を把握し、作業を再開できる。

---

## 🔴 最重要: 現在のプロジェクト状態（毎回ここから確認）

```
プロジェクト名  : CALLOUT
バージョン      : v1.0.0（リリース済み）
GitHub URL     : https://github.com/naughtydream050-cloud/callout-vst/releases/tag/v1.0.0
ローカルパス   : C:\dev\CallOut（OneDriveを回避したASCIIパス）
ステータス      : Step 4（QA & Refinement）まで完了
次のアクション  : 新規プラグインの設計 or CALLOUT の改修
```

---

## 1. プロジェクト全容

### 1.1 CALLOUTとは何か

- **カテゴリ**: DistortionプラグインのVST3（Windows x64）
- **開発者**: よっこー（ユーザー）
- **DSP**: 2ノブ（BUCK: 低域プッシュ / GRIT: 歪み量）のウェーブシェーパー
- **UI**: 700×420 px、背景画像あり、ダークインダストリアルテイスト
- **ノブ外観**: 木目調の暗いノブ＋アンバーグロー発光リング（画像: `knob.png`）

### 1.2 解決済みの技術的課題

| 問題 | 原因 | 解決済み対策 |
|------|------|------------|
| juceaide MSB8066クラッシュ | OneDrive日本語パス | `C:\dev\CallOut` に移動 |
| 日本語コメントコンパイルエラー | MSVC SJIS誤認 | CMakeLists.txtに `/utf-8` フラグ追加 |
| VS2026でgeneratorエラー | VS2026はジェネレーター名が異なる | `"Visual Studio 18 2026"` を使用 |
| KnobLookAndFeelリンクエラー | CMakeLists.txtへの追加漏れ | `target_sources` に `.cpp` を追加済み |

---

## 2. マルチエージェント体制

### 役割分担

```
┌──────────────────────────────────────────────────────────┐
│  Human（よっこー）                                        │
│  最終意思決定・UI承認・設計方向性の決定                    │
└──────────────┬───────────────────────────────────────────┘
               │
       ┌───────┴───────┐
       ▼               ▼
┌─────────────┐  ┌─────────────────────────────────────────┐
│   Gemini    │  │   Claude Code（Orchestrator）            │
│  Design     │◄─►   実装管理・ドキュメント整備・Push・Release│
│  Partner    │  │   GitHub: naughtydream050-cloud アカウント│
└─────────────┘  └──────────────────┬──────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
             ┌──────────┐  ┌──────────────┐  ┌──────────┐
             │ Windsurf │  │ GitHub Actions│  │  Jules   │
             │ 実装者   │  │ ビルド工場    │  │デバッグ  │
             └──────────┘  └──────────────┘  └──────────┘
```

### Geminiの役割

- `PLUGIN_DESIGN_SPEC`（JSON）を生成してClaude Codeに渡す
- UIデザインの決定権を持つ（座標・色・画像・サイズ）
- `docs/05_ai_common_protocol.md` のJSON仕様に従ってデータを生成する
- 設計変更時は `version` をインクリメントして JSON を再送する

### Claude Code の役割

- OrchestratorとしてGeminiのJSONを受け取り、Windsurfへの実装指示に変換する
- ビルド管理・GitHub Push・Release作成を担当する
- `docs/` ディレクトリを最新状態に維持する

---

## 3. ドキュメント群の要約

```
docs/
├── 01_workflow_standard.md       ← 開発4ステップの定義
├── 02_knob_implementation_skill.md ← ノブ実装の技術仕様書（最重要）
├── 03_plugin_blueprint_template.md ← 新規プラグイン用設計図フォーマット
├── 04_agent_workflow.md          ← マルチエージェントパイプライン定義
├── 05_ai_common_protocol.md      ← Gemini-Claude間の共通プロトコル
└── gemini_context_refresher.md   ← このファイル（Gemini自己再起動用）
```

### 各ドキュメントの要点

**01: 4ステップワークフロー**
```
Step 1: UI Perfect Build（背景・コンポーネント配置の完全再現）
Step 2: Custom Knob Implementation ★最重要★（画像を使ったノブ実装）
Step 3: Core Logic（DSP・パラメータ処理）
Step 4: QA & Refinement（動作確認・GitHub Release）
各ステップ間に人間の承認チェックポイントあり
```

**02: ノブ実装技術仕様（Geminiが特に参照すべき内容）**
```
方式  : 1枚画像 + AffineTransform::rotation（スプライトシート不使用）
角度  : sliderPos 0.0→1.0 を rotaryStartAngle→rotaryEndAngle にマッピング
標準角: startAngle = π*1.25（7時方向）/ endAngle = π*2.75（5時方向）
JSON角度の変換式: degToJuceRad(deg) = (270 + deg) * π / 180
レイヤー順: ドロップシャドウ → アークリング → ノブ本体画像 → インジケータードット
```

**03: 設計図テンプレート**
```
Geminiが設計するとき、このテンプレートの構造をJSONで表現してClaude Codeに送る。
座標系: 左上(0,0)起点 / X右正 / Y下正 / 単位px / ノブはwidth==height（正方形）
```

**04: マルチエージェントパイプライン**
```
正常フロー: Human → Orchestrator(Claude) → Windsurf → Actions → Release
エラー時: Actions失敗 → Jules → 修正PR → merge → 再ビルド
```

**05: AI共通プロトコル**
```
JSON仕様: PLUGIN_DESIGN_SPEC v1.0
通信形式: 【PLUGIN_DESIGN_SPEC v1.0】...【END SPEC】
座標系: 左上(0,0)起点、px、整数値
回転角: docs/02の数式で変換
```

---

## 4. 共通プロトコルのクイックリファレンス

### Gemini → Claude Code への送信テンプレート

```
【PLUGIN_DESIGN_SPEC v1.0】
{
  "$schema": "plugin_design_spec_v1",
  "version": "X.Y.Z",
  "meta": {
    "plugin_name": "...",
    "category": "...",
    "formats": ["VST3"],
    "targets": ["Windows-x64"],
    "repo": "naughtydream050-cloud/...",
    "created_by": "Gemini",
    "last_updated": "YYYY-MM-DD"
  },
  "canvas": {
    "width_px": ...,
    "height_px": ...,
    "background_image": "background.png",
    "primary_color": "#......",
    "secondary_color": "#......"
  },
  "components": {
    "knobs": [
      {
        "var_name": "...",
        "param_id": "...",
        "image_file": "knob.png",
        "x": ..., "y": ...,
        "width": ..., "height": ...,
        "range_min": 0.0, "range_max": 1.0, "default_value": 0.5,
        "rotation": { "start_deg": -150, "end_deg": 150 },
        "arc": { "enabled": true, "color": "#FFB800", "glow": true },
        "label": { "text": "...", "offset_y": -28 }
      }
    ]
  },
  "dsp": { "signal_chain": "...", "parameters": [] },
  "build": {
    "juce_path": "C:/JUCE",
    "project_path": "C:/dev/{plugin_name}",
    "cmake_extra_flags": "/utf-8",
    "resources": ["background.png", "knob.png"]
  }
}
【END SPEC】
変更点: （自然言語で説明）
```

---

## 5. 環境情報（固定値）

```
OS               : Windows 11
IDE              : Visual Studio 18 2026 Community
CMake Generator  : "Visual Studio 18 2026"
JUCE             : C:\JUCE
プロジェクトRoot: C:\dev\（OneDrive外・ASCII パス必須）
GitHub アカウント: naughtydream050-cloud
GH_TOKEN        : $env:GH_TOKEN （環境変数から取得。直書き禁止）
CMake追加フラグ : /utf-8（MSVC日本語コメント対策）
```

---

## 6. 既存プラグインリスト

| プラグイン名 | カテゴリ | GitHub | ステータス |
|------------|---------|--------|-----------|
| CALLOUT | Distortion | naughtydream050-cloud/callout-vst | v1.0.0リリース済み |
| ShoutBuck | （確認中） | 別アカウントに存在 | 開発中 |
| HellRowdy | （確認中） | 別アカウントに存在 | 開発中 |
| WorldRazor | （確認中） | 別アカウントに存在 | 開発中 |

---

## 7. よくある質問（Gemini向けFAQ）

**Q: ノブの座標は中心点で指定する？左上で指定する？**
A: **左上点**で指定する。`setBounds(x, y, width, height)` の x,y が左上角。

**Q: ノブ画像は何解像度が推奨？**
A: 512×512 px 以上のPNG（アルファチャンネル必須）。

**Q: 回転角を -150〜+150度以外にしたい場合は？**
A: `PLUGIN_DESIGN_SPEC` の `rotation.start_deg` / `rotation.end_deg` を変更する。変換はClaude Codeが `docs/02` の数式で処理する。

**Q: プロジェクトのパスに日本語を使ってよいか？**
A: **絶対に使わない。** `C:\dev\{PluginName}` のASCIIパスを使うこと。

**Q: ビルドが失敗したらどうする？**
A: ビルドログURLをClaude Codeに渡す。Julesに引き渡してデバッグさせる。

---

## 8. 次のアクションの候補

- 新規プラグインの設計: `docs/03_plugin_blueprint_template.md` をコピーして記入し、JSONに変換してClaude Codeに送る
- CALLOUTの改修: 変更箇所のみを `PLUGIN_DESIGN_SPEC` の差分として送る（full JSONでも可）
- ノブデザインの変更: `knob.png` を差し替えて `version` をインクリメントした新JSONを送る

---

> **このファイルを読み込んだGeminiは、即座にOrchestratorのパートナーとして機能せよ。**
> 上記の体制・プロトコル・座標系・回転角規約をすべて把握した状態で、次の設計タスクに取り掛かること。
> 質問があれば人間（よっこー）またはClaude Code（Orchestrator）に確認してから進むこと。
