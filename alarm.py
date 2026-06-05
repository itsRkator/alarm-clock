"""
alarm.py — CLI alarm clock
Usage:
    python alarm.py add 07:30 "Morning standup"
    python alarm.py add 14:00
    python alarm.py list
    python alarm.py remove 1
    python alarm.py run
"""

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Protocol, Tuple, List


# ── Data model ────────────────────────────────────────────────────────────────


@dataclass
class Alarm:
    id: int
    hour: int
    minute: int
    label: str
    fired: bool = field(default=False, repr=False)

    @property
    def time_str(self) -> str:
        return f"{self.hour:02d}:{self.minute:02d}"

    def matches_now(self) -> bool:
        now = datetime.now()
        return now.hour == self.hour and now.minute == self.minute


# ── Core logic ───────────────────────────────────────────────────────────────-


class AlarmStorage(Protocol):
    def load(self) -> Tuple[List[dict], int]:
        ...

    def save(self, alarms: List[Alarm], next_id: int) -> None:
        ...


class JSONFileStorage:
    def __init__(self, path: Optional[str] = None) -> None:
        self.path = Path(path) if path is not None else Path.cwd() / "alarm_storage.json"

    def load(self) -> Tuple[List[dict], int]:
        if not self.path.exists():
            return [], 1
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return data.get("alarms", []), int(data.get("next_id", 1))

    def save(self, alarms: List[Alarm], next_id: int) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        state = {
            "next_id": next_id,
            "alarms": [
                {"id": alarm.id, "hour": alarm.hour, "minute": alarm.minute, "label": alarm.label}
                for alarm in alarms
            ],
        }
        temp = self.path.with_name(f"{self.path.name}.tmp")
        temp.write_text(json.dumps(state, indent=2), encoding="utf-8")
        temp.replace(self.path)


