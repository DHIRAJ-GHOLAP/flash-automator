"""Unit tests for the independent DateEngine."""
import datetime
import pytest
from flash_automator.core.date_engine import (
    DateEngine,
    DateEngineConfig,
    DateRule,
)


def test_october_31_days_generation():
    start = datetime.date(2026, 10, 1)
    end = datetime.date(2026, 10, 31)
    cfg = DateEngineConfig(
        start_date=start,
        end_date=end,
        date_format="DD/MM/YYYY",
        rule=DateRule.EVERY_DAY,
    )
    engine = DateEngine(cfg)
    dates = engine.generate_dates()

    assert len(dates) == 31
    assert dates[0] == datetime.date(2026, 10, 1)
    assert dates[-1] == datetime.date(2026, 10, 31)


def test_date_engine_skip_sundays():
    start = datetime.date(2026, 10, 1)  # Thursday
    end = datetime.date(2026, 10, 31)    # Saturday
    cfg = DateEngineConfig(
        start_date=start,
        end_date=end,
        date_format="DD/MM/YYYY",
        rule=DateRule.SKIP_SUNDAYS,
    )
    engine = DateEngine(cfg)
    dates = engine.generate_dates()

    # In October 2026, Sundays are Oct 4, 11, 18, 25 (4 Sundays)
    assert len(dates) == 31 - 4
    for d in dates:
        assert d.weekday() != 6  # No Sunday


def test_date_engine_weekdays_only():
    start = datetime.date(2026, 10, 1)
    end = datetime.date(2026, 10, 7)  # 1 week
    cfg = DateEngineConfig(
        start_date=start,
        end_date=end,
        rule=DateRule.WEEKDAYS_ONLY,
    )
    engine = DateEngine(cfg)
    dates = engine.generate_dates()

    # Oct 1 (Thu), Oct 2 (Fri), Oct 5 (Mon), Oct 6 (Tue), Oct 7 (Wed) -> 5 weekdays
    assert len(dates) == 5
    for d in dates:
        assert d.weekday() < 5


def test_date_engine_custom_excluded_dates():
    start = datetime.date(2026, 10, 1)
    end = datetime.date(2026, 10, 5)
    holiday = datetime.date(2026, 10, 2)  # Gandhi Jayanti
    cfg = DateEngineConfig(
        start_date=start,
        end_date=end,
        excluded_dates={holiday},
    )
    engine = DateEngine(cfg)
    dates = engine.generate_dates()
    assert holiday not in dates
    assert len(dates) == 4


def test_date_context_dictionary_fields():
    d = datetime.date(2026, 10, 8)
    cfg = DateEngineConfig(
        start_date=d,
        end_date=d,
        date_format="DD/MM/YYYY",
    )
    engine = DateEngine(cfg)
    context = engine.build_context_for_date(d, iteration_index=8, total_iterations=31)

    assert context["STATEMENT_DATE"] == "08/10/2026"
    assert context["DATE_DD"] == "08"
    assert context["DATE_MM"] == "10"
    assert context["DATE_YYYY"] == "2026"
    assert context["DAY"] == "08"
    assert context["MONTH"] == "10"
    assert context["YEAR"] == "2026"
    assert context["DATE_YY"] == "26"
    assert context["MONTH_NAME"] == "October"
    assert context["DAY_NAME"] == "Thursday"
    assert context["ITERATION"] == "8"
    assert context["COUNTER"] == "8"
    assert context["TOTAL_ITERATIONS"] == "31"


def test_step_days():
    start = datetime.date(2026, 10, 1)
    end = datetime.date(2026, 10, 10)
    cfg = DateEngineConfig(
        start_date=start,
        end_date=end,
        step_days=2,
    )
    engine = DateEngine(cfg)
    dates = engine.generate_dates()
    # 1, 3, 5, 7, 9 -> 5 dates
    assert len(dates) == 5
