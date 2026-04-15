"""
insta_base_sync.py — BASE × Instagram 自動同期スクリプト
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ECC Trust Score: 0.90 | docs/14 参照パターン: M001-M010
docs/10 Safety Guardrails 準拠:
  - OAuthException 発生時はリトライしない → 即 exit(1)
  - continue-on-error は使わない
  - 認証情報はすべて環境変数から取得

Usage:
    python insta_base_sync.py

Environment variables (GitHub Secrets から注入):
    INSTAGRAM_TOKEN    : Meta Long-Lived Token or System User Token
    IG_USER_ID         : Instagram Business User ID
    BASE_ACCESS_TOKEN  : BASE API アクセストークン
    BASE_SHOP_ID       : killstreet ショップID
    META_APP_ID        : Meta App ID (オプション)
"""

import os
import sys
import json
import time
import datetime
import requests
from pathlib import Path


# ── 定数 ─────────────────────────────────────────────────────────────────────
GRAPH_BASE    = "https://graph.facebook.com/v20.0"
BASE_API      = "https://api.thebase.in/1"
MEMORY_LOG    = Path(__file__).parent.parent / "docs" / "08_memory_log.md"
STATE_FILE    = Path(__file__).parent / ".last_sync_state.json"  # ローカル状態管理

# docs/14 地雷マップ: エラーコード → パターンID
ERROR_MAP = {
    190: ("M001/M007", "Token invalid/expired → System User Token に移行してください"),
    200: ("M005",      "Permission denied → Meta App Review で instagram_content_publish を申請"),
    10:  ("M005",      "Permission denied → instagram_basic スコープが欠如している可能性"),
    4:   ("M009",      "App-level Rate Limit → 実行間隔を広げてください"),
    17:  ("M009",      "User-level Rate Limit → 1時間待機してから再実行"),
    100: ("M006",      "Invalid parameter → フィールド名を BASE API ドキュメントで確認"),
    368: (None,        "Account temporarily blocked → Meta サポートに連絡"),
}


# ── ECC ロガー ────────────────────────────────────────────────────────────────
def log_to_memory(status: str, detail: str, trust: float = 0.9) -> None:
    ts  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    row = f"| {ts} | insta_base_sync | {status} | {detail[:120]} | {trust} |\n"
    try:
        with open(MEMORY_LOG, "a", encoding="utf-8") as f:
            f.write(row)
    except OSError:
        print(f"[WARN] docs/08 への書き込みに失敗", file=sys.stderr)


# ── Dead-End Detection ────────────────────────────────────────────────────────
def handle_meta_error(resp_json: dict, context: str = "") -> None:
    """
    Meta API エラーを受け取り、人間が読める診断を出力して即 exit(1) する。
    リトライは行わない（docs/10 Safety Guardrails 準拠）。
    docs/14 地雷マップを参照してパターンIDを特定する。
    """
    err      = resp_json.get("error", {})
    code     = err.get("code", 0)
    subcode  = err.get("error_subcode", 0)
    msg      = err.get("message", "Unknown error")
    err_type = err.get("type", "")

    print(f"\n{'='*60}", file=sys.stderr)
    print(f"❌ Dead-End Detection — Meta API エラー検出", file=sys.stderr)
    print(f"   コンテキスト: {context}", file=sys.stderr)
    print(f"   エラーコード: {code} (subcode: {subcode})", file=sys.stderr)
    print(f"   タイプ      : {err_type}", file=sys.stderr)
    print(f"   メッセージ  : {msg}", file=sys.stderr)

    if code in ERROR_MAP:
        pattern_id, diagnosis = ERROR_MAP[code]
        print(f"\n   📍 docs/14 地雷パターン: {pattern_id}", file=sys.stderr)
        print(f"   診断: {diagnosis}", file=sys.stderr)
    else:
        print(f"\n   ⚠️  未知のエラーコード — docs/14 に新パターンとして追記してください", file=sys.stderr)
        print(f"   Trust Score 0.7 で M0XX として記録することを推奨", file=sys.stderr)

    # 不足スコープの推定
    if code in (200, 10) or err_type == "OAuthException":
        scope_map = {
            "instagram_content_publish": "投稿の作成・公開",
            "instagram_basic":           "アカウント情報の読み取り",
        }
        print(f"\n   💡 必要なスコープを確認してください:", file=sys.stderr)
        for scope, desc in scope_map.items():
            print(f"      - {scope}  ({desc})", file=sys.stderr)
        print(f"\n   申請手順:", file=sys.stderr)
        print(f"   https://developers.facebook.com/ → App Review → Permissions and Features", file=sys.stderr)

    print(f"{'='*60}\n", file=sys.stderr)

    log_to_memory(
        f"DEAD_END_DETECTED",
        f"code={code} type={err_type}: {msg[:80]}",
        trust=0.9
    )
    sys.exit(1)


