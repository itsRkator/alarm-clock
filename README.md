# alarm.py — CLI Alarm Clock

A minimal, dependency-free Python CLI alarm clock with local JSON storage.

## Quickstart

```bash
# Add alarms
python alarm.py add 07:30 "Morning standup"
python alarm.py add 14:00

# List alarms
python alarm.py list

# Remove by ID
python alarm.py remove 1

# Start the clock (blocks; Ctrl+C to stop)
python alarm.py run
```

## Design decisions

**Local JSON storage.** Alarms persist in a small `alarm_storage.json` file in
the current working directory. That keeps the CLI usable across separate runs
without introducing a database.

**Single-file.** `alarm.py` contains everything. No over-engineered package
structure for a tool this size.

**Terminal bell + visual banner.** `\a` works without any install. The visual
banner ensures it's visible even if the bell is muted.

**1-second polling.** Simple and correct for minute-granularity alarms.
Not a busy loop — `time.sleep(1)` keeps CPU usage negligible.

**`fired` flag per alarm.** Prevents double-firing within the same minute
if the loop ticks twice during the matching window.

**Persistent IDs.** Alarm IDs are stored with the schedule so `remove` stays
stable after restarting the CLI.

## Running tests

```bash
python -m pytest test_alarm.py -v
```

## AI usage

Used AI to:

- Refine the MVP scope for a 30-minute build
- Identify edge cases (time already passed, double-firing, SIGINT)
- Review the persistence model for a CLI app without a database
- Generate test case names

All architecture decisions and implementation were written manually.
See `DESIGN_AND_IMPLEMENTATION_THOUGH.md` for the full requirement refinement session.
