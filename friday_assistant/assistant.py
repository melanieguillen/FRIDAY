from __future__ import annotations

import argparse
import platform
import re
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
    audio_device: int | str | None
    require_locked_or_idle: bool
    idle_arm_seconds: float


def macos_session_is_locked() -> bool:
    if platform.system() != "Darwin":
        return False

    try:
        result = subprocess.run(
            ["/usr/sbin/ioreg", "-l", "-n", "Root", "-d", "1"],
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception:
        return False

    return '"IOConsoleLocked" = Yes' in result.stdout


def macos_idle_seconds() -> float | None:
    if platform.system() != "Darwin":
        return None

    try:
        result = subprocess.run(
            ["/usr/sbin/ioreg", "-r", "-c", "IOHIDSystem", "-k", "HIDIdleTime"],
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None

    match = re.search(r'"HIDIdleTime"\s*=\s*(\d+)', result.stdout)
    if match:
        return float(match.group(1)) / 1_000_000_000

    return None


class WakeGate:
    def __init__(self, *, require_locked_or_idle: bool, idle_arm_seconds: float) -> None:
        self.require_locked_or_idle = require_locked_or_idle
        self.idle_arm_seconds = idle_arm_seconds
        self._armed = not require_locked_or_idle
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_ignored_at = 0.0

    def start(self) -> None:
        if not self.require_locked_or_idle:
            print("FRIDAY will trigger while the computer is active.")
            return

        self._thread = threading.Thread(target=self._monitor, name="friday-wake-gate", daemon=True)
        self._thread.start()
        print(
            "FRIDAY will only trigger after the Mac is locked "
            f"or idle for {self.idle_arm_seconds:.0f} seconds."
        )

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)

    def allow_trigger(self, source: str) -> bool:
        if not self.require_locked_or_idle:
            return True

        with self._lock:
            if self._armed:
                self._armed = False
                return True

        now = time.monotonic()
        if now - self._last_ignored_at > 10:
            print(f"Ignored {source}; FRIDAY is waiting for lock or idle.")
            self._last_ignored_at = now

        return False

    def _monitor(self) -> None:
        while not self._stop.is_set():
            reason = self._armed_reason()
            if reason:
                with self._lock:
                    was_armed = self._armed
                    self._armed = True
                if not was_armed:
                    print(f"FRIDAY armed because the Mac is {reason}.")

            self._stop.wait(2)

    def _armed_reason(self) -> str | None:
        if macos_session_is_locked():
            return "locked"

        idle_seconds = macos_idle_seconds()
        if idle_seconds is not None and idle_seconds >= self.idle_arm_seconds:
            return f"idle for {idle_seconds:.0f} seconds"

        return None


class FridayAssistant:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._last_triggered_at = 0.0
        self._trigger_lock = threading.Lock()
        self._gate = WakeGate(
            require_locked_or_idle=settings.require_locked_or_idle,
            idle_arm_seconds=settings.idle_arm_seconds,
        )

    def start_gate(self) -> None:
        self._gate.start()

    def stop_gate(self) -> None:
        self._gate.stop()

    def trigger(self, source: str, *, force: bool = False) -> None:
        if not force and not self._gate.allow_trigger(source):
            return

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

    def _run(self, command: list[str], *, description: str) -> int:
        if self.settings.dry_run:
            print(f"[dry-run] {description}: {' '.join(command)}")
            return 0

        try:
            result = subprocess.run(command, check=False, capture_output=True, text=True)
        except FileNotFoundError:
            print(f"Skipped {description}: command not found: {command[0]}")
            return 127

        if result.returncode != 0:
            message = (result.stderr or result.stdout).strip()
            if message:
                print(f"Skipped {description}: {message}")
            else:
                print(f"Skipped {description}: command exited with {result.returncode}")

        return result.returncode

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
            opened_spotify = self._run(
                ["open", SPOTIFY_LIKED_SONGS_URI],
                description="open Spotify Liked Songs",
            )
            if opened_spotify != 0:
                self._run(
                    ["open", SPOTIFY_LIKED_SONGS_WEB_URL],
                    description="open Spotify Liked Songs in browser",
                )
                return

            if not self.settings.dry_run:
                time.sleep(1.5)
            self._run(
                [
                    "osascript",
                    "-e",
                    'tell application "Spotify"',
                    "-e",
                    "activate",
                    "-e",
                    "play",
                    "-e",
                    "end tell",
                ],
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
        audio_device: int | str | None,
    ) -> None:
        self.callback = callback
        self.threshold = threshold
        self.clap_window_seconds = clap_window_seconds
        self.audio_device = audio_device
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

        try:
            self._stream = sd.InputStream(
                channels=1,
                callback=on_audio,
                blocksize=1024,
                device=self.audio_device,
            )
            self._stream.start()
        except Exception as exc:
            raise RuntimeError(f"Could not start clap listener: {exc}") from exc

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
    parser.add_argument(
        "--idle-arm-seconds",
        type=float,
        default=300.0,
        help="Arm FRIDAY after this many seconds with no user input.",
    )
    parser.add_argument(
        "--always-trigger",
        action="store_true",
        help="Trigger even while the computer is active. Useful for testing.",
    )
    parser.add_argument("--no-input", action="store_true", help="Disable mouse and keyboard detection.")
    parser.add_argument("--no-claps", action="store_true", help="Disable two-clap detection.")
    parser.add_argument(
        "--audio-device",
        help="Audio input device index or name to use for clap detection.",
    )
    parser.add_argument(
        "--list-audio-devices",
        action="store_true",
        help="Print available audio devices and exit.",
    )
    parser.add_argument("--run-once", action="store_true", help="Run the welcome sequence once and exit.")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without opening apps or speaking.")
    return parser.parse_args(argv)


def coerce_audio_device(value: str | None) -> int | str | None:
    if value is None:
        return None

    try:
        return int(value)
    except ValueError:
        return value


def list_audio_devices() -> int:
    try:
        import sounddevice as sd
    except ImportError:
        print("Missing dependency: sounddevice. Run `pip install -r requirements.txt`.", file=sys.stderr)
        return 1

    print(sd.query_devices())
    print(f"default {sd.default.device}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.list_audio_devices:
        return list_audio_devices()

    assistant = FridayAssistant(
        Settings(
            welcome_message=args.welcome,
            clap_threshold=args.clap_threshold,
            clap_window_seconds=args.clap_window,
            cooldown_seconds=args.cooldown,
            dry_run=args.dry_run,
            enable_input=not args.no_input,
            enable_claps=not args.no_claps,
            audio_device=coerce_audio_device(args.audio_device),
            require_locked_or_idle=not args.always_trigger,
            idle_arm_seconds=args.idle_arm_seconds,
        )
    )

    if args.run_once:
        assistant.trigger("manual run", force=True)
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
                audio_device=assistant.settings.audio_device,
            )
        )

    if not listeners:
        print("Nothing to listen for. Remove --no-input or --no-claps, or use --run-once.")
        return 2

    try:
        assistant.start_gate()

        started_listeners: list[object] = []
        for listener in listeners:
            try:
                listener.start()
                started_listeners.append(listener)
            except RuntimeError as exc:
                print(exc, file=sys.stderr)

        if not started_listeners:
            print("No listeners started.")
            return 1

        print("FRIDAY is running. Press Ctrl+C to quit.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down FRIDAY.")
    finally:
        for listener in locals().get("started_listeners", []):
            stop = getattr(listener, "stop", None)
            if stop:
                stop()
        assistant.stop_gate()

    return 0
