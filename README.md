# PresenceCast

PresenceCast is a Windows desktop utility for shaping Discord Rich Presence with a custom activity name, details, state, display mode, and timer.

## Features

- Custom activity name through Discord RPC
- Details and state editing
- Activity-specific artwork for `Playing`, `Listening`, and `Watching`
- Default mascot badge on every activity
- Emoji-aware artwork override for common gaming, music, and watching emojis
- Display mode selection
- Activity type selection
- Optional Discord buttons with URLs
- Built-in templates
- Local saved profiles for repeat setups
- Packaged Windows `.exe`

## Requirements

- Windows
- Discord desktop app running
- Python 3.x for local builds

## Setup

1. Open the Discord Developer Portal.
2. Create a new application.
3. Copy the numeric **Application ID**.
4. In that Discord application, upload these Rich Presence assets:
   - `chibi_cloud.png` with the key `chibi_cloud`
   - `Chibi Cloud Playing.png` with the key `chibi_cloud_playing`
   - `Chibi Cloud Listening.png` with the key `chibi_cloud_listening`
   - `Chibi Cloud Watching.png` with the key `chibi_cloud_watching`
5. Copy `config.example.json` to `config.json` if needed.
6. Put your Application ID into `config.json`.
7. Launch Discord desktop.

PresenceCast now sends:
- the mascot as the default small badge on every activity
- the matching activity art as the large image for `Playing`, `Listening`, and `Watching`
- the mascot as the large-image fallback when a specific activity asset is not configured
- up to two optional link buttons when you fill them in

If `Auto-match art from emojis` is enabled, PresenceCast can switch the artwork automatically when your text includes common cues like `🎮`, `🎧`, `🎵`, `📺`, `🎬`, or `👀`.

Saved profiles are stored locally in `profiles.json` next to the app so you can keep repeat setups like work, study, or stream modes without cluttering the repo.

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
- Release builds also inject the default mascot and activity asset keys automatically
- Keep the public repo blank in `config.json`; let releases provide the ready-to-run config

## Notes

- A Discord Application ID is not a private token, so users can still discover it from a shipped desktop app
- The safe approach is to keep it out of the public source repo and inject it only during release builds

## License

MIT
