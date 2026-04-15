"""
BASE API から商品を取得し、Instagram Graph API に投稿するスクリプト。

環境変数:
  BASE_CLIENT_ID      : BASE OAuth2 クライアントID
  BASS_CLIENT_ID      : BASE_CLIENT_ID のタイポ版フォールバック
  BASE_CLIENT_SECRET  : BASE OAuth2 クライアントシークレット
  BASE_REFRESH_TOKEN  : BASE OAuth2 リフレッシュトークン
  BASE_ACCESS_TOKEN   : BASE アクセストークン（リフレッシュ失敗時フォールバック）
  INSTAGRAM_TOKEN     : Instagram Graph API アクセストークン
  IG_USER_ID          : Instagram ユーザーID
  SHOP_ID             : BASE ショップID（省略時: killstreet2）
  DEBUG               : 'true' のとき投稿せず商品情報を stdout に出力
"""

import os
import sys
import time
import random
import requests

BASE_TOKEN_URL = "https://api.thebase.in/1/oauth/token"
BASE_API_ROOT = "https://api.thebase.in/1"
IG_API_ROOT = "https://graph.facebook.com/v19.0"

SHOP_ID = os.environ.get("SHOP_ID", "killstreet2")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

MAX_RETRIES = 3
RETRY_WAIT = 60  # seconds for 429


# ── 認証 ────────────────────────────────────────────────────────────────

def get_base_access_token():
    """
    リフレッシュトークンで新しいアクセストークンを取得。
    失敗した場合は BASE_ACCESS_TOKEN 環境変数をフォールバックで使用。
    """
    client_id = (
        os.environ.get("BASE_CLIENT_ID", "").strip()
        or os.environ.get("BASS_CLIENT_ID", "").strip()  # タイポ版フォールバック
    )
    client_secret = os.environ.get("BASE_CLIENT_SECRET", "").strip()
    refresh_token = os.environ.get("BASE_REFRESH_TOKEN", "").strip()
    fallback_token = os.environ.get("BASE_ACCESS_TOKEN", "").strip()

    if refresh_token and client_id and client_secret:
        print("[INFO] リフレッシュトークンでアクセストークンを更新中...")
        try:
            resp = requests.post(
                BASE_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": refresh_token,
                },
                timeout=30,
            )
            if resp.status_code == 200:
                token_data = resp.json()
                new_token = token_data.get("access_token", "")
                if new_token:
                    print("[INFO] アクセストークンの更新に成功しました。")
                    return new_token
                else:
                    print(f"[WARN] トークンレスポンスに access_token がありません: {resp.text[:200]}")
            else:
                print(f"[WARN] トークン更新失敗: status={resp.status_code}, body={resp.text[:200]}")
        except requests.RequestException as e:
            print(f"[WARN] トークン更新リクエスト例外: {e}")

    if fallback_token:
        print("[INFO] BASE_ACCESS_TOKEN をフォールバックとして使用します。")
        return fallback_token

    print("[ERROR] BASE アクセストークンを取得できません。")
    print("[ERROR]   - BASE_REFRESH_TOKEN + BASE_CLIENT_ID + BASE_CLIENT_SECRET を設定するか")
    print("[ERROR]   - BASE_ACCESS_TOKEN を直接設定してください。")
    sys.exit(1)


# ── BASE API 商品取得 ────────────────────────────────────────────────────

def fetch_items(access_token):
    """公開中の商品をページネーションで全件取得。"""
    headers = {"Authorization": f"Bearer {access_token}"}
    items = []
    offset = 0
    limit = 100

    while True:
        params = {
            "shop_id": SHOP_ID,
            "limit": limit,
            "offset": offset,
            "visible": 1,  # 公開中のみ
        }

        resp = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = requests.get(
                    f"{BASE_API_ROOT}/items",
                    headers=headers,
                    params=params,
                    timeout=30,
                )
            except requests.RequestException as e:
                print(f"[ERROR] リクエスト例外: {e}")
                sys.exit(1)

            if resp.status_code == 200:
                break
            elif resp.status_code == 401:
                print("[ERROR] 401 Unauthorized — BASE アクセストークンが無効または期限切れです。")
                print(f"[ERROR] Response: {resp.text[:200]}")
                sys.exit(1)
            elif resp.status_code == 429:
                print(f"[WARN] 429 Too Many Requests — {RETRY_WAIT}秒後にリトライ ({attempt}/{MAX_RETRIES})...")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_WAIT)
                else:
                    print("[ERROR] リトライ上限に達しました。")
                    sys.exit(1)
            else:
                print(f"[ERROR] 予期しないステータスコード: {resp.status_code}")
                print(f"[ERROR] Response body: {resp.text[:400]}")
                sys.exit(1)

        data = resp.json()

        # デバッグ: レスポンス構造を確認
        if DEBUG or offset == 0:
            keys = list(data.keys())
            print(f"[DEBUG] レスポンスキー: {keys}")
            if not data.get("items"):
                print(f"[DEBUG] status_code={resp.status_code}")
                print(f"[DEBUG] response_body={resp.text[:400]}")

        page_items = data.get("items", [])
        items.extend(page_items)
        print(f"[INFO] 取得: offset={offset}, 件数={len(page_items)}, 累計={len(items)}")

        if len(page_items) < limit:
            break
        offset += limit

    return items


