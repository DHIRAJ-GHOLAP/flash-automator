"""Independent Date Automation Engine for generating iterative date contexts."""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator, Optional, Sequence


class DateRule(str, Enum):
    EVERY_DAY = "EVERY_DAY"
    EVERY_N_DAYS = "EVERY_N_DAYS"
    WEEKDAYS_ONLY = "WEEKDAYS_ONLY"
    SKIP_SUNDAYS = "SKIP_SUNDAYS"
    SKIP_SATURDAYS = "SKIP_SATURDAYS"
    SKIP_WEEKENDS = "SKIP_WEEKENDS"


# Maps human-friendly date format templates to Python strftime directives
FORMAT_MAPPINGS: dict[str, str] = {
    "DD/MM/YYYY": "%d/%m/%Y",
    "DD-MM-YYYY": "%d-%m-%Y",
    "YYYY-MM-DD": "%Y-%m-%d",
    "YYYY/MM/DD": "%Y/%m/%d",
    "MM/DD/YYYY": "%m/%d/%Y",
    "MM-DD-YYYY": "%m-%d-%Y",
    "DD.MM.YYYY": "%d.%m.%Y",
    "YYYYMMDD": "%Y%m%d",
    "DDMMYYYY": "%d%m%Y",
}


def normalize_format(fmt: str) -> str:
    """Translate UI friendly formats (e.g. DD/MM/YYYY) to strftime format (%d/%m/%Y)."""
    if fmt in FORMAT_MAPPINGS:
        return FORMAT_MAPPINGS[fmt]
    # Replace individual tokens if mixed
    res = fmt
    res = res.replace("YYYY", "%Y").replace("YY", "%y")
    res = res.replace("MM", "%m").replace("DD", "%d")
    return res


@dataclass
class DateEngineConfig:
    start_date: datetime.date
    end_date: datetime.date
    date_format: str = "DD/MM/YYYY"
    step_days: int = 1
    rule: DateRule = DateRule.EVERY_DAY
    excluded_dates: set[datetime.date] = field(default_factory=set)

    def is_date_allowed(self, d: datetime.date) -> bool:
        """Check if date meets inclusion rules and is not in excluded list."""
        if d in self.excluded_dates:
            return False

        weekday = d.weekday()  # Monday is 0, Sunday is 6

        if self.rule == DateRule.WEEKDAYS_ONLY:
            return weekday < 5  # Mon-Fri
        elif self.rule == DateRule.SKIP_SUNDAYS:
            return weekday != 6
        elif self.rule == DateRule.SKIP_SATURDAYS:
            return weekday != 5
        elif self.rule == DateRule.SKIP_WEEKENDS:
            return weekday < 5

        return True


class DateEngine:
    """
    Independent Date Generation Engine.
    Produces sequences of dates and builds full variable context dictionaries
    for each iteration.
    """

    def __init__(self, config: DateEngineConfig) -> None:
        self.config = config

    def generate_dates(self) -> list[datetime.date]:
        """Generate all dates satisfying configuration rules."""
        cfg = self.config
        if cfg.start_date > cfg.end_date:
            return []

        step = max(1, cfg.step_days)
        current = cfg.start_date
        dates: list[datetime.date] = []

        while current <= cfg.end_date:
            if cfg.is_date_allowed(current):
                dates.append(current)
            current += datetime.timedelta(days=step)

        return dates

    def format_date(self, d: datetime.date) -> str:
        """Format a date using the configured format template."""
        fmt_code = normalize_format(self.config.date_format)
        return d.strftime(fmt_code)

    def build_context_for_date(
        self,
        d: datetime.date,
        iteration_index: int = 1,
        total_iterations: Optional[int] = None,
    ) -> dict[str, str]:
        """
        Build the dictionary of variable substitutions for a specific date iteration.
        """
        formatted_date = self.format_date(d)
        total_str = str(total_iterations) if total_iterations is not None else ""

        return {
            "STATEMENT_DATE": formatted_date,
            "DATE": formatted_date,
            "DAY": f"{d.day:02d}",
            "MONTH": f"{d.month:02d}",
            "YEAR": str(d.year),
            "DATE_DD": f"{d.day:02d}",
            "DATE_MM": f"{d.month:02d}",
            "DATE_YYYY": str(d.year),
            "DATE_YY": f"{d.year % 100:02d}",
            "DATE_DDMMYYYY": f"{d.day:02d}{d.month:02d}{d.year}",
            "DATE_YYYYMMDD": f"{d.year}{d.month:02d}{d.day:02d}",
            "DATE_RAW": f"{d.day:02d}{d.month:02d}{d.year}",
            "DATE_DIGITS": f"{d.day:02d}{d.month:02d}{d.year}",
            "MONTH_NAME": d.strftime("%B"),
            "MONTH_SHORT": d.strftime("%b"),
            "DAY_NAME": d.strftime("%A"),
            "DAY_SHORT": d.strftime("%a"),
            "COUNTER": str(iteration_index),
            "ITERATION": str(iteration_index),
            "TOTAL_ITERATIONS": total_str,
        }

    def iter_contexts(self) -> Iterator[dict[str, str]]:
        """Yield a variable context dictionary for each generated date in sequence."""
        dates = self.generate_dates()
        total = len(dates)
        for idx, d in enumerate(dates, start=1):
            yield self.build_context_for_date(d, iteration_index=idx, total_iterations=total)
