# docs/14_api_minefield_map.md — API 地雷原マップ

> ECC Trust Score: **0.95** | 作成日: 2026-04-11 | 参照元: セッション履歴 10件以上
>
> **用途**: 新しいエラーに遭遇した際、このマップを照合して過去パターンと一致するか確認し、
> 対処法を即座に適用する。新パターンは trust score 0.7 で末尾に追記すること。

---

## 地雷パターン一覧

| ID | 症状 | エラーメッセージ（代表例） | 原因 | 発生API | 対処法 | 信頼度 |
|----|------|--------------------------|------|---------|--------|--------|
| M001 | 投稿が24時間後から全て403 | `code: 190, type: OAuthException` | Short-Lived Token をそのまま使用 | Meta Graph | Long-Lived Token に交換 → 推奨はSystem User Token | 1.0 |
| M002 | `git push` が拒否される | `remote: Push cannot contain secrets` | PAT をファイルにハードコード | GitHub | `$env:GH_TOKEN` / GitHub Secrets に移行 | 1.0 |
| M003 | スクリプトが永久にハング | （タイムアウト後 killed） | OAuth認可コードのブラウザリダイレクト待機 | BASE OAuth2 | 初回認証は手動実行。Refresh Token を Secrets 保存 | 1.0 |
| M004 | ワークフローが60秒でfail | `Process timeout` | `git credential` がインタラクティブ入力待ち | GitHub Actions | URL にトークン埋め込み or `GH_TOKEN` 環境変数 | 0.9 |
| M005 | 権限エラーだが原因不明 | `code: 200, Requires instagram_content_publish` | App Review 未通過 | Meta Graph | Meta App Review 申請 → 審査中はテストアカウントのみ使用 | 0.95 |
| M006 | 画像なしで投稿される / KeyError | `KeyError: 'product_image'` | BASE API のフィールド名誤り | BASE API | 正しいフィールド: `list_image_url` / `detail_image_url` | 0.85 |
| M007 | 60日後に突然全停止 | `code: 190, Token expired` | Long-Lived Token のTTL失効 | Meta Graph | `check_token_health.py` で残り15日前にリフレッシュ | 1.0 |
| M008 | 重複投稿が発生 | （症状：Instagramに同じ商品が複数回投稿） | 最終投稿タイムスタンプの状態管理なし | BASE + Meta | `last_synced_at` をファイルまたはGist に保存して比較 | 0.8 |
| M009 | BASE API が 429 | `rate limit exceeded` | 1日1,000リクエスト制限に到達 | BASE API | バッチサイズを削減、`/1/items?limit=20` に変更 | 0.75 |
| M010 | Instagram 投稿が非公開になる | 投稿が自分にしか見えない | Instagramアカウントが個人アカウントのまま | Meta / IG | Business または Creator アカウントに変換 | 0.9 |

---

## エラーコード → パターンID マッピングテーブル

```python
# このテーブルは check_token_health.py / insta_base_sync.py で参照される
ERROR_MAP = {
    # Meta Graph API エラーコード
    190:  "M001/M007",  # OAuthException (token invalid/expired)
    200:  "M005",       # Permission error
    10:   "M005",       # Permission denied
    4:    "M009",       # Rate limit (App level)
    17:   "M009",       # Rate limit (User level)
    100:  "M006",       # Invalid parameter (フィールド名誤り)
    368:  None,         # Temporarily blocked (新パターン → M011 候補)

    # BASE API HTTP ステータス
    "base_401": "M003", # 認証失敗 (token expired or invalid)
    "base_429": "M009", # Rate limit

    # GitHub Actions
    "git_secret": "M002",   # Push protection
    "git_timeout": "M004",  # Process timeout
}
```

---

## Self-Healing Protocol（AI自律修復プロトコル）

AIが新しいエラーに遭遇したとき、以下の手順を厳守すること:

### Step 1: パターン照合
```
エラーメッセージ / HTTPステータスコード
    ↓
ERROR_MAP で検索
    ↓
一致するパターンID を特定（例: M001）
```

### Step 2: 対処法の適用
```
地雷パターン一覧の「対処法」を実行
    ↓
Trust Score ≥ 0.9 → そのまま適用
Trust Score 0.7-0.89 → ユーザーに確認してから適用
Trust Score < 0.7 → 必ずユーザーに報告し、手動対処を依頼
```

### Step 3: 新パターンの記録
```
ERROR_MAP に一致しない新しいエラーの場合:
    1. このファイルの地雷パターン一覧に新行を追加
    2. Trust Score は 0.7 から開始
    3. 同じパターンが再現したら +0.1 ずつ引き上げ
    4. 3回再現で 1.0 に格上げ
```

### Step 4: ECC メモリへの記録
```python
# docs/08_memory_log.md に以下の形式で追記:
# | 日時 | エラー概要 | 適用したパターンID | 解決したか | Trust増減 |
```

---

## 禁止事項（docs/10 Safety Guardrails 準拠）

エラー対処において以下は**絶対に行わない**:

- `continue-on-error: true` を設定してエラーを無視する ❌
- 同じエラーを5回以上リトライする ❌（Dead-End として即 exit(1)）
- 認証エラーをログに出力せずにスキップする ❌
- 新しいエラーを「一時的なもの」と判断してマップ登録をスキップする ❌

---

## 未解決パターン（要観察）

| ID | 症状 | 仮説 | 次のアクション |
|----|------|------|--------------|
| U001 | BASE の画像URLが一時的に失効 | 署名付き一時URLの可能性 | 実データで TTL を確認 |
| U002 | Instagram がキャプションを拒否 | ハッシュタグ数過多（30個制限） | キャプション生成で制限を実装 |

---

*最終更新: 2026-04-11 | 次回エラー発生時にこのマップを更新し Trust Score を調整すること*
