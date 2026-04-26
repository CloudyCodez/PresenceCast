# PresenceCast

PresenceCast is a Windows desktop utility for shaping Discord Rich Presence with a cinematic studio workflow. PresenceCast 2.0 expands the original utility into a richer desktop experience for crafting narrative, timing, party state, art direction, and clickable surfaces.

## Features

- Studio-style UI with a richer live Discord card preview
- Custom activity name, details, and state through Discord RPC
- Activity type and status display mode controls
- Static, elapsed, and countdown timing modes
- Party context with current/max sizing plus session identifiers
- Join, spectate, and match secret fields for advanced social flows
- Activity-specific artwork for `Playing`, `Listening`, `Watching`, and `Competing`
- Default mascot badge on every activity
- Emoji-aware artwork override for common gaming, music, and watching emojis
- Manual image overrides using asset keys or external image URLs
- Up to two custom Discord buttons
- Field URL support for `details`, `state`, large art, and badge art
- Built-in scene presets
- Built-in branded theme bundles
- Local saved profiles for repeat setups
- Automatic recent-cast history
- Theme import/export as JSON bundles
- Subtle live motion across the preview studio surfaces
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
- optional party metadata, timers, and session secrets when you fill them in
- up to two optional link buttons when you fill them in
- optional field URLs for richer clickable surfaces

If `Auto-match art from emojis` is enabled, PresenceCast can switch the artwork automatically when your text includes common cues like `🎮`, `🎧`, `🎵`, `📺`, `🎬`, or `👀`.

Saved profiles are stored locally in `profiles.json` next to the app so you can keep repeat setups like work, study, or stream modes without cluttering the repo. Recent successful broadcasts are stored in `history.json`.

Exported theme bundles are stored wherever you choose, with `theme_bundles\` used as the default suggestion folder next to the app.

## Discord Notes

- Rich Presence via RPC requires the Discord desktop client to be running
- Custom buttons are only visible to other users, not to the account sending the presence
- Discord surfaces reward concise `details` and `state` text that fit on one line
- Discord recommends expressive 1024x1024 artwork for Rich Presence assets

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
