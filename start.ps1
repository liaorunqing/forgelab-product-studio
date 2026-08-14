$ErrorActionPreference = 'Stop'
$port = 8000
Start-Process "http://127.0.0.1:$port/"
if (Test-Path "$PSScriptRoot\ForgeLabServer.exe") {
  & "$PSScriptRoot\ForgeLabServer.exe"
} else {
  py -m uvicorn backend:app --host 127.0.0.1 --port $port
}
