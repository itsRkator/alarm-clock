# Alarm Clock CLI — Requirement Refinement

## Requirements Decisions (with reasoning)

### What an alarm clock actually needs

1. **Add an alarm** — time + optional label
2. **List alarms** — show what's scheduled
3. **Remove an alarm** — by ID
4. **Run the clock** — blocking loop that fires alarms when time matches

### What to cut (30-minute constraint)

- ❌ Database — the app should stay dependency-free and lightweight
- ❌ Recurring alarms — adds complexity without core value in 30 min
- ❌ Snooze — nice to have, skip
- ❌ Timezone support — assume local system time

### Edge cases worth handling

- Alarm time already passed today → warn the user
- Duplicate alarm at same time → allow (different labels)
- Invalid time format → clear error message
- No alarms set → graceful message when running
- SIGINT (Ctrl+C) → clean shutdown message

### Architecture decision

- `Alarm` dataclass — clean data model
- `AlarmClock` class — owns the alarm list, run loop, and JSON persistence
- `argparse` subcommands: `add`, `list`, `remove`, `run`
- Single file — appropriate for scope; not over-engineered
- Small JSON file in the working directory — enough persistence for a CLI

### Sound strategy

- Primary: system bell via `\a` (works everywhere, no deps)
- Enhanced: `print` with visual banner so it's visible even if bell is muted
- No `playsound` dependency — avoids install issues in a timed exercise

---

## Implementation Plan

1. `Alarm` dataclass with `id`, `time`, `label`, `fired` flag
2. `AlarmClock` with `add()`, `remove()`, `list_alarms()`, `run()`, and JSON load/save
3. `run()` = 1-second polling loop, fires alarm when `HH:MM` matches current time
4. `main()` with argparse subcommands wiring everything together
5. `__main__` guard for clean import behaviour

Total estimated time: 20 minutes code + 5 minutes test + 5 minutes README