# ── 環境変数ロード ────────────────────────────────────────────────────────────
def load_env() -> dict:
    required = {
        "INSTAGRAM_TOKEN":   os.environ.get("INSTAGRAM_TOKEN", ""),
        "IG_USER_ID":        os.environ.get("IG_USER_ID", ""),
        "BASE_ACCESS_TOKEN": os.environ.get("BASE_ACCESS_TOKEN", ""),
        "BASE_SHOP_ID":      os.environ.get("BASE_SHOP_ID", ""),
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        print(f"❌ 環境変数が未設定: {', '.join(missing)}", file=sys.stderr)
        print(f"   GitHub Secrets に登録してください", file=sys.stderr)
        log_to_memory("ENV_ERROR", f"未設定: {missing}", trust=0.5)
        sys.exit(3)
    return required


# ── 状態管理（重複投稿防止）─────────────────────────────────────────────────
def load_last_sync() -> datetime.datetime | None:
    """最後に同期したタイムスタンプを読み込む（docs/14 M008 対策）"""
    try:
        if STATE_FILE.exists():
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            ts   = data.get("last_synced_at", "")
            if ts:
                return datetime.datetime.fromisoformat(ts)
    except (json.JSONDecodeError, ValueError):
        pass
    # 状態ファイルがなければ30分前を基準とする
    return datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=35)


def save_last_sync(ts: datetime.datetime) -> None:
    data = {"last_synced_at": ts.isoformat()}
    STATE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ── BLOCK 2: BASE API — 新着商品取得 ─────────────────────────────────────────
