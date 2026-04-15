# docs/12_post_mortem_report.md — Post-Mortem: BASE × Instagram 自動連携

> ECC Trust Score: **0.95** | 作成日: 2026-04-11 | バージョン: 2.0

---

## 概要

BASEショップ（killstreet）とInstagramの自動連携を、過去に**10件以上のセッション**にわたって試みた。
すべての試みは最終的に動作しなかった。本ドキュメントはセッション履歴から確認できた失敗原因をECC形式で記録し、
今後の再実装における「同じ穴に落ちない」ための防衛マップを提供する。

---

## 確認済み失敗原因（証拠あり）

### F001 — GitHub トークン平文埋め込みによるPush Rejection
- **症状**: `git push` が GitHub Push Protection によって拒否される
- **セッション**: `git履歴からトークン消去`, `killstreet token-based push fix`, `auto-fix.yml 最終 push`
- **根本原因**: `ghp_pE0RmEsD51z...` 形式のPersonal Access Tokenを `.ps1` スクリプトや `.github/workflows/*.yml` にハードコード
- **被害**: リポジトリが一時的にプッシュ不能になった。GitHub が PAT を自動無効化した可能性がある
- **対策**: 全トークンを `$env:GH_TOKEN` / GitHub Secrets に移行済み（2026-04-11 callout-vst セッションで実施）
- **ECC Trust**: 1.0

### F002 — META Short-Lived Token をそのまま使用 → 24時間後に403
- **症状**: 初日は動くが翌日には `{"error": {"code": 190, "type": "OAuthException"}}` で全失敗
- **セッション**: `BASE OAuth2リフレッシュ実装` (3セッション), `BASE OAuth2 自動リフレッシュ実装`
- **根本原因**: Meta Graph API は Short-Lived Token（TTL 1〜2時間）と Long-Lived Token（TTL 60日）の区別がある。
  Graph Explorer やブラウザフローで取得したトークンは Short-Lived。自動化スクリプトは Long-Lived Token が必要
- **副次問題**: Long-Lived Token も60日で失効する。Refresh フローを実装しないと2ヶ月後に再び全停止する
- **対策**: System User Token（無期限）の使用 + 60日ごとの自動リフレッシュ実装
- **ECC Trust**: 1.0

### F003 — BASE OAuth2 認可コードの手動取得フローがボトルネック
- **症状**: スクリプトが `localhost:8080` でコールバックを待ち続けて永久にハング
- **セッション**: `BASE OAuth2 認可コード自動取得`, `localhost:8080 コード待受サーバー起動`
- **根本原因**: BASE API はOAuth2 Authorization Code Grantを採用。ブラウザリダイレクトが必要なため、
  GitHub Actions などのヘッドレス環境では初回認証コードの取得が不可能
- **影響**: CI/CD 環境への自動デプロイが構造的に不可能だった
- **対策**: 初回認証は**必ず手動で行い**、取得した Refresh Token を GitHub Secrets に保存する運用に変更
- **ECC Trust**: 1.0

### F004 — GitHub Actions の Bash コマンドがハング（インタラクティブ入力待ち）
- **症状**: `git push` ステップが60秒タイムアウトで停止し、ワークフローが常にfailure
- **セッション**: 複数の `killstreet-*` セッション
- **根本原因**: `git credential` プロンプト、または `pip install` の確認入力を待機していた
- **対策**: `git remote set-url` でトークンを URL に埋め込む方式 + `pip install --quiet` + `echo "y" | ...` 形式
- **ECC Trust**: 0.9

### F005 — `instagram_content_publish` スコープ未申請
- **症状**: `{"error": {"code": 200, "message": "Requires instagram_content_publish permission"}}`
- **セッション**: `BASE→Instagram フィード自動生成システム構築`, `killstreet-catalog-sync`
- **根本原因**: Meta App に `instagram_content_publish` パーミッションを追加しても、
  **Meta App Review** を通過しないと本番では使えない。テスト環境（自分のアカウントのみ）では動く
- **対策**: Meta App Review の申請を事前に完了させること。テスト中はテストアカウントで検証する
- **ECC Trust**: 0.95

### F006 — BASE API のレスポンス構造と仮定したフィールド名の不一致
- **症状**: `KeyError: 'product_image'` または空の画像URLが投稿される
- **セッション**: `KILLSTREET カタログ定期更新`, `スクレイパー直接実行 → API upload`
- **根本原因**: BASE API の商品レスポンスで画像フィールドは `detail_image_url` や `list_image_url` など
  複数存在し、フィールド名を間違えていた。また、画像なし商品のハンドリングが欠如していた
- **対策**: BASE API ドキュメント `https://docs.thebase.in/api/` で正確なフィールド名を確認。
  `# TODO:` マーカーでユーザーが実データで確認できるよう明示する
- **ECC Trust**: 0.85

---

## 仮説的失敗原因（証拠は薄いが発生確率が高い）

### H001 — Webhook の代替として cron を使ったが頻度不足
- BASE は Webhook をサポートしないため、30分ごとのポーリングを採用
- 新着商品が30分以内に複数登録された場合、2件目以降が重複投稿または漏れる可能性がある
- **対策**: 「最終投稿済みタイムスタンプ」を状態として保存し、次回ポーリング時のフィルタに使う

### H002 — Instagram への画像URL が一時的URLで失効
- BASE の商品画像URLは署名付き一時URLの可能性がある
- Meta Graph API は画像URLを取得してサーバー側でキャッシュするが、取得前に失効すると投稿失敗
- **対策**: 画像URLは投稿直前に取得。キャッシュしない

---

## 対策マトリクス

| 失敗ID | 重大度 | 再発確率 | 実装での対策 |
|--------|--------|----------|-------------|
| F001 | 致命的 | 高 | GitHub Secrets 必須化 |
| F002 | 致命的 | 高 | System User Token + check_token_health.py |
| F003 | 致命的 | 高 | 初回認証は手動、Refresh Token を Secrets に保存 |
| F004 | 高 | 中 | `--no-input` フラグ、URL埋め込み認証 |
| F005 | 高 | 高 | App Review 申請チェックリストを docs/13 に追記 |
| F006 | 中 | 中 | `# TODO:` マーカー + 実データ確認を必須手順化 |
| H001 | 中 | 低 | タイムスタンプ状態管理 |
| H002 | 中 | 低 | URL 取得タイミングを投稿直前に限定 |

---

## アーキテクチャフロー（防御設計込み）

```
[GitHub Actions cron: */30 * * * *]
        │
        ├─ STEP 1: check_token_health.py
        │          ├─ TOKEN DEAD   → exit(1) + docs/08 追記 + GitHub Annotation
        │          ├─ < 15 days    → ⚠️ REFRESH REQUIRED + Annotation（人間に通知）
        │          └─ OK           → 次ステップへ
        │
        ├─ STEP 2: insta_base_sync.py
        │          ├─ BASE API 新着商品取得
        │          │    └─ エラー → Dead-End Detection → docs/08 追記 → exit(1)
        │          │
        │          ├─ Instagram Graph API 投稿
        │          │    ├─ OAuthException → 不足スコープ診断 → exit(1)（リトライなし）
        │          │    └─ その他エラー → docs/08 追記 → exit(1)
        │          │
        │          └─ 全正常完了 → docs/08 に success エントリ
        │
        └─ ワークフロー完了
```

---

*このドキュメントは ECC 思想に基づき、次回エラー発生時に自動更新されること*
*参照: docs/14_api_minefield_map.md（地雷原マップ）*
