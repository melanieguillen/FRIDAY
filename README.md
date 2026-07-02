# FRIDAY

FRIDAY is a small macOS-first personal wake assistant. It waits until the Mac is locked, idle, or resumed from sleep, then launches your work session. When triggered, it wakes the display, says:

> Welcome, doctor Soler

After that it opens the native Spotify app to your Liked Songs, starts playback, and opens the native Claude app.

## What it can and cannot do

FRIDAY can wake the display and react when this script is already running. It does not bypass a locked screen, type your password, or defeat macOS security.

When a Mac is truly asleep, Python is paused and cannot hear claps or watch keyboard/mouse input. FRIDAY handles this safely by triggering after Python resumes from a long pause, or after it sees the Mac move from locked to unlocked.

FRIDAY must be running before you lock the Mac or close the lid. If you quit the terminal or reboot, start FRIDAY again.

## Requirements

- macOS
- Python 3.10+
- Spotify installed and logged in for native playback
- Claude desktop app installed and logged in
- Microphone permission for the app running FRIDAY
- Accessibility permission for the app running FRIDAY if you use mouse/keyboard detection
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

By default, FRIDAY can trigger in three ways:

- after the Mac unlocks
- after the Mac wakes and FRIDAY notices it was paused for at least 60 seconds
- after the Mac has been locked or idle for 5 minutes, then a mouse/keyboard/clap event arrives

Change the idle window:

```bash
python -m friday_assistant --idle-arm-seconds 60
```

Change the wake/resume pause threshold:

```bash
python -m friday_assistant --resume-gap-seconds 30
```

Test without waiting for lock/idle:

```bash
python -m friday_assistant --run-once --dry-run
python -m friday_assistant --always-trigger
```

Run only the unlock/wake-resume monitor:

```bash
python -m friday_assistant --no-input --no-claps
```

Run only the clap listener:

```bash
python -m friday_assistant --no-input
```

Run only mouse and keyboard detection:

```bash
python -m friday_assistant --no-claps
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

FRIDAY opens native apps by default. If your app names are different:

```bash
python -m friday_assistant --spotify-app "Spotify" --claude-app "Claude"
```

If you ever want the older browser fallback behavior:

```bash
python -m friday_assistant --browser-fallback
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
