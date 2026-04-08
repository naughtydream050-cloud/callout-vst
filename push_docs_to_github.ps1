# push_docs_to_github.ps1
# 使い方:
#   1. 環境変数を設定（PowerShellで一度だけ）:
#      $env:GH_TOKEN = "ghp_..." （System → Environment Variables でも可）
#   2. このスクリプトを実行:
#      .\push_docs_to_github.ps1

# ── トークン取得（環境変数から）──────────────────────────────────
if (-not $env:GH_TOKEN) {
    Write-Host "[ERROR] 環境変数 GH_TOKEN が設定されていません。" -ForegroundColor Red
    Write-Host "        PowerShellで以下を実行してから再実行してください:" -ForegroundColor Yellow
    Write-Host '        $env:GH_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxx"' -ForegroundColor White
    exit 1
}

# ── パス設定（$PSScriptRoot ベース = 日本語パス対応）────────────
$repo   = $PSScriptRoot
$remote = "https://naughtydream050-cloud:$($env:GH_TOKEN)@github.com/naughtydream050-cloud/callout-vst.git"

Write-Host "[INFO] リポジトリ: $repo" -ForegroundColor Gray

Set-Location $repo

git remote set-url origin $remote

# docs/ と scripts/ を両方 add（新規ファイルをすべて含む）
git add docs/
git add scripts/

$commitMsg = "Update: harness docs and gemma_bridge v2.0 [$(Get-Date -Format 'yyyy-MM-dd HH:mm')]"
git commit -m $commitMsg
git push origin main

# リモートURLからトークンを除去（ログ汚染防止）
git remote set-url origin "https://github.com/naughtydream050-cloud/callout-vst.git"

Write-Host ""
Write-Host "=== Done! ===" -ForegroundColor Green
Write-Host "Docs:    https://github.com/naughtydream050-cloud/callout-vst/tree/main/docs"    -ForegroundColor Cyan
Write-Host "Scripts: https://github.com/naughtydream050-cloud/callout-vst/tree/main/scripts" -ForegroundColor Cyan
Write-Host ""
Write-Host "--- 今日の成果 ---" -ForegroundColor Yellow
Write-Host "docs/08_memory_log.md              ECC永続メモリ＆信頼度スコア体系"       -ForegroundColor White
Write-Host "docs/09_self_evaluation_harness.md OpenHarness採点基準（9点合格制）"      -ForegroundColor White
Write-Host "docs/10_safety_guardrails.md       設定弱体化禁止令＆監視ルール"          -ForegroundColor White
Write-Host "docs/11_browser_context.md         Browser Use受け入れ口（仮設）"        -ForegroundColor White
Write-Host "scripts/gemma_bridge.py v2.0       eval/doc/compress/browserモード追加"  -ForegroundColor White
