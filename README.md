# FRIDAY

FRIDAY is a small macOS-first personal wake assistant. It listens for mouse movement, keyboard activation, or two claps, then wakes the display, says:

> Welcome, doctor Soler

After that it opens Spotify to your Liked Songs, starts playback, and opens Claude.

## What it can and cannot do

FRIDAY can wake the display and react when this script is already running. It does not bypass a locked screen, type your password, or defeat macOS security. If the Mac is asleep or the microphone/input listeners are stopped, it cannot hear claps or detect keyboard/mouse activity.

## Requirements

- macOS
- Python 3.10+
- Spotify installed and logged in
- A browser logged into Claude
- Microphone permission for your terminal app
- Accessibility permission for your terminal app if you use mouse/keyboard detection

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

Test without opening anything:

```bash
python -m friday_assistant --run-once --dry-run
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

## macOS permissions

For keyboard and mouse detection:

1. Open **System Settings**.
2. Go to **Privacy & Security**.
3. Add your terminal app under **Accessibility**.

For clap detection:

1. Open **System Settings**.
2. Go to **Privacy & Security**.
3. Add your terminal app under **Microphone**.

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
