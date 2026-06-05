"""
Tests for alarm.py
Run: python -m pytest test_alarm.py -v
"""

from pathlib import Path

import pytest
from alarm import Alarm, AlarmClock


def make_clock(tmp_path: Path) -> AlarmClock:
    return AlarmClock(storage_path=tmp_path / "alarms.json")


class TestAlarmParsing:
    def test_valid_time(self, tmp_path):
        clock = make_clock(tmp_path)
        alarm = clock.add("07:30", "standup")
        assert alarm.hour == 7
        assert alarm.minute == 30

    def test_midnight(self, tmp_path):
        clock = make_clock(tmp_path)
        alarm = clock.add("00:00")
        assert alarm.hour == 0
        assert alarm.minute == 0

    def test_end_of_day(self, tmp_path):
        clock = make_clock(tmp_path)
        alarm = clock.add("23:59")
        assert alarm.hour == 23
        assert alarm.minute == 59

    def test_invalid_format_no_colon(self, tmp_path):
        clock = make_clock(tmp_path)
        with pytest.raises(ValueError, match="Invalid time format"):
            clock.add("0730")

    def test_invalid_format_letters(self, tmp_path):
        clock = make_clock(tmp_path)
        with pytest.raises(ValueError, match="must contain numbers"):
            clock.add("ab:cd")

    def test_invalid_hour_out_of_range(self, tmp_path):
        clock = make_clock(tmp_path)
        with pytest.raises(ValueError, match="out of range"):
            clock.add("25:00")

    def test_invalid_minute_out_of_range(self, tmp_path):
        clock = make_clock(tmp_path)
        with pytest.raises(ValueError, match="out of range"):
            clock.add("12:60")


class TestAlarmManagement:
    def test_add_assigns_sequential_ids(self, tmp_path):
        clock = make_clock(tmp_path)
        a1 = clock.add("07:00")
        a2 = clock.add("08:00")
        a3 = clock.add("09:00")
        assert a1.id == 1
        assert a2.id == 2
        assert a3.id == 3

    def test_add_default_label(self, tmp_path):
        clock = make_clock(tmp_path)
        alarm = clock.add("07:00")
        assert alarm.label == "Alarm 1"

    def test_add_custom_label(self, tmp_path):
        clock = make_clock(tmp_path)
        alarm = clock.add("07:00", "Morning run")
        assert alarm.label == "Morning run"

    def test_list_empty(self, tmp_path):
        clock = make_clock(tmp_path)
        assert clock.list_alarms() == []

    def test_list_returns_all(self, tmp_path):
        clock = make_clock(tmp_path)
        clock.add("07:00")
        clock.add("08:00")
        alarms = clock.list_alarms()
        assert len(alarms) == 2

    def test_list_is_copy(self, tmp_path):
        clock = make_clock(tmp_path)
        clock.add("07:00")
        result = clock.list_alarms()
        result.clear()
        assert len(clock.list_alarms()) == 1

    def test_remove_existing(self, tmp_path):
        clock = make_clock(tmp_path)
        clock.add("07:00", "Wake up")
        removed = clock.remove(1)
        assert removed is not None
        assert removed.id == 1
        assert len(clock.list_alarms()) == 0

    def test_remove_nonexistent(self, tmp_path):
        clock = make_clock(tmp_path)
        result = clock.remove(99)
        assert result is None

    def test_remove_correct_alarm_when_multiple(self, tmp_path):
        clock = make_clock(tmp_path)
        clock.add("07:00", "First")
        clock.add("08:00", "Second")
        clock.add("09:00", "Third")
        clock.remove(2)
        remaining = clock.list_alarms()
        assert len(remaining) == 2
        assert all(a.id != 2 for a in remaining)

    def test_duplicate_times_allowed(self, tmp_path):
        clock = make_clock(tmp_path)
        clock.add("07:00", "First")
        clock.add("07:00", "Second")
        assert len(clock.list_alarms()) == 2

    def test_state_persists_between_instances(self, tmp_path):
        storage_path = tmp_path / "alarms.json"
        first_clock = AlarmClock(storage_path=storage_path)
        first_clock.add("06:45", "Persisted")

        second_clock = AlarmClock(storage_path=storage_path)
        alarms = second_clock.list_alarms()

        assert len(alarms) == 1
        assert alarms[0].label == "Persisted"
        assert alarms[0].time_str == "06:45"


class TestAlarmModel:
    def test_time_str_formatting(self):
        alarm = Alarm(id=1, hour=7, minute=5, label="test")
        assert alarm.time_str == "07:05"

    def test_time_str_midnight(self):
        alarm = Alarm(id=1, hour=0, minute=0, label="test")
        assert alarm.time_str == "00:00"

    def test_fired_default_false(self):
        alarm = Alarm(id=1, hour=7, minute=0, label="test")
        assert alarm.fired is False
