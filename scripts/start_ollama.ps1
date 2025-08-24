# === 设置 Ollama 环境变量 ===
$env:OLLAMA_MODELS = "embeddings/.ollama/models"
$env:OLLAMA_CACHE  = "embeddings/.ollama/cache"
$env:NO_PROXY      = "127.0.1.1,localhost"

Write-Host "=============================="
Write-Host "OLLAMA_MODELS = $env:OLLAMA_MODELS"
Write-Host "OLLAMA_CACHE  = $env:OLLAMA_CACHE"
Write-Host "NO_PROXY      = $env:NO_PROXY"
Write-Host "=============================="
Write-Host "环境变量已设置完成！"
Write-Host ""

# 打开交互式 shell，保持变量有效
powershell -NoExit