def pick_item_with_image(items):
    """
    画像URLが有効な商品をランダムに1件選んで返す。
    BASE API の正しいフィールド:
      - images[].url           (items エンドポイントの配列形式)
      - list_image_url         (一部エンドポイントで使われるフラット形式)
      - detail_image_url       (同上)
    """
    candidates = []
    for item in items:
        image_url = _extract_image_url(item)
        if image_url:
            candidates.append((item, image_url))

    if not candidates:
        return None, None

    item, image_url = random.choice(candidates)
    return item, image_url


def _extract_image_url(item):
    """商品データから最初に見つかった有効な画像URLを返す。"""
    # パターン1: images 配列
    images = item.get("images")
    if isinstance(images, list) and images:
        url = images[0].get("url", "")
        if url:
            return url

    # パターン2: list_image_url
    url = item.get("list_image_url", "")
    if url:
        return url

    # パターン3: detail_image_url
    url = item.get("detail_image_url", "")
    if url:
        return url

    return ""


# ── Instagram 投稿 ───────────────────────────────────────────────────────

def post_to_instagram(item, image_url):
    """Instagram Graph API で画像投稿を行う。"""
    ig_token = os.environ.get("INSTAGRAM_TOKEN", "").strip()
    ig_user_id = os.environ.get("IG_USER_ID", "").strip()

    if not ig_token:
        print("[ERROR] INSTAGRAM_TOKEN が設定されていません。")
        sys.exit(1)
    if not ig_user_id:
        print("[ERROR] IG_USER_ID が設定されていません。")
        sys.exit(1)

    title = item.get("title", "")
    price = item.get("price", 0)
    item_url = item.get("item_url", "")

    caption = f"{title}\n\n¥{price:,}\n\n{item_url}\n\n#killstreet #ストリートファッション"

    # Step 1: メディアコンテナ作成
    print(f"[INFO] Instagram メディアコンテナを作成中... image_url={image_url[:60]}...")
    create_resp = requests.post(
        f"{IG_API_ROOT}/{ig_user_id}/media",
        params={
            "image_url": image_url,
            "caption": caption,
            "access_token": ig_token,
        },
        timeout=60,
    )

    if create_resp.status_code != 200:
        err = create_resp.json().get("error", {})
        print(f"[ERROR] メディアコンテナ作成失敗: status={create_resp.status_code}")
        print(f"[ERROR]   error_code={err.get('code')}, subcode={err.get('error_subcode')}")
        print(f"[ERROR]   message={err.get('message')}")
        print(f"[ERROR]   type={err.get('type')}")
        sys.exit(1)

    container_id = create_resp.json().get("id", "")
    if not container_id:
        print(f"[ERROR] コンテナIDが取得できません: {create_resp.text[:200]}")
        sys.exit(1)

    print(f"[INFO] コンテナID: {container_id}")

    # Step 2: 公開
    print("[INFO] Instagram に投稿中...")
    publish_resp = requests.post(
        f"{IG_API_ROOT}/{ig_user_id}/media_publish",
        params={
            "creation_id": container_id,
            "access_token": ig_token,
        },
        timeout=60,
    )

    if publish_resp.status_code != 200:
        err = publish_resp.json().get("error", {})
        print(f"[ERROR] 投稿失敗: status={publish_resp.status_code}")
        print(f"[ERROR]   error_code={err.get('code')}, subcode={err.get('error_subcode')}")
        print(f"[ERROR]   message={err.get('message')}")
        print(f"[ERROR]   type={err.get('type')}")
        sys.exit(1)

    media_id = publish_resp.json().get("id", "")
    print(f"[INFO] 投稿成功! media_id={media_id}")
    return media_id


# ── メイン ───────────────────────────────────────────────────────────────

def main():
    print(f"=== BASE → Instagram 同期開始 (SHOP_ID={SHOP_ID}, DEBUG={DEBUG}) ===")

    # 1. アクセストークン取得
    access_token = get_base_access_token()

    # 2. 商品取得
    items = fetch_items(access_token)

    if not items:
        print("[ERROR] 商品が0件でした。")
        print("[ERROR] 考えられる原因:")
        print("[ERROR]   - BASE_ACCESS_TOKEN が無効または期限切れ")
        print("[ERROR]   - SHOP_ID が誤っている (現在: " + SHOP_ID + ")")
        print("[ERROR]   - 公開中の商品が存在しない (?visible=1 フィルタ)")
        sys.exit(1)

    print(f"[INFO] 合計 {len(items)} 件の商品を取得しました。")

    # 3. 画像付き商品を選択
    item, image_url = pick_item_with_image(items)

    if not item:
        print("[ERROR] 有効な画像URLを持つ商品が見つかりませんでした。")
        print("[ERROR] 取得した商品サンプル (先頭3件のキー):")
        for i, s in enumerate(items[:3]):
            print(f"[ERROR]   item[{i}] keys={list(s.keys())}")
        sys.exit(1)

    print(f"[INFO] 投稿対象商品: {item.get('title')} (image={image_url[:60]}...)")

    # 4. DEBUGモード: 投稿せず終了
    if DEBUG:
        print("[DEBUG] DEBUG=true のため投稿をスキップします。")
        print(f"[DEBUG] title    = {item.get('title')}")
        print(f"[DEBUG] price    = {item.get('price')}")
        print(f"[DEBUG] item_url = {item.get('item_url')}")
        print(f"[DEBUG] image_url= {image_url}")
        print("=== DEBUG 完了 ===")
        return

    # 5. Instagram 投稿
    post_to_instagram(item, image_url)
    print("=== 完了 ===")


if __name__ == "__main__":
    main()
