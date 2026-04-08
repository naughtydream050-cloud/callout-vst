# AI Common Protocol — AI間連携プロトコル仕様書
> **System Prompt / Orchestration Rule v1.0**
> このファイルはClaude Code（Orchestrator）とGemini（Design Partner）が共通言語で通信するためのプロトコルを定義する。
> **このファイルに定義されたJSON仕様が、全AI間の唯一の正解形式である。**

---

## 1. 基本原則

| 項目 | 規約 |
|------|------|
| **設計の権威** | Geminiが生成する `PLUGIN_DESIGN_SPEC`（JSON形式）を設計の正解とする |
| **実装の権威** | Claude Code がJSON仕様を受け取り、コードへの変換・タスク指示を行う |
| **競合時の解決** | 最新のJSONが常に優先される。変更履歴を `version` フィールドで管理する |
| **曖昧な仕様の扱い** | 実装前に必ず人間に確認を求める。推測で実装しない |

---

## 2. PLUGIN_DESIGN_SPEC — 共通JSON仕様

### 2.1 完全スキーマ定義

```json
{
  "$schema": "plugin_design_spec_v1",
  "version": "1.0.0",
  "meta": {
    "plugin_name": "string",
    "category": "Distortion | Dynamics | Reverb | Delay | Filter | Utility | Other",
    "formats": ["VST3", "AU", "AAX"],
    "targets": ["Windows-x64", "macOS-Universal"],
    "repo": "github_owner/repo_name",
    "created_by": "Gemini",
    "last_updated": "YYYY-MM-DD"
  },
  "canvas": {
    "width_px": 700,
    "height_px": 420,
    "background_image": "background.png",
    "primary_color": "#FF9900",
    "secondary_color": "#CC7700",
    "font_family": "Helvetica Neue"
  },
  "components": {
    "knobs": [
      {
        "var_name": "buckKnob",
        "param_id": "buck",
        "image_file": "knob.png",
        "x": 38,
        "y": 80,
        "width": 230,
        "height": 230,
        "range_min": 0.0,
        "range_max": 1.0,
        "default_value": 0.5,
        "unit": "%",
        "rotation": {
          "start_deg": -150,
          "end_deg": 150,
          "center_value": 0.5
        },
        "arc": {
          "enabled": true,
          "color": "#FFB800",
          "glow": true
        },
        "label": {
          "text": "BUCK",
          "offset_y": -28,
          "font_size_pt": 14,
          "bold": true,
          "color": "#FF9900"
        },
        "value_label": {
          "enabled": true,
          "offset_y_from_bottom": 8,
          "font_size_pt": 13,
          "color": "#CC7700",
          "format": "~{value}%"
        }
      }
    ],
    "sliders": [],
    "buttons": [],
    "labels": []
  },
  "dsp": {
    "signal_chain": "Input → Pre-Gain → Waveshaper → Output",
    "parameters": [
      {
        "param_id": "buck",
        "type": "float",
        "min": 0.0,
        "max": 1.0,
        "default": 0.5,
        "automatable": true,
        "smoothing_ms": 10
      }
    ]
  },
  "build": {
    "juce_path": "C:/JUCE",
    "project_path": "C:/dev/{plugin_name}",
    "cmake_extra_flags": "/utf-8",
    "resources": ["background.png", "knob.png"]
  }
}
```

### 2.2 フィールド詳細仕様

#### 座標系

```
原点 (0, 0): ウィンドウ左上
X軸: 右方向が正
Y軸: 下方向が正
単位: ピクセル（px）、整数値のみ
```

コンポーネントの座標は**左上角**を基準とする:

```
component.x = コンポーネント左上の X 座標
component.y = コンポーネント左上の Y 座標
```

ノブのバウンズは必ず **正方形**（width == height）:
```
setBounds(x, y, width, height)  // width と height は同値
```

#### 回転角マッピング（ノブ）

`rotation` フィールドは `docs/02_knob_implementation_skill.md` の数式に従って変換する:

```
degrees → radians: rad = deg * π / 180

rotation.start_deg = -150  →  startAngle = (270 + (-150)) * π/180 = π * 1.25 ≈ 3.927 rad
rotation.end_deg   = +150  →  endAngle   = (270 + (+150)) * π/180 = π * 2.75 ≈ 8.639 rad
```

