# FRIDAY

FRIDAY is a small macOS-first personal wake assistant. It waits until the Mac moves from locked to unlocked, then launches your work session. When triggered, it wakes the display, says:

> Welcome, doctor Soler

After that it opens Spotify Web to your Liked Songs, starts playback, and starts Claude Code in a new Terminal window.

## What it can and cannot do

FRIDAY can wake the display and react when this script is already running. It does not bypass a locked screen, type your password, or defeat macOS security.

When a Mac is truly asleep, Python is paused and cannot hear claps or watch keyboard/mouse input. FRIDAY handles this safely by waiting until it sees the Mac move from locked to unlocked.

FRIDAY must be running before you lock the Mac or close the lid. If you quit the terminal or reboot, start FRIDAY again.

## Requirements

- macOS
- Python 3.10+
- A browser logged into Spotify
- Claude Code installed and logged in
- Microphone permission for the app running FRIDAY
- Accessibility permission for the app running FRIDAY to start Spotify Web playback or use mouse/keyboard detection
- Input Monitoring permission for the app running FRIDAY if mouse/keyboard events do not arrive

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

Start FRIDAY:

```bash
python -m friday_assistant
```

By default, FRIDAY triggers only after the Mac unlocks.

To also trigger after a wake/resume pause:

```bash
python -m friday_assistant --resume-trigger unlock-or-resume
```

Change the wake/resume pause threshold if resume triggers are enabled:

```bash
python -m friday_assistant --resume-gap-seconds 30
```

Manual test commands fire immediately. Use these only to verify the welcome sequence:

```bash
python -m friday_assistant --run-once --dry-run
python -m friday_assistant --run-once
```

Run only the unlock monitor:

```bash
python -m friday_assistant --no-input --no-claps
```

Enable the clap listener as an extra trigger after lock/idle:

```bash
python -m friday_assistant --claps
```

Enable mouse and keyboard as extra triggers after lock/idle:

```bash
python -m friday_assistant --input-events
```

If your room is noisy, raise the clap threshold:

```bash
python -m friday_assistant --clap-threshold 0.5
```

List microphones and choose one for claps:

```bash
python -m friday_assistant --list-audio-devices
python -m friday_assistant --audio-device "MacBook Pro Microphone"
```

FRIDAY opens Spotify Web by default because the Spotify desktop app is optional. It waits 5 seconds for your Liked Songs page to load, then sends the space-bar play command. Make sure your browser is already logged into Spotify.

If Spotify needs more time to load:

```bash
python -m friday_assistant --spotify-web-play-delay 8
```

To open Spotify Web without pressing play:

```bash
python -m friday_assistant --no-spotify-web-play
```

If you install Spotify.app later:

```bash
python -m friday_assistant --spotify-target app --spotify-app "Spotify"
```

FRIDAY opens Claude Code in Terminal by default. To choose where Claude Code starts:

```bash
python -m friday_assistant --claude-workdir "~/Documents"
```

If the `claude` command has a different name or path:

```bash
python -m friday_assistant --claude-command "/opt/homebrew/bin/claude"
```

## macOS permissions

For keyboard and mouse detection:

1. Open **System Settings**.
2. Go to **Privacy & Security**.
3. Add the app running FRIDAY under **Accessibility**. This may be Terminal, iTerm, Python, or Codex depending on how you start it.
4. If FRIDAY starts without warnings but does not react to movement or keys, add the same app under **Input Monitoring**.

For clap detection:

1. Open **System Settings**.
2. Go to **Privacy & Security**.
3. Add the app running FRIDAY under **Microphone**. This may be Terminal, iTerm, Python, or Codex depending on how you start it.

## Publish to GitHub

This local project is already ready to publish. It expects this remote:

```bash
https://github.com/melanieguillen/FRIDAY.git
```

If GitHub CLI is installed and authenticated, create the empty GitHub repo:

```bash
gh repo create melanieguillen/FRIDAY --public
git push -u origin main
```

If you prefer the GitHub website, create an empty public repo named `FRIDAY` under `melanieguillen` with no README, then run:

```bash
git push -u origin main
```
