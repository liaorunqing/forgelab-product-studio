$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$dist = Join-Path $root 'dist\ForgeLab'
$zip = Join-Path $root 'dist\ForgeLab-Windows.zip'

Write-Host 'Preparing ForgeLab Windows package...'
Remove-Item (Join-Path $root 'dist') -Recurse -Force -ErrorAction SilentlyContinue
New-Item $dist -ItemType Directory -Force | Out-Null

python -m PyInstaller --noconfirm --clean --onedir --name ForgeLabServer `
  --add-data "index.html;." --add-data "styles.css;." --add-data "extras.css;." `
  --add-data "app.js;." --add-data ".env.example;." `
  --exclude-module torch --exclude-module tensorflow --exclude-module tensorboard `
  --exclude-module matplotlib --exclude-module pandas --exclude-module scipy `
  --exclude-module IPython --exclude-module pytest backend.py

Copy-Item (Join-Path $root 'dist\ForgeLabServer\*') $dist -Recurse -Force
Copy-Item (Join-Path $root 'start.ps1') $dist -Force
Copy-Item (Join-Path $root '.env.example') $dist -Force
Compress-Archive -Path (Join-Path $dist '*') -DestinationPath $zip -Force
Write-Host "Portable package: $zip"

$iscc = Get-Command iscc -ErrorAction SilentlyContinue
if ($iscc) {
  & $iscc.Source (Join-Path $root 'installer.iss')
  Write-Host 'Installer created under dist\installer.'
} else {
  Write-Host 'Inno Setup not found; skipped .exe installer. Install Inno Setup and rerun this script to create one.'
}
