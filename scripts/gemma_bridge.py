#!/usr/bin/env python3
"""
gemma_bridge.py — Gemma Local Assistant ブリッジスクリプト v2.0
=====================================================
blueprint.md やエラーログを Gemma が読みやすいプロンプトに変換し、
クリップボードにコピー または ファイル出力します。

【使い方】

  # 設計図の座標チェック
  python scripts/gemma_bridge.py --mode design

  # ビルドエラーの初期診断
  python scripts/gemma_bridge.py --mode debug --log path/to/error.log

  # Instagram/X 宣伝文10案生成
  python scripts/gemma_bridge.py --mode copy --plugin-name "CALLOUT"

  # OpenHarness 採点（9点未満はREJECT）
  python scripts/gemma_bridge.py --mode eval

  # docs整合性チェック＆更新提案
  python scripts/gemma_bridge.py --mode doc

  # コンテキスト圧縮（重要事項をdocs/08に退避）
  python scripts/gemma_bridge.py --mode compress

  # ブラウザ取得コンテンツの振り分け
  python scripts/gemma_bridge.py --mode browser --url https://...

  # ファイル出力
  python scripts/gemma_bridge.py --mode design --output file

  # Ollama直接呼び出し
  python scripts/gemma_bridge.py --mode eval --send-to-ollama
"""

import argparse
import os
import sys
import json
import datetime

# ── 定数・パス ──────────────────────────────────────────────────

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DOCS_DIR     = os.path.join(PROJECT_ROOT, "docs")
BLUEPRINT_PATH   = os.path.join(DOCS_DIR, "blueprint.md")
MEMORY_LOG_PATH  = os.path.join(DOCS_DIR, "08_memory_log.md")
EVAL_HARNESS_PATH = os.path.join(DOCS_DIR, "09_self_evaluation_harness.md")
GUARDRAILS_PATH  = os.path.join(DOCS_DIR, "10_safety_guardrails.md")

CONTEXT_BUDGET_RATIO = 0.50  # コンテキストがこの割合に達したらcompressを推奨

# ── ユーティリティ ──────────────────────────────────────────────

