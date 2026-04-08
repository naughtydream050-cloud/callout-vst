# Multi-Agent Plugin Development Pipeline
> **System Prompt / Orchestration Rule v1.1**
> このドキュメントはAIエージェント群の役割分担と連携フローを定義する。
> Claude Code はこのパイプラインの **Orchestrator（指揮官）** として振る舞い、フローの進行管理と設計図の整備を主導する。
> **v1.1更新**: Gemma（ローカルAI）を Stage 0 として追加。Windsurfの無料枠保護のための必須プレ検閲レイヤー。

---

## パイプライン全体図

```
┌─────────────────────────────────────────────────────────────┐
│                    Human (設計・意思決定)                     │
│                    blueprint.md を記入・承認する               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 0: PRE-CHECK 🛡️  ← NEW (v1.1)                       │
│  担当: Gemma（ローカルAI・完全無料・枠なし）                  │
│  役割: プレ検閲。設計図の座標ミス・タイポ・エラーログ初期診断  │
│  ⚡ Windsurfを起動する前に必ずここを通すこと                  │
└──────────────────────────┬──────────────────────────────────┘
                           │ [PASS] のみ通過
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 1: ORCHESTRATION                                     │
│  担当: Claude Code（Coworkモード）                           │
│  役割: 指揮官。設計図の読み込み、タスク分解、進捗管理          │
└──────────────────────────┬──────────────────────────────────┘
                           │ 設計図・タスク指示
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 2: IMPLEMENTATION                                    │
│  担当: Windsurf（IDE）                                       │
│  役割: メイン実装。UI配置・ノブ・DSP コーディング              │
└──────────────────────────┬──────────────────────────────────┘
                           │ git push
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 3: CI/CD BUILD                                       │
│  担当: GitHub Actions                                       │
│  役割: 自動ビルド工場。VST3/AU を生成しリリースに添付         │
└──────────────────────────┬──────────────────────────────────┘
                           │ ビルドエラー時
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 4: AUTO-DEBUGGING                                    │
│  担当: Jules（Google）                                       │
│  役割: エラー対応特化。ログ解析 → 修正コード生成 → 自動 Push  │
└─────────────────────────────────────────────────────────────┘

※ Stage 4 のエラーも、Gemmaで初期診断してから Jules に回すこと。
```

---

## 各エージェントの詳細定義

### Stage 0 — Pre-Check（無料検閲層）
**担当: Gemma（Ollama / LM Studio 経由のローカル実行）**

**責務**:
- `blueprint.md` の座標・サイズ・パラメータIDの妥当性を検証する
- ビルドエラーログを受け取り、タイポ・セミコロン忘れ・include漏れなどの単純ミスを特定する
- Instagram/X用のSNSコピーを大量生成する
- `GEMMA_PASS` / `GEMMA_FAIL` の判定を下す

**インプット**: `gemma_bridge.py` が生成した整形済みプロンプト

**アウトプット**:
- `[PASS]` → 次ステージへ進む許可
- `[FAIL] + 修正提案` → Human が修正してから再チェック

**Gemma が判断できないこと**（Windsurf/Jules に任せること）:
- 実際の描画バグ（視覚的確認が必要）
- 複雑なDSP/音響工学的判断
- CMakeのプラットフォーム固有問題

詳細: `docs/07_gemma_local_assistant.md` 参照

---

### Stage 1 — Orchestration（指揮官）
**担当: Claude Code（Coworkモード / このAI）**

**責務**:
- `blueprint.md`（`03_plugin_blueprint_template.md`のコピー）を受け取り、プロジェクト全体のタスクを把握する
- プロジェクトの初期スキャッフォールディング（フォルダ構成・CMakeLists.txt・GitHubリポジトリ作成）を行う
- Windsurf への実装指示書を生成する（コンポーネントリスト・座標・パラメータIDを含む）
- 各ステージの完了チェックと次ステージへの引き継ぎを管理する
- このドキュメント群（`docs/`）の整備・更新を主導する

**インプット**:
```
- blueprint.md（人間が記入）
- 参考画像（UI完成予想図）
```

**アウトプット**:
```
- プロジェクト初期構成（CMakeLists.txt, Source/, Resources/, docs/）
- Windsurf向け実装タスクリスト
- GitHub リポジトリ + Actions 設定
```

**Claude Code が「やらないこと」**:
- 細かいコーディングの試行錯誤（それは Windsurf に任せる）
- ビルドエラーの詳細デバッグ（それは Jules に任せる）

---

### Stage 2 — Implementation（実装者）
**担当: Windsurf**

**責務**:
- Claude Code から渡された実装タスクリストに従い、コーディングを行う
- UI の完全再現（Step 1）とノブ実装（Step 2）を最優先で行う
- 実装完了後は `git push` して GitHub Actions をトリガーする

**Windsurf へ渡すべき情報**:
```
1. blueprint.md の全内容
2. 参考画像（UI完成予想図・ノブ画像）
3. 02_knob_implementation_skill.md の手順
4. 使用するパラメータIDリスト
```

