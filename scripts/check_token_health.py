"""
check_token_health.py — Token Health Dashboard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ECC Trust Score: 0.95 | docs/14 参照パターン: M001, M007
docs/10 Safety Guardrails 準拠: リトライなし、エラー時は即 exit(1)

Usage:
    python check_token_health.py

Environment variables required:
    INSTAGRAM_TOKEN   : Meta System User Token or Long-Lived Token
    META_APP_ID       : Meta App ID (debug_token に必要)
    META_APP_SECRET   : Meta App Secret (debug_token に必要)

Exit codes:
    0 : TOKEN OK (残り日数 > 15日、または無期限)
    1 : TOKEN DEAD (失効済み)
    2 : TOKEN WARNING (残り ≤ 15日)
    3 : 環境変数未設定 / API エラー
"""

import os
import sys
import json
import datetime
import requests


# ── 定数 ─────────────────────────────────────────────────────────────────────
WARN_DAYS      = 15
GRAPH_BASE     = "https://graph.facebook.com/v20.0"
MEMORY_LOG     = os.path.join(os.path.dirname(__file__), "..", "docs", "08_memory_log.md")
MINEFIELD_MAP  = os.path.join(os.path.dirname(__file__), "..", "docs", "14_api_minefield_map.md")


# ── ECC ロガー ────────────────────────────────────────────────────────────────
def log_to_memory(status: str, detail: str, trust: float = 0.9) -> None:
    """docs/08_memory_log.md に ECC エントリを追記する"""
    ts  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    row = f"| {ts} | check_token_health | {status} | {detail} | {trust} |\n"
    try:
        with open(MEMORY_LOG, "a", encoding="utf-8") as f:
            f.write(row)
    except OSError:
        print(f"[WARN] docs/08 への書き込みに失敗: {MEMORY_LOG}", file=sys.stderr)


# ── 環境変数チェック ──────────────────────────────────────────────────────────
def load_env() -> tuple[str, str, str]:
    token  = os.environ.get("INSTAGRAM_TOKEN", "")
    app_id = os.environ.get("META_APP_ID", "")
    secret = os.environ.get("META_APP_SECRET", "")

    missing = [k for k, v in [
        ("INSTAGRAM_TOKEN", token),
        ("META_APP_ID",     app_id),
        ("META_APP_SECRET", secret),
    ] if not v]

    if missing:
        print(f"❌ 環境変数が未設定です: {', '.join(missing)}", file=sys.stderr)
        print("   GitHub Secrets または .env ファイルに設定してください", file=sys.stderr)
        log_to_memory("ENV_ERROR", f"未設定: {missing}", trust=0.5)
        sys.exit(3)

    return token, app_id, secret


# ── トークン生存確認 ──────────────────────────────────────────────────────────
def check_token_alive(token: str) -> dict:
    """GET /me?fields=id,name でトークンが生きているか確認"""
    url    = f"{GRAPH_BASE}/me"
    params = {"fields": "id,name", "access_token": token}
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
    except requests.RequestException as e:
        print(f"❌ Meta API への接続失敗: {e}", file=sys.stderr)
        log_to_memory("NETWORK_ERROR", str(e), trust=0.5)
        sys.exit(3)

    if "error" in data:
        return {"alive": False, "error": data["error"]}

    return {"alive": True, "id": data.get("id"), "name": data.get("name")}


