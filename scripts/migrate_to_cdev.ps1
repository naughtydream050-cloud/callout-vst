# CallOut プロジェクトを C:\dev\CallOut へ移行するスクリプト
# 実行: powershell -ExecutionPolicy Bypass -File scripts\migrate_to_cdev.ps1

$src = "C:\Users\user\OneDrive\Desktop\開発\CallOut"
$dst = "C:\dev\CallOut"

if (Test-Path $dst) {
    Write-Host "[SKIP] $dst already exists. Nothing to do." -ForegroundColor Yellow
    exit 0
}

New-Item -ItemType Directory -Path "C:\dev" -Force | Out-Null
Write-Host "[COPY] $src -> $dst ..." -ForegroundColor Cyan
Copy-Item -Path $src -Destination $dst -Recurse -Force
Write-Host "[DONE] Project copied to $dst" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Open C:\dev\CallOut in your IDE"
Write-Host "  2. cmake -B build -A x64 -DCMAKE_BUILD_TYPE=Release"
Write-Host "  3. cmake --build build --config Release"