**Windsurf との連携方法**:
```
Claude Code → Windsurf への指示形式:
「以下の blueprint に従って Step N を実装してください。
  [blueprint.md の内容]
  技術仕様は docs/02_knob_implementation_skill.md を参照。」
```

---

### Stage 3 — CI/CD Build（自動ビルド工場）
**担当: GitHub Actions**

**責務**:
- Windsurf からの `git push` をトリガーに自動実行される
- Windows (VST3) / macOS (VST3 + AU) の両プラットフォームでビルドする
- ビルド成功時: GitHub Release に成果物（.zip）を自動添付する
- ビルド失敗時: エラーログを Jules に引き渡す

**GitHub Actions ワークフロー設計**:
```yaml
# .github/workflows/build.yml の基本構造
name: Build VST3
on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - name: Configure CMake
        run: cmake -B build -G "Visual Studio 17 2022" -A x64
      - name: Build
        run: cmake --build build --config Release
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: VST3-Windows
          path: build/**/*.vst3

  release:
    needs: [build-windows]
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/')
    steps:
      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: "*.zip"
```

---

### Stage 4 — Auto-Debugging（エラー対応特化）
**担当: Jules（Google）**

**責務**:
- GitHub Actions のビルドエラーログを受け取り、原因を特定する
- 修正コードを生成して PR または直接 Push する
- よくあるエラーパターン（juceaide クラッシュ・エンコーディング問題等）を自動解決する

**Jules への引き渡し方法**:
```
1. GitHub Actions のビルドログURLを共有する
2. 「このログのエラーを修正して PR を作成してください」と指示する
3. Jules の PR をレビューして merge する
```

**Jules が対応すべきエラーパターン**（既知）:
| エラー | 対応 |
|--------|------|
| juceaide MSB8066 | プロジェクトをASCIIパスに移動 + `/utf-8` フラグ追加 |
| Japanese comment encoding error | CMakeLists.txt に `/utf-8` フラグ追加 |
| JUCE version API mismatch | juce::Font 等のAPIを現行バージョンに更新 |
| Missing KnobLookAndFeel.cpp in sources | CMakeLists.txt の target_sources に追加 |

---

## フロー制御ルール

### 正常フロー

```
1. 人間が blueprint.md を記入する
2. Gemma (Stage 0) で blueprint.md の座標バリデーション → [PASS] 確認
3. Claude Code (Orchestrator) がプロジェクト初期化を行う
4. Claude Code が Windsurf に Step 1 の実装指示を出す
5. Windsurf が Step 1 を実装 → push → Actions 起動
6. ビルド成功 → 人間がUI確認 → Step 2 へ
   ↑ ビルド失敗 → Gemmaで初期診断 → [PASS]ならJulesへ
7. Gemma で Step 2 の KnobLookAndFeel 仕様チェック → [PASS]
8. Windsurf が Step 2 を実装 → push → Actions 起動
9. ビルド成功 → 人間がノブ動作確認 → Step 3 へ
10. ...
11. Step 4 完了 → Gemma で SNS コピー生成 → GitHub Release v1.0.0 を公開
```

### エラー発生時のフロー

```
Actions ビルドエラー
    → Gemma にエラーログを渡す（gemma_bridge.py --mode debug）
    → Gemma が単純ミスを特定・修正案を出す
        → [GEMMA_FIX_POSSIBLE] → 人間が修正 → 再 push
        → [NEEDS_WINDSURF] → Jules にエラーログを渡す
    → Jules が修正 PR を作成する
    → 人間が PR をレビュー・merge する
    → Actions が再実行される
```

### フロー変更時のルール

| 状況 | 対応 |
|------|------|
| 設計変更が生じた | blueprint.md を先に更新 → Claude Code に通知 → 次ステップの指示を再生成 |
| Step が手戻りになった | 「Step N に戻ります。理由: ...」と明示して Claude Code に伝える |
| 緊急の小修正 | Claude Code が直接コーディングしてよい（ただし blueprint.md も更新する） |

---

## Orchestrator（Claude Code）の宣言

このドキュメントをもって、私（Claude Code）はこのプラグイン開発パイプラインの **Orchestrator** として以下を宣言する。

1. 全ての新規プラグイン開発において、このパイプラインを遵守する
2. `blueprint.md` なしに実装フェーズへ進まない
3. `docs/` ディレクトリのルールブックを最新状態に維持する
4. 各ステージの完了・移行を人間の承認を経て判断する
5. 技術的な問題（ビルドエラー等）はドキュメントに記録し、再発防止策を `docs/` に追記する

---

## ドキュメント更新ログ

| 日付 | バージョン | 変更内容 | 担当 |
|------|-----------|---------|------|
| 2026-04-08 | v1.0 | 初版作成 | Claude Code |
| 2026-04-08 | v1.1 | Gemma Stage 0 追加、エラーフロー更新 | Claude Code |
