# Safety Guardrails — 設定弱体化禁止令
> **Operational Security Standard v1.0**
> AIエージェントがエラー回避のためにコンパイラ警告・リンター設定・セキュリティ制約を
> 「緩和」することを禁止し、検知時にプロセスを即座に停止させる監視ルールの定義書。

---

## 0. なぜこれが必要か

```
【問題パターン】
ビルドエラーが出る
    → AIが「警告を無効にすれば通る」と判断
    → /W0 フラグを追加、-Wno-error を設定
    → ビルドは通る
    → 深刻なバグが警告なしに本番リリースされる

【もう一つの問題パターン】
リンクエラーが出る
    → AIが依存ライブラリの安全チェックを無効化して解決
    → セキュリティホールが生まれる

【ガードレールの目的】
「エラーを隠す」のではなく「エラーを正しく解決する」ことを強制する。
設定の弱体化は「解決策」ではなく「隠蔽」である。
```

---

## 1. 絶対禁止リスト（FORBIDDEN ACTIONS）

以下の操作は、**どんな理由があっても実行禁止**。

### 1.1 コンパイラ警告の抑制

```cmake
# ❌ 絶対禁止
target_compile_options(${PROJECT_NAME} PRIVATE /W0)
target_compile_options(${PROJECT_NAME} PRIVATE -w)
target_compile_options(${PROJECT_NAME} PRIVATE /wd4996)  # 個別警告の無効化も禁止
target_compile_options(${PROJECT_NAME} PRIVATE -Wno-everything)
target_compile_options(${PROJECT_NAME} PRIVATE -Wno-error)

# ❌ CMakeのwarning suppressionも禁止
set(CMAKE_SUPPRESS_DEVELOPER_WARNINGS ON)
```

```cpp
// ❌ コード内での警告抑制マクロも禁止
#pragma warning(disable: 4996)
#pragma warning(push, 0)
// ただし JUCE 内部のシステムヘッダー由来の警告は例外とする（後述）
```

### 1.2 リンカーの安全設定の緩和

```cmake
# ❌ 禁止
set_target_properties(... PROPERTIES LINK_FLAGS "/NODEFAULTLIB")
target_link_options(... PRIVATE -Wl,--no-as-needed)
```

### 1.3 CMakeのエラーをワーニングに格下げ

```cmake
# ❌ 禁止
cmake_policy(SET CMP0XXX OLD)  # エラーを旧動作に戻す
```

### 1.4 GitHub Actions での失敗を無視

```yaml
# ❌ 禁止
- run: cmake --build build --config Release
  continue-on-error: true  # ← これで失敗を隠すのは禁止
```

### 1.5 JUCE の Debug Assertions 無効化

```cpp
// ❌ 禁止
#define JUCE_DISABLE_ASSERTIONS 1
#define JUCE_LOG_ASSERTIONS 0
```

---

## 2. 許可リスト（ALLOWED EXCEPTIONS）

以下のみ、正当な理由付きで許可。

| 操作 | 許可条件 | 禁止条件 |
|------|---------|---------|
| `#pragma warning(push/pop)` でシステムヘッダーの警告を一時抑制 | JUCEや外部ライブラリのヘッダー include 部分のみ | 自分のコードへの適用 |
| `/utf-8` フラグ | 日本語ソースのエンコーディング修正が目的 | 警告を隠すことが目的の場合 |
| `-Wno-deprecated-declarations` | 特定のJUCE非推奨APIを使用中で、移行計画がある場合 | 移行計画なしに放置するための使用 |
| CMake minimum_required の指定 | 適切なバージョンを要求するため | エラーを回避するためにバージョンを下げる場合 |

---

## 3. 監視ルール（DETECTION RULES）

Orchestrator（Claude）またはGemmaは、以下のパターンをコードレビュー時に検出した場合、
**即座にプロセスを停止し、人間に報告すること**。

### Rule 1: /W0 または -w の検出

```
検出パターン: CMakeLists.txt または ソースファイルに /W0, /w, -w, -Wall -w が含まれる
アクション: [SAFETY_VIOLATION] を発報。ビルドを中断。修正提案を出す。
```

### Rule 2: `continue-on-error: true` の検出

```
検出パターン: GitHub Actions workflow の steps に continue-on-error: true が含まれる
アクション: [SAFETY_VIOLATION] を発報。PRのマージを停止。
```

### Rule 3: 設定ファイルの警告閾値引き下げ

```
検出パターン: .clang-tidy, .eslintrc 等で警告をエラーから外す変更
アクション: [SAFETY_VIOLATION] を発報。変更を差し戻す。
```

### Rule 4: 警告数の増加を無視したコミット

```
検出パターン: ビルドログの警告数が前回より増加しているのに、説明なしでコミット
アクション: [WARNING_ESCALATION] を発報。原因説明を要求。
```

---

## 4. SAFETY_VIOLATION 発報時のプロセス

```
[SAFETY_VIOLATION] 検出
         ↓
① 違反内容を具体的にログ出力
   例: "CMakeLists.txt:45に /W0 フラグを検出。設定弱体化禁止令(docs/10)に違反。"
         ↓
② 現在進行中のビルド・デプロイを即座に中断
         ↓
③ 人間にエスカレーション（Coworkチャットに報告）
   「[SAFETY_VIOLATION] 設定弱体化を検出しました。詳細: ...」
         ↓
④ 正当な代替手段をリスト化して提示
   「警告の原因は [XXX] です。正しい修正方法は: ...」
         ↓
⑤ 人間の明示的な承認後のみ、作業を再開
```

---

## 5. 正しいエラー解決のアプローチ

設定を弱体化させる前に、必ず以下を試すこと。

| 問題 | 設定弱体化（禁止） | 正しいアプローチ |
|------|-----------------|----------------|
| コンパイル警告が出る | /W0 で全警告を無効化 | 警告の原因となっているコードを修正する |
| JUCE の非推奨API警告 | #pragma warning(disable) | JUCE最新APIに移行する |
| リンクエラー | デフォルトライブラリを無効化 | 不足しているライブラリを正しく追加する |
| juceaideクラッシュ | ビルドステップをスキップ | プロジェクトをASCIIパスに移動する |
| Actions が失敗する | continue-on-error: true | エラーログを読んで根本原因を修正する |

---

## 6. 緊急リセット手順

もし誰かが（AIを含む）設定を弱体化させてしまった場合:

```bash
# 弱体化した設定変更を特定
git diff HEAD~1 -- CMakeLists.txt .github/workflows/

# 直前のコミットに戻す（設定ファイルのみ）
git checkout HEAD~1 -- CMakeLists.txt

# 修正コミット
git commit -m "revert: remove safety-weakening compiler flags"
```

---

## ドキュメント更新ログ

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2026-04-08 | v1.0 | 初版作成 |
