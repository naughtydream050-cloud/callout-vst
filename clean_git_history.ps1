# clean_git_history.ps1
# git 履歴から機密情報（GitHub トークン）を含むコミットを除去する。
# PowerShell で実行: .\clean_git_history.ps1

$repo = $PSScriptRoot
Set-Location $repo

Write-Host "=== 現在の git 状態を確認 ===" -ForegroundColor Yellow
git status
git log --oneline -10

Write-Host ""
Write-Host "未コミット変更があればコミット..." -ForegroundColor Yellow
$status = git status --porcelain
if ($status) {
    git add -A
    git commit -m "fix: remove exposed GitHub token from all files"
    Write-Host "[OK] クリーンアップコミット完了" -ForegroundColor Green
} else {
    Write-Host "[INFO] 変更なし。スキップ。" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== 履歴を確認してリセット範囲を決定 ===" -ForegroundColor Yellow
git log --oneline -10

Write-Host ""
Write-Host "直近3コミットを soft reset でまとめます..." -ForegroundColor Yellow
git reset --soft HEAD~3

Write-Host ""
Write-Host "スカッシュコミットを作成..." -ForegroundColor Yellow
git commit -m "chore: squash history - docs, harness, and cleanup"

Write-Host ""
Write-Host "=== 最終確認 ===" -ForegroundColor Yellow
git log --oneline -5

Write-Host ""
Write-Host "=== 完了 ===" -ForegroundColor Green
Write-Host "ローカル履歴を整理しました。" -ForegroundColor Cyan
Write-Host "次のステップ: 環境変数を設定してから push_docs_to_github.ps1 を実行してください。" -ForegroundColor Cyan
Write-Host ""
Write-Host "環境変数の設定方法:" -ForegroundColor Yellow
Write-Host '  $env:GH_TOKEN = "ghp_新しいトークン"  # GitHub で Personal Access Token を再発行してください' -ForegroundColor White
Write-Host ""
Write-Host "⚠️  旧トークン (ghp_pE0R...) は GitHub で今すぐ無効化してください:" -ForegroundColor Red
Write-Host "   https://github.com/settings/tokens" -ForegroundColor White
