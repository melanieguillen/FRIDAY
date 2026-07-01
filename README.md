# FRIDAY

FRIDAY is a small macOS-first personal wake assistant. It waits until the Mac is locked or idle, then listens for mouse movement, keyboard activation, or two claps. When triggered, it wakes the display, says:

> Welcome, doctor Soler

After that it opens Spotify to your Liked Songs, starts playback, and opens Claude.

If the native Spotify app is not installed, FRIDAY opens Spotify Web instead. Browser autoplay rules may require you to press play manually in that fallback path.

## What it can and cannot do

FRIDAY can wake the display and react when this script is already running. It does not bypass a locked screen, type your password, or defeat macOS security.

When a Mac is truly asleep, Python is paused and cannot hear claps or watch keyboard/mouse input. FRIDAY handles this safely by arming itself after the Mac is locked or has been idle for a while; once the machine wakes or receives an allowed event, it can run the welcome sequence.

## Requirements

- macOS
- Python 3.10+
- Spotify installed and logged in for native playback
- A browser logged into Claude
- Microphone permission for the app running FRIDAY
- Accessibility permission for the app running FRIDAY if you use mouse/keyboard detection

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

By default, FRIDAY only triggers after the Mac is locked or idle for 5 minutes. Change that idle window:

```bash
python -m friday_assistant --idle-arm-seconds 60
```

Test without waiting for lock/idle:

```bash
python -m friday_assistant --run-once --dry-run
python -m friday_assistant --always-trigger
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

## macOS permissions

For keyboard and mouse detection:

1. Open **System Settings**.
2. Go to **Privacy & Security**.
3. Add the app running FRIDAY under **Accessibility**. This may be Terminal, iTerm, Python, or Codex depending on how you start it.

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
