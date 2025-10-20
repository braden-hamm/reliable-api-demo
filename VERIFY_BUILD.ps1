Invoke-RestMethod -Uri "http://localhost:8080/healthz" -TimeoutSec 5 | Out-Null; Write-Host "OK" -ForegroundColor Green
