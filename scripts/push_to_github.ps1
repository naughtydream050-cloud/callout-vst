# CallOut — GitHub push スクリプト
# 実行: powershell -ExecutionPolicy Bypass -File scripts\push_to_github.ps1
# 変更をコミットしてmainにpushする

$ErrorActionPreference = "Stop"
$repoRoot = "C:\Users\user\OneDrive\Desktop\開発\CallOut"

Set-Location $repoRoot

# index.lock 自動削除（コードセッションハング後の残留ファイル対策）
$lockFile = Join-Path $repoRoot ".git\index.lock"
if (Test-Path $lockFile) {
    Remove-Item $lockFile -Force
    Write-Host "[AUTO] Removed stale index.lock" -ForegroundColor Yellow
}

Write-Host "[GIT] Status:" -ForegroundColor Cyan
git status --short

Write-Host "`n[GIT] Adding all changes..." -ForegroundColor Cyan
git add -A

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
$msg = "feat: image knob rotation + amber arc, CI generator fix, path migration script [$timestamp]"
Write-Host "[GIT] Committing: $msg" -ForegroundColor Cyan
git commit -m $msg

Write-Host "[GIT] Pushing to origin/main..." -ForegroundColor Cyan
git push origin main

Write-Host "`n[DONE] Push complete!" -ForegroundColor Green
Write-Host "GitHub Actions: https://github.com/naughtydream050-cloud/callout-vst/actions"
