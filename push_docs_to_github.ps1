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

# docs/ scripts/ .github/ CMakeLists.txt Source/ を add
git add docs/
git add scripts/
git add .github/
git add CMakeLists.txt
git add Source/KnobLookAndFeel.h
git add Source/KnobLookAndFeel.cpp
git add .gitignore
git add insta_base_sync.py

$commitMsg = "feat: killstreet insta_base_sync.py 移植 + post.yml (毎週日曜22JST) [$(Get-Date -Format 'yyyy-MM-dd HH:mm')]"
git commit -m $commitMsg
git push origin main

# リモートURLからトークンを除去（ログ汚染防止）
git remote set-url origin "https://github.com/naughtydream050-cloud/callout-vst.git"

Write-Host ""
Write-Host "=== Done! ===" -ForegroundColor Green
Write-Host "Docs:    https://github.com/naughtydream050-cloud/callout-vst/tree/main/docs"      -ForegroundColor Cyan
Write-Host "Scripts: https://github.com/naughtydream050-cloud/callout-vst/tree/main/scripts"   -ForegroundColor Cyan
Write-Host "Actions: https://github.com/naughtydream050-cloud/callout-vst/actions"             -ForegroundColor Cyan
Write-Host ""
Write-Host "--- 今日の成果 ---" -ForegroundColor Yellow
Write-Host ".github/workflows/build.yml        GitHub Actions CI (Windows VST3)"        -ForegroundColor White
Write-Host ".github/workflows/insta_sync.yml   BASE×Instagram 30分同期ワークフロー"     -ForegroundColor White
Write-Host "scripts/insta_base_sync.py         同期スクリプト＆Dead-End Detection"      -ForegroundColor White
Write-Host "scripts/check_token_health.py      Token Health Dashboard"                  -ForegroundColor White
Write-Host "docs/12_post_mortem_report.md      10件の失敗ログ分析＆防御設計"            -ForegroundColor White
Write-Host "docs/13_architecture_proposal.md   2026年API現状調査＋推奨アーキ"           -ForegroundColor White
Write-Host "docs/14_api_minefield_map.md       API地雷原マップ＋Self-Healingプロトコル" -ForegroundColor White
Write-Host "CMakeLists.txt                     FetchContent JUCE fallback追加"          -ForegroundColor White
Write-Host "Source/KnobLookAndFeel v2.0        Cold-Rolled Steel (V-Groove+amber)"     -ForegroundColor White
