# docs/13_architecture_proposal.md — アーキテクチャ提案

> ECC Trust Score: **0.90** | 作成日: 2026-04-11

---

## 1. 2026年現在の API 状況調査

### Meta / Instagram Graph API

| 項目 | 現状（2026-04） |
|------|---------------|
| トークン種別 | Short-Lived (1-2h) / Long-Lived (60日) / System User Token (無期限) |
| 投稿API | `POST /{ig-user-id}/media` → `POST /{ig-user-id}/media_publish` |
| 必要スコープ | `instagram_content_publish`, `instagram_basic` |
| App Review | `instagram_content_publish` は **本番使用に審査必須** |
| Token Refresh | Long-Lived: `GET /oauth/access_token?grant_type=ig_refresh_token` |
| System User Token | Business Manager 経由で発行、**有効期限なし**（推奨） |
| レート制限 | 200 calls / hour / user |

**推奨**: System User Token を使用することでリフレッシュ問題を根本的に解決できる。
取得は Meta Business Suite → ビジネス設定 → システムユーザー → トークン生成。

### BASE API

| 項目 | 現状（2026-04） |
|------|---------------|
| 認証方式 | OAuth 2.0 Authorization Code Grant |
| Webhook | **非対応**（ポーリング必須） |
| 商品一覧 | `GET /1/items?limit=100&order=new` |
| 商品画像 | `list_image_url`, `detail_image_url` フィールド |
| Token TTL | Access Token: 90日, Refresh Token: 180日 |
| Rate Limit | 1,000 req / day |
| ドキュメント | https://docs.thebase.in/api/ |

**重要**: BASE は Webhook を持たないため、新着商品はポーリングで検出する必要がある。

---

## 2. 実行環境比較: GitHub Actions vs 常時稼働サーバー

### Option A: GitHub Actions（推奨）

```yaml
on:
  schedule:
    - cron: '*/30 * * * *'  # 30分ごと
  workflow_dispatch:          # 手動実行も可能
```

**メリット:**
- 無料枠: publicリポジトリは無制限、privateは月2,000分（= 約66回/日の30分ジョブで十分）
- インフラ管理不要
- GitHub Secrets で認証情報を安全管理
- ログが Actions タブに自動保存される
- 既存の `callout-vst` リポジトリに追加するだけ

**デメリット:**
- 最小実行間隔が5分（Meta ポリシー）
- ジョブ起動に30-60秒のコールドスタートがある
- 正確な30分ごとは保証されない（+数分の遅延あり）

**適合度: ✅ killstreet規模には完全に十分**

### Option B: 常時稼働サーバー（Railway / Render）

**メリット:**
- Webhook受信が可能になる（BASE が対応すれば）
- リアルタイムに近い投稿タイミング

**デメリット:**
- Railway/Render 無料枠: 500時間/月 → 常時稼働には不足
- 環境変数管理が別途必要
- インフラ監視コストが発生

**適合度: ❌ 現時点では過剰設計。BASE が Webhook 対応した時点で再検討**

### 結論: **GitHub Actions で MVP 実装**

---

## 3. トークン管理設計

### System User Token フロー（推奨）

```
[初回セットアップ - 手動]
Meta Business Suite
  → ビジネス設定
    → システムユーザー
      → 「管理者」ロールで作成
        → 「新しいトークンを生成」
          → instagram_content_publish, instagram_basic を選択
            → トークンをコピー
              → GitHub Secrets に INSTAGRAM_TOKEN として登録
```

System User Token は**期限なし**なので、以後のリフレッシュは不要。

### Long-Lived Token フロー（代替）

```
[初回]
Short-Lived Token（Graph Explorer）
  → GET /oauth/access_token?grant_type=fb_exchange_token
    → Long-Lived Token（60日）
      → GitHub Secrets に INSTAGRAM_TOKEN として登録

[58日ごとに自動実行]
check_token_health.py
  → 残り < 15日を検出
    → GET /oauth/access_token?grant_type=ig_refresh_token
      → 新しいトークン取得
        → gh secret set INSTAGRAM_TOKEN --body "新トークン"（要 GH_TOKEN 権限）
```

---

## 4. GitHub Secrets 設定一覧

| Secret 名 | 内容 | 取得場所 |
|-----------|------|---------|
| `INSTAGRAM_TOKEN` | System User Token または Long-Lived Token | Meta Business Suite / Graph Explorer |
| `IG_USER_ID` | Instagram Business アカウントのユーザーID | Graph Explorer: `GET /me?fields=id` |
| `META_APP_ID` | Meta App の App ID | developers.facebook.com → My Apps |
| `META_APP_SECRET` | Meta App の App Secret | 同上 → Settings → Basic |
| `BASE_ACCESS_TOKEN` | BASE API アクセストークン | BASE Developers → OAuth認証フロー |
| `BASE_SHOP_ID` | killstreet のショップID | BASE 管理画面 → ショップ情報 |

---

## 5. MVP ロードマップ

### Phase 1（現在）: 基本投稿
- [x] docs/12 Post-Mortem 完成
- [x] docs/13 アーキテクチャ提案
- [ ] System User Token 取得（手動）
- [ ] GitHub Secrets 設定（手動）
- [ ] `scripts/insta_base_sync.py` の `# TODO:` を実データで埋める
- [ ] `insta_sync.yml` ワークフローを push して初回テスト実行

### Phase 2（安定化）: Token Health Monitoring
- [ ] `check_token_health.py` による失効監視
- [ ] 失効15日前通知の確認
- [ ] エラーログの `docs/08_memory_log.md` への自動追記確認

### Phase 3（高度化）: Instagram Shopping
- [ ] Instagram Shopping タグ対応（商品カタログとの連携）
- [ ] Facebookページのカタログとの同期
- [ ] 商品ページへのDeepLink生成
