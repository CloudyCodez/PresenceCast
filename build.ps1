$ErrorActionPreference = "Stop"

$pythonCandidates = @(
    "C:\Users\conno\AppData\Local\Python\bin\python.exe",
    (Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue),
    (Get-Command py -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue)
) | Where-Object { $_ }

$python = $pythonCandidates | Select-Object -First 1

if (-not $python) {
    throw "Python was not found. Install Python 3 and ensure python or py is available."
}

$clientId = $env:PRESENCECAST_CLIENT_ID
if ($clientId) {
    @"
{
  "client_id": "$clientId",
  "large_image_key": "chibi_cloud",
  "large_image_text": "PresenceCast by Cloud",
  "small_image_key": "chibi_cloud",
  "small_image_text": "PresenceCast by Cloud",
  "playing_image_key": "chibi_cloud_playing",
  "playing_image_text": "PresenceCast | Playing",
  "listening_image_key": "chibi_cloud_listening",
  "listening_image_text": "PresenceCast | Listening",
  "watching_image_key": "chibi_cloud_watching",
  "watching_image_text": "PresenceCast | Watching",
  "competing_image_key": "",
  "competing_image_text": "PresenceCast | Competing",
  "emoji_asset_override": true
}
"@ | Set-Content -LiteralPath "config.json" -Encoding utf8
} elseif (-not (Test-Path "config.json")) {
    Copy-Item -LiteralPath "config.example.json" -Destination "config.json"
}

& $python -m pip install -r requirements.txt
& $python generate_icon.py
& $python -m PyInstaller --noconfirm --onefile --windowed --add-data "config.json;." --add-data "presencecast.ico;." --add-data "presencecast.png;." --add-data "chibi_cloud.png;." --add-data "Chibi Cloud Playing.png;." --add-data "Chibi Cloud Listening.png;." --add-data "Chibi Cloud Watching.png;." --icon presencecast.ico --name PresenceCast app.py

Write-Host ""
Write-Host "Build complete:"
Write-Host "  dist\PresenceCast.exe"
