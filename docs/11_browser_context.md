# Browser Context — ブラウザ情報の自動取り込み口
> **Browser Use Integration Layer v1.0 (仮設)**
> Webリサーチで取得した情報を「Gemmaが要約・分類して内部ハーネスへ振り分ける」ための受け入れ口。
> 将来の Claude in Chrome / Browser Use 統合に備えた事前設計。

---

## 0. このドキュメントの目的

```
現状: Webリサーチの結果を手動でコピペ → Gemmaに渡す → docsを更新
目標: ブラウザが取得した情報を自動でGemmaに渡し、
      適切なdocsに振り分けるパイプラインを構築する
```

---

## 1. ブラウザ取得情報の分類ルール

取得した情報は必ず以下のカテゴリのいずれかに分類する。

| カテゴリ | 振り分け先 | 例 |
|---------|-----------|-----|
| **JUCE API変更** | docs/02_knob_implementation_skill.md | JUCEバージョンアップでのAPIシグネチャ変更 |
| **ビルド環境変化** | docs/08_memory_log.md → 確認後docs/02へ | 新CMakeバージョンでの挙動変更 |
| **セキュリティ情報** | docs/10_safety_guardrails.md | CVE、コンパイラ脆弱性情報 |
| **SNSトレンド** | docs/07_gemma_local_assistant.md（コピー欄） | Krump/音楽シーンの最新動向 |
| **競合プラグイン調査** | 新規 docs/12_market_research.md（将来作成） | 類似VST製品の機能・価格 |
| **技術記事・チュートリアル** | docs/08_memory_log.md（教訓候補として記録） | JUCE実装のベストプラクティス |
| **未分類** | このファイルのキューに一時保管 | 分類不能な情報 |

---

## 2. 受け入れフォーマット

ブラウザから取得した情報は以下のフォーマットでGemmaに渡す。

```
【BROWSER_CONTEXT v1.0】
取得日時: YYYY-MM-DD HH:MM
ソースURL: https://...
取得方法: [手動コピー / Browser Use自動取得]

=== RAW CONTENT ===
{ここに取得したテキスト}
=== END CONTENT ===

Gemmaへの指示:
1. 上記コンテンツをPlugin Development Harness（docs/01-10）の観点で分析してください
2. 分類カテゴリを判定してください（docs/11のルール参照）
3. 関連するdocsを特定し、追記すべき内容を抽出してください
4. docs/08_memory_log.md に新規エントリとして追加すべき教訓があれば草稿を作成してください
【END BROWSER_CONTEXT】
```

---

## 3. Gemmaによる自動振り分けフロー

```
ブラウザから情報取得
         ↓
gemma_bridge.py --mode browser で整形
（または手動でフォーマットに貼り付け）
         ↓
Gemmaが分析・分類
         ↓
振り分け結果を出力:
  [→ docs/02] 「drawRotarySlider の第3引数が JUCE 8で変更」
  [→ docs/08] 「新教訓候補: スコア 0.3」
  [→ DISCARD] 「無関係な広告コンテンツ」
         ↓
Orchestratorが振り分け結果を確認
         ↓
承認したものを対応するdocsに反映
```

---

## 4. 優先収集ターゲット（定期リサーチ推奨）

以下のURLは定期的にチェックして最新情報をハーネスに取り込む。

### 4.1 技術情報
| URL | 目的 | 頻度 |
|-----|------|------|
| `https://forum.juce.com` | JUCE APIの変更・バグ報告 | 週1回 |
| `https://github.com/juce-framework/JUCE/releases` | JUCEリリースノート | リリース時 |
| `https://cmake.org/cmake/help/latest/` | CMakeの新機能 | 月1回 |

### 4.2 マーケット情報
| URL | 目的 | 頻度 |
|-----|------|------|
| `https://www.pluginboutique.com` | 競合VST価格・機能調査 | リリース前 |
| `https://www.kvraudio.com` | KVRコミュニティのトレンド | 月1回 |

### 4.3 クリエイティブ情報
| URL | 目的 | 頻度 |
|-----|------|------|
| Instagram #krump | Krumpシーンのトレンド | 週1回 |
| Twitter/X #vst #plugin | SNSマーケティング動向 | 週1回 |

---

## 5. 一時キュー（未分類情報の仮置き場）

> ここに未分類の情報を一時保存する。次回のGemmaレビュー時に処理する。

| 日付 | ソース | 概要 | 処理状況 |
|------|--------|------|---------|
| （記録なし） | | | |

---

## 6. Browser Use 統合時の将来設計（メモ）

```
Phase 1（現在・手動）:
  Human がブラウザでURLを開く → 手動コピー → gemma_bridge.py

Phase 2（Claude in Chrome統合後）:
  Claude が自動でURLにアクセス → テキスト抽出 → Gemmaへ自動送信

Phase 3（完全自律）:
  定期スケジューラが優先URLを自動クロール
  → Gemmaが分類 → 確信度の高い知見は自動でdocsに追記
  → 人間は「承認/棄却」の判断のみ
```

---

## ドキュメント更新ログ

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2026-04-08 | v1.0 | 初版作成（仮設）|