def fetch_new_base_products(env: dict, since: datetime.datetime) -> list[dict]:
    """
    BASE API から新着商品を取得し、since より新しいものを返す。

    # TODO: BASE API ドキュメント https://docs.thebase.in/api/ で
    #       実際のレスポンスフィールド名を確認してください。
    #       よく混乱するフィールド名:
    #         - 画像: "list_image_url" または "detail_image_url" (どちらが存在するか確認)
    #         - 作成日: "add_datetime" (形式: "YYYY-MM-DD HH:MM:SS")
    #         - ショップ内商品ID: "item_id"
    """
    headers = {"Authorization": f"Bearer {env['BASE_ACCESS_TOKEN']}"}
    url     = f"{BASE_API}/items"
    params  = {
        "shop_id": env["BASE_SHOP_ID"],
        "limit":   20,
        "order":   "new",  # 新着順
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
    except requests.RequestException as e:
        print(f"❌ BASE API への接続失敗: {e}", file=sys.stderr)
        log_to_memory("BASE_NETWORK_ERROR", str(e), trust=0.5)
        sys.exit(3)

    if resp.status_code == 401:
        print(f"❌ BASE API 認証失敗 (401) — docs/14 M003: BASE_ACCESS_TOKEN を再取得してください", file=sys.stderr)
        log_to_memory("BASE_AUTH_ERROR", "HTTP 401", trust=0.9)
        sys.exit(1)

    if resp.status_code == 429:
        print(f"❌ BASE API Rate Limit (429) — docs/14 M009: 1日1,000リクエスト制限", file=sys.stderr)
        log_to_memory("BASE_RATE_LIMIT", "HTTP 429", trust=0.9)
        sys.exit(1)

    if resp.status_code != 200:
        print(f"❌ BASE API エラー: HTTP {resp.status_code}", file=sys.stderr)
        log_to_memory("BASE_ERROR", f"HTTP {resp.status_code}", trust=0.7)
        sys.exit(1)

    data  = resp.json()
    # TODO: レスポンスの実際のキー名を確認してください（"items" または "item"）
    items = data.get("items", data.get("item", []))

    new_items = []
    for item in items:
        # TODO: 日時フィールド名を確認（"add_datetime" または "created" など）
        added_str = item.get("add_datetime", "")
        if not added_str:
            continue
        try:
            # BASE の日時は "YYYY-MM-DD HH:MM:SS" 形式（UTC+9 JST）
            added_dt = datetime.datetime.strptime(added_str, "%Y-%m-%d %H:%M:%S")
            added_dt = added_dt.replace(tzinfo=datetime.timezone(datetime.timedelta(hours=9)))
            added_dt = added_dt.astimezone(datetime.timezone.utc)
        except ValueError:
            continue

        if added_dt > since:
            # TODO: 画像URLのフィールド名を確認してください
            image_url = item.get("list_image_url") or item.get("detail_image_url", "")
            if not image_url:
                print(f"[SKIP] 商品ID {item.get('item_id')} は画像なし — スキップ (docs/14 M006対策)")
                continue
            new_items.append({
                "item_id":   item.get("item_id", ""),
                "title":     item.get("title", ""),
                "price":     item.get("price", 0),
                "image_url": image_url,
                "item_url":  f"https://killstreet.base.shop/items/{item.get('item_id', '')}",
                # TODO: 実際のショップURLを確認してください
            })

    print(f"[INFO] 新着商品: {len(new_items)} 件 (since: {since.strftime('%Y-%m-%d %H:%M UTC')})")
    return new_items


# ── BLOCK 3: Instagram Graph API — 投稿 ──────────────────────────────────────
def post_to_instagram(env: dict, item: dict) -> bool:
    """
    Instagram Graph API の2ステップ投稿フロー:
      Step 1: POST /{ig-user-id}/media → container_id 取得
      Step 2: POST /{ig-user-id}/media_publish → container_id を公開

    失敗時は Dead-End Detection → exit(1)（リトライなし）
    """
    ig_user_id = env["IG_USER_ID"]
    token      = env["INSTAGRAM_TOKEN"]
    headers    = {"Content-Type": "application/json"}

    # キャプション生成（ハッシュタグ30個制限に注意 docs/14 U002）
    caption = (
        f"{item['title']}\n\n"
        f"¥{item['price']:,}\n\n"
        f"📦 商品ページ: {item['item_url']}\n\n"
        # TODO: ブランドに合ったハッシュタグを追記（最大30個）
        f"#killstreet #streetwear #fashion"
    )

    # Step 1: メディアコンテナ作成
    print(f"[POST] {item['title']} を投稿中...")
    container_resp = requests.post(
        f"{GRAPH_BASE}/{ig_user_id}/media",
        params={
            "image_url":   item["image_url"],
            "caption":     caption,
            "access_token": token,
        },
        timeout=30,
    )
    container_data = container_resp.json()

    if "error" in container_data:
        handle_meta_error(container_data, context=f"media container作成: {item['title']}")
        return False  # unreachable (exit(1) が呼ばれる)

    container_id = container_data.get("id")
    if not container_id:
        print(f"❌ container_id が取得できませんでした", file=sys.stderr)
        log_to_memory("CONTAINER_ERROR", f"item_id={item['item_id']}", trust=0.7)
        sys.exit(1)

    # Step 2: 公開（コンテナ作成後10秒以上待つことを推奨）
    time.sleep(10)

    publish_resp = requests.post(
        f"{GRAPH_BASE}/{ig_user_id}/media_publish",
        params={
            "creation_id":  container_id,
            "access_token": token,
        },
        timeout=30,
    )
    publish_data = publish_resp.json()

    if "error" in publish_data:
        handle_meta_error(publish_data, context=f"media_publish: {item['title']}")
        return False  # unreachable

    post_id = publish_data.get("id", "?")
    print(f"   ✅ 投稿完了 — Post ID: {post_id}")
    log_to_memory(
        "POST_SUCCESS",
        f"item_id={item['item_id']} title={item['title'][:40]} post_id={post_id}",
        trust=1.0
    )
    return True


# ── メイン ────────────────────────────────────────────────────────────────────
def main() -> None:
    print("=" * 60)
    print("  BASE × Instagram Sync — insta_base_sync.py")
    print(f"  実行時刻: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)

    # BLOCK 1: 環境変数ロード
    env = load_env()

    # 状態ロード（重複投稿防止）
    last_sync = load_last_sync()

    # BLOCK 2: BASE 新着商品取得
    new_items = fetch_new_base_products(env, since=last_sync)

    if not new_items:
        print("[INFO] 新着商品なし — 処理を終了します")
        log_to_memory("NO_NEW_ITEMS", f"since={last_sync.isoformat()}", trust=1.0)
        sys.exit(0)

    # BLOCK 3: Instagram 投稿
    posted_count = 0
    now_utc = datetime.datetime.now(datetime.timezone.utc)

    for item in new_items:
        success = post_to_instagram(env, item)
        if success:
            posted_count += 1
        # Instagram の投稿間隔（連続投稿でレート制限を避ける）
        time.sleep(5)

    # BLOCK 4: 状態保存 + サマリー
    save_last_sync(now_utc)
    print(f"\n{'='*60}")
    print(f"  完了: {posted_count}/{len(new_items)} 件投稿")
    print(f"  次回の基準時刻: {now_utc.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}")
    log_to_memory(
        "SYNC_COMPLETE",
        f"投稿={posted_count}/{len(new_items)} since={last_sync.isoformat()}",
        trust=1.0
    )


if __name__ == "__main__":
    main()
