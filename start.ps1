$ErrorActionPreference = 'Stop'
if (Test-Path "$PSScriptRoot\ForgeLabServer.exe") {
  & "$PSScriptRoot\ForgeLabServer.exe"
} else {
  py -m uvicorn backend:app --host 127.0.0.1 --port $port
}