def read_file(path: str) -> str:
    if not os.path.exists(path):
        print(f"[ERROR] ファイルが見つかりません: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return f.read()


def read_file_optional(path: str, fallback: str = "") -> str:
    if not os.path.exists(path):
        return fallback
    with open(path, encoding="utf-8") as f:
        return f.read()


def copy_to_clipboard(text: str) -> bool:
    """クリップボードにコピー（Windows / macOS / Linux対応）"""
    if sys.platform == "win32":
        try:
            import subprocess
            proc = subprocess.Popen(["clip"], stdin=subprocess.PIPE, close_fds=False)
            proc.communicate(input=text.encode("utf-16-le"))
            return True
        except Exception:
            pass
    if sys.platform == "darwin":
        try:
            import subprocess
            proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            proc.communicate(input=text.encode("utf-8"))
            return True
        except Exception:
            pass
    try:
        import subprocess
        proc = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
        proc.communicate(input=text.encode("utf-8"))
        return True
    except Exception:
        pass
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except ImportError:
        return False


def send_to_ollama(prompt: str, model: str = "gemma2:9b") -> str:
    """Ollama API に直接プロンプトを送信して結果を返す"""
    try:
        import urllib.request
        payload = json.dumps({
            "model": model,
            "prompt": prompt,
            "stream": False
        }).encode("utf-8")
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("response", "")
    except Exception as e:
        print(f"[ERROR] Ollama接続失敗: {e}", file=sys.stderr)
        print("       起動確認: ollama serve", file=sys.stderr)
        sys.exit(1)


def append_to_memory_log(entry: str):
    """docs/08_memory_log.md に新規エントリを追記する"""
    if not os.path.exists(MEMORY_LOG_PATH):
        print(f"[WARN] memory_log が見つかりません: {MEMORY_LOG_PATH}", file=sys.stderr)
        return
    with open(MEMORY_LOG_PATH, "a", encoding="utf-8") as f:
        f.write("\n\n" + entry)
    print(f"[OK] docs/08_memory_log.md に記録しました。")


# ── プロンプトテンプレート ─────────────────────────────────────

def make_design_prompt(blueprint_content: str) -> str:
    """[Design Check] blueprint座標バリデーション"""
    import re
    canvas_width, canvas_height = "700", "420"
    for line in blueprint_content.splitlines():
        if "キャンバス幅" in line:
            m = re.search(r"(\d{3,4})", line)
            if m: canvas_width = m.group(1)
        if "キャンバス高さ" in line:
            m = re.search(r"(\d{3,4})", line)
            if m: canvas_height = m.group(1)

    return f"""あなたはJUCEプラグインのUI設計レビュアーです。
以下のblueprint.mdの内容を、JUCE座標系（原点=左上、X右正、Y下正、単位px）として検証してください。

キャンバスサイズ: {canvas_width} x {canvas_height} px

チェック項目:
1. 各コンポーネントの X + W が {canvas_width}px を超えていないか
2. 各コンポーネントの Y + H が {canvas_height}px を超えていないか
3. ノブ（RotarySlider）の W = H が守られているか（正方形必須）
4. パラメータIDが重複していないか
5. 全コンポーネントの X, Y が 0 以上か

---
{blueprint_content}
---

## 判定
[ PASS ] または [ FAIL ]

## 失敗した項目
（箇条書き。PASSの場合は「なし」）

## 修正提案
（具体的な数値で）

## 総評（1〜2文）
"""


def make_debug_prompt(error_log: str) -> str:
    """[Debug Assistant] ビルドエラー初期診断"""
    return f"""あなたはC++/JUCEのビルドエラー診断専門家です。
以下のエラーログを解析し、問題を2つのカテゴリに分類してください。

「単純なミス」: タイポ、セミコロン忘れ、括弧不一致、#include漏れ、変数名/型名ミス
「複雑な問題」: アーキテクチャ問題、JUCE API変更対応、プラットフォーム固有問題

---
{error_log}
---

## 単純なミス（Gemmaが修正案を提示）
（ファイル名:行番号 — 原因 — 修正案。なければ「なし」）

## 複雑な問題（Windsurfに回す）
（概要。なければ「なし」）

## 判定
[ GEMMA_FIX_POSSIBLE ] または [ NEEDS_WINDSURF ] または [ BOTH ]

## 次のアクション（1〜3ステップ）
"""


def make_copy_prompt(plugin_name: str, plugin_desc: str) -> str:
    """[Creative Copy] Instagram/X宣伝文生成"""
    return f"""あなたはKrumpダンス文化に精通した音楽プロデューサー向けのコピーライターです。
以下のVSTプラグインのInstagram/X用宣伝文を10案生成してください。

プラグイン情報:
- 名前: {plugin_name}
- 効果: {plugin_desc}
- ターゲット: ヒップホップ・Krump系アーティスト・ビートメイカー

トーンの要件:
- 攻撃的・エネルギッシュ（Krumpのバトル精神）
- 技術的すぎない（感情に訴える）
- ハッシュタグ3〜5個を含む
- 英語または日英ミックスOK
- 各案 140文字以内（X/Twitter用）

10案を番号付きで出力してください。
"""


def make_eval_prompt(eval_target: str, eval_harness: str) -> str:
    """[Eval] OpenHarness型採点 — 9点未満はREJECT"""
    return f"""あなたは厳格なJUCEプラグイン開発品質評価官です。
以下の実装案/設計図を「OpenHarness Evaluation Standard v1.0」に従い採点してください。

採点基準:
- カテゴリA: UI設計 (4点満点) — 座標精度、パラメータID、DSPチェーン、ノブ仕様
- カテゴリB: コード品質 (4点満点) — LookAndFeel実装、リソース管理、CMake、エラーハンドリング
- カテゴリC: ワークフロー遵守 (2点満点) — フロー準拠、Gemmaゲート準拠

合格ライン: 9点以上 → PASS
条件付き合格: 8点 → CONDITIONAL_PASS（軽微な懸念のみ）
不合格: 7点以下 → REJECT（修正・再提出が必須）

詳細採点基準:
{eval_harness[:2000] if eval_harness else '（docs/09_self_evaluation_harness.md を参照）'}

---
【評価対象】
{eval_target}
---

## 採点結果

### カテゴリA: UI設計
- A1 座標精度: X.X / 1.0 — （理由）
- A2 パラメータID: X.X / 1.0 — （理由）
- A3 DSPチェーン: X.X / 1.0 — （理由）
- A4 ノブ仕様: X.X / 1.0 — （理由）
小計: X.X / 4.0

### カテゴリB: コード品質（コードがない場合は「N/A」）
小計: X.X / 4.0

### カテゴリC: ワークフロー
小計: X.X / 2.0

### 合計スコア: X.X / 10.0

## 判定
[ PASS ] または [ CONDITIONAL_PASS ] または [ REJECT ]

## 改善必須事項（REJECT/CONDITIONAL_PASS の場合）
（番号付き。具体的な修正内容を記載）

## 次のアクション
"""


def make_doc_prompt(docs_snapshot: dict) -> str:
    """[Doc] docs整合性チェック＆更新提案"""
    snapshot_text = "\n\n".join(
        f"=== {name} ===\n{content[:1500]}{'...(省略)' if len(content) > 1500 else ''}"
        for name, content in docs_snapshot.items()
    )
    return f"""あなたはJUCEプラグイン開発ドキュメント管理者です。
以下の内部ハーネス文書群の整合性をチェックし、更新が必要な箇所を特定してください。

チェック観点:
1. docs/01と他ドキュメントで矛盾した手順・ルールがないか
2. docs/08の「昇格済み」教訓が、対応するdocs/01-07に反映されているか
3. バージョン番号・日付が古いままになっていないか
4. 参照リンク（docs/XX_XXX.md）が実在するファイルを指しているか
5. 鉄の掟（4ステージフロー）がdocs/04と矛盾していないか

---
{snapshot_text}
---

## 整合性チェック結果

### 問題なし
（問題のないドキュメント一覧）

### 更新が必要な箇所
（ドキュメント名: 問題の説明 + 具体的な修正案）

### 優先度高（今すぐ修正すべき）
（箇条書き）

## 判定
[ ALL_GOOD ] または [ UPDATES_NEEDED ]
"""


def make_compress_prompt(context_content: str) -> str:
    """[Compress] コンテキスト圧縮 → docs/08への退避"""
    today = datetime.date.today().strftime("%Y-%m-%d")
    return f"""あなたはAI開発セッションの「重要情報アーキビスト」です。
以下のセッションコンテキストから、将来のセッションで必要になる重要情報を抽出し、
docs/08_memory_log.md のフォーマットで記録してください。

抽出基準:
- 解決したバグ・エラーとその対処法
- 確認された技術的事実（APIの動作、ツールの挙動等）
- 次回セッションで忘れると困るコンテキスト
- 廃棄すべき誤った情報（反証が確認されたもの）

不要な情報（抽出しない）:
- 一時的なファイルパス・変数名
- 試行錯誤の過程（結果のみ残す）
- 重複した会話

---
{context_content}
---

## 抽出された重要情報

以下のフォーマットで各教訓を出力してください:

### [{today}] （タイトル）
- **スコア**: 0.X / 1.0
- **カテゴリ**: Build / UI / DSP / Workflow / Git / Security
- **状況**: （何をしていたときか）
- **教訓**: （具体的に学んだこと）
- **昇格先**: （該当するdocsがあれば記載、なければ「未定」）
- **反証記録**: なし

---

## 廃棄推奨情報
（誤りが確認された情報があれば）

## 圧縮後の要約（次回セッションへの引き継ぎメモ）
（200文字以内で現在の状況を要約）
"""


def make_browser_prompt(url: str, raw_content: str) -> str:
    """[Browser] ブラウザ取得情報の振り分け"""
    today = datetime.date.today().strftime("%Y-%m-%d")
    return f"""あなたはJUCEプラグイン開発ハーネスのドキュメント管理者です。
以下のWebコンテンツを分析し、内部ハーネス（docs/01-11）への振り分けを提案してください。

取得日時: {today}
ソースURL: {url}

分類カテゴリ:
- [→ docs/02] JUCE API変更・ビルド技術情報
- [→ docs/08] 新しい教訓候補（スコア0.3で記録）
- [→ docs/10] セキュリティ情報
- [→ docs/07] SNSトレンド・コピー素材
- [→ DISCARD] 無関係なコンテンツ

---
{raw_content[:3000]}{'...(省略)' if len(raw_content) > 3000 else ''}
---

## 振り分け結果

| 情報 | 振り分け先 | 理由 |
|------|-----------|------|
（テーブル形式で記載）

## docs/08 への追記案（教訓候補がある場合）

### [{today}] （タイトル）
- **スコア**: 0.3 / 1.0
- **カテゴリ**: （カテゴリ）
- **教訓**: （内容）

## 判定
[ VALUABLE ] または [ PARTIALLY_VALUABLE ] または [ DISCARD ]
"""


# ── メイン処理 ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Gemma Local Assistant ブリッジスクリプト v2.0"
    )
    parser.add_argument(
        "--mode",
        choices=["design", "debug", "copy", "eval", "doc", "compress", "browser"],
        required=True,
        help=(
            "動作モード:\n"
            "  design   = 座標検証\n"
            "  debug    = エラー診断\n"
            "  copy     = SNSコピー生成\n"
            "  eval     = OpenHarness採点（9点未満REJECT）\n"
            "  doc      = docs整合性チェック＆更新提案\n"
            "  compress = コンテキスト圧縮→docs/08退避\n"
            "  browser  = ブラウザ情報振り分け"
        )
    )
    parser.add_argument("--log",          default=None, help="[debug] エラーログファイルのパス")
    parser.add_argument("--eval-target",  default=None, help="[eval] 評価対象ファイルのパス（省略時はblueprint.md）")
    parser.add_argument("--context-file", default=None, help="[compress] 圧縮対象のコンテキストファイルパス")
    parser.add_argument("--url",          default="(不明)", help="[browser] ソースURL")
    parser.add_argument("--browser-content", default=None, help="[browser] ブラウザ取得コンテンツのファイルパス")
    parser.add_argument("--plugin-name",  default="CALLOUT",                            help="[copy] プラグイン名")
    parser.add_argument("--plugin-desc",  default="ハードなサチュレーションとKrump魂のディストーション", help="[copy] 効果説明")
    parser.add_argument("--blueprint",    default=BLUEPRINT_PATH,                       help="[design/eval] blueprint.mdのパス")
    parser.add_argument("--output",       choices=["clipboard", "file", "stdout"], default="clipboard",
                        help="出力先 (clipboard / file / stdout)")
    parser.add_argument("--send-to-ollama", action="store_true", help="Ollama APIに直接送信して結果を表示")
    parser.add_argument("--model",        default="gemma2:9b",  help="[--send-to-ollama] 使用モデル名")
    parser.add_argument("--save-to-log",  action="store_true",  help="[compress] 結果をdocs/08に自動追記")

    args = parser.parse_args()

    # ── プロンプト生成 ──
    if args.mode == "design":
        content = read_file(args.blueprint)
        prompt = make_design_prompt(content)

    elif args.mode == "debug":
        if args.log:
            content = read_file(args.log)
        else:
            print("[INFO] エラーログをペーストしてください（空行2回で終了）:")
            lines, blank_count = [], 0
            while True:
                try:
                    line = input()
                    if line == "":
                        blank_count += 1
                        if blank_count >= 2: break
                    else:
                        blank_count = 0
                    lines.append(line)
                except EOFError:
                    break
            content = "\n".join(lines)
        prompt = make_debug_prompt(content)

    elif args.mode == "copy":
        prompt = make_copy_prompt(args.plugin_name, args.plugin_desc)

    elif args.mode == "eval":
        target_path = args.eval_target or args.blueprint
        eval_target = read_file(target_path)
        eval_harness = read_file_optional(EVAL_HARNESS_PATH)
        prompt = make_eval_prompt(eval_target, eval_harness)

    elif args.mode == "doc":
        # 主要docsのスナップショットを収集
        doc_files = {
            "01_workflow_standard.md": "01_workflow_standard.md",
            "04_agent_workflow.md":    "04_agent_workflow.md",
            "07_gemma_local_assistant.md": "07_gemma_local_assistant.md",
            "08_memory_log.md":        "08_memory_log.md",
        }
        snapshot = {}
        for label, fname in doc_files.items():
            fpath = os.path.join(DOCS_DIR, fname)
            snapshot[label] = read_file_optional(fpath, f"（{fname} が見つかりません）")
        prompt = make_doc_prompt(snapshot)

    elif args.mode == "compress":
        if args.context_file:
            content = read_file(args.context_file)
        else:
            print("[INFO] 圧縮したいコンテキストをペーストしてください（空行2回で終了）:")
            lines, blank_count = [], 0
            while True:
                try:
                    line = input()
                    if line == "":
                        blank_count += 1
                        if blank_count >= 2: break
                    else:
                        blank_count = 0
                    lines.append(line)
                except EOFError:
                    break
            content = "\n".join(lines)
        prompt = make_compress_prompt(content)

    elif args.mode == "browser":
        if args.browser_content:
            raw_content = read_file(args.browser_content)
        else:
            print("[INFO] ブラウザ取得コンテンツをペーストしてください（空行2回で終了）:")
            lines, blank_count = [], 0
            while True:
                try:
                    line = input()
                    if line == "":
                        blank_count += 1
                        if blank_count >= 2: break
                    else:
                        blank_count = 0
                    lines.append(line)
                except EOFError:
                    break
            raw_content = "\n".join(lines)
        prompt = make_browser_prompt(args.url, raw_content)

    # ── Ollama直接送信 ──
    if args.send_to_ollama:
        print(f"[INFO] Ollamaに送信中... (model: {args.model})")
        result = send_to_ollama(prompt, model=args.model)
        print("\n" + "="*60)
        print("【Gemma応答】")
        print("="*60)
        print(result)

        # compress モードで --save-to-log が付いていたら自動追記
        if args.mode == "compress" and args.save_to_log:
            today = datetime.date.today().strftime("%Y-%m-%d")
            entry = f"---\n\n<!-- compress自動記録 {today} -->\n{result}"
            append_to_memory_log(entry)
        return

    # ── 出力 ──
    label_map = {
        "design":   "設計チェック",
        "debug":    "デバッグ診断",
        "copy":     "SNSコピー生成",
        "eval":     "OpenHarness採点",
        "doc":      "docs整合性チェック",
        "compress": "コンテキスト圧縮",
        "browser":  "ブラウザ情報振り分け",
    }
    label = label_map.get(args.mode, args.mode)

    if args.output == "clipboard":
        if copy_to_clipboard(prompt):
            print(f"[OK] Gemmaプロンプトをクリップボードにコピーしました。")
            print(f"     モード: {label} | 文字数: {len(prompt)}")
            print(f"     Gemmaに貼り付けてください（Ollama / LM Studio）。")
            if args.mode == "eval":
                print(f"     ⚡ 9点未満は REJECT — 修正後に再実行してください。")
        else:
            print("[WARN] クリップボードへのコピーに失敗しました。--output stdout で確認してください。")
            print("\n" + prompt)
    elif args.output == "file":
        out_path = os.path.join(PROJECT_ROOT, "gemma_prompt_output.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(prompt)
        print(f"[OK] プロンプトを保存しました: {out_path}")
    elif args.output == "stdout":
        print(prompt)


if __name__ == "__main__":
    main()
