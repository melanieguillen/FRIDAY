from __future__ import annotations

import argparse
import platform
import subprocess
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Callable


WELCOME_MESSAGE = "Welcome, doctor Soler"
CLAUDE_URL = "https://claude.ai/new"
SPOTIFY_LIKED_SONGS_URI = "spotify:collection:tracks"
SPOTIFY_LIKED_SONGS_WEB_URL = "https://open.spotify.com/collection/tracks"


@dataclass(frozen=True)
class Settings:
    welcome_message: str
    clap_threshold: float
    clap_window_seconds: float
    cooldown_seconds: float
    dry_run: bool
    enable_input: bool
    enable_claps: bool


class FridayAssistant:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._last_triggered_at = 0.0
        self._trigger_lock = threading.Lock()

    def trigger(self, source: str) -> None:
        with self._trigger_lock:
            now = time.monotonic()
            if now - self._last_triggered_at < self.settings.cooldown_seconds:
                return
            self._last_triggered_at = now

        print(f"FRIDAY triggered by {source}.")
        self._wake_display()
        self._speak(self.settings.welcome_message)
        self._open_spotify_liked_songs()
        self._open_claude()

    def _run(self, command: list[str], *, description: str) -> None:
        if self.settings.dry_run:
            print(f"[dry-run] {description}: {' '.join(command)}")
            return

        try:
            subprocess.run(command, check=False)
        except FileNotFoundError:
            print(f"Skipped {description}: command not found: {command[0]}")

    def _wake_display(self) -> None:
        if platform.system() == "Darwin":
            self._run(["caffeinate", "-u", "-t", "2"], description="wake display")
        else:
            print("Wake display is only implemented for macOS.")

    def _speak(self, text: str) -> None:
        if platform.system() == "Darwin":
            self._run(["say", text], description="speak welcome message")
        else:
            print(text)

    def _open_spotify_liked_songs(self) -> None:
        if platform.system() == "Darwin":
            self._run(["open", SPOTIFY_LIKED_SONGS_URI], description="open Spotify Liked Songs")
            if not self.settings.dry_run:
                time.sleep(1.5)
            self._run(
                ["osascript", "-e", 'tell application "Spotify" to play'],
                description="start Spotify playback",
            )
            return

        self._run(["xdg-open", SPOTIFY_LIKED_SONGS_WEB_URL], description="open Spotify Liked Songs")

    def _open_claude(self) -> None:
        if platform.system() == "Darwin":
            self._run(["open", CLAUDE_URL], description="open Claude")
            return

        self._run(["xdg-open", CLAUDE_URL], description="open Claude")


class InputListener:
    def __init__(self, callback: Callable[[str], None]) -> None:
        self.callback = callback
        self._listeners: list[object] = []

    def start(self) -> None:
        try:
            from pynput import keyboard, mouse
        except ImportError as exc:
            raise RuntimeError("Missing dependency: pynput. Run `pip install -r requirements.txt`.") from exc

        mouse_listener = mouse.Listener(
            on_move=lambda _x, _y: self.callback("mouse movement"),
            on_click=lambda _x, _y, _button, _pressed: self.callback("mouse click"),
            on_scroll=lambda _x, _y, _dx, _dy: self.callback("mouse scroll"),
        )
        keyboard_listener = keyboard.Listener(on_press=lambda _key: self.callback("keyboard"))
        mouse_listener.start()
        keyboard_listener.start()
        self._listeners = [mouse_listener, keyboard_listener]
        print("Mouse and keyboard activation listener is running.")

    def stop(self) -> None:
        for listener in self._listeners:
            stop = getattr(listener, "stop", None)
            if stop:
                stop()


class ClapListener:
    def __init__(
        self,
        callback: Callable[[str], None],
        *,
        threshold: float,
        clap_window_seconds: float,
    ) -> None:
        self.callback = callback
        self.threshold = threshold
        self.clap_window_seconds = clap_window_seconds
        self._stream = None
        self._clap_times: deque[float] = deque(maxlen=4)
        self._last_clap_at = 0.0

    def start(self) -> None:
        try:
            import numpy as np
            import sounddevice as sd
        except ImportError as exc:
            raise RuntimeError(
                "Missing dependencies: sounddevice and numpy. Run `pip install -r requirements.txt`."
            ) from exc

        def on_audio(indata, _frames, _time_info, status) -> None:
            if status:
                print(f"Audio input status: {status}", file=sys.stderr)

            peak = float(np.max(np.abs(indata)))
            now = time.monotonic()
            if peak < self.threshold or now - self._last_clap_at < 0.08:
                return

            self._last_clap_at = now
            self._clap_times.append(now)
            while self._clap_times and now - self._clap_times[0] > self.clap_window_seconds:
                self._clap_times.popleft()

            if len(self._clap_times) >= 2:
                self._clap_times.clear()
                self.callback("two claps")

        self._stream = sd.InputStream(channels=1, callback=on_audio, blocksize=1024)
        self._stream.start()
        print("Two-clap listener is running.")

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="friday",
        description="FRIDAY wakes on mouse, keyboard, or two claps and launches your work session.",
    )
    parser.add_argument("--welcome", default=WELCOME_MESSAGE, help="Spoken welcome phrase.")
    parser.add_argument(
        "--clap-threshold",
        type=float,
        default=0.35,
        help="Audio peak threshold for clap detection. Raise this in noisy rooms.",
    )
    parser.add_argument(
        "--clap-window",
        type=float,
        default=0.75,
        help="Maximum seconds between two claps.",
    )
    parser.add_argument(
        "--cooldown",
        type=float,
        default=45.0,
        help="Seconds to ignore repeated wake events after FRIDAY runs.",
    )
    parser.add_argument("--no-input", action="store_true", help="Disable mouse and keyboard detection.")
    parser.add_argument("--no-claps", action="store_true", help="Disable two-clap detection.")
    parser.add_argument("--run-once", action="store_true", help="Run the welcome sequence once and exit.")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without opening apps or speaking.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    assistant = FridayAssistant(
        Settings(
            welcome_message=args.welcome,
            clap_threshold=args.clap_threshold,
            clap_window_seconds=args.clap_window,
            cooldown_seconds=args.cooldown,
            dry_run=args.dry_run,
            enable_input=not args.no_input,
            enable_claps=not args.no_claps,
        )
    )

    if args.run_once:
        assistant.trigger("manual run")
        return 0

    listeners: list[object] = []
    if assistant.settings.enable_input:
        listeners.append(InputListener(assistant.trigger))
    if assistant.settings.enable_claps:
        listeners.append(
            ClapListener(
                assistant.trigger,
                threshold=assistant.settings.clap_threshold,
                clap_window_seconds=assistant.settings.clap_window_seconds,
            )
        )

    if not listeners:
        print("Nothing to listen for. Remove --no-input or --no-claps, or use --run-once.")
        return 2

    for listener in listeners:
        try:
            listener.start()
        except RuntimeError as exc:
            print(exc, file=sys.stderr)

    print("FRIDAY is armed. Press Ctrl+C to quit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down FRIDAY.")
    finally:
        for listener in listeners:
            stop = getattr(listener, "stop", None)
            if stop:
                stop()

    return 0