変換コード:

```cpp
// PLUGIN_DESIGN_SPEC の rotation フィールドから JUCE の角度パラメータを生成
auto degToJuceRad = [](float deg) {
    return (270.0f + deg) * juce::MathConstants<float>::pi / 180.0f;
};
slider.setRotaryParameters(
    degToJuceRad(spec.rotation.start_deg),  // -150 → π*1.25
    degToJuceRad(spec.rotation.end_deg),    // +150 → π*2.75
    true
);
```

---

## 3. AI間通信プロトコル

### 3.1 Gemini → Claude Code（設計仕様の送信）

**形式**:
```
【PLUGIN_DESIGN_SPEC v1.0】
[JSONブロック]
【END SPEC】

変更点サマリー（自然言語）:
- buckKnobのサイズを200→230pxに変更
- gritKnobをX:400→432に移動
```

**Claude Code の受信後アクション**:
1. JSON を `docs/blueprint.json` として保存する
2. 変更差分を確認し、影響を受けるファイルを特定する
3. 実装タスクリストを生成して Windsurf に渡す
4. 「仕様受領・実装開始」を人間に報告する

### 3.2 Claude Code → Gemini（実装状況のフィードバック）

**形式**:
```
【IMPLEMENTATION_STATUS v1.0】
{
  "status": "completed | in_progress | blocked",
  "step": 1,
  "completed_items": ["背景画像配置", "buckKnob配置"],
  "issues": [
    {
      "type": "coordinate_mismatch",
      "description": "gritKnob の X座標が仕様432に対して実測430",
      "action_required": "仕様の再確認を求む"
    }
  ],
  "screenshot": "docs/screenshots/step1_result.png",
  "next": "Step 2 に進む準備ができています"
}
【END STATUS】
```

### 3.3 エラー報告プロトコル

```
【BUILD_ERROR v1.0】
{
  "stage": "CMake Build",
  "error_code": "MSB8066",
  "error_message": "juceaide unhandled exception",
  "suspected_cause": "日本語パス / OneDrive",
  "workaround_applied": "C:/dev/ へ移動 + /utf-8 フラグ追加",
  "result": "resolved | unresolved",
  "log_url": "https://github.com/owner/repo/actions/runs/XXXXXXX"
}
【END ERROR】
```

---

## 4. バージョン管理ルール

### 4.1 PLUGIN_DESIGN_SPEC のバージョニング

| フィールド | ルール |
|-----------|--------|
| `version` | semver 形式（major.minor.patch） |
| major | スキーマ構造の破壊的変更 |
| minor | 新フィールド追加 |
| patch | 値の修正のみ |

### 4.2 変更履歴の記録

JSON の最後に `changelog` フィールドを追記する:

```json
"changelog": [
  { "version": "1.0.0", "date": "2026-04-08", "by": "Gemini", "note": "初版" },
  { "version": "1.0.1", "date": "2026-04-09", "by": "Gemini", "note": "gritKnob X座標修正: 400→432" }
]
```

---

## 5. ファイル命名規約

| ファイル | 命名ルール |
|---------|-----------|
| 背景画像 | `background.png`（固定） |
| ノブ画像 | `knob.png` または `{name}_knob.png` |
| ボタン画像(ON) | `{name}_on.png` |
| ボタン画像(OFF) | `{name}_off.png` |
| 設計JSON | `docs/blueprint.json` |
| 設計図MD | `docs/blueprint.md` |
| スクリーンショット | `docs/screenshots/step{N}_{label}.png` |

**画像の解像度推奨値**:
- ノブ: 512×512 px 以上（PNG、アルファチャンネル必須）
- 背景: キャンバス実寸と同解像度

---

## 6. 禁止事項

以下の行為は全AIエージェントに禁止する:

| 禁止 | 理由 |
|------|------|
| `blueprint.json` なしに座標をハードコード | 後からの変更追跡が不可能になる |
| 座標・サイズの「大体合ってる」での実装 | UI完全再現の原則に反する |
| 回転角を `docs/02` の数式以外で計算 | 挙動の不一致が生じる |
| `KnobLookAndFeel.cpp` を `CMakeLists.txt` に追加せずにビルド | 必ずリンクエラーになる |
| デストラクタで `setLookAndFeel(nullptr)` を省略 | JUCEアサートが発生する |
