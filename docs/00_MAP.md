# 00_MAP.md — CallOut Project Index (Long-Term Memory)
> CTO Harness v2.0 | 生成: 2026-04-15
> **このファイルを最初に読め。他のdocsはタスクに応じてピンポイントで参照すること。**

---

## プロジェクト概要

| 項目 | 値 |
|------|---|
| リポジトリ | https://github.com/naughtydream050-cloud/callout-vst |
| ローカルパス | `C:\Users\user\OneDrive\Desktop\開発\CallOut` （日本語+OneDrive → ローカルビルド不可）|
| 安全ビルドパス | `C:\dev\CallOut` （移行スクリプト: `scripts/migrate_to_cdev.ps1`）|
| ビルド方式 | GitHub Actions 一択（CI: `.github/workflows/build.yml`）|
| アカウント | naughtydream050@gmail.com / GitHub: naughtydream050-cloud |
| 現在のStep | **Step 2 完了** — ノブ画像回転実装済み、push待ち |

---

## ハーネス・ドキュメントマップ

| ファイル | 役割 | 読む条件 |
|---------|------|---------|
| `docs/00_MAP.md` | **このファイル**。全体インデックス | セッション開始時に必読 |
| `docs/01_workflow_standard.md` | 4ステップ開発フロー・Gemmaゲート定義 | Step開始時 / フロー確認時 |
| `docs/02_knob_implementation_skill.md` | ノブ実装の完全技術仕様（JUCE） | ノブ/LookAndFeel変更時 |
| `docs/03_plugin_blueprint_template.md` | blueprint.mdのテンプレート | 新プラグイン開始時 |
| `docs/04_agent_workflow.md` | Stage 0-4のAIエージェント役割定義 | エージェント連携設計時 |
| `docs/05_ai_common_protocol.md` | Gemini/Claude間のJSON通信仕様 | Geminiとの設計連携時 |
| `docs/07_gemma_local_assistant.md` | Gemmaローカルプレ検閲の使い方 | Windsurf起動前 |
| `docs/08_memory_log.md` | **ECC教訓ログ**（信頼スコア付き） | エラー発生時・教訓記録時 |
| `docs/09_self_evaluation_harness.md` | OpenHarness採点基準（10点満点） | コードレビュー・採点時 |
| `docs/10_safety_guardrails.md` | コンパイラ警告弱体化禁止令 | ビルドエラー対処時 |
| `docs/11_browser_context.md` | ブラウザ操作コンテキスト | ブラウザ連携時 |
| `docs/12_post_mortem_report.md` | BASE×Instagram自動連携の失敗記録 | Instagram/BASE作業時（必読）|
| `docs/13_architecture_proposal.md` | BASE/Instagram APIアーキテクチャ提案 | 連携実装時 |
| `docs/14_api_minefield_map.md` | API地雷マップ | 外部API接続時 |
| `docs/gemini_context_refresher.md` | Geminiへのコンテキスト注入テンプレート | Gemini連携時 |

---

## 確定知見サマリー（ECC Trust 1.0 のみ）

| # | 教訓 | 参照 |
|---|------|------|
| 1 | `C:\Users\...\開発\...` でjuceaide.exeがクラッシュ。ASCII+OneDrive外パス必須 | docs/08 |
| 2 | MSVCは日本語コメントをSJIS誤認。`/utf-8`フラグ必須（CMakeLists.txt設定済み）| docs/08 |
| 3 | VS2026 ローカル: `-G "Visual Studio 18 2026"` / GitHub Actions: Generator省略 | docs/08 |
| 4 | GitHub PAT平文埋め込みでPush Rejection → 自動無効化 → Secrets必須 | docs/12 |
| 5 | Meta Short-Lived Token (TTL 1-2h) を自動化に使うと24時間後に403 | docs/12 |
| 6 | BASE OAuth2初回認証はブラウザ必須 → GitHub Actionsヘッドレス環境では取得不可 | docs/12 |

---

## 現在の開発状態

```
[Step 1] UI配置         ✅ 完了
[Step 2] ノブ実装       ✅ コード完成（push待ち）
[Step 3] Core DSP      ⏳ 未着手
[Step 4] QA            ⏳ 未着手
```

### push待ちファイル（未コミット）
- `Source/KnobLookAndFeel.cpp` — 画像回転方式 v3.0（AffineTransform + アンバーアーク）
- `Source/KnobLookAndFeel.h` — メソッド刷新（drawValueArc / drawIndicatorDot）
- `.github/workflows/build.yml` — Generator省略・pwsh統一・cacheキー改善
- `scripts/migrate_to_cdev.ps1` — C:\dev\CallOut 移行スクリプト
- `scripts/push_to_github.ps1` — pushワンライナースクリプト
- `docs/08_memory_log.md` — 教訓2件追記

### git操作ブロック要因
- `.git/index.lock` が残存（コードセッションのgit pushハング由来）
- 解除: `Remove-Item "C:\Users\user\OneDrive\Desktop\開発\CallOut\.git\index.lock" -Force`

---

## 欠落ファイル（要作成）

| ファイル | 優先度 | 理由 |
|---------|--------|------|
| `docs/blueprint.md` | HIGH | 正規フロー（docs/01）ではblueprint.md必須。現在未存在 |
| `PROJECT_WISDOM.md` | HIGH | セッション間永続メモリ（v2.0ハーネス要件）|
| `docs/06_*.md` | LOW | 番号欠番（意図的か不明）|

---

## 自律ループ（v2.0）の実行パラメータ

```
最大ループ数: 5
合格ライン: GitHub Actions ビルド成功（green）
失敗時: git revert で前コミットに戻し別アプローチ
Push手段: scripts/push_to_github.ps1（index.lock自動削除込み）
破壊的操作: rm -rf 等は必ずユーザー確認を求める
```

---

## 他プロジェクト（触るな）

| プロジェクト | 場所 | 状態 |
|-------------|------|------|
| SHOUT BUCK | 別リポジトリ | 現状維持 |
| VOID CHANT | 別リポジトリ | 現状維持 |
| Ghost Tape | 別リポジトリ | 現状維持 |
| Grief Sequencer | 別リポジトリ | 現状維持 |
| KILLSTREET BASE/Instagram | `callout-vst` repo内 `.github/workflows/insta_sync.yml` | 現状維持 |