class AlarmClock:
    def __init__(self, storage_path: Optional[str] = None, storage: Optional[AlarmStorage] = None) -> None:
        # Allow injection of a storage implementation (Dependency Inversion)
        if storage is not None:
            self._storage: AlarmStorage = storage
        else:
            self._storage = JSONFileStorage(storage_path)

        self._alarms: list[Alarm] = []
        self._next_id: int = 1
        self._load_state()

    # ── Alarm management ─────────────────────────────────────────────────----

    def add(self, time_str: str, label: str = "") -> Alarm:
        """Parse HH:MM and schedule a new alarm."""
        hour, minute = self._parse_time(time_str)
        alarm = Alarm(
            id=self._next_id,
            hour=hour,
            minute=minute,
            label=label or f"Alarm {self._next_id}",
        )
        self._alarms.append(alarm)
        self._next_id += 1
        self._save_state()

        # Warn if time has already passed today
        now = datetime.now()
        if (hour, minute) < (now.hour, now.minute):
            print(f"  ⚠  {time_str} has already passed today — alarm will fire tomorrow.")

        return alarm

    def remove(self, alarm_id: int) -> Optional[Alarm]:
        """Remove alarm by ID. Returns the removed alarm or None."""
        for i, alarm in enumerate(self._alarms):
            if alarm.id == alarm_id:
                removed = self._alarms.pop(i)
                self._save_state()
                return removed
        return None

    def list_alarms(self) -> list[Alarm]:
        # Return alarms sorted ascending by time (hour, minute) and then id
        return sorted(self._alarms, key=lambda a: (a.hour, a.minute, a.id))

    # ── Run loop ─────────────────────────────────────────────────────────----

    def run(self) -> None:
        """Block and fire alarms as their time arrives. Ctrl+C to stop."""
        if not self._alarms:
            print("No alarms set. Use `add` first.")
            return

        print(f"Clock running — {len(self._alarms)} alarm(s) scheduled. Ctrl+C to stop.\n")
        self._print_alarms()

        try:
            last_fired_minute = -1  # prevent double-firing within the same minute

            while True:
                now = datetime.now()

                for alarm in self._alarms:
                    if (
                        alarm.matches_now()
                        and not alarm.fired
                        and now.minute != last_fired_minute
                    ):
                        self._fire(alarm)
                        alarm.fired = True
                        last_fired_minute = now.minute

                # Reset fired flags at minute boundary so each alarm can fire again tomorrow.
                if now.second == 0:
                    for alarm in self._alarms:
                        if not alarm.matches_now():
                            alarm.fired = False
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n\nClock stopped. Goodbye.")

    # ── Helpers ─────────────────────────────────────────────────────────----

    @staticmethod
    def _parse_time(time_str: str) -> tuple[int, int]:
        """Parse 'HH:MM' and return (hour, minute). Raises ValueError on bad input."""
        parts = time_str.strip().split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid time format '{time_str}'. Use HH:MM (e.g. 07:30).")

        try:
            hour, minute = int(parts[0]), int(parts[1])
        except ValueError:
            raise ValueError(f"Time must contain numbers. Got '{time_str}'.")

        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError(f"Time out of range: {time_str}. Hour 0–23, minute 0–59.")

        return hour, minute

    @staticmethod
    def _fire(alarm: Alarm) -> None:
        """Fire an alarm — visual banner + terminal bell."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print("\n" + "=" * 50)
        print(f"  🔔  ALARM  —  {alarm.time_str}")
        print(f"  {alarm.label}")
        print(f"  Fired at {timestamp}")
        print("=" * 50 + "\n")
        # Terminal bell — works without any dependency
        sys.stdout.write("\a\a\a")
        sys.stdout.flush()

    def _print_alarms(self) -> None:
        for alarm in self._alarms:
            status = "✓ fired" if alarm.fired else "pending"
            print(f"  [{alarm.id}]  {alarm.time_str}  —  {alarm.label}  ({status})")
        print()

    def _load_state(self) -> None:
        raw_alarms, next_id = self._storage.load()
        self._alarms = [
            Alarm(id=int(item["id"]), hour=int(item["hour"]), minute=int(item["minute"]), label=str(item.get("label", "")))
            for item in raw_alarms
        ]
        self._next_id = int(next_id) if next_id is not None else (max((alarm.id for alarm in self._alarms), default=0) + 1)

    def _save_state(self) -> None:
        self._storage.save(self._alarms, self._next_id)


# ── CLI ───────────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="alarm",
        description="A simple CLI alarm clock.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python alarm.py add 07:30 "Morning standup"
  python alarm.py add 14:00
  python alarm.py list
  python alarm.py remove 1
  python alarm.py run
        """,
    )
    parser.add_argument(
        "--storage",
        default=None,
        help="Optional path to the local JSON alarm store.",
    )
    sub = parser.add_subparsers(dest="command", metavar="command")
    sub.required = True

    # add
    p_add = sub.add_parser("add", help="Schedule a new alarm")
    p_add.add_argument("time", help="Alarm time in HH:MM format")
    p_add.add_argument("label", nargs="?", default="", help="Optional label")

    # list
    sub.add_parser("list", help="Show all scheduled alarms")

    # remove
    p_remove = sub.add_parser("remove", help="Remove an alarm by ID")
    p_remove.add_argument("id", type=int, help="Alarm ID (from `list`)")

    # run
    sub.add_parser("run", help="Start the clock and fire alarms")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        clock = AlarmClock(args.storage)
    except ValueError as e:
        print(f"  ✗  {e}", file=sys.stderr)
        sys.exit(1)

    if args.command == "add":
        try:
            alarm = clock.add(args.time, args.label)
            print(f"  ✓  Alarm [{alarm.id}] set for {alarm.time_str} — {alarm.label}")
        except ValueError as e:
            print(f"  ✗  {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "list":
        alarms = clock.list_alarms()
        if not alarms:
            print("  No alarms scheduled.")
        else:
            print(f"  {len(alarms)} alarm(s):")
            for alarm in alarms:
                print(f"    [{alarm.id}]  {alarm.time_str}  —  {alarm.label}")

    elif args.command == "remove":
        removed = clock.remove(args.id)
        if removed:
            print(f"  ✓  Removed alarm [{removed.id}] — {removed.time_str} {removed.label}")
        else:
            print(f"  ✗  No alarm with ID {args.id}.", file=sys.stderr)
            sys.exit(1)

    elif args.command == "run":
        clock.run()


if __name__ == "__main__":
    main()