# ── トークン期限確認 ──────────────────────────────────────────────────────────
def check_token_expiry(token: str, app_id: str, secret: str) -> dict:
    """GET /debug_token で expiry_time を取得し、残り日数を算出する"""
    url    = f"{GRAPH_BASE}/debug_token"
    params = {
        "input_token":  token,
        "access_token": f"{app_id}|{secret}",  # App Access Token
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
    except requests.RequestException as e:
        print(f"❌ debug_token API への接続失敗: {e}", file=sys.stderr)
        log_to_memory("NETWORK_ERROR", str(e), trust=0.5)
        sys.exit(3)

    if "error" in data:
        return {"expires": False, "error": data["error"]}

    token_data  = data.get("data", {})
    expires_at  = token_data.get("expires_at", 0)  # Unix timestamp, 0 = never expires
    is_valid    = token_data.get("is_valid", False)

    if not is_valid:
        return {"expires": True, "days_left": -1, "is_valid": False}

    if expires_at == 0:
        # System User Token: 無期限
        return {"expires": False, "days_left": None, "is_valid": True}

    now         = datetime.datetime.now(datetime.timezone.utc)
    expiry_dt   = datetime.datetime.fromtimestamp(expires_at, tz=datetime.timezone.utc)
    days_left   = (expiry_dt - now).days
    return {"expires": True, "days_left": days_left, "is_valid": True, "expiry_dt": expiry_dt}


# ── メイン ────────────────────────────────────────────────────────────────────
def main() -> None:
    print("=" * 60)
    print("  TOKEN HEALTH CHECK — Instagram / Meta Graph API")
    print("=" * 60)

    token, app_id, secret = load_env()

    # Step 1: トークン生存確認
    print("\n[1/2] トークン生存確認中...")
    alive_result = check_token_alive(token)

    if not alive_result["alive"]:
        err = alive_result.get("error", {})
        code = err.get("code", "?")
        msg  = err.get("message", "Unknown error")
        print(f"\n❌ TOKEN DEAD")
        print(f"   エラーコード: {code}")
        print(f"   メッセージ  : {msg}")
        # docs/14 地雷原マップ参照
        if code == 190:
            print(f"\n   📍 地雷パターン: M001/M007 (OAuthException)")
            print(f"   対処法: Long-Lived Token に交換 → 推奨は System User Token")
            print(f"   → https://business.facebook.com/ → ビジネス設定 → システムユーザー")
        log_to_memory("TOKEN_DEAD", f"code={code}: {msg}", trust=0.9)
        sys.exit(1)

    ig_id   = alive_result.get("id", "?")
    ig_name = alive_result.get("name", "?")
    print(f"   ✅ 生存確認OK  — IG User: {ig_name} (ID: {ig_id})")

    # Step 2: 期限確認
    print("\n[2/2] 有効期限確認中...")
    expiry_result = check_token_expiry(token, app_id, secret)

    if not expiry_result.get("is_valid", True):
        print(f"\n❌ TOKEN INVALID (debug_token API が invalid と報告)")
        log_to_memory("TOKEN_INVALID", "debug_token is_valid=False", trust=0.9)
        sys.exit(1)

    if not expiry_result.get("expires", True):
        # System User Token: 無期限
        print(f"\n✅ TOKEN OK — 有効期限: 無期限（System User Token）")
        log_to_memory("TOKEN_OK", "System User Token (無期限)", trust=1.0)
        sys.exit(0)

    days_left = expiry_result.get("days_left", -1)
    expiry_dt = expiry_result.get("expiry_dt")
    expiry_str = expiry_dt.strftime("%Y-%m-%d %H:%M UTC") if expiry_dt else "不明"

    if days_left < 0:
        print(f"\n❌ TOKEN DEAD — 有効期限切れ ({expiry_str})")
        print(f"\n   再取得手順:")
        print(f"   1. https://developers.facebook.com/tools/explorer/ を開く")
        print(f"   2. 右上のアプリを選択 → 「ユーザートークンを生成」")
        print(f"   3. 必要な権限を選択: instagram_content_publish, instagram_basic")
        print(f"   4. 取得した Short-Lived Token を Long-Lived Token に交換:")
        print(f"      GET https://graph.facebook.com/oauth/access_token")
        print(f"         ?grant_type=fb_exchange_token")
        print(f"         &client_id=APP_ID")
        print(f"         &client_secret=APP_SECRET")
        print(f"         &fb_exchange_token=SHORT_LIVED_TOKEN")
        print(f"   5. GitHub Secrets の INSTAGRAM_TOKEN を更新")
        log_to_memory("TOKEN_DEAD", f"expired: {expiry_str}", trust=0.9)
        sys.exit(1)

    elif days_left <= WARN_DAYS:
        print(f"\n⚠️  REFRESH REQUIRED — 残り {days_left} 日 (期限: {expiry_str})")
        print(f"\n   リフレッシュコマンド:")
        print(f"   curl -G https://graph.facebook.com/oauth/access_token \\")
        print(f"        --data-urlencode 'grant_type=ig_refresh_token' \\")
        print(f"        --data-urlencode 'access_token=YOUR_TOKEN'")
        print(f"   → 取得した新トークンを GitHub Secrets に登録してください")
        log_to_memory("TOKEN_WARNING", f"残り{days_left}日: {expiry_str}", trust=0.9)
        sys.exit(2)

    else:
        print(f"\n✅ TOKEN OK — 残り {days_left} 日 (期限: {expiry_str})")
        log_to_memory("TOKEN_OK", f"残り{days_left}日", trust=1.0)
        sys.exit(0)


if __name__ == "__main__":
    main()
