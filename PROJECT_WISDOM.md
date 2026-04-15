# PROJECT_WISDOM.md — セッション間永続メモリ
> CTO Harness v2.0 | 初版: 2026-04-15
> **セッション開始時に 00_MAP.md の次に必ず読め。**
> 各タスク完了後、得られた教訓をECCスコア付きで追記すること。

---

## 現在の状態スナップショット（最終更新: 2026-04-15）

### プロジェクト進捗
- Step 2（ノブ実装）: コード完成。`push_to_github.ps1` 実行でGitHub Actionsビルド開始可能
- 残タスク: index.lock削除 → push → Actions green確認 → Step 3（DSP）着手

### 直近のアーキテクチャ決定
- ノブ実装: `knob.png` を `AffineTransform::rotation` で回転（画像ベース、docs/02準拠）
- バリューアーク: `0xFFFFB800`（アンバー）多層グロー、`rotaryStartAngle` から `currentAngle`
- GitHub Actions CI: Generator省略（CMakeデフォルト）、全pwsh統一

---

## ECC知見ログ（このプロジェクト固有）

### [2026-04-15] コードセッション + 日本語パス = git pushデッドロック（Trust 0.8）
- cwd に日本語文字が含まれると、コードセッションのBash/gitがハングする
- **回避策確定**: Coworkでファイル直接編集 → `push_to_github.ps1` をユーザーが手動実行

### [2026-04-15] knobImage ロードはするが描画しない（Trust 0.9）
- v2.0実装でコンストラクタでロード済みでも、`drawRotarySlider` 内の `if (knobImage.isValid())` ブランチが欠けると描画ゼロ
- **修正済み**: v3.0（現在のKnobLookAndFeel.cpp）で対応

### [2026-04-15] git index.lock 残存（Trust 0.7）
- コードセッションのgit pushがハングするとindex.lockが残留する
- **回避**: `Remove-Item ".git\index.lock" -Force` を push前に自動実行するよう push_to_github.ps1 に組み込むべき

---

## 次セッション開始時の復元コマンド

```
1. docs/00_MAP.md を読む（全体把握）
2. PROJECT_WISDOM.md を読む（このファイル、直近状態把握）
3. Source/KnobLookAndFeel.cpp の先頭コメントでバージョン確認
4. git log --oneline -3 でコミット状態確認
```
