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
4. In that Discord application, upload `chibi-cloud-watermark.png` as a Rich Presence asset with the key `chibi_cloud`.
5. Copy `config.example.json` to `config.json` if needed.
6. Put your Application ID into `config.json`.
7. Launch Discord desktop.

PresenceCast now sends `large_image=chibi_cloud` by default, so the Discord activity card will use the mascot once that asset exists on the Discord application.

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
- Release builds can inject a Discord Application ID from the GitHub secret `PRESENCECAST_CLIENT_ID`
- Release builds also inject the default mascot asset key `chibi_cloud`
- Keep the public repo blank in `config.json`; let releases provide the ready-to-run config

## Notes

- A Discord Application ID is not a private token, so users can still discover it from a shipped desktop app
- The safe approach is to keep it out of the public source repo and inject it only during release builds

## License

MIT
