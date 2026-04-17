# PROJECT_WISDOM.md — セッション間永続メモリ
> CTO Harness v2.0 | 初版: 2026-04-15
> **セッション開始時に 00_MAP.md の次に必ず読め。**
> 各タスク完了後、得られた教訓をECCスコア付きで追記すること。

---

## 現在の状態スナップショット（最終更新: 2026-04-18）

### プロジェクト進捗
- Step 3（UI翻訳）: 完了。Actions GREEN ✅ run#24572941481
- 完了済み: input_design.png → JUCE コード完全翻訳、artifact生成確認
- 残タスク: Step 4（DSP実装）

### 直近のアーキテクチャ決定
- ノブ実装: `knob.png` を `AffineTransform::rotation` で回転（画像ベース、docs/02準拠）
- バリューアーク: green(0xFF00FF55)→amber(0xFFFFB800)→red(0xFFFF2200) スライダー値ドリブン
- GitHub Actions CI: Generator省略（CMakeデフォルト）、全pwsh統一
- UIサイズ: 420×420px、DARK MELODY(128,205)/GRIT(292,205)、LCD "ODD SPICE"、クリップLED x2、SELボタン

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

### [2026-04-18] build/ をコミットすると CI CMakeCache パス不一致で失敗（Trust 1.0）
- ローカルパス（C:/Users/user/OneDrive/…）が CMakeCache.txt に焼き込まれる
- CI runner (D:/a/…) と不一致 → `Re-run cmake with a different source directory` エラー
- **修正**: `git rm -r --cached build/` + `.gitignore` に `build/` を追加。二度とコミットするな

### [2026-04-18] PAT ファイルが UTF-16LE（BOM付き）エンコード（Trust 1.0）
- `cat` / `tr` でトークン抽出するとヌルバイトが混入して認証失敗
- **修正**: `python -c "open(...,'rb').read().decode('utf-16-le')"` で正しく抽出

### [2026-04-18] juce::FontOptions は JUCE 7.0.12 では使用禁止（Trust 1.0）
- `juce::Font(juce::FontOptions().withHeight(x).withStyle("Bold"))` はコンパイルできても CI でエラー
- **必須API**: `juce::Font(14.0f, juce::Font::bold)` / `juce::Font(11.0f)` の古いスタイルを使え

---

## 次セッション開始時の復元コマンド

```
1. docs/00_MAP.md を読む（全体把握）
2. PROJECT_WISDOM.md を読む（このファイル、直近状態把握）
3. Source/KnobLookAndFeel.cpp の先頭コメントでバージョン確認
4. git log --oneline -3 でコミット状態確認
```
