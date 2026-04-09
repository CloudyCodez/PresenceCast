# PresenceCast

PresenceCast is a Windows desktop utility for shaping Discord Rich Presence with a custom activity name, details, state, display mode, and timer.

## Features

- Custom activity name through Discord RPC
- Details and state editing
- Display mode selection
- Activity type selection
- Built-in templates
- Packaged Windows `.exe`

## Requirements

- Windows
- Discord desktop app running
- Python 3.x for local builds

## Setup

1. Open the Discord Developer Portal.
2. Create a new application.
3. Copy the numeric **Application ID**.
4. Copy `config.example.json` to `config.json` if needed.
5. Put your Application ID into `config.json`.
6. Launch Discord desktop.

## Run From Source

```powershell
python app.py
```

## Build The Executable

```powershell
.\build.ps1
```

The built executable is created at `dist\PresenceCast.exe`.

## GitHub Releases

This repo includes a GitHub Actions workflow at `.github/workflows/release.yml`.

- Pushing a tag like `v1.0.0` builds the Windows executable
- The workflow uploads `PresenceCast.exe`
- Tagged builds are published to GitHub Releases automatically

## License

MIT
